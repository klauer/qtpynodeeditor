import math

from qtpy.QtCore import QPointF, QRect, QRectF
from qtpy.QtGui import QFont, QFontMetrics, QTransform


from .base import NodeBase
from .enums import NodeValidationState, PortType
from .node_data import NodeDataModel
from .port import PortIndex, INVALID
from .style import StyleCollection


class NodeGeometry:
    def __init__(self, data_model: NodeDataModel):
        super().__init__()
        self._node_data_model = data_model
        # some variables are mutable because we need to change drawing metrics
        # corresponding to font_metrics but self doesn't change constness of
        # Node
        self._width = 100
        self._height = 150
        self._input_port_width = 70
        self._output_port_width = 70
        self._entry_height = 20
        self._spacing = 20
        self._hovered = False
        self._n_sources = data_model.n_ports(PortType.Out)
        self._n_sinks = data_model.n_ports(PortType.In)
        self._dragging_pos = QPointF(-1000, -1000)
        self._data_model = data_model
        self._font_metrics = QFontMetrics(QFont())

        f = QFont()
        f.setBold(True)
        self._bold_font_metrics = QFontMetrics(f)

    def height(self) -> int:
        """
        height

        Returns
        -------
        value : int
        """
        return self._height

    def set_height(self, h: int):
        """
        set_height

        Parameters
        ----------
        h : int
        """
        self._height = int(h)

    def width(self) -> int:
        """
        width

        Returns
        -------
        value : int
        """
        return self._width

    def set_width(self, w: int):
        """
        set_width

        Parameters
        ----------
        w : int
        """
        self._width = int(w)

    def entry_height(self) -> int:
        """
        entry_height

        Returns
        -------
        value : int
        """
        return self._entry_height

    def set_entry_height(self, h: int):
        """
        set_entry_height

        Parameters
        ----------
        h : int
        """
        self._entry_height = int(h)

    def entry_width(self) -> int:
        """
        entry_width

        Returns
        -------
        value : int
        """
        return self._entry_width

    def set_entry_width(self, w: int):
        """
        set_entry_width

        Parameters
        ----------
        w : int
        """
        self._entry_width = int(w)

    def spacing(self) -> int:
        """
        spacing

        Returns
        -------
        value : int
        """
        return self._spacing

    def set_spacing(self, s: int):
        """
        set_spacing

        Parameters
        ----------
        s : int
        """
        self._spacing = int(s)

    def hovered(self) -> bool:
        """
        hovered

        Returns
        -------
        value : bool
        """
        return self._hovered

    def set_hovered(self, h: int):
        """
        set_hovered

        Parameters
        ----------
        h : int
        """
        self._hovered = bool(h)

    def n_sources(self) -> int:
        """
        n_sources

        Returns
        -------
        value : int
        """
        return self._data_model.n_ports(PortType.Out)

    def n_sinks(self) -> int:
        """
        n_sinks

        Returns
        -------
        value : int
        """
        return self._data_model.n_ports(PortType.In)

    def dragging_pos(self) -> QPointF:
        """
        dragging_pos

        Returns
        -------
        value : QPointF
        """
        return self._dragging_pos

    def set_dragging_position(self, pos: QPointF):
        """
        set_dragging_position

        Parameters
        ----------
        pos : QPointF
        """
        self._dragging_pos = pos

    def entry_bounding_rect(self, *, addon=0.0) -> QRectF:
        """
        entry_bounding_rect

        Returns
        -------
        value : QRectF
        """
        return QRectF(0 - addon, 0 - addon,
                      self._entry_width + 2 * addon,
                      self._entry_height + 2 * addon)

    def bounding_rect(self) -> QRectF:
        """
        bounding_rect

        Returns
        -------
        value : QRectF
        """
        node_style = StyleCollection.node_style()
        addon = 4 * node_style.connection_point_diameter
        return QRectF(0 - addon, 0 - addon,
                      self._width + 2 * addon, self._height + 2 * addon)

    def recalculate_size(self, font: QFont = None):
        """
        If font is unspecified,
            Updates size unconditionally
        Otherwise,
            Updates size if the QFontMetrics is changed
        """
        if font is not None:
            font_metrics = QFontMetrics(font)
            bold_font = QFont(font)
            bold_font.setBold(True)
            bold_font_metrics = QFontMetrics(bold_font)
            if self._bold_font_metrics == bold_font_metrics:
                return

            self._font_metrics = font_metrics
            self._bold_font_metrics = bold_font_metrics

        self._entry_height = self._font_metrics.height()

        max_num_of_entries = max((self._n_sinks, self._n_sources))
        step = self._entry_height + self._spacing
        height = step * max_num_of_entries

        w = self._data_model.embedded_widget()
        if w:
            height = max((height, w.height()))

        height += self.caption_height()
        self._input_port_width = self.port_width(PortType.In)
        self._output_port_width = self.port_width(PortType.Out)
        width = self._input_port_width + self._output_port_width + 2 * self._spacing

        w = self._data_model.embedded_widget()
        if w:
            width += w.width()

        width = max((width, self.caption_width()))

        if self._data_model.validation_state() != NodeValidationState.Valid:
            width = max((width, self.validation_width()))
            height += self.validation_height() + self._spacing

        self._width = width
        self._height = height

    def port_scene_position(self, index: PortIndex, port_type: PortType, t: QTransform = None) -> QPointF:
        """
        port_scene_position

        Parameters
        ----------
        index : PortIndex
        port_type : PortType
        t : QTransform

        Returns
        -------
        value : QPointF
        """
        if t is None:
            t = QTransform()
        node_style = StyleCollection.node_style()
        step = self._entry_height + self._spacing

        total_height = float(self.caption_height()) + step * index
        # TODO_UPSTREAM: why?
        total_height += step / 2.0

        if port_type == PortType.Out:
            x = self._width + node_style.connection_point_diameter
            result = QPointF(x, total_height)
        elif port_type == PortType.In:
            x = 0.0 - node_style.connection_point_diameter
            result = QPointF(x, total_height)
        else:
            raise ValueError(port_type)

        return t.map(result)

    def check_hit_scene_point(self, port_type: PortType, scene_point: QPointF,
                              scene_transform: QTransform) -> PortIndex:
        """
        check_hit_scene_point

        Parameters
        ----------
        port_type : PortType
        scene_point : QPointF
        scene_transform : QTransform

        Returns
        -------
        value : PortIndex
        """
        node_style = StyleCollection.node_style()
        if port_type == PortType.none:
            return INVALID

        tolerance = 2.0 * node_style.connection_point_diameter
        for i in range(self._data_model.n_ports(port_type)):
            pp = self.port_scene_position(i, port_type, scene_transform)
            p = pp - scene_point
            distance = math.sqrt(QPointF.dotProduct(p, p))
            if distance < tolerance:
                return PortIndex(i)

        return INVALID

    def resize_rect(self) -> QRect:
        """
        resize_rect

        Returns
        -------
        value : QRect
        """
        rect_size = 7
        return QRect(self._width - rect_size, self._height - rect_size, rect_size, rect_size)

    def widget_position(self) -> QPointF:
        """
        Returns the position of a widget on the Node surface

        Returns
        -------
        value : QPointF
        """
        w = self._data_model.embedded_widget()
        if not w:
            return QPointF()

        if self._data_model.validation_state() != NodeValidationState.Valid:
            return QPointF(
                self._spacing + self.port_width(PortType.In),
                (self.caption_height() + self._height - self.validation_height() - self._spacing - w.height()) / 2.0,
            )

        return QPointF(
            self._spacing + self.port_width(PortType.In), (self.caption_height() + self._height - w.height()) / 2.0
        )

    def validation_height(self) -> int:
        """
        validation_height

        Returns
        -------
        value : int
        """
        msg = self._data_model.validation_message()
        return self._bold_font_metrics.boundingRect(msg).height()

    def validation_width(self) -> int:
        """
        validation_width

        Returns
        -------
        value : int
        """
        msg = self._data_model.validation_message()
        return self._bold_font_metrics.boundingRect(msg).width()

    @staticmethod
    def calculate_node_position_between_node_ports(
            target_port_index: PortIndex, target_port: PortType, target_node:
            NodeBase, source_port_index: PortIndex, source_port: PortType,
            source_node: NodeBase, new_node: NodeBase) -> QPointF:
        """
        calculate node position between node ports

        Calculating the nodes position in the scene. It'll be positioned half
        way between the two ports that it "connects".  The first line
        calculates the halfway point between the ports (node position + port
        position on the node for both nodes averaged).  The second line offsets
        self coordinate with the size of the new node, so that the new nodes
        center falls on the originally calculated coordinate, instead of it's
        upper left corner.

        Parameters
        ----------
        target_port_index : PortIndex
        target_port : PortType
        target_node : Node
        source_port_index : PortIndex
        source_port : PortType
        source_node : Node
        new_node : Node

        Returns
        -------
        value : QPointF
        """
        converter_node_pos = (
            source_node.node_graphics_object().pos()
            + source_node.node_geometry().port_scene_position(source_port_index, source_port)
            + target_node.node_graphics_object().pos()
            + target_node.node_geometry().port_scene_position(target_port_index, target_port)
        ) / 2.0
        converter_node_pos.setX(converter_node_pos.x() - new_node.node_geometry().width() / 2.0)
        converter_node_pos.setY(converter_node_pos.y() - new_node.node_geometry().height() / 2.0)
        return converter_node_pos

    def caption_height(self) -> int:
        """
        caption_height

        Returns
        -------
        value : int
        """
        if not self._data_model.caption_visible():
            return 0
        name = self._data_model.caption()
        return self._bold_font_metrics.boundingRect(name).height()

    def caption_width(self) -> int:
        """
        caption_width

        Returns
        -------
        value : int
        """
        if not self._data_model.caption_visible():
            return 0
        name = self._data_model.caption()
        return self._bold_font_metrics.boundingRect(name).width()

    def port_width(self, port_type: PortType) -> int:
        """
        port_width

        Parameters
        ----------
        port_type : PortType

        Returns
        -------
        value : int
        """
        def get_name(i):
            if self._data_model.port_caption_visible(port_type, i):
                return self._data_model.port_caption(port_type, i)
            else:
                return self._data_model.data_type(port_type, i).name

        return max(self._font_metrics.width(get_name(i))
                   for i in range(self._data_model.n_ports(port_type))
                   )
