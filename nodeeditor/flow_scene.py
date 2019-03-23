import os
import json
from qtpy.QtCore import (QDir, QPoint, QPointF, QSizeF, Qt)
from qtpy.QtCore import Signal
from qtpy.QtWidgets import QFileDialog, QGraphicsScene

from . import style as style_module
from .connection import Connection
from .connection_graphics_object import ConnectionGraphicsObject
from .data_model_registry import DataModelRegistry
from .node import Node
from .node_data import NodeDataType, NodeDataModel
from .node_graphics_object import NodeGraphicsObject
from .port import PortType, PortIndex
from .type_converter import TypeConverter, DefaultTypeConverter


def locate_node_at(scene_point, scene, view_transform):
    # items under cursor
    items = scene.items(scene_point, Qt.IntersectsItemShape,
                        Qt.DescendingOrder, view_transform)
    filtered_items = [item for item in items
                      if isinstance(item, NodeGraphicsObject)]
    return filtered_items[0].node() if filtered_items else None


class FlowScene(QGraphicsScene):
    connection_created = Signal(Connection)
    connection_deleted = Signal(Connection)
    connection_hover_left = Signal(Connection)
    connection_hovered = Signal(Connection, QPoint)

    # Node has been created but not on the scene yet. (see: node_placed())
    node_created = Signal(Node)

    #  Node has been added to the scene.
    #  Connect to self signal if need a correct position of node.
    node_placed = Signal(Node)
    node_context_menu = Signal(Node, QPointF)
    node_deleted = Signal(Node)
    node_double_clicked = Signal(Node)
    node_hover_left = Signal(Node)
    node_hovered = Signal(Node, QPoint)
    node_moved = Signal(Node, QPointF)

    def __init__(self, registry=None, style=None, parent=None):
        '''
        Create a new flow scene

        Parameters
        ----------
        registry : DataModelRegistry, optional
        style : StyleCollection, optional
        parent : QObject, optional
        '''
        super().__init__(parent=parent)
        self._connections = []
        self._nodes = {}

        if registry is None:
            registry = DataModelRegistry()

        if style is None:
            style = style_module.default_style

        self._style = style
        self._registry = registry

        self.setItemIndexMethod(QGraphicsScene.NoIndex)

        # self connection should come first
        self.connection_created.connect(self.setup_connection_signals)
        self.connection_created.connect(self.send_connection_created_to_nodes)
        self.connection_deleted.connect(self.send_connection_deleted_to_nodes)

    def _cleanup(self):
        self.clear_scene()

    def __del__(self):
        try:
            self._cleanup()
        except Exception:
            ...

    def locate_node_at(self, point, transform):
        return locate_node_at(point, self, transform)

    def create_connection_node(self, node: Node, connected_port: PortType,
                               port_index: PortIndex) -> Connection:
        """
        Create connection

        Parameters
        ----------
        node : Node
        connected_port : PortType
        port_index : PortIndex

        Returns
        -------
        value : Connection
        """
        connection = Connection.from_node(connected_port, node, port_index,
                                          style=self._style)
        cgo = ConnectionGraphicsObject(self, connection)

        # after self function connection points are set to node port
        connection.graphics_object = cgo
        self._connections.append(connection)

        # Note: self connection isn't truly created yet. It's only partially created.
        # Thus, don't send the connection_created(...) signal.
        connection.connection_completed.connect(self.connection_created.emit)
        return connection

    def create_connection(self,
                          node_in: Node, port_index_in: PortIndex,
                          node_out: Node, port_index_out: PortIndex,
                          converter: TypeConverter) -> Connection:
        """
        Create connection

        Parameters
        ----------
        node_in : Node
        port_index_in : PortIndex
        node_out : Node
        port_index_out : PortIndex
        converter : TypeConverter

        Returns
        -------
        value : Connection
        """
        connection = Connection.from_nodes(node_in, port_index_in,
                                           node_out, port_index_out,
                                           converter=converter,
                                           style=self._style)
        cgo = ConnectionGraphicsObject(self, connection)
        node_in.state.set_connection(PortType.input, port_index_in, connection)
        node_out.state.set_connection(PortType.output, port_index_out, connection)

        # after self function connection points are set to node port
        connection.graphics_object = cgo

        # trigger data propagation
        node_out.on_data_updated(port_index_out)
        self._connections.append(connection)
        self.connection_created.emit(connection)
        return connection

    def restore_connection(self, connection_json: dict) -> Connection:
        """
        Restore connection

        Parameters
        ----------
        connection_json : dict

        Returns
        -------
        value : Connection
        """
        node_in_id = connection_json["in_id"]
        node_out_id = connection_json["out_id"]

        port_index_in = connection_json["in_index"]
        port_index_out = connection_json["out_index"]
        node_in = self._nodes[node_in_id]
        node_out = self._nodes[node_out_id]

        def get_converter():
            converter = connection_json.get("converter", None)
            if converter is None:
                return DefaultTypeConverter

            in_type = NodeDataType(
                id=converter["in"]["id"],
                name=converter["in"]["name"],
            )

            out_type = NodeDataType(
                id=converter["out"]["id"],
                name=converter["out"]["name"],
            )

            return self._registry.get_type_converter(out_type, in_type)

        connection = self.create_connection(
            node_in, port_index_in,
            node_out, port_index_out,
            converter=get_converter())

        # Note: the connection_created(...) signal has already been sent by
        # create_connection(...)
        return connection

    def delete_connection(self, connection: Connection):
        """
        Delete connection

        Parameters
        ----------
        connection : Connection
        """
        try:
            self._connections.remove(connection)
        except ValueError:
            ...
        else:
            connection.remove_from_nodes()
            connection._cleanup()

    def create_node(self, data_model: NodeDataModel) -> Node:
        """
        Create node

        Parameters
        ----------
        data_model : NodeDataModel

        Returns
        -------
        value : Node
        """
        model = self._registry.create(data_model.name)
        node = Node(model)
        ngo = NodeGraphicsObject(self, node)
        node.graphics_object = ngo
        self._nodes[node.id] = node
        self.node_created.emit(node)
        return node

    def restore_node(self, node_json: dict) -> Node:
        """
        Restore node

        Parameters
        ----------
        node_json : dict

        Returns
        -------
        value : Node
        """
        model_name = node_json["model"]["name"]
        data_model = self._registry.create(model_name)
        if not data_model:
            raise ValueError("No registered model with name {}".format(model_name))

        node = Node(data_model)
        node.graphics_object = NodeGraphicsObject(self, node)
        node.__setstate__(node_json)

        self._nodes[node.id] = node
        self.node_created.emit(node)
        return node

    def remove_node(self, node: Node):
        """
        Remove node

        Parameters
        ----------
        node : Node
        """
        # call signal
        self.node_deleted.emit(node)
        for conn in list(node.state.all_connections):
            self.delete_connection(conn)

        node._cleanup()
        del self._nodes[node.id]

    @property
    def registry(self) -> DataModelRegistry:
        """
        Registry

        Returns
        -------
        value : DataModelRegistry
        """
        return self._registry

    @registry.setter
    def registry(self, registry: DataModelRegistry):
        self._registry = registry

    def to_digraph(self):
        '''
        Create a networkx digraph

        Returns
        -------
        digraph : networkx.DiGraph
            The generated DiGraph

        Raises
        ------
        ImportError
            If networkx is unavailable
        '''
        import networkx
        graph = networkx.DiGraph()
        for node in self._nodes.values():
            graph.add_node(node)

        for node in self._nodes.values():
            graph.add_edges_from(conn.nodes
                                 for conn in node.state.all_connections)

        return graph

    def auto_arrange(self, layout='bipartite', scale=700, align='horizontal',
                     **kwargs):
        '''
        Automatically arrange nodes with networkx, if available

        Raises
        ------
        ImportError
            If networkx is unavailable
        '''
        import networkx
        dig = self.to_digraph()

        layouts = {
            name: getattr(networkx.layout, '{}_layout'.format(name))
            for name in ('bipartite', 'circular', 'kamada_kawai', 'random',
                         'shell', 'spring', 'spectral')
        }

        try:
            layout_func = layouts[layout]
        except KeyError:
            raise ValueError('Unknown layout type {}'.format(layout)) from None

        layout = layout_func(dig, **kwargs)
        for node, pos in layout.items():
            pos_x, pos_y = pos
            self.set_node_position(node, (pos_x * scale, pos_y * scale))

    def iterate_over_nodes(self):
        """
        Generator: Iterate over nodes
        """
        for node in self._nodes.values():
            yield node

    def iterate_over_node_data(self):
        """
        Generator: Iterate over node data
        """
        for node in self._nodes.values():
            yield node.data

    def iterate_over_node_data_dependent_order(self):
        """
        Generator: Iterate over node data dependent order
        """
        visited_nodes = []

        # A leaf node is a node with no input ports, or all possible input ports empty
        def is_node_leaf(node, model):
            for i in range(model.n_ports(PortType.input)):
                connections = node.state.connections(PortType.input, i)
                if connections is None:
                    return False

            return True

        # Iterate over "leaf" nodes
        for node in self._nodes.values():
            model = node.data
            if is_node_leaf(node, model):
                yield model
                visited_nodes.append(node)

        def are_node_inputs_visited_before(node, model):
            for i in range(model.n_ports(PortType.input)):
                connections = node.state.connections(PortType.input, i)
                for conn in connections:
                    other = conn.get_node(PortType.output)
                    if visited_nodes and other == visited_nodes[-1]:
                        return False
            return True

        # Iterate over dependent nodes
        while len(self._nodes) != len(visited_nodes):
            for node in self._nodes.values():
                if node in visited_nodes and node is not visited_nodes[-1]:
                    continue

                model = node.data
                if are_node_inputs_visited_before(node, model):
                    yield model
                    visited_nodes.append(node)

    def get_node_position(self, node: Node) -> QPointF:
        """
        Get node position

        Parameters
        ----------
        node : Node

        Returns
        -------
        value : QPointF
        """
        return node.graphics_object.pos()

    def set_node_position(self, node: Node, pos: QPointF):
        """
        Set node position

        Parameters
        ----------
        node : Node
        pos : QPointF
        """
        if not isinstance(pos, QPointF):
            px, py = pos
            pos = QPointF(px, py)

        ngo = node.graphics_object
        ngo.setPos(pos)
        ngo.move_connections()

    def get_node_size(self, node: Node) -> QSizeF:
        """
        Get node size

        Parameters
        ----------
        node : Node

        Returns
        -------
        value : QSizeF
        """
        return QSizeF(node.geometry.width, node.geometry.height)

    def nodes(self) -> dict:
        """
        Nodes

        Returns
        -------
        value : dict
            Key: uuid
            Value: Node
        """
        return dict(self._nodes)

    def connections(self) -> dict:
        """
        Connections

        Returns
        -------
        conn : list of Connection
        """
        return list(self._connections)

    def selected_nodes(self) -> list:
        """
        Selected nodes

        Returns
        -------
        value : list of Node
        """
        return [item.node() for item in self.selectedItems()
                if isinstance(item, NodeGraphicsObject)]

    def clear_scene(self):
        # Manual node cleanup. Simply clearing the holding datastructures
        # doesn't work, the code crashes when there are both nodes and
        # connections in the scene. (The data propagation internal logic tries
        # to propagate data through already freed connections.)
        for conn in list(self._connections):
            self.delete_connection(conn)

        for node in list(self._nodes.values()):
            self.remove_node(node)

    def save(self, file_name=None):
        if file_name is None:
            file_name, _ = QFileDialog.getSaveFileName(
                None, "Open Flow Scene", QDir.homePath(),
                "Flow Scene Files (.flow)")

        if file_name:
            file_name = str(file_name)
            if not file_name.endswith(".flow"):
                file_name += ".flow"

            with open(file_name, 'wt') as f:
                json.dump(self.__getstate__(), f)

    def load(self, file_name=None):
        if file_name is None:
            file_name, _ = QFileDialog.getOpenFileName(
                None, "Open Flow Scene", QDir.homePath(),
                "Flow Scene Files (.flow)")

        if not os.path.exists(file_name):
            return

        with open(file_name, 'rt') as f:
            doc = json.load(f)

        self.__setstate__(doc)

    def __getstate__(self) -> dict:
        """
        Save scene state to a dictionary

        Returns
        -------
        value : dict
        """
        scene_json = {}
        nodes_json_array = []
        connection_json_array = []
        for node in self._nodes.values():
            nodes_json_array.append(node.__getstate__())

        scene_json["nodes"] = nodes_json_array
        for connection in self._connections:
            connection_json = connection.__getstate__()
            if connection_json:
                connection_json_array.append(connection_json)

        scene_json["connections"] = connection_json_array
        return scene_json

    def __setstate__(self, doc: dict):
        """
        Load scene state from a dictionary

        Parameters
        ----------
        doc : dict
            Dictionary of settings
        """
        self.clear_scene()

        for node in doc["nodes"]:
            self.restore_node(node)

        for connection in doc["connections"]:
            self.restore_connection(connection)

    def setup_connection_signals(self, conn: Connection):
        """
        Setup connection signals

        Parameters
        ----------
        conn : Connection
        """
        conn.connection_made_incomplete.connect(
            self.connection_deleted.emit, Qt.UniqueConnection)

    def send_connection_created_to_nodes(self, conn: Connection):
        """
        Send connection created to nodes

        Parameters
        ----------
        conn : Connection
        """
        from_ = conn.get_node(PortType.output)
        to = conn.get_node(PortType.input)
        assert from_ is not None
        assert to is not None
        from_.data.output_connection_created(conn)
        to.data.input_connection_created(conn)

    def send_connection_deleted_to_nodes(self, conn: Connection):
        """
        Send connection deleted to nodes

        Parameters
        ----------
        conn : Connection
        """
        from_ = conn.get_node(PortType.output)
        to = conn.get_node(PortType.input)
        assert from_ is not None
        assert to is not None
        from_.data.output_connection_deleted(conn)
        to.data.input_connection_deleted(conn)
