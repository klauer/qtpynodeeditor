from collections import OrderedDict

from .enums import ReactToConnectionState
from .base import ConnectionBase
from .node_data import NodeDataType
from .port import PortType, PortIndex, NodePort


class NodeState:
    def __init__(self, model):
        '''
        node_state

        Parameters
        ----------
        model : NodeDataModel
        '''
        self._max_in = model.num_ports[PortType.input]
        self._max_out = model.num_ports[PortType.output]
        self._connections = {
            PortType.input: OrderedDict((i, []) for i in range(self._max_in)),
            PortType.output: OrderedDict((i, []) for i in range(self._max_out)),
        }
        self._reaction = ReactToConnectionState.not_reacting
        self._reacting_port_type = PortType.none
        self._reacting_data_type = None
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
                for port_type in (PortType.input, PortType.output)
                for port, connections in self._connections[port_type].items()
                for connection in connections
                ]

    def connections(self, port_type: PortType, port_index: PortIndex) -> list:
        """
        Connections

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
        Set connection

        Parameters
        ----------
        port_type : PortType
        port_index : PortIndex
        connection : Connection
        """
        self._connections[port_type][port_index].append(connection)

    def erase_connection(self, port_type: PortType, port_index: PortIndex, connection: ConnectionBase):
        """
        Erase connection

        Parameters
        ----------
        port_type : PortType
        port_index : PortIndex
        connection : Connection
        """
        try:
            self._connections[port_type][port_index].remove(connection)
        except ValueError:
            # TODO: should not be reaching this
            ...

    @property
    def reaction(self) -> ReactToConnectionState:
        """
        Reaction

        Returns
        -------
        value : NodeState.ReactToConnectionState
        """
        return self._reaction

    @property
    def reacting_port_type(self) -> PortType:
        """
        Reacting port type

        Returns
        -------
        value : PortType
        """
        return self._reacting_port_type

    @property
    def reacting_data_type(self) -> NodeDataType:
        """
        Reacting data type

        Returns
        -------
        value : NodeDataType
        """
        return self._reacting_data_type

    def set_reaction(self, reaction: ReactToConnectionState,
                     reacting_port_type: PortType = PortType.none,
                     reacting_data_type: NodeDataType = None):
        """
        Set reaction

        Parameters
        ----------
        reaction : NodeState.ReactToConnectionState
        reacting_port_type : PortType, optional
        reacting_data_type : NodeDataType
        """
        self._reaction = ReactToConnectionState(reaction)
        self._reacting_port_type = reacting_port_type
        self._reacting_data_type = reacting_data_type

    @property
    def is_reacting(self) -> bool:
        """
        Is the node reacting to a mouse event?

        Returns
        -------
        value : bool
        """
        return self._reaction == ReactToConnectionState.reacting

    @property
    def resizing(self) -> bool:
        """
        Resizing

        Returns
        -------
        value : bool
        """
        return self._resizing

    @resizing.setter
    def resizing(self, resizing: bool):
        self._resizing = resizing
