import math
import typing

from qtpy.QtCore import QPointF, QRectF, Qt
from qtpy.QtGui import QFontMetrics, QLinearGradient, QPainter, QPen

from .enums import NodeValidationState, PortType
from .node_data import NodeDataModel
from .node_geometry import NodeGeometry
from .node_graphics_object import NodeGraphicsObject
from .node_state import NodeState
from .style import ConnectionStyle, NodeStyle

if typing.TYPE_CHECKING:
    from .connection import Connection  # noqa
    from .flow_scene import FlowScene  # noqa
    from .node import Node  # noqa


class NodePainterDelegate:
    def paint(self, painter: QPainter, geom: NodeGeometry, model: NodeDataModel):
        """
        Paint

        Parameters
        ----------
        painter : QPainter
        geom : NodeGeometry
        model : NodeDataModel
        """
        ...


class NodePainter:
    @staticmethod
    def paint(painter: QPainter, node: 'Node', scene: 'FlowScene',
              node_style: NodeStyle, connection_style: ConnectionStyle):
        """
        Paint

        Parameters
        ----------
        painter : QPainter
        node : Node
        scene : FlowScene
        node_style : NodeStyle
        connection_style : ConnectionStyle
        """
        geom = node.geometry
        state = node.state
        graphics_object = node.graphics_object

        if graphics_object is None:
            # On CI, we might not have a graphics object
            return

        geom.recalculate_size(painter.font())

        model = node.model
        NodePainter.draw_node_rect(painter, geom, model, graphics_object,
                                   node_style)
        NodePainter.draw_connection_points(painter, geom, state, model, scene,
                                           node_style, connection_style)
        NodePainter.draw_filled_connection_points(painter, geom, state, model,
                                                  node_style, connection_style
                                                  )
        NodePainter.draw_model_name(painter, geom, state, model, node_style)
        NodePainter.draw_entry_labels(painter, geom, state, model, node_style)
        NodePainter.draw_resize_rect(painter, geom, model)
        NodePainter.draw_validation_rect(painter, geom, model, graphics_object,
                                         node_style)

        # call custom painter
        painter_delegate = model.painter_delegate()
        if painter_delegate:
            painter_delegate.paint(painter, geom, model)

    @staticmethod
    def draw_node_rect(painter: QPainter, geom: NodeGeometry,
                       model: NodeDataModel,
                       graphics_object: NodeGraphicsObject,
                       node_style: NodeStyle):
        """
        Draw node rect

        Parameters
        ----------
        painter : QPainter
        geom : NodeGeometry
        model : NodeDataModel
        graphics_object : NodeGraphicsObject
        node_style : NodeStyle
        """
        color = (node_style.selected_boundary_color
                 if graphics_object.isSelected()
                 else node_style.normal_boundary_color
                 )
        p = QPen(color, (node_style.hovered_pen_width
                         if geom.hovered
                         else node_style.pen_width))
        painter.setPen(p)

        gradient = QLinearGradient(QPointF(0.0, 0.0),
                                   QPointF(2.0, geom.height))
        for at_, color in node_style.gradient_colors:
            gradient.setColorAt(at_, color)
        painter.setBrush(gradient)

        diam = node_style.connection_point_diameter
        boundary = QRectF(-diam,
                          -diam,
                          2.0 * diam + geom.width,
                          2.0 * diam + geom.height)
        radius = 3.0
        painter.drawRoundedRect(boundary, radius, radius)

    @staticmethod
    def draw_model_name(painter: QPainter, geom: NodeGeometry,
                        state: NodeState,
                        model: NodeDataModel,
                        node_style: NodeStyle):
        """
        Draw model name

        Parameters
        ----------
        painter : QPainter
        geom : NodeGeometry
        state : NodeState
        model : NodeDataModel
        """
        if not model.caption_visible:
            return
        name = model.caption
        f = painter.font()
        f.setBold(True)
        metrics = QFontMetrics(f)
        rect = metrics.boundingRect(name)
        position = QPointF((geom.width - rect.width()) / 2.0,
                           (geom.spacing + geom.entry_height) / 3.0)
        painter.setFont(f)
        painter.setPen(node_style.font_color)
        painter.drawText(position, name)
        f.setBold(False)
        painter.setFont(f)

    @staticmethod
    def draw_entry_labels(painter: QPainter, geom: NodeGeometry,
                          state: NodeState, model: NodeDataModel,
                          node_style: NodeStyle):
        """
        Draw entry labels

        Parameters
        ----------
        painter : QPainter
        geom : NodeGeometry
        state : NodeState
        model : NodeDataModel
        node_style : NodeStyle
        """
        metrics = painter.fontMetrics()

        for port in state.ports:
            scene_pos = port.scene_position
            if not port.connections:
                painter.setPen(node_style.font_color_faded)
            else:
                painter.setPen(node_style.font_color)

            display_text = port.display_text
            rect = metrics.boundingRect(display_text)
            scene_pos.setY(scene_pos.y() + rect.height() / 4.0)
            if port.port_type == PortType.input:
                scene_pos.setX(5.0)
            elif port.port_type == PortType.output:
                scene_pos.setX(geom.width - 5.0 - rect.width())

            painter.drawText(scene_pos, display_text)

    @staticmethod
    def draw_connection_points(painter: QPainter, geom: NodeGeometry,
                               state: NodeState, model: NodeDataModel,
                               scene: 'FlowScene', node_style: NodeStyle,
                               connection_style: ConnectionStyle
                               ):
        """
        Draw connection points

        Parameters
        ----------
        painter : QPainter
        geom : NodeGeometry
        state : NodeState
        model : NodeDataModel
        scene : FlowScene
        connection_style : ConnectionStyle
        """
        diameter = node_style.connection_point_diameter
        reduced_diameter = diameter * 0.6
        for port in state.ports:
            scene_pos = port.scene_position
            can_connect = port.can_connect
            port_type = port.port_type
            data_type = port.data_type

            r = 1.0
            if state.is_reacting and can_connect and port_type == state.reacting_port_type:
                diff = geom.dragging_pos - scene_pos
                dist = math.sqrt(QPointF.dotProduct(diff, diff))

                registry = scene.registry
                dtype1, dtype2 = state.reacting_data_type, data_type
                if port_type != PortType.input:
                    dtype2, dtype1 = dtype1, dtype2

                type_convertable = registry.get_type_converter(dtype1, dtype2) is not None
                if dtype1.id == dtype2.id or type_convertable:
                    thres = 40.0
                    r = ((2.0 - dist / thres)
                         if dist < thres
                         else 1.0)
                else:
                    thres = 80.0
                    r = ((dist / thres)
                         if dist < thres
                         else 1.0)

            if connection_style.use_data_defined_colors:
                brush = connection_style.get_normal_color(data_type.id)
            else:
                brush = node_style.connection_point_color

            painter.setBrush(brush)
            painter.drawEllipse(scene_pos, reduced_diameter * r, reduced_diameter * r)

    @staticmethod
    def draw_filled_connection_points(painter: QPainter, geom: NodeGeometry,
                                      state: NodeState, model: NodeDataModel,
                                      node_style: NodeStyle,
                                      connection_style: ConnectionStyle
                                      ):

        """
        Draw filled connection points

        Parameters
        ----------
        painter : QPainter
        geom : NodeGeometry
        state : NodeState
        model : NodeDataModel
        node_style : NodeStyle
        connection_style : ConnectionStyle
        """
        diameter = node_style.connection_point_diameter
        for port in state.ports:
            if not port.connections:
                continue

            scene_pos = port.scene_position
            if connection_style.use_data_defined_colors:
                c = connection_style.get_normal_color(port.data_type.id)
            else:
                c = node_style.filled_connection_point_color
            painter.setPen(c)
            painter.setBrush(c)
            painter.drawEllipse(scene_pos, diameter * 0.4, diameter * 0.4)

    @staticmethod
    def draw_resize_rect(painter: QPainter, geom: NodeGeometry, model: NodeDataModel):
        """
        Draw resize rect

        Parameters
        ----------
        painter : QPainter
        geom : NodeGeometry
        model : NodeDataModel
        """
        if model.resizable():
            painter.setBrush(Qt.gray)
            painter.drawEllipse(geom.resize_rect)

    @staticmethod
    def draw_validation_rect(painter: QPainter, geom: NodeGeometry,
                             model: NodeDataModel,
                             graphics_object: NodeGraphicsObject,
                             node_style: NodeStyle):
        """
        Draw validation rect

        Parameters
        ----------
        painter : QPainter
        geom : NodeGeometry
        model : NodeDataModel
        graphics_object : NodeGraphicsObject
        node_style : NodeStyle
        """
        model_validation_state = model.validation_state()
        if model_validation_state == NodeValidationState.valid:
            return

        color = (node_style.selected_boundary_color
                 if graphics_object.isSelected()
                 else node_style.normal_boundary_color)

        if geom.hovered:
            p = QPen(color, node_style.hovered_pen_width)
        else:
            p = QPen(color, node_style.pen_width)

        painter.setPen(p)

        # Drawing the validation message background
        if model_validation_state == NodeValidationState.error:
            painter.setBrush(node_style.error_color)
        else:
            painter.setBrush(node_style.warning_color)

        radius = 3.0
        diam = node_style.connection_point_diameter
        boundary = QRectF(
            -diam,
            -diam + geom.height - geom.validation_height,
            2.0 * diam + geom.width,
            2.0 * diam + geom.validation_height,
        )
        painter.drawRoundedRect(boundary, radius, radius)
        painter.setBrush(Qt.gray)

        # Drawing the validation message itself
        error_msg = model.validation_message()
        f = painter.font()
        metrics = QFontMetrics(f)
        rect = metrics.boundingRect(error_msg)
        position = QPointF(
            (geom.width - rect.width()) / 2.0,
            geom.height - (geom.validation_height - diam) / 2.0
        )
        painter.setFont(f)
        painter.setPen(node_style.font_color)
        painter.drawText(position, error_msg)
