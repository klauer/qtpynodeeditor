import collections
from collections import OrderedDict
from qtpy.QtCore import QUuid


from .enums import ReactToConnectionState
from .base import ConnectionBase
from .node_data import NodeDataType
from .port import PortType, PortIndex


class NodeState:
    def __init__(self, model):
        '''
        node_state

        Parameters
        ----------
        model : NodeDataModel
        '''
        self._max_in = model.n_ports(PortType.In)
        self._max_out = model.n_ports(PortType.Out)
        self._connections = {
            PortType.In: OrderedDict((i, []) for i in range(self._max_in)),
            PortType.Out: OrderedDict((i, []) for i in range(self._max_out)),
        }
        self._reaction = ReactToConnectionState.NOT_REACTING
        self._reacting_port_type = PortType.none
        self._resizing = False

    def get_entries(self, port_type: PortType) -> list:
        """
        Returns vector of connections.

        Parameters
        ----------
        port_type : PortType

        Returns
        -------
        value : list
            List of Connection lists
        """
        return list(self._connections[port_type].values())

    @property
    def all_connections(self):
        return [connection
                for port_type in (PortType.In, PortType.Out)
                for port, connections in self._connections[port_type].items()
                for connection in connections
                ]

    def connections(self, port_type: PortType, port_index: PortIndex) -> list:
        """
        connections

        Parameters
        ----------
        port_type : PortType
        port_index : PortIndex

        Returns
        -------
        value : list
        """
        return list(self._connections[port_type][port_index])

    def set_connection(self, port_type: PortType, port_index: PortIndex, connection: ConnectionBase):
        """
        set_connection

        Parameters
        ----------
        port_type : PortType
        port_index : PortIndex
        connection : Connection
        """
        self._connections[port_type][port_index].append(connection)

    def erase_connection(self, port_type: PortType, port_index: PortIndex, connection: ConnectionBase):
        """
        erase_connection

        Parameters
        ----------
        port_type : PortType
        port_index : PortIndex
        connection : Connection
        """
        try:
            self._connections[port_type][port_index].remove(connection)
        except ValueError:
            ...

    def reaction(self) -> ReactToConnectionState:
        """
        reaction

        Returns
        -------
        value : NodeState.ReactToConnectionState
        """
        return self._reaction

    def reacting_port_type(self) -> PortType:
        """
        reacting_port_type

        Returns
        -------
        value : PortType
        """
        return self._reacting_port_type

    def reacting_data_type(self) -> NodeDataType:
        """
        reacting_data_type

        Returns
        -------
        value : NodeDataType
        """
        return self._reacting_data_type

    def set_reaction(
        self, reaction: ReactToConnectionState, reacting_port_type:
            PortType = PortType.none,
            reacting_data_type: NodeDataType = None
    ):
        """
        set_reaction

        Parameters
        ----------
        reaction : NodeState.ReactToConnectionState
        reacting_port_type : PortType, optional
        reacting_data_type : NodeDataType
        """
        self._reaction = reaction
        self._reacting_port_type = reacting_port_type
        self._reacting_data_type = reacting_data_type

    def is_reacting(self) -> bool:
        """
        is_reacting

        Returns
        -------
        value : bool
        """
        return self._reaction == ReactToConnectionState.REACTING

    def set_resizing(self, resizing: bool):
        """
        set_resizing

        Parameters
        ----------
        resizing : bool
        """
        self._resizing = resizing

    def resizing(self) -> bool:
        """
        resizing

        Returns
        -------
        value : bool
        """
        return self._resizing
