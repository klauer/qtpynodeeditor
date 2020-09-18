import typing
import uuid

from qtpy.QtCore import QObject, Signal

from . import exceptions
from .base import Serializable
from .connection_geometry import ConnectionGeometry
from .connection_graphics_object import ConnectionGraphicsObject
from .node import Node, NodeDataType
from .node_data import NodeData
from .port import Port, PortType, opposite_port
from .style import StyleCollection
from .type_converter import TypeConverter


class Connection(QObject, Serializable):
    connection_completed = Signal(QObject)
    connection_made_incomplete = Signal(QObject)
    updated = Signal(QObject)

    def __init__(self, port_a: Port, port_b: Port = None, *,
                 style: StyleCollection, converter: TypeConverter = None):
        super().__init__()
        self._uid = str(uuid.uuid4())

        if port_a is None:
            raise ValueError('port_a is required')
        elif port_a is port_b:
            raise ValueError('Cannot connect a port to itself')

        if port_a.port_type == PortType.input:
            in_port = port_a
            out_port = port_b
        else:
            in_port = port_b
            out_port = port_a

        if in_port is not None and out_port is not None:
            if in_port.port_type == out_port.port_type:
                raise exceptions.PortsOfSameTypeError(
                    'Cannot connect two ports of the same type')

        self._ports = {
            PortType.input: in_port,
            PortType.output: out_port
        }

        if in_port is not None:
            if in_port.connections:
                conn, = in_port.connections
                existing_in, existing_out = conn.ports
                if existing_in == in_port and existing_out == out_port:
                    raise exceptions.PortsAlreadyConnectedError(
                        'Specified ports already connected')
                raise exceptions.MultipleInputConnectionError(
                    f'Maximum one connection per input port '
                    f'(existing: {conn})')

        if in_port and out_port:
            self._required_port = PortType.none
        elif in_port:
            self._required_port = PortType.output
        else:
            self._required_port = PortType.input

        self._last_hovered_node = None
        self._converter = converter
        self._style = style
        self._connection_geometry = ConnectionGeometry(style)
        self._graphics_object = None

    def _cleanup(self):
        if self.is_complete:
            self.connection_made_incomplete.emit(self)

        self.propagate_empty_data()
        self.last_hovered_node = None

        for port_type, port in self.valid_ports.items():
            if port.node.graphics_object is not None:
                port.node.graphics_object.update()
            self._ports[port] = None

        if self._graphics_object is not None:
            self._graphics_object._cleanup()
            self._graphics_object = None

    @property
    def style(self) -> StyleCollection:
        return self._style

    def __getstate__(self) -> dict:
        """
        save

        Returns
        -------
        value : dict
        """
        in_port, out_port = self.ports
        if not in_port and not out_port:
            return {}

        connection_json = dict(
            in_id=in_port.node.id,
            in_index=in_port.index,
            out_id=out_port.node.id,
            out_index=out_port.index,
        )

        if self._converter:
            def get_type_json(type: PortType):
                node_type = self.data_type(type)
                return dict(
                    id=node_type.id,
                    name=node_type.name
                )

            connection_json["converter"] = {
                "in": get_type_json(PortType.input),
                "out": get_type_json(PortType.output),
            }

        return connection_json

    @property
    def id(self) -> str:
        """
        Unique identifier (uuid)

        Returns
        -------
        uuid : str
        """
        return self._uid

    @property
    def required_port(self) -> PortType:
        """
        Required port

        Returns
        -------
        value : PortType
        """
        return self._required_port

    @required_port.setter
    def required_port(self, dragging: PortType):
        """
        Remembers the end being dragged. Invalidates Node address. Grabs mouse.

        Parameters
        ----------
        dragging : PortType
        """
        self._required_port = dragging
        try:
            port = self.valid_ports[dragging]
        except KeyError:
            ...
        else:
            port.remove_connection(self)

    @property
    def graphics_object(self) -> ConnectionGraphicsObject:
        """
        Get the connection graphics object

        Returns
        ----------
        graphics : ConnectionGraphicsObject
        """
        return self._graphics_object

    @graphics_object.setter
    def graphics_object(self, graphics: ConnectionGraphicsObject):
        self._graphics_object = graphics

        # this function is only called when the ConnectionGraphicsObject is
        # newly created. At self moment both end coordinates are (0, 0) in
        # Connection G.O. coordinates. The position of the whole Connection GO
        # in scene coordinate system is also (0, 0).  By moving the whole
        # object to the Node Port position we position both connection ends
        # correctly.
        if self.required_port != PortType.none:
            attached_port = opposite_port(self.required_port)
            attached_port_index = self.get_port_index(attached_port)
            node = self.get_node(attached_port)
            node_scene_transform = node.graphics_object.sceneTransform()
            pos = node.geometry.port_scene_position(attached_port,
                                                    attached_port_index,
                                                    node_scene_transform)
            self._graphics_object.setPos(pos)

        self._graphics_object.move()

    def connect_to(self, port: Port):
        """
        Assigns a node to the required port.

        Parameters
        ----------
        port : Port
        """
        if self._ports[port.port_type] is not None:
            raise ValueError('Port already specified')

        was_incomplete = not self.is_complete
        self._ports[port.port_type] = port
        self.updated.emit(self)
        self.required_port = PortType.none
        if self.is_complete and was_incomplete:
            self.connection_completed.emit(self)

    def remove_from_nodes(self):
        for port in self._ports.values():
            if port is not None:
                port.remove_connection(self)

    @property
    def geometry(self) -> ConnectionGeometry:
        """
        Connection geometry

        Returns
        -------
        value : ConnectionGeometry
        """
        return self._connection_geometry

    def get_node(self, port_type: PortType) -> typing.Optional[Node]:
        """
        Get node

        Parameters
        ----------
        port_type : PortType

        Returns
        -------
        value : Node
        """
        port = self._ports[port_type]
        return port.node if port is not None else None

    @property
    def nodes(self):
        # TODO namedtuple; TODO order
        return (self.get_node(PortType.input), self.get_node(PortType.output))

    @property
    def ports(self):
        # TODO namedtuple; TODO order
        return (self._ports[PortType.input], self._ports[PortType.output])

    def get_port_index(self, port_type: PortType) -> int:
        """
        Get port index

        Parameters
        ----------
        port_type : PortType

        Returns
        -------
        index : int
        """
        return self._ports[port_type].index

    def clear_node(self, port_type: PortType):
        """
        Clear node

        Parameters
        ----------
        port_type : PortType
        """
        if self.is_complete:
            self.connection_made_incomplete.emit(self)

        port = self._ports[port_type]
        self._ports[port_type] = None
        port.remove_connection(self)

    @property
    def valid_ports(self):
        return {port_type: port
                for port_type, port in self._ports.items()
                if port is not None
                }

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
        ports = self.valid_ports
        if not ports:
            raise ValueError('No ports set')

        try:
            return ports[port_type].data_type
        except KeyError:
            valid_type, = ports
            return ports[valid_type].data_type

    @property
    def type_converter(self) -> typing.Optional[TypeConverter]:
        """
        The type converter used for the connection.

        Returns
        -------
        converter : TypeConverter or None
        """
        return self._converter

    @type_converter.setter
    def type_converter(self, converter: TypeConverter):
        self._converter = converter

    @property
    def is_complete(self) -> bool:
        """
        Connection is complete - in/out nodes are set

        Returns
        -------
        value : bool
        """
        return all(self._ports.values())

    def propagate_data(self, node_data: NodeData):
        """
        Propagate the given data from the output port -> input port.

        Parameters
        ----------
        node_data : NodeData
        """
        in_port, out_port = self.ports
        if not in_port:
            return

        if node_data is not None and self._converter:
            node_data = self._converter(node_data)

        in_port.node.propagate_data(node_data, in_port)

    @property
    def input_node(self) -> Node:
        'Input node'
        return self._ports[PortType.input].node

    @property
    def output_node(self) -> Node:
        'Output node'
        return self._ports[PortType.output].node

    # For backward-compatibility:
    output = output_node

    def propagate_empty_data(self):
        self.propagate_data(None)

    @property
    def last_hovered_node(self) -> Node:
        """
        Last hovered node

        Returns
        -------
        value : Node
        """
        return self._last_hovered_node

    @last_hovered_node.setter
    def last_hovered_node(self, node: Node):
        """
        Set last hovered node

        Parameters
        ----------
        node : Node
        """
        if node is None and self._last_hovered_node:
            self._last_hovered_node.reset_reaction_to_connection()
        self._last_hovered_node = node

    def interact_with_node(self, node: Node):
        """
        Interact with node

        Parameters
        ----------
        node : Node
        """
        self.last_hovered_node = node

    @property
    def requires_port(self) -> bool:
        """
        Requires port

        Returns
        -------
        value : bool
        """
        return self._required_port != PortType.none

    def __repr__(self):
        return (f'<{self.__class__.__name__} ports={self._ports}>')
