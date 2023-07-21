import logging
import typing
from typing import Optional

from qtpy.QtCore import QPointF

from .exceptions import (ConnectionCycleFailure, ConnectionDataTypeFailure,
                         ConnectionPointFailure, ConnectionPortNotEmptyFailure,
                         ConnectionRequiresPortFailure, ConnectionSelfFailure,
                         NodeConnectionFailure)
from .port import PortType, opposite_port
from .type_converter import TypeConverter

if typing.TYPE_CHECKING:
    from .connection import Connection  # noqa
    from .flow_scene import FlowScene  # noqa
    from .node import Node  # noqa
    from .port import Port  # noqa


logger = logging.getLogger(__name__)


class NodeConnectionInteraction:
    def __init__(self, node: 'Node',
                 connection: 'Connection',
                 scene: 'FlowScene'):
        '''
        An interactive connection interaction to complete `connection` with the
        given node

        Parameters
        ----------
        node : Node
        connection : Connection
        scene : FlowScene
        '''
        self._node = node
        self._connection = connection
        self._scene = scene

    @property
    def creates_cycle(self):
        """Would completing the connection introduce a cycle?"""
        required_port = self.connection_required_port
        return self.connection_node.has_connection_by_port_type(
            self._node, required_port)

    def can_connect(self) -> tuple['Port', Optional[TypeConverter]]:
        """
        Can connect when following conditions are met:
            1) Connection 'requires' a port - i.e., is missing either a start
               node or an end node
            2) Connection's vacant end is above the node port in the user
               interface
            3) Node port is vacant
            4) Connection does not introduce a cycle in the graph
            5) Connection type equals node port type, or there is a registered
               type conversion that can translate between the two

        Parameters
        ----------

        Returns
        -------
        port : Port
            The port to be connected.

        converter : TypeConverter
            The data type converter to use.

        Raises
        ------
        NodeConnectionFailure
        ConnectionDataTypeFailure
            If port data types are not compatible
        """
        # 1) Connection requires a port
        required_port = self.connection_required_port
        if required_port == PortType.none:
            raise ConnectionRequiresPortFailure('Connection requires a port')
        elif required_port not in (PortType.input, PortType.output):
            raise ValueError(f'Invalid port specified {required_port}')

        # 1.5) Forbid connecting the node to itself
        node = self.connection_node
        if node == self._node:
            raise ConnectionSelfFailure(f'Cannot connect {node} to itself')

        # 2) connection point is on top of the node port
        connection_point = self.connection_end_scene_position(required_port)
        port = self.node_port_under_scene_point(required_port,
                                                connection_point)
        if not port:
            raise ConnectionPointFailure(
                f'Connection point {connection_point} is not on node {node}')

        # 3) Node port is vacant
        if not port.can_connect:
            raise ConnectionPortNotEmptyFailure(
                f'Port {required_port} {port} cannot connect'
            )

        # 4) Cycle check
        if self.creates_cycle:
            raise ConnectionCycleFailure(
                f'Connecting {self._node} and {node} would introduce a '
                f'cycle in the graph'
            )

        # 5) Connection type equals node port type, or there is a registered
        #    type conversion that can translate between the two
        connection_data_type = self._connection.data_type(opposite_port(required_port))

        candidate_node_data_type = port.data_type
        if connection_data_type.id == candidate_node_data_type.id:
            return port, None

        registry = self._scene.registry
        if required_port == PortType.input:
            converter = registry.get_type_converter(connection_data_type,
                                                    candidate_node_data_type)
        else:
            converter = registry.get_type_converter(candidate_node_data_type,
                                                    connection_data_type)
        if not converter:
            raise ConnectionDataTypeFailure(
                f'{connection_data_type} and {candidate_node_data_type} are not compatible'
            )

        return port, converter

    def try_connect(self) -> bool:
        """
        Try to connect the nodes. Steps::

            1) Check conditions from 'can_connect'
            1.5) If the connection is possible but a type conversion is needed, add
                 a converter node to the scene, and connect it properly
            2) Assign node to required port in Connection
            3) Assign Connection to empty port in NodeState
            4) Adjust Connection geometry
            5) Poke model to initiate data transfer

        Returns
        -------
        value : bool
        """
        # 1) Check conditions from 'can_connect'
        try:
            port, converter = self.can_connect()
        except NodeConnectionFailure as ex:
            logger.debug('Cannot connect node', exc_info=ex)
            logger.info('Cannot connect node: %s', ex)
            return False

        # 1.5) If the connection is possible but a type conversion is needed,
        # assign a convertor to connection
        if converter:
            self._connection.type_converter = converter

        # 2) Assign node to required port in Connection
        port.add_connection(self._connection)

        # 3) Assign Connection to empty port in NodeState
        # The port is not longer required after this function
        self._connection.connect_to(port)

        # 4) Adjust Connection geometry
        self._node.graphics_object.move_connections()

        # 5) Poke model to intiate data transfer
        _, out_port = self._connection.ports
        if out_port:
            out_port.node.on_data_updated(out_port)

        return True

    def disconnect(self, port_to_disconnect: PortType):
        """
        1) Node and Connection should be already connected
        2) If so, clear Connection entry in the NodeState
        3) Propagate invalid data to IN node
        4) Set Connection end to 'requiring a port'

        Parameters
        ----------
        port_to_disconnect : PortType
        """
        port_index = self._connection.get_port_index(port_to_disconnect)
        state = self._node.state

        # clear pointer to Connection in the NodeState
        state.erase_connection(port_to_disconnect, port_index,
                               self._connection)

        # Propagate invalid data to IN node
        self._connection.propagate_empty_data()

        # clear Connection side
        self._connection.clear_node(port_to_disconnect)
        self._connection.required_port = port_to_disconnect
        self._connection.graphics_object.grabMouse()

    @property
    def connection_required_port(self) -> PortType:
        """
        The required port type to complete the connection

        Returns
        -------
        value : PortType
        """
        return self._connection.required_port

    @property
    def connection_node(self):
        """The node already specified for the connection"""
        required_port = self.connection_required_port
        return self._connection.get_node(opposite_port(required_port))

    def connection_end_scene_position(self, port_type: PortType) -> QPointF:
        """
        Connection end scene position

        Parameters
        ----------
        port_type : PortType

        Returns
        -------
        value : QPointF
        """
        go = self._connection.graphics_object
        geometry = self._connection.geometry
        end_point = geometry.get_end_point(port_type)
        return go.mapToScene(end_point)

    def node_port_scene_position(self, port_type: PortType, port_index: int) -> QPointF:
        """
        Node port scene position

        Parameters
        ----------
        port_type : PortType
        port_index : int

        Returns
        -------
        value : QPointF
        """
        port = self._node.state[port_type][port_index]
        return port.get_mapped_scene_position(
            self._node.graphics_object.sceneTransform())

    def node_port_under_scene_point(self,
                                    port_type: PortType,
                                    scene_point: QPointF) -> Optional['Port']:
        """
        Node port under scene point

        Parameters
        ----------
        port_type : PortType
        p : QPointF

        Returns
        -------
        port : Port
        """
        node_geom = self._node.geometry
        scene_transform = self._node.graphics_object.sceneTransform()
        return node_geom.check_hit_scene_point(port_type, scene_point, scene_transform)

    def node_port_is_empty(self, port_type: PortType, port_index: int) -> bool:
        """
        Node port is empty

        Parameters
        ----------
        port_type : PortType
        port_index : int

        Returns
        -------
        value : bool
        """
        port = self._node.state[port_type][port_index]
        return port.can_connect
