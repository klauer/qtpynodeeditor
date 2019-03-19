from qtpy.QtCore import QObject, QUuid
from qtpy.QtCore import Signal


from .base import ConnectionBase, NodeBase
from .connection_geometry import ConnectionGeometry
from .connection_graphics_object import ConnectionGraphicsObject
from .connection_state import ConnectionState
from .node import NodeDataType
from .node_data import NodeData
from .port import PortType, INVALID, opposite_port, PortIndex
from .serializable import Serializable
from .type_converter import TypeConverter


class Connection(QObject, Serializable, ConnectionBase):
    connection_completed = Signal(QObject)
    connection_made_incomplete = Signal(QObject)
    updated = Signal(QObject)

    def __init__(self, in_node: NodeBase, out_node: NodeBase, *,
                 port_index_in=INVALID, port_index_out=INVALID,
                 converter=None):
        super().__init__()
        self._uid = QUuid.createUuid()
        self._in_node = in_node
        self._in_port_index = port_index_in
        self._out_node = out_node
        self._out_port_index = port_index_out
        self._connection_state = ConnectionState()
        self._converter = converter
        self._connection_geometry = ConnectionGeometry()
        self._connection_graphics_object = None

    @classmethod
    def from_node(cls, port_type: PortType, node: NodeBase, port_index: PortIndex):
        '''
        New Connection is attached to the port of the given Node. The port has
        parameters (port_type, port_index). The opposite connection end will
        require another port.

        Parameters
        ----------
        port_type : PortType
        node : Node
        port_index : PortIndex
        '''
        inst = cls(None, None)
        inst.set_node_to_port(node, port_type, port_index)
        inst.set_required_port(opposite_port(port_type))
        return inst

    @classmethod
    def from_nodes(cls, node_in, port_index_in, node_out, port_index_out, *,
                   converter):
        '''
        Create connection

        Parameters
        ----------
        node_in : Node
        port_index_in : PortIndex
        node_out : Node
        port_index_out : PortIndex
        converter : TypeConverter
        '''
        inst = cls(node_in, node_out, port_index_in=port_index_in,
                   port_index_out=port_index_out, converter=converter)
        inst.set_node_to_port(node_in, PortType.In, port_index_in)
        inst.set_node_to_port(node_out, PortType.Out, port_index_out)
        return inst

    def _cleanup(self):
        if self.complete():
            self.connection_made_incomplete.emit(self)

        self.propagate_empty_data()
        if self._in_node:
            self._in_node.node_graphics_object().update()
            self._in_node = None

        if self._out_node:
            self._out_node.node_graphics_object().update()
            self._out_node = None

        if self._connection_graphics_object is not None:
            self._connection_graphics_object._cleanup()
            self._connection_graphics_object = None

    def __del__(self):
        try:
            self._cleanup()
        except Exception:
            ...

    def save(self) -> dict:
        """
        save

        Returns
        -------
        value : dict
        """
        if not (self._in_node and self._out_node):
            return {}

        connection_json = dict(
            in_id=self._in_node.id().toString(),
            in_index=self._in_port_index,
            out_id=self._out_node.id().toString(),
            out_index=self._out_port_index,
        )

        if self._converter:
            def get_type_json(type: PortType):
                node_type = self.data_type(type)
                return dict(
                    id=node_type.id,
                    name=node_type.name
                )

            connection_json["converter"] = {
                "in": get_type_json(PortType.In),
                "out": get_type_json(PortType.Out),
            }

        return connection_json

    def id(self) -> QUuid:
        """
        Id

        Returns
        -------
        value : QUuid
        """
        return self._uid

    def set_required_port(self, dragging: PortType):
        """
        Remembers the end being dragged. Invalidates Node address. Grabs mouse.

        Parameters
        ----------
        dragging : PortType
        """
        self._connection_state.set_required_port(dragging)
        if dragging == PortType.Out:
            self._out_node = None
            self._out_port_index = INVALID
        elif dragging == PortType.In:
            self._in_node = None
            self._in_port_index = INVALID

    def required_port(self) -> PortType:
        """
        Required port

        Returns
        -------
        value : PortType
        """
        return self._connection_state.required_port()

    def set_graphics_object(self, graphics: ConnectionGraphicsObject):
        """
        Set graphics object

        Parameters
        ----------
        graphics : ConnectionGraphicsObject
        """
        self._connection_graphics_object = graphics

        # this function is only called when the ConnectionGraphicsObject is
        # newly created. At self moment both end coordinates are (0, 0) in
        # Connection G.O. coordinates. The position of the whole Connection GO
        # in scene coordinate system is also (0, 0).  By moving the whole
        # object to the Node Port position we position both connection ends
        # correctly.
        if self.required_port() != PortType.none:
            attached_port = opposite_port(self.required_port())
            attached_port_index = self.get_port_index(attached_port)
            node = self.get_node(attached_port)
            node_scene_transform = node.node_graphics_object().sceneTransform()
            pos = node.node_geometry().port_scene_position(attached_port_index, attached_port, node_scene_transform)
            self._connection_graphics_object.setPos(pos)

        self._connection_graphics_object.move()

    def set_node_to_port(self, node: NodeBase, port_type: PortType, port_index: PortIndex):
        """
        Assigns a node to the required port. It is assumed that there is a required port, no extra checks

        Parameters
        ----------
        node : Node
        port_type : PortType
        port_index : PortIndex
        """
        was_incomplete = not self.complete()
        if port_type == PortType.Out:
            self._out_node = node
            self._out_port_index = port_index
        else:
            self._in_node = node
            self._in_port_index = port_index

        self._connection_state.set_no_required_port()
        self.updated.emit(self)
        if self.complete() and was_incomplete:
            self.connection_completed.emit(self)

    def remove_from_nodes(self):
        if self._in_node:
            self._in_node.node_state().erase_connection(PortType.In,
                                                        self._in_port_index,
                                                        self)
        if self._out_node:
            self._out_node.node_state().erase_connection(PortType.Out,
                                                         self._out_port_index,
                                                         self)

    def get_connection_graphics_object(self) -> ConnectionGraphicsObject:
        """
        Get connection graphics object

        Returns
        -------
        value : ConnectionGraphicsObject
        """
        return self._connection_graphics_object

    def connection_state(self) -> ConnectionState:
        """
        Connection state

        Returns
        -------
        value : ConnectionState
        """
        return self._connection_state

    def connection_geometry(self) -> ConnectionGeometry:
        """
        Connection geometry

        Returns
        -------
        value : ConnectionGeometry
        """
        return self._connection_geometry

    def get_node(self, port_type: PortType) -> NodeBase:
        """
        Get node

        Parameters
        ----------
        port_type : PortType

        Returns
        -------
        value : Node
        """
        if port_type == PortType.In:
            return self._in_node
        elif port_type == PortType.Out:
            return self._out_node

        return None

    def get_port_index(self, port_type: PortType) -> PortIndex:
        """
        Get port index

        Parameters
        ----------
        port_type : PortType

        Returns
        -------
        value : PortIndex
        """
        if port_type == PortType.In:
            return self._in_port_index
        elif port_type == PortType.Out:
            return self._out_port_index
        return INVALID

    def clear_node(self, port_type: PortType):
        """
        Clear node

        Parameters
        ----------
        port_type : PortType
        """
        if self.complete():
            self.connection_made_incomplete.emit(self)

        if port_type == PortType.In:
            self._in_port_index = INVALID
            self._in_node = None
        else:
            self._out_port_index = INVALID
            self._out_node = None

    def data_type(self, port_type: PortType) -> NodeDataType:
        """
        Data type

        Parameters
        ----------
        port_type : PortType

        Returns
        -------
        value : NodeDataType
        """
        if self._in_node and self._out_node:
            model = (self._in_node.node_data_model()
                     if port_type == PortType.In
                     else self._out_node.node_data_model()
                     )
            index = (self._in_port_index
                     if port_type == PortType.In
                     else self._out_port_index
                     )
            return model.data_type(port_type, index)

        index = INVALID
        valid_node = None
        if self._in_node:
            index = self._in_port_index
            port_type = PortType.In
            valid_node = self._in_node
        elif self._out_node:
            index = self._out_port_index
            port_type = PortType.Out
            valid_node = self._out_node
        else:
            assert False, "Should not reach here"

        model = valid_node.node_data_model()
        return model.data_type(port_type, index)

    def set_type_converter(self, converter: TypeConverter):
        """
        Set type converter

        Parameters
        ----------
        converter : TypeConverter
        """
        self._converter = converter

    def complete(self) -> bool:
        """
        Complete

        Returns
        -------
        value : bool
        """
        return self._in_node is not None and self._out_node is not None

    def propagate_data(self, node_data: NodeData):
        """
        Propagate data

        Parameters
        ----------
        node_data : NodeData
        """
        if not self._in_node:
            return

        if self._converter:
            node_data = self._converter(node_data)

        self._in_node.propagate_data(node_data, self._in_port_index)

    def propagate_empty_data(self):
        self.propagate_data(NodeData())
