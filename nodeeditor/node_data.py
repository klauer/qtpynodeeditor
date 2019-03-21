from qtpy.QtCore import QObject
from qtpy.QtWidgets import QWidget
from qtpy.QtCore import Signal

from . import style as style_module
from .enums import NodeValidationState, PortType, ConnectionPolicy
from .serializable import Serializable
from .port import PortIndex


class NodeDataType:
    def __init__(self, id: str, name: str):
        self.id = id
        self.name = name


class NodeData:
    """
    Class represents data transferred between nodes.

    The actual data is stored in subtypes
    """

    def __init__(self):
        ...

    def same_type(self, node_data) -> bool:
        """
        Same type

        Parameters
        ----------
        node_data : NodeData

        Returns
        -------
        value : bool
        """
        return self.type().id == node_data.type().id

    @classmethod
    def type(cls) -> NodeDataType:
        """
        Type for inner use

        Returns
        -------
        value : NodeDataType
        """
        return cls._type


class NodeDataModel(QObject, Serializable):
    data_updated = Signal(PortIndex)
    data_invalidated = Signal(PortIndex)
    computing_started = Signal()
    computing_finished = Signal()
    embedded_widget_size_updated = Signal()

    def __init__(self, style=None, parent=None):
        super().__init__(parent=parent)
        if style is None:
            style = style_module.default_style
        self._style = style

    @property
    def style(self):
        'Style collection for drawing this data model'
        return self._style

    def caption(self) -> str:
        """
        Caption is used in GUI

        Returns
        -------
        value : str
        """
        ...

    def caption_visible(self) -> bool:
        """
        It is possible to hide caption in GUI

        Returns
        -------
        value : bool
        """
        return True

    def port_caption(self, port_type: PortType, port_index: PortIndex) -> str:
        """
        Port caption is used in GUI to label individual ports

        Parameters
        ----------
        port_type : PortType
        port_index : PortIndex

        Returns
        -------
        value : str
        """
        return ""

    def port_caption_visible(self, port_type: PortType, port_index: PortIndex) -> bool:
        """
        It is possible to hide port caption in GUI

        Parameters
        ----------
        port_type : PortType
        port_index : PortIndex

        Returns
        -------
        value : bool
        """
        return False

    @staticmethod
    def name() -> str:
        """
        Name makes self model unique

        Returns
        -------
        value : str
        """
        return ''

    def save(self) -> dict:
        """
        Save

        Returns
        -------
        value : QJsonObject
        """
        return {'name': self.name()}

    def n_ports(self, port_type: PortType) -> int:
        """
        N ports

        Parameters
        ----------
        port_type : PortType

        Returns
        -------
        value : int
        """
        ...

    def data_type(self, port_type: PortType, port_index: PortIndex):
        """
        Data type

        Parameters
        ----------
        port_type : PortType
        port_index : PortIndex

        Returns
        -------
        value : NodeDataType
        """
        ...

    def port_out_connection_policy(self, port_index: PortIndex) -> ConnectionPolicy:
        """
        Port out connection policy

        Parameters
        ----------
        port_index : PortIndex

        Returns
        -------
        value : ConnectionPolicy
        """
        return ConnectionPolicy.Many

    # @property
    def node_style(self) -> style_module.NodeStyle:
        """
        Node style

        Returns
        -------
        value : NodeStyle
        """
        return self._style.node

    def set_in_data(self, node_data: NodeData, port: PortIndex):
        """
        Triggers the algorithm

        Parameters
        ----------
        node_data : NodeData
        port : PortIndex
        """
        ...

    def out_data(self, port: PortIndex) -> NodeData:
        """
        Out data

        Parameters
        ----------
        port : PortIndex

        Returns
        -------
        value : NodeData
        """
        ...

    def embedded_widget(self) -> QWidget:
        """
        Embedded widget

        Returns
        -------
        value : QWidget
        """
        ...

    def resizable(self) -> bool:
        """
        Resizable

        Returns
        -------
        value : bool
        """
        return False

    def validation_state(self) -> NodeValidationState:
        """
        Validation state

        Returns
        -------
        value : NodeValidationState
        """
        return NodeValidationState.Valid

    def validation_message(self) -> str:
        """
        Validation message

        Returns
        -------
        value : str
        """
        return ""

    def painter_delegate(self):
        """
        Painter delegate

        Returns
        -------
        value : NodePainterDelegate
        """
        return None

    def input_connection_created(self, connection):
        """
        Input connection created

        Parameters
        ----------
        connection : Connection
        """
        ...

    def input_connection_deleted(self, connection):
        """
        Input connection deleted

        Parameters
        ----------
        connection : Connection
        """
        ...

    def output_connection_created(self, connection):
        """
        Output connection created

        Parameters
        ----------
        connection : Connection
        """
        ...

    def output_connection_deleted(self, connection):
        """
        Output connection deleted

        Parameters
        ----------
        connection : Connection
        """
        ...
