import typing

from qtpy.QtCore import QRectF
from qtpy.QtGui import QPainter, QPainterPath
from qtpy.QtWidgets import (QGraphicsBlurEffect, QGraphicsItem,
                            QGraphicsObject, QGraphicsSceneHoverEvent,
                            QGraphicsSceneMouseEvent, QStyleOptionGraphicsItem,
                            QWidget)

from .connection_painter import ConnectionPainter
from .node_connection_interaction import NodeConnectionInteraction
from .port import PortType, opposite_port

if typing.TYPE_CHECKING:
    from .connection import Connection  # noqa


debug_drawing = False


class ConnectionGraphicsObject(QGraphicsObject):
    def __init__(self, scene, connection):
        '''
        connection_graphics_object

        Parameters
        ----------
        scene : FlowScene
        connection : Connection
        '''
        super().__init__()
        self._scene = scene
        self._connection = connection
        self._geometry = connection.geometry
        self._style = connection.style.connection

        self._scene.addItem(self)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)

        # self.add_graphics_effect()
        self.setZValue(-1.0)

    def _cleanup(self):
        if self._scene is not None:
            self._scene.removeItem(self)
            self._scene = None

    @property
    def connection(self) -> 'Connection':
        """
        Connection

        Returns
        -------
        value : Connection
        """
        return self._connection

    def boundingRect(self) -> QRectF:
        """
        boundingRect

        Returns
        -------
        value : QRectF
        """
        return self._geometry.bounding_rect

    def shape(self) -> QPainterPath:
        """
        Shape

        Returns
        -------
        value : QPainterPath
        """
        # TODO DEBUG_DRAWING
        if debug_drawing:
            path = QPainterPath()
            path.addRect(self.boundingRect())
            return path

        return ConnectionPainter.get_painter_stroke(self._geometry)

    def set_geometry_changed(self):
        self.prepareGeometryChange()

    def move(self):
        """
        Updates the position of both ends
        """
        conn = self._connection
        cgo = conn.graphics_object

        for port_type in (PortType.input, PortType.output):
            node = self._connection.get_node(port_type)
            if node is None:
                continue

            node_graphics = node.graphics_object
            node_geom = node.geometry
            scene_pos = node_geom.port_scene_position(
                port_type, self._connection.get_port_index(port_type),
                node_graphics.sceneTransform()
            )

            inverted, invertible = self.sceneTransform().inverted()
            if invertible:
                connection_pos = inverted.map(scene_pos)
                self._geometry.set_end_point(port_type, connection_pos)

            cgo.set_geometry_changed()
            cgo.update()

    def lock(self, locked: bool):
        """
        Lock

        Parameters
        ----------
        locked : bool
        """
        self.setFlag(QGraphicsItem.ItemIsMovable, not locked)
        self.setFlag(QGraphicsItem.ItemIsFocusable, not locked)
        self.setFlag(QGraphicsItem.ItemIsSelectable, not locked)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget):
        """
        Paint

        Parameters
        ----------
        painter : QPainter
        option : QStyleOptionGraphicsItem
        widget : QWidget
        """
        painter.setClipRect(option.exposedRect)
        ConnectionPainter.paint(painter, self._connection, self._style)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        """
        mousePressEvent

        Parameters
        ----------
        event : QGraphicsSceneMouseEvent
        """
        super().mousePressEvent(event)
        # event.ignore()

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        """
        mouseMoveEvent

        Parameters
        ----------
        event : QGraphicsSceneMouseEvent
        """
        self.prepareGeometryChange()
        # view = event.widget()
        # TODO/BUG: widget is returning QWidget(), not QGraphicsView...
        view = self._scene.views()[0]

        node = self._scene.locate_node_at(event.scenePos(), view.transform())
        self._connection.interact_with_node(node)
        state_required = self._connection.required_port
        if node:
            node.react_to_possible_connection(
                state_required,
                self._connection.data_type(opposite_port(state_required)),
                event.scenePos()
            )

        # -------------------
        offset = event.pos() - event.lastPos()
        required_port = self._connection.required_port
        if required_port != PortType.none:
            self._geometry.move_end_point(required_port, offset)

        # -------------------
        self.update()
        event.accept()

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        """
        mouseReleaseEvent

        Parameters
        ----------
        event : QGraphicsSceneMouseEvent
        """
        self.ungrabMouse()
        event.accept()
        node = self._scene.locate_node_at(event.scenePos(), self._scene.views()[0].transform())

        interaction = NodeConnectionInteraction(node, self._connection, self._scene)
        if node and interaction.try_connect():
            node.reset_reaction_to_connection()
            self._scene.connection_created.emit(self._connection)

        if self._connection.requires_port:
            self._scene.delete_connection(self._connection)

    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent):
        """
        hoverEnterEvent

        Parameters
        ----------
        event : QGraphicsSceneHoverEvent
        """
        self._geometry.hovered = True
        self.update()
        self._scene.connection_hovered.emit(self.connection, event.screenPos())
        event.accept()

    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent):
        """
        hoverLeaveEvent

        Parameters
        ----------
        event : QGraphicsSceneHoverEvent
        """
        self._geometry.hovered = False
        self.update()
        self._scene.connection_hover_left.emit(self.connection)
        event.accept()

    def add_graphics_effect(self):
        effect = QGraphicsBlurEffect()
        effect.setBlurRadius(5)
        self.setGraphicsEffect(effect)

        # effect = QGraphicsDropShadowEffect()
        # effect = ConnectionBlurEffect(self)
        # effect.setOffset(4, 4)
        # effect.setColor(QColor(Qt.gray).darker(800))
