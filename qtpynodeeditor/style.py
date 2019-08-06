import json
import logging
import random

from qtpy.QtGui import QColor

logger = logging.getLogger(__name__)


def _get_qcolor(style_dict, key):
    if key not in style_dict:
        return QColor()

    name_or_list = style_dict[key]
    if isinstance(name_or_list, list):
        color = QColor(*name_or_list)
    else:
        color = QColor(name_or_list)
    logger.debug('Loaded color %s = %s -> %d %d %d %d', key, name_or_list,
                 *color.getRgb())
    return color


class Style:
    default_style = {
        "FlowViewStyle": {
            "BackgroundColor": [53, 53, 53],
            "FineGridColor": [60, 60, 60],
            "CoarseGridColor": [25, 25, 25]
        },
        "NodeStyle": {
            "NormalBoundaryColor": [255, 255, 255],
            "SelectedBoundaryColor": [255, 165, 0],
            "GradientColor0": "gray",
            "GradientColor1": [80, 80, 80],
            "GradientColor2": [64, 64, 64],
            "GradientColor3": [58, 58, 58],
            "ShadowColor": [20, 20, 20],
            "FontColor": "white",
            "FontColorFaded": "gray",
            "ConnectionPointColor": [169, 169, 169],
            "FilledConnectionPointColor": "cyan",
            "ErrorColor": "red",
            "WarningColor": [128, 128, 0],

            "PenWidth": 1.0,
            "HoveredPenWidth": 1.5,

            "ConnectionPointDiameter": 8.0,

            "Opacity": 0.8
        },
        "ConnectionStyle": {
            "ConstructionColor": "gray",
            "NormalColor": "darkcyan",
            "SelectedColor": [100, 100, 100],
            "SelectedHaloColor": "orange",
            "HoveredColor": "lightcyan",
            "LineWidth": 3.0,
            "ConstructionLineWidth": 2.0,
            "PointDiameter": 10.0,
            "UseDataDefinedColors": False
        }
    }

    def __init__(self, json_style=None):
        if json_style is None:
            json_style = self.default_style

        self.load_from_json(json_style)

    def load_from_json(self, json_style: str):
        """
        Load from json

        Parameters
        ----------
        json_style : str or dict
        """
        if isinstance(json_style, dict):
            return json_style
        else:
            return json.loads(json_style)


class FlowViewStyle(Style):
    def __init__(self, json_style=None):
        self.background_color = QColor()
        self.fine_grid_color = QColor()
        self.coarse_grid_color = QColor()
        super().__init__(json_style=json_style)

    def load_from_json(self, json_style: str):
        """
        Load from json

        Parameters
        ----------
        json_style : str or dict
        """
        doc = super().load_from_json(json_style)
        style = doc["FlowViewStyle"]
        self.background_color = _get_qcolor(style, 'BackgroundColor')
        self.fine_grid_color = _get_qcolor(style, 'FineGridColor')
        self.coarse_grid_color = _get_qcolor(style, 'CoarseGridColor')


class ConnectionStyle(Style):
    '''
    Style for connections

    Attributes
    ----------
    construction_color : QColor
    normal_color : QColor
    selected_color : QColor
    selected_halo_color : QColor
    hovered_color : QColor
    line_width : float
    construction_line_width : float
    point_diameter : float
    use_data_defined_colors : bool
    '''

    def __init__(self, json_style=None):
        self.construction_color = QColor()
        self.normal_color = QColor()
        self.selected_color = QColor()
        self.selected_halo_color = QColor()
        self.hovered_color = QColor()

        self.line_width = 0.0
        self.construction_line_width = 0.0
        self.point_diameter = 0.0

        self.use_data_defined_colors = True

        super().__init__(json_style=json_style)

    def load_from_json(self, json_style: str):
        """
        Load from json

        Parameters
        ----------
        json_style : str
        """
        doc = super().load_from_json(json_style)
        style = doc["ConnectionStyle"]
        self.construction_color = _get_qcolor(style, 'ConstructionColor')
        self.normal_color = _get_qcolor(style, 'NormalColor')
        self.selected_color = _get_qcolor(style, 'SelectedColor')
        self.selected_halo_color = _get_qcolor(style, 'SelectedHaloColor')
        self.hovered_color = _get_qcolor(style, 'HoveredColor')

        self.line_width = float(style['LineWidth'])
        self.construction_line_width = float(style['ConstructionLineWidth'])
        self.point_diameter = float(style['PointDiameter'])
        self.use_data_defined_colors = bool(style['UseDataDefinedColors'])

    def get_normal_color(self, type_id: str = None) -> QColor:
        """
        Normal color

        Parameters
        ----------
        type_id : str

        Returns
        -------
        value : QColor
        """
        if type_id is None:
            return self.normal_color

        hue_range = 0xFF
        random.seed(type_id)
        hue = random.randint(0, hue_range)
        sat = 120 + id(type_id) % 129
        return QColor.fromHsl(hue, sat, 160)


class NodeStyle(Style):
    def __init__(self, json_style=None):
        self.normal_boundary_color = QColor()
        self.selected_boundary_color = QColor()
        self.gradient_colors = ((0, QColor()), )
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

        super().__init__(json_style=json_style)

    def load_from_json(self, json_style: str):
        """
        Load from json

        Parameters
        ----------
        json_style : str
        """
        doc = super().load_from_json(json_style)
        style = doc["NodeStyle"]

        self.normal_boundary_color = _get_qcolor(style, 'NormalBoundaryColor')
        self.selected_boundary_color = _get_qcolor(
            style, 'SelectedBoundaryColor')
        self.gradient_colors = (
            (0.0, _get_qcolor(style, 'GradientColor0')),
            (0.03, _get_qcolor(style, 'GradientColor1')),
            (0.97, _get_qcolor(style, 'GradientColor2')),
            (1.0, _get_qcolor(style, 'GradientColor3')),
        )
        self.shadow_color = _get_qcolor(style, 'ShadowColor')
        self.font_color = _get_qcolor(style, 'FontColor')
        self.font_color_faded = _get_qcolor(style, 'FontColorFaded')
        self.connection_point_color = _get_qcolor(
            style, 'ConnectionPointColor')
        self.filled_connection_point_color = _get_qcolor(
            style, 'FilledConnectionPointColor')
        self.warning_color = _get_qcolor(style, 'WarningColor')
        self.error_color = _get_qcolor(style, 'ErrorColor')

        self.pen_width = float(style['PenWidth'])
        self.hovered_pen_width = float(style['HoveredPenWidth'])
        self.connection_point_diameter = float(
            style['ConnectionPointDiameter'])
        self.opacity = float(style['Opacity'])


class StyleCollection:
    'Container for all styles'

    def __init__(self, *, node=None, connection=None, flow_view=None):
        if node is None:
            node = NodeStyle()
        self.node = node

        if connection is None:
            connection = ConnectionStyle()
        self.connection = connection

        if flow_view is None:
            flow_view = FlowViewStyle()
        self.flow_view = flow_view

    @classmethod
    def from_json(cls, json_doc):
        if isinstance(json_doc, dict):
            json_style = json_doc
        else:
            json_style = json.loads(json_doc)

        return StyleCollection(
            node=NodeStyle(json_style),
            connection=ConnectionStyle(json_style),
            flow_view=FlowViewStyle(json_style),
        )


default_style = StyleCollection()
