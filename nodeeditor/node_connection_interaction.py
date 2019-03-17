from qtpy.QtCore import QPointF

from .enums import ConnectionPolicy
from .base import NodeBase, FlowSceneBase, ConnectionBase
from .node_data import NodeDataModel
from .port import PortType, PortIndex, opposite_port, INVALID
from .type_converter import TypeConverter, DefaultTypeConverter


class NodeConnectionInteraction:
    def __init__(self, node: NodeBase, connection: ConnectionBase, scene: FlowSceneBase):
        '''
        node_connection_interaction

        Parameters
        ----------
        node : Node
        connection : Connection
        scene : FlowScene
        '''
        self._node = node
        self._connection = connection
        self._scene = scene

    def can_connect(self, port_index: PortIndex) -> bool:
        """
        Can connect when following conditions are met:
            1) Connection 'requires' a port
            2) Connection's vacant end is above the node port
            3) Node port is vacant
            4) Connection type equals node port type, or there is a registered
               type conversion that can translate between the two

        Parameters
        ----------
        port_index : PortIndex
        converter : TypeConverter

        Returns
        -------
        value : bool
        """
        # 1) Connection requires a port
        required_port = self.connection_required_port()
        if required_port == PortType.none:
            return False, None

        # 1.5) Forbid connecting the node to itself
        node = self._connection.get_node(opposite_port(required_port))
        if node == self._node:
            return False, None

        # 2) connection point is on top of the node port
        connection_point = self.connection_end_scene_position(required_port)
        port_index = self.node_port_index_under_scene_point(required_port, connection_point)
        if port_index == INVALID:
            return False, None

        # 3) Node port is vacant

        # port should be empty
        if not self.node_port_is_empty(required_port, port_index):
            return False, None

        # 4) Connection type equals node port type, or there is a registered type conversion that can translate between the two
        connection_data_type = self._connection.data_type(opposite_port(required_port))
        model_target = self._node.node_data_model()

        candidate_node_data_type = model_target.data_type(required_port, port_index)
        if connection_data_type.id == candidate_node_data_type.id:
            return True, DefaultTypeConverter

        registry = self._scene.registry()
        if required_port == PortType.In:
            return True, registry.get_type_converter(connection_data_type,
                                                     candidate_node_data_type)
        elif required_port == PortType.Out:
            return True, registry.get_type_converter(candidate_node_data_type,
                                                     connection_data_type)

        return False, None

    def try_connect(self) -> bool:
        """
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
        port_index = INVALID
        can_connect, converter = self.can_connect(port_index)
        if not can_connect:
            return False

        # 1.5) If the connection is possible but a type conversion is needed,
        # assign a convertor to connection
        if converter:
            self._connection.set_type_converter(converter)

        # 2) Assign node to required port in Connection
        required_port = self.connection_required_port()
        self._node.node_state().set_connection(required_port, port_index, self._connection)

        # 3) Assign Connection to empty port in NodeState

        # The port is not longer required after self function
        self._connection.set_node_to_port(self._node, required_port, port_index)

        # 4) Adjust Connection geometry
        self._node.node_graphics_object().move_connections()

        # 5) Poke model to intiate data transfer
        out_node = self._connection.get_node(PortType.Out)
        if out_node:
            out_port_index = self._connection.get_port_index(PortType.Out)
            out_node.on_data_updated(out_port_index)

        return True

    def disconnect(self, port_to_disconnect: PortType) -> bool:
        """
        1) Node and Connection should be already connected 2) If so, clear Connection entry in the NodeState 3) Propagate invalid data to IN node 4) Set Connection end to 'requiring a port'

        Parameters
        ----------
        port_to_disconnect : PortType

        Returns
        -------
        value : bool
        """
        port_index = self._connection.get_port_index(port_to_disconnect)
        state = self._node.node_state()

        # clear pointer to Connection in the NodeState
        state.erase_connection(port_to_disconnect, port_index)

        # 4) Propagate invalid data to IN node
        self._connection.propagate_empty_data()

        # clear Connection side
        self._connection.clear_node(port_to_disconnect)
        self._connection.set_required_port(port_to_disconnect)
        self._connection.get_connection_graphics_object().grabMouse()
        return True

    def connection_required_port(self) -> PortType:
        """
        connection_required_port

        Returns
        -------
        value : PortType
        """
        state = self._connection.connection_state()
        return state.required_port()

    def connection_end_scene_position(self, port_type: PortType) -> QPointF:
        """
        connection_end_scene_position

        Parameters
        ----------
        port_type : PortType

        Returns
        -------
        value : QPointF
        """
        go = self._connection.get_connection_graphics_object()
        geometry = self._connection.connection_geometry()
        end_point = geometry.get_end_point(port_type)
        return go.mapToScene(end_point)

    def node_port_scene_position(self, port_type: PortType, port_index: PortIndex) -> QPointF:
        """
        node_port_scene_position

        Parameters
        ----------
        port_type : PortType
        port_index : PortIndex

        Returns
        -------
        value : QPointF
        """
        geom = self._node.node_geometry()
        p = geom.port_scene_position(port_index, port_type)
        ngo = self._node.node_graphics_object()
        return ngo.sceneTransform().map(p)

    def node_port_index_under_scene_point(self, port_type: PortType, scene_point: QPointF) -> PortIndex:
        """
        node_port_index_under_scene_point

        Parameters
        ----------
        port_type : PortType
        p : QPointF

        Returns
        -------
        value : PortIndex
        """
        node_geom = self._node.node_geometry()
        scene_transform = self._node.node_graphics_object().sceneTransform()
        port_index = node_geom.check_hit_scene_point(port_type, scene_point, scene_transform)
        return port_index

    def node_port_is_empty(self, port_type: PortType, port_index: PortIndex) -> bool:
        """
        node_port_is_empty

        Parameters
        ----------
        port_type : PortType
        port_index : PortIndex

        Returns
        -------
        value : bool
        """
        node_state = self._node.node_state()
        entries = node_state.get_entries(port_type)
        if entries[port_index] is None:
            return True
        out_policy = self._node.node_data_model().port_out_connection_policy(port_index)
        return port_type == PortType.Out and out_policy == ConnectionPolicy.Many
