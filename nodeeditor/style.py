import pathlib
import json
import logging
import random

from qtpy.QtCore import QByteArray, QFile, QIODevice, QJsonDocument, QJsonValue
from qtpy.QtGui import QColor


logger = logging.getLogger(__name__)


def _get_qcolor(style_dict, key):
    if key not in style_dict:
        return QColor()

    name_or_list = style_dict[key]
    if isinstance(name_or_list, list):
        return QColor(*name_or_list)

    return QColor(name_or_list)


class Style:
    default_json = pathlib.Path(__file__).parent / 'DefaultStyle.json'

    def __init__(self, json_text=None):
        if json_text:
            self.load_json_text(json_text)
        else:
            self.load_json_file(self.default_json)

    def load_json_text(self, json_text: str):
        """
        load_json_text

        Parameters
        ----------
        json_text : str
        """
        self.load_from_json(json_text)

    def load_json_file(self, file_name: str):
        """
        load_json_file

        Parameters
        ----------
        file_name : str
        """
        with open(file_name, 'rt') as f:
            self.load_from_json(f.read())

    def load_from_json(self, byte_array: QByteArray):
        """
        load_from_json

        Parameters
        ----------
        byte_array : QByteArray
        """
        ...


class FlowViewStyle(Style):
    def __init__(self, json_text=None):
        self.background_color = QColor()
        self.fine_grid_color = QColor()
        self.coarse_grid_color = QColor()
        super().__init__(json_text=json_text)

    @staticmethod
    def set_style(json_text: str):
        """
        set_style

        Parameters
        ----------
        json_text : str
        """
        style = FlowViewStyle(json_text)
        StyleCollection.set_flow_view_style(style)

    def load_from_json(self, byte_array: QByteArray):
        """
        load_from_json

        Parameters
        ----------
        byte_array : QByteArray
        """
        doc = json.loads(byte_array)
        style = doc["FlowViewStyle"]
        self.background_color = _get_qcolor(style, 'BackgroundColor')
        self.fine_grid_color = _get_qcolor(style, 'FineGridColor')
        self.coarse_grid_color = _get_qcolor(style, 'CoarseGridColor')


class ConnectionStyle(Style):
    def __init__(self, json_text=None):
        self._construction_color = QColor()
        self._normal_color = QColor()
        self._selected_color = QColor()
        self._selected_halo_color = QColor()
        self._hovered_color = QColor()

        self._line_width = 0.0
        self._construction_line_width = 0.0
        self._point_diameter = 0.0

        self._use_data_defined_colors = True

        super().__init__(json_text=json_text)

    @staticmethod
    def set_connection_style(json_text: str):
        """
        set_connection_style

        Parameters
        ----------
        json_text : str
        """
        style = ConnectionStyle(json_text)
        StyleCollection.set_connection_style(style)

    def load_from_json(self, byte_array: QByteArray):
        """
        load_from_json

        Parameters
        ----------
        byte_array : QByteArray
        """
        doc = json.loads(byte_array)
        style = doc["ConnectionStyle"]
        self._construction_color = _get_qcolor(style, 'ConstructionColor')
        self._normal_color = _get_qcolor(style, 'NormalColor')
        self._selected_color = _get_qcolor(style, 'SelectedColor')
        self._selected_halo_color = _get_qcolor(style, 'SelectedHaloColor')
        self._hovered_color = _get_qcolor(style, 'HoveredColor')

        self._line_width = float(style['LineWidth'])
        self._construction_line_width = float(style['ConstructionLineWidth'])
        self._point_diameter = float(style['PointDiameter'])
        self._use_data_defined_colors = bool(style['UseDataDefinedColors'])

    def construction_color(self) -> QColor:
        """
        construction_color

        Returns
        -------
        value : QColor
        """
        return self._construction_color

    def normal_color(self, type_id: str = None) -> QColor:
        """
        normal_color

        Parameters
        ----------
        type_id : str

        Returns
        -------
        value : QColor
        """
        # TODO verify
        #   std::size_t hash = qHash(type_id);
        #   std::size_t const hue_range = 0xFF;
        #   qsrand(hash);
        #   std::size_t hue = qrand() % hue_range;
        #   std::size_t sat = 120 + hash % 129;
        #   return QColor::fromHsl(hue, sat, 160);
        # }
        if type_id is None:
            return self._normal_color

        hash = id(type_id)
        hue_range = 0xFF

        hue = random.randint(0, hue_range)
        sat = 120 + hash % 129
        return QColor.fromHsl(hue, sat, 160)

    def selected_color(self) -> QColor:
        """
        selected_color

        Returns
        -------
        value : QColor
        """
        return self._selected_color

    def selected_halo_color(self) -> QColor:
        """
        selected_halo_color

        Returns
        -------
        value : QColor
        """
        return self._selected_halo_color

    def hovered_color(self) -> QColor:
        """
        hovered_color

        Returns
        -------
        value : QColor
        """
        return self._hovered_color

    def line_width(self) -> float:
        """
        line_width

        Returns
        -------
        value : float
        """
        return self._line_width

    def construction_line_width(self) -> float:
        """
        construction_line_width

        Returns
        -------
        value : float
        """
        return self._construction_line_width

    def point_diameter(self) -> float:
        """
        point_diameter

        Returns
        -------
        value : float
        """
        return self._point_diameter

    def use_data_defined_colors(self) -> bool:
        """
        use_data_defined_colors

        Returns
        -------
        value : bool
        """
        return self._use_data_defined_colors


class NodeStyle(Style):
    def __init__(self, json_text=None):
        self.normal_boundary_color = QColor()
        self.selected_boundary_color = QColor()
        self.gradient_color0 = QColor()
        self.gradient_color1 = QColor()
        self.gradient_color2 = QColor()
        self.gradient_color3 = QColor()
        self.shadow_color = QColor()
        self.font_color = QColor()
        self.font_color_faded = QColor()

        self.connection_point_color = QColor()
        self.filled_connection_point_color = QColor()

        self.warning_color = QColor()
        self.error_color = QColor()

        self.pen_width = 1.0
        self.hovered_pen_width = 2.0
        self.connection_point_diameter = 5.0
        self.opacity = 1.0

        super().__init__(json_text=json_text)

    @staticmethod
    def set_node_style(json_text: str):
        """
        set_node_style

        Parameters
        ----------
        json_text : str
        """
        style = NodeStyle(json_text)
        StyleCollection.set_node_style(style)

    def load_from_json(self, byte_array: QByteArray):
        """
        load_from_json

        Parameters
        ----------
        byte_array : QByteArray
        """
        doc = json.loads(byte_array)
        style = doc["NodeStyle"]

        self.normal_boundary_color = _get_qcolor(style, 'NormalBoundaryColor')
        self.selected_boundary_color = _get_qcolor(style, 'SelectedBoundaryColor')
        self.gradient_color0 = _get_qcolor(style, 'GradientColor0')
        self.gradient_color1 = _get_qcolor(style, 'GradientColor1')
        self.gradient_color2 = _get_qcolor(style, 'GradientColor2')
        self.gradient_color3 = _get_qcolor(style, 'GradientColor3')
        self.shadow_color = _get_qcolor(style, 'ShadowColor')
        self.font_color = _get_qcolor(style, 'FontColor')
        self.font_color_faded = _get_qcolor(style, 'FontColorFaded')
        self.connection_point_color = _get_qcolor(style, 'ConnectionPointColor')
        self.filled_connection_point_color = _get_qcolor(style, 'FilledConnectionPointColor')
        self.warning_color = _get_qcolor(style, 'WarningColor')
        self.error_color = _get_qcolor(style, 'ErrorColor')

        self.pen_width = float(style['PenWidth'])
        self.hovered_pen_width = float(style['HoveredPenWidth'])
        self.connection_point_diameter = float(style['ConnectionPointDiameter'])
        self.opacity = float(style['Opacity'])


class StyleCollection:
    _node_style = NodeStyle()
    _connection_style = ConnectionStyle()
    _flow_view_style = FlowViewStyle()

    @staticmethod
    def node_style() -> NodeStyle:
        """
        node_style

        Returns
        -------
        value : NodeStyle
        """
        return _style_collection._node_style

    @staticmethod
    def connection_style() -> ConnectionStyle:
        """
        connection_style

        Returns
        -------
        value : ConnectionStyle
        """
        return _style_collection._connection_style

    @staticmethod
    def flow_view_style() -> FlowViewStyle:
        """
        flow_view_style

        Returns
        -------
        value : FlowViewStyle
        """
        return _style_collection._flow_view_style

    @staticmethod
    def set_node_style(node_style: NodeStyle):
        """
        set_node_style

        Parameters
        ----------
        node_style : NodeStyle
        """
        _style_collection._node_style = node_style

    @staticmethod
    def set_connection_style(connection_style: ConnectionStyle):
        """
        set_connection_style

        Parameters
        ----------
        connection_style : ConnectionStyle
        """
        _style_collection._connection_style = connection_style

    @staticmethod
    def set_flow_view_style(flow_view_style: FlowViewStyle):
        """
        set_flow_view_style

        Parameters
        ----------
        flow_view_style : FlowViewStyle
        """
        _style_collection._flow_view_style = flow_view_style

    @staticmethod
    def instance():
        """
        instance

        Returns
        -------
        value : StyleCollection
        """
        return _style_collection


_style_collection = StyleCollection()
