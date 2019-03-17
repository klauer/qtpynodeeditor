import math
from qtpy.QtCore import QPointF, QRectF, Qt
from qtpy.QtGui import QFontMetrics, QLinearGradient, QPainter, QPen


from .base import NodeBase, FlowSceneBase
from .enums import NodeValidationState, PortType, ConnectionPolicy
from .node_data import NodeDataModel
from .node_geometry import NodeGeometry
from .node_graphics_object import NodeGraphicsObject
from .node_state import NodeState
from .style import StyleCollection


class NodePainterDelegate:
    def paint(self, painter: QPainter, geom: NodeGeometry, model: NodeDataModel):
        """
        paint

        Parameters
        ----------
        painter : QPainter
        geom : NodeGeometry
        model : NodeDataModel
        """
        ...


class NodePainter:
    @staticmethod
    def paint(painter: QPainter, node: NodeBase, scene: FlowSceneBase):
        """
        paint

        Parameters
        ----------
        painter : QPainter
        node : Node
        scene : FlowScene
        """
        geom = node.node_geometry()
        state = node.node_state()
        graphics_object = node.node_graphics_object()
        geom.recalculate_size(painter.font())

        model = node.node_data_model()
        NodePainter.draw_node_rect(painter, geom, model, graphics_object)
        NodePainter.draw_connection_points(painter, geom, state, model, scene)
        NodePainter.draw_filled_connection_points(painter, geom, state, model)
        NodePainter.draw_model_name(painter, geom, state, model)
        NodePainter.draw_entry_labels(painter, geom, state, model)
        NodePainter.draw_resize_rect(painter, geom, model)
        NodePainter.draw_validation_rect(painter, geom, model, graphics_object)

        # call custom painter
        painter_delegate = model.painter_delegate()
        if painter_delegate:
            painter_delegate.paint(painter, geom, model)

    @staticmethod
    def draw_node_rect(painter: QPainter, geom: NodeGeometry, model:
                       NodeDataModel, graphics_object: NodeGraphicsObject):
        """
        draw_node_rect

        Parameters
        ----------
        painter : QPainter
        geom : NodeGeometry
        model : NodeDataModel
        graphics_object : NodeGraphicsObject
        """
        node_style = model.node_style()
        color = (node_style.selected_boundary_color
                 if graphics_object.isSelected()
                 else node_style.normal_boundary_color
                 )
        p = QPen(color, (node_style.hovered_pen_width
                         if geom.hovered()
                         else node_style.pen_width))
        painter.setPen(p)

        gradient = QLinearGradient(QPointF(0.0, 0.0), QPointF(2.0, geom.height()))
        gradient.setColorAt(0.0, node_style.gradient_color0)
        gradient.setColorAt(0.03, node_style.gradient_color1)
        gradient.setColorAt(0.97, node_style.gradient_color2)
        gradient.setColorAt(1.0, node_style.gradient_color3)
        painter.setBrush(gradient)

        diam = node_style.connection_point_diameter
        boundary = QRectF(-diam, -diam, 2.0 * diam + geom.width(), 2.0 * diam + geom.height())
        radius = 3.0
        painter.drawRoundedRect(boundary, radius, radius)

    @staticmethod
    def draw_model_name(painter: QPainter, geom: NodeGeometry,
                        state: NodeState,
                        model: NodeDataModel):
        """
        draw_model_name

        Parameters
        ----------
        painter : QPainter
        geom : NodeGeometry
        state : NodeState
        model : NodeDataModel
        """
        node_style = model.node_style()
        if not model.caption_visible():
            return
        name = model.caption()
        f = painter.font()
        f.setBold(True)
        metrics = QFontMetrics(f)
        rect = metrics.boundingRect(name)
        position = QPointF((geom.width() - rect.width()) / 2.0,
                           (geom.spacing() + geom.entry_height()) / 3.0)
        painter.setFont(f)
        painter.setPen(node_style.font_color)
        painter.drawText(position, name)
        f.setBold(False)
        painter.setFont(f)

    @staticmethod
    def draw_entry_labels(painter: QPainter, geom: NodeGeometry, state: NodeState, model: NodeDataModel):
        """
        draw_entry_labels

        Parameters
        ----------
        painter : QPainter
        geom : NodeGeometry
        state : NodeState
        model : NodeDataModel
        """
        metrics = painter.fontMetrics()
        for port_type in (PortType.Out, PortType.In):
            node_style = model.node_style()

            for i, entries in enumerate(state.get_entries(port_type)):
                p = geom.port_scene_position(i, port_type)
                if not entries:
                    painter.setPen(node_style.font_color_faded)
                else:
                    painter.setPen(node_style.font_color)

                if model.port_caption_visible(port_type, i):
                    s = model.port_caption(port_type, i)
                else:
                    s = model.data_type(port_type, i).name

                rect = metrics.boundingRect(s)
                p.setY(p.y() + rect.height() / 4.0)
                if port_type == PortType.In:
                    p.setX(5.0)
                elif port_type == PortType.Out:
                    p.setX(geom.width() - 5.0 - rect.width())

                painter.drawText(p, s)

    @staticmethod
    def draw_connection_points(
        painter: QPainter, geom: NodeGeometry, state: NodeState, model: NodeDataModel, scene: FlowSceneBase
    ):
        """
        draw_connection_points

        Parameters
        ----------
        painter : QPainter
        geom : NodeGeometry
        state : NodeState
        model : NodeDataModel
        scene : FlowScene
        """
        node_style = model.node_style()
        connection_style = StyleCollection.connection_style()
        diameter = node_style.connection_point_diameter
        reduced_diameter = diameter * 0.6
        for port_type in (PortType.Out, PortType.In):
            for i, entries in enumerate(state.get_entries(port_type)):
                p = geom.port_scene_position(i, port_type)
                data_type = model.data_type(port_type, i)
                can_connect = (
                    not entries or
                    (port_type == PortType.Out and
                     model.port_out_connection_policy(i) == ConnectionPolicy.Many
                     )
                )

                r = 1.0
                if state.is_reacting() and can_connect and port_type == state.reacting_port_type():
                    diff = geom.dragging_pos() - p
                    dist = math.sqrt(QPointF.dotProduct(diff, diff))

                    registry = scene.registry()
                    if port_type == PortType.In:
                        type_convertable = (
                            registry.get_type_converter(state.reacting_data_type(), data_type) is not None
                        )
                    else:
                        type_convertable = (
                            registry.get_type_converter(data_type, state.reacting_data_type()) is not None
                        )

                    if state.reacting_data_type().id == data_type.id or type_convertable:
                        thres = 40.0
                        r = ((2.0 - dist / thres)
                             if dist < thres
                             else 1.0)
                    else:
                        thres = 80.0
                        r = ((dist / thres)
                             if dist < thres
                             else 1.0)

                if connection_style.use_data_defined_colors():
                    painter.setBrush(connection_style.normal_color(data_type.id))
                else:
                    painter.setBrush(node_style.connection_point_color)

                painter.drawEllipse(p, reduced_diameter * r, reduced_diameter * r)

    @staticmethod
    def draw_filled_connection_points(painter: QPainter, geom: NodeGeometry, state: NodeState, model: NodeDataModel):
        """
        draw_filled_connection_points

        Parameters
        ----------
        painter : QPainter
        geom : NodeGeometry
        state : NodeState
        model : NodeDataModel
        """
        node_style = model.node_style()
        connection_style = StyleCollection.connection_style()
        diameter = node_style.connection_point_diameter
        for port_type in (PortType.Out, PortType.In):
            for i, entries in enumerate(state.get_entries(port_type)):
                if not entries:
                    continue

                p = geom.port_scene_position(i, port_type)
                data_type = model.data_type(port_type, i)
                if connection_style.use_data_defined_colors():
                    c = connection_style.normal_color(data_type.id)
                else:
                    c = node_style.filled_connection_point_color
                painter.setPen(c)
                painter.setBrush(c)
                painter.drawEllipse(p, diameter * 0.4, diameter * 0.4)

    @staticmethod
    def draw_resize_rect(painter: QPainter, geom: NodeGeometry, model: NodeDataModel):
        """
        draw_resize_rect

        Parameters
        ----------
        painter : QPainter
        geom : NodeGeometry
        model : NodeDataModel
        """
        if model.resizable():
            painter.setBrush(Qt.gray)
            painter.drawEllipse(geom.resize_rect())

    @staticmethod
    def draw_validation_rect(
        painter: QPainter, geom: NodeGeometry, model: NodeDataModel, graphics_object: NodeGraphicsObject
    ):
        """
        draw_validation_rect

        Parameters
        ----------
        painter : QPainter
        geom : NodeGeometry
        model : NodeDataModel
        graphics_object : NodeGraphicsObject
        """
        model_validation_state = model.validation_state()
        if model_validation_state == NodeValidationState.Valid:
            return

        node_style = model.node_style()
        color = node_style.selected_boundary_color if graphics_object.isSelected() else node_style.normal_boundary_color

        if geom.hovered():
            p = QPen(color, node_style.hovered_pen_width)
        else:
            p = QPen(color, node_style.pen_width)

        painter.setPen(p)

        # Drawing the validation message background
        if model_validation_state == NodeValidationState.Error:
            painter.setBrush(node_style.error_color)
        else:
            painter.setBrush(node_style.warning_color)

        radius = 3.0
        diam = node_style.connection_point_diameter
        boundary = QRectF(
            -diam,
            -diam + geom.height() - geom.validation_height(),
            2.0 * diam + geom.width(),
            2.0 * diam + geom.validation_height(),
        )
        painter.drawRoundedRect(boundary, radius, radius)
        painter.setBrush(Qt.gray)

        # Drawing the validation message itself
        error_msg = model.validation_message()
        f = painter.font()
        metrics = QFontMetrics(f)
        rect = metrics.boundingRect(error_msg)
        position = QPointF(
            (geom.width() - rect.width()) / 2.0,
            geom.height() - (geom.validation_height() - diam) / 2.0
        )
        painter.setFont(f)
        painter.setPen(node_style.font_color)
        painter.drawText(position, error_msg)
