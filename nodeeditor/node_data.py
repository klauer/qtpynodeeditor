from qtpy.QtCore import QObject, Qt
from qtpy.QtWidgets import QWidget
from qtpy.QtCore import Signal

from .style import NodeStyle, StyleCollection
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

    def __init__(self, data_type=None):
        if data_type is not None:
            self._type = data_type

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

    def type(self) -> NodeDataType:
        """
        Type for inner use

        Returns
        -------
        value : NodeDataType
        """
        return self._type


class NodeDataModel(QObject, Serializable):
    data_updated = Signal(PortIndex)
    data_invalidated = Signal(PortIndex)
    computing_started = Signal()
    computing_finished = Signal()
    embedded_widget_size_updated = Signal()

    def __init__(self, node_style=None, parent=None):
        super().__init__(parent=parent)
        if node_style is None:
            node_style = StyleCollection.node_style()
        self._node_style = node_style

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

    def name(self) -> str:
        """
        Name makes self model unique

        Returns
        -------
        value : str
        """
        ...

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

    def node_style(self) -> NodeStyle:
        """
        Node style

        Returns
        -------
        value : NodeStyle
        """
        return self._node_style

    def set_node_style(self, style: NodeStyle):
        """
        Set node style

        Parameters
        ----------
        style : NodeStyle
        """
        self._node_style = style

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
