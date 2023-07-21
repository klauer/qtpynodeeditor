import logging
import math

from qtpy.QtCore import QLineF, QPoint, QRectF, Qt
from qtpy.QtGui import (QContextMenuEvent, QKeyEvent, QKeySequence,
                        QMouseEvent, QPainter, QPen, QShowEvent, QWheelEvent)
from qtpy.QtWidgets import (QAction, QGraphicsView, QLineEdit, QMenu,
                            QTreeWidget, QTreeWidgetItem, QWidgetAction)

from .connection_graphics_object import ConnectionGraphicsObject
from .flow_scene import FlowScene
from .node_graphics_object import NodeGraphicsObject

logger = logging.getLogger(__name__)


class FlowView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(parent=parent)

        self._clear_selection_action = None
        self._delete_selection_action = None
        self._scene = None
        self._click_pos = None

        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setRenderHint(QPainter.Antialiasing)

        # setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        # setViewportUpdateMode(QGraphicsView.MinimalViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

        self.setCacheMode(QGraphicsView.CacheBackground)
        # setViewport(new QGLWidget(QGLFormat(QGL.SampleBuffers)))
        if scene is not None:
            self.setScene(scene)

        self._style = self._scene.style_collection
        self.setBackgroundBrush(self._style.flow_view.background_color)

    def clear_selection_action(self) -> QAction:
        """
        Clear selection action

        Returns
        -------
        value : QAction
        """
        return self._clear_selection_action

    def delete_selection_action(self) -> QAction:
        """
        Delete selection action

        Returns
        -------
        value : QAction
        """
        return self._delete_selection_action

    def setScene(self, scene: FlowScene):
        """
        setScene

        Parameters
        ----------
        scene : FlowScene
        """
        self._scene = scene
        super().setScene(self._scene)

        # setup actions
        del self._clear_selection_action
        self._clear_selection_action = QAction("Clear Selection", self)
        self._clear_selection_action.setShortcut(QKeySequence.Cancel)
        self._clear_selection_action.triggered.connect(self._scene.clearSelection)

        self.addAction(self._clear_selection_action)
        del self._delete_selection_action
        self._delete_selection_action = QAction("Delete Selection", self)
        self._delete_selection_action.setShortcut(QKeySequence.Backspace)
        self._delete_selection_action.setShortcut(QKeySequence.Delete)
        self._delete_selection_action.triggered.connect(self.delete_selected)
        self.addAction(self._delete_selection_action)

    def scale_up(self):
        step = 1.2
        factor = step ** 1.0
        t = self.transform()
        if t.m11() <= 2.0:
            self.scale(factor, factor)

    def scale_down(self):
        step = 1.2
        factor = step ** -1.0
        self.scale(factor, factor)

    def delete_selected(self):
        # Delete the selected connections first, ensuring that they won't be
        # automatically deleted when selected nodes are deleted (deleting a node
        # deletes some connections as well)
        for item in self._scene.selectedItems():
            if isinstance(item, ConnectionGraphicsObject):
                self._scene.delete_connection(item.connection)

        if not self._scene.allow_node_deletion:
            return

        # Delete the nodes; self will delete many of the connections.
        # Selected connections were already deleted prior to self loop, otherwise
        # qgraphicsitem_cast<NodeGraphicsObject*>(item) could be a use-after-free
        # when a selected connection is deleted by deleting the node.
        for item in self._scene.selectedItems():
            if isinstance(item, NodeGraphicsObject):
                self._scene.remove_node(item.node)

    def generate_context_menu(self, pos: QPoint):
        """
        Generate a context menu for contextMenuEvent

        Parameters
        ----------
        pos : QPoint
            The point where the context menu was requested
        """
        model_menu = QMenu()
        skip_text = "skip me"

        # Add filterbox to the context menu
        txt_box = QLineEdit(model_menu)
        txt_box.setPlaceholderText("Filter")
        txt_box.setClearButtonEnabled(True)
        txt_box_action = QWidgetAction(model_menu)
        txt_box_action.setDefaultWidget(txt_box)
        model_menu.addAction(txt_box_action)

        # Add result treeview to the context menu
        tree_view = QTreeWidget(model_menu)
        tree_view.header().close()
        tree_view_action = QWidgetAction(model_menu)
        tree_view_action.setDefaultWidget(tree_view)
        model_menu.addAction(tree_view_action)

        top_level_items = {}
        for cat in self._scene.registry.categories():
            item = QTreeWidgetItem(tree_view)
            item.setText(0, cat)
            item.setData(0, Qt.UserRole, skip_text)
            top_level_items[cat] = item

        registry = self._scene.registry
        for model, category in registry.registered_models_category_association().items():
            self.parent = top_level_items[category]
            item = QTreeWidgetItem(self.parent)
            item.setText(0, model)
            item.setData(0, Qt.UserRole, model)

        tree_view.expandAll()

        def click_handler(item):
            model_name = item.data(0, Qt.UserRole)
            if model_name == skip_text:
                return

            try:
                model, _ = self._scene.registry.get_model_by_name(model_name)
            except ValueError:
                logger.error("Model not found: %s", model_name)
            else:
                node = self._scene.create_node(model)
                pos_view = self.mapToScene(pos)
                node.graphics_object.setPos(pos_view)
                self._scene.node_placed.emit(node)

            model_menu.close()

        tree_view.itemClicked.connect(click_handler)

        # Setup filtering
        def filter_handler(text):
            for name, top_lvl_item in top_level_items.items():
                for i in range(top_lvl_item.childCount()):
                    child = top_lvl_item.child(i)
                    model_name = child.data(0, Qt.UserRole)
                    child.setHidden(text not in model_name)

        txt_box.textChanged.connect(filter_handler)

        # make sure the text box gets focus so the user doesn't have to click on it
        txt_box.setFocus()
        return model_menu

    def contextMenuEvent(self, event: QContextMenuEvent):
        """
        contextMenuEvent

        Parameters
        ----------
        event : QContextMenuEvent
        """
        if self.itemAt(event.pos()):
            super().contextMenuEvent(event)
            return
        elif not self._scene.allow_node_creation:
            return

        menu = self.generate_context_menu(event.pos())
        menu.exec_(event.globalPos())

    def wheelEvent(self, event: QWheelEvent):
        """
        wheelEvent

        Parameters
        ----------
        event : QWheelEvent
        """
        delta = event.angleDelta()
        if delta.y() == 0:
            event.ignore()
            return

        d = delta.y() / abs(delta.y())
        if d > 0.0:
            self.scale_up()
        else:
            self.scale_down()

    def keyPressEvent(self, event: QKeyEvent):
        """
        keyPressEvent

        Parameters
        ----------
        event : QKeyEvent
        """
        if event.key() == Qt.Key_Shift:
            self.setDragMode(QGraphicsView.RubberBandDrag)

        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent):
        """
        keyReleaseEvent

        Parameters
        ----------
        event : QKeyEvent
        """
        if event.key() == Qt.Key_Shift:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
        super().keyReleaseEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        """
        mousePressEvent

        Parameters
        ----------
        event : QMouseEvent
        """
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            self._click_pos = self.mapToScene(event.pos())

    def mouseMoveEvent(self, event: QMouseEvent):
        """
        mouseMoveEvent

        Parameters
        ----------
        event : QMouseEvent
        """
        super().mouseMoveEvent(event)
        if self._scene.mouseGrabberItem() is None and event.buttons() == Qt.LeftButton:
            # Make sure shift is not being pressed
            if not (event.modifiers() & Qt.ShiftModifier):
                difference = self._click_pos - self.mapToScene(event.pos())
                self.setSceneRect(self.sceneRect().translated(difference.x(), difference.y()))

    def drawBackground(self, painter: QPainter, r: QRectF):
        """
        drawBackground

        Parameters
        ----------
        painter : QPainter
        r : QRectF
        """
        super().drawBackground(painter, r)

        def draw_grid(grid_step):
            window_rect = self.rect()
            tl = self.mapToScene(window_rect.topLeft())
            br = self.mapToScene(window_rect.bottomRight())
            left = math.floor(tl.x() / grid_step - 0.5)
            right = math.floor(br.x() / grid_step + 1.0)
            bottom = math.floor(tl.y() / grid_step - 0.5)
            top = math.floor(br.y() / grid_step + 1.0)

            # vertical lines
            lines = [
                QLineF(xi * grid_step, bottom * grid_step, xi * grid_step, top * grid_step)
                for xi in range(int(left), int(right) + 1)
            ]

            # horizontal lines
            lines.extend(
                [QLineF(left * grid_step, yi * grid_step, right * grid_step, yi * grid_step)
                 for yi in range(int(bottom), int(top) + 1)
                 ]
            )

            painter.drawLines(lines)

        style = self._style.flow_view
        # brush = self.backgroundBrush()
        pfine = QPen(style.fine_grid_color, 1.0)
        painter.setPen(pfine)
        draw_grid(15)
        p = QPen(style.coarse_grid_color, 1.0)
        painter.setPen(p)
        draw_grid(150)

    def showEvent(self, event: QShowEvent):
        """
        showEvent

        Parameters
        ----------
        event : QShowEvent
        """
        self._scene.setSceneRect(QRectF(self.rect()))
        super().showEvent(event)

    @property
    def scene(self) -> FlowScene:
        """
        Scene

        Returns
        -------
        value : FlowScene
        """
        return self._scene
