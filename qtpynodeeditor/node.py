import collections
import typing
import uuid
from typing import Optional

from qtpy.QtCore import QObject, QPointF, QSizeF

from .base import Serializable
from .enums import ReactToConnectionState
from .node_data import NodeData, NodeDataModel, NodeDataType
from .node_geometry import NodeGeometry
from .node_graphics_object import NodeGraphicsObject
from .node_state import NodeState
from .port import Port, PortType
from .style import NodeStyle


class Node(QObject, Serializable):
    _model: NodeDataModel
    _uid: str
    _style: NodeStyle
    _state: NodeState
    _geometry: NodeGeometry
    _graphics_obj: Optional[NodeGraphicsObject]

    def __init__(self, data_model: NodeDataModel):
        '''
        A single Node in the scene

        Parameters
        ----------
        data_model : NodeDataModel
        '''
        super().__init__()
        self._model = data_model
        self._uid = str(uuid.uuid4())
        self._style = data_model.node_style
        self._state = NodeState(self)
        self._geometry = NodeGeometry(self)
        self._graphics_obj = None
        self._geometry.recalculate_size()

        # propagate data: model => node
        self._model.data_updated.connect(self._on_port_index_data_updated)
        self._model.embedded_widget_size_updated.connect(self.on_node_size_updated)

    def __hash__(self):
        return id(self._uid)

    def __eq__(self, node):
        try:
            return node.id == self.id and self.model is node.model
        except AttributeError:
            return False

    def has_any_connection(self, node: 'Node') -> bool:
        """
        Is this node connected to `node` through any port?

        Parameters
        ----------
        node : Node
            The node to check connectivity

        Returns
        -------
        connected : bool
        """
        return any(self.has_connection_by_port_type(node, port_type)
                   for port_type in PortType)

    def has_connection_by_port_type(self, target: 'Node',
                                    port_type: PortType) -> bool:
        """
        Is this node connected to `target` through an input/output port?

        Parameters
        ----------
        target : Node
            The target node to check connectivity
        port_type : PortType
            The port type (``PortType.input``, ``PortType.output``) to check

        Returns
        -------
        connected : bool
        """
        return any(
            path[-1] == target
            for path in self.walk_paths_by_port_type(port_type)
        )

    def walk_paths_by_port_type(
        self, port_type: PortType
    ) -> typing.Generator[tuple["Node", ...], None, None]:
        """
        Yields paths to connected nodes by port type

        Yields
        ------
        node_path : tuple
            The path to the node
        """
        seen: set[typing.Union[Node, None]]
        pending: typing.Deque[
            tuple[list[Node], Node]
        ]

        seen = {None}
        pending = collections.deque([([], self)])

        if port_type == PortType.output:
            def get_connection_nodes(state):
                for con in state.output_connections:
                    yield con.input_node
        elif port_type == PortType.input:
            def get_connection_nodes(state):
                for con in state.input_connections:
                    yield con.output_node
        else:
            raise ValueError(f'Unexpected port_type {port_type}')

        while pending:
            node_path, node = pending.popleft()
            seen.add(node)
            if node is not self:
                yield tuple(node_path) + (node, )

            node_path = list(node_path) + [node]
            for node in get_connection_nodes(node.state):
                if node not in seen:
                    pending.append((node_path, node))

    def __getitem__(self, key):
        return self._state[key]

    def _cleanup(self):
        if self._graphics_obj is not None:
            self._graphics_obj._cleanup()
            self._graphics_obj = None
            self._geometry = None

    def __getstate__(self) -> dict:
        """
        Save

        Returns
        -------
        value : dict
        """
        assert self._graphics_obj is not None
        return {
            "id": self._uid,
            "model": self._model.__getstate__(),
            "position": {"x": self._graphics_obj.pos().x(),
                         "y": self._graphics_obj.pos().y()}
        }

    def __setstate__(self, state: dict):
        """
        Restore

        Parameters
        ----------
        state : dict
        """
        self._uid = state["id"]
        if self._graphics_obj:
            pos = state["position"]
            self.position = (pos["x"], pos["y"])
        self._model.__setstate__(state["model"])

    @property
    def id(self) -> str:
        """
        Node unique identifier (uuid)

        Returns
        -------
        value : str
        """
        return self._uid

    def react_to_possible_connection(self, reacting_port_type: PortType,
                                     reacting_data_type: NodeDataType,
                                     scene_point: QPointF
                                     ):
        """
        React to possible connection

        Parameters
        ----------
        port_type : PortType
        node_data_type : NodeDataType
        scene_point : QPointF
        """
        if self._graphics_obj is None:
            return

        transform = self._graphics_obj.sceneTransform()
        inverted, invertible = transform.inverted()
        if invertible:
            pos = inverted.map(scene_point)
            self._geometry.dragging_position = pos
        self._graphics_obj.update()
        self._state.set_reaction(ReactToConnectionState.reacting,
                                 reacting_port_type, reacting_data_type)

    def reset_reaction_to_connection(self):
        self._state.set_reaction(ReactToConnectionState.not_reacting)
        self._graphics_obj.update()

    @property
    def graphics_object(self) -> Optional[NodeGraphicsObject]:
        """
        Get/set the associated node graphics object.

        Returns
        -------
        value : NodeGraphicsObject
        """
        return self._graphics_obj

    @graphics_object.setter
    def graphics_object(self, graphics: NodeGraphicsObject):
        self._graphics_obj = graphics
        self._geometry.recalculate_size()

    @property
    def geometry(self) -> NodeGeometry:
        """
        Get the node geometry.

        Returns
        -------
        value : NodeGeometry
        """
        return self._geometry

    @property
    def model(self) -> NodeDataModel:
        """
        Get the node data model.

        Returns
        -------
        value : NodeDataModel
        """
        return self._model

    def propagate_data(self, node_data: NodeData, input_port: Port):
        """
        Propagates incoming data to the underlying model.

        Parameters
        ----------
        node_data : NodeData
        input_port : int
        """
        if input_port.node is not self:
            raise ValueError('Port does not belong to this Node')
        elif input_port.port_type != PortType.input:
            raise ValueError('Port is not an input port')

        self._model.set_in_data(node_data, input_port)

        if self._graphics_obj is not None:
            # Recalculate the nodes visuals. A data change can result in the
            # node taking more space than before, so self forces a
            # recalculate+repaint on the affected node
            self._graphics_obj.set_geometry_changed()
            self._geometry.recalculate_size()
            self._graphics_obj.update()
            self._graphics_obj.move_connections()

    def _on_port_index_data_updated(self, port_index: int):
        """
        Data has been updated on this Node's output port port_index;
        propagate it to any connections.

        Parameters
        ----------
        index : int
        """
        port = self[PortType.output][port_index]
        self.on_data_updated(port)

    def on_data_updated(self, port: Port):
        """
        Fetches data from model's output port and propagates it along the
        connection

        Parameters
        ----------
        port : Port
        """
        node_data = port.data
        for conn in port.connections:
            conn.propagate_data(node_data)

    def on_node_size_updated(self):
        """
        update the graphic part if the size of the embeddedwidget changes
        """
        widget = self.model.embedded_widget()
        if widget:
            widget.adjustSize()

        self.geometry.recalculate_size()
        for conn in self.state.all_connections:
            conn.graphics_object.move()

    @property
    def size(self) -> QSizeF:
        """
        Get the node size

        Parameters
        ----------
        node : Node

        Returns
        -------
        value : QSizeF
        """
        return self._geometry.size

    @property
    def position(self) -> QPointF:
        """
        Get the node position

        Parameters
        ----------
        node : Node

        Returns
        -------
        value : QPointF
        """
        if self._graphics_obj is not None:
            return self._graphics_obj.pos()

    @position.setter
    def position(self, pos):
        if not isinstance(pos, QPointF):
            px, py = pos
            pos = QPointF(px, py)

        self._graphics_obj.setPos(pos)
        self._graphics_obj.move_connections()

    @property
    def style(self) -> NodeStyle:
        'Node style'
        return self._style

    @property
    def state(self) -> NodeState:
        """
        Node state

        Returns
        -------
        value : NodeState
        """
        return self._state

    def __repr__(self):
        return (f'<{self.__class__.__name__} model={self._model} '
                f'uid={self._uid!r}>')
