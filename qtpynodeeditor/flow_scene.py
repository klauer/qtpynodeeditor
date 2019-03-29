import contextlib
import os
import json
from qtpy.QtCore import QDir, QPoint, QPointF, Qt, QObject, Signal
from qtpy.QtWidgets import QFileDialog, QGraphicsScene

from . import style as style_module
from .connection import Connection
from .connection_graphics_object import ConnectionGraphicsObject
from .data_model_registry import DataModelRegistry
from .node import Node
from .node_data import NodeDataType, NodeDataModel
from .node_graphics_object import NodeGraphicsObject
from .port import PortType, Port
from .type_converter import TypeConverter, DefaultTypeConverter


def locate_node_at(scene_point, scene, view_transform):
    items = scene.items(scene_point, Qt.IntersectsItemShape,
                        Qt.DescendingOrder, view_transform)
    filtered_items = [item for item in items
                      if isinstance(item, NodeGraphicsObject)]
    return filtered_items[0].node if filtered_items else None


class FlowSceneModel(QObject):
    connection_created = Signal(Connection)
    connection_deleted = Signal(Connection)

    # Node has been created but not on the scene yet. (see: node_placed())
    node_created = Signal(Node)
    node_deleted = Signal(Node)

    def __init__(self, registry=None, parent=None):
        super().__init__(parent=parent)
        self._connections = []
        self._nodes = {}

        if registry is None:
            registry = DataModelRegistry()

        self._registry = registry

        # this connection should come first
        self.connection_created.connect(self._setup_connection_signals)
        self.connection_created.connect(self._send_connection_created_to_nodes)
        self.connection_deleted.connect(self._send_connection_deleted_to_nodes)

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

    @property
    def nodes(self) -> dict:
        """
        All nodes in the scene

        Returns
        -------
        value : dict
            Key: uuid
            Value: Node
        """
        return dict(self._nodes)

    @property
    def connections(self) -> list:
        """
        All connections in the scene

        Returns
        -------
        conn : list of Connection
        """
        return list(self._connections)

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

    def _setup_connection_signals(self, conn: Connection):
        """
        Setup connection signals

        Parameters
        ----------
        conn : Connection
        """
        conn.connection_made_incomplete.connect(
            self.connection_deleted.emit, Qt.UniqueConnection)

    def _send_connection_created_to_nodes(self, conn: Connection):
        """
        Send connection created to nodes

        Parameters
        ----------
        conn : Connection
        """
        input_node, output_node = conn.nodes
        assert input_node is not None
        assert output_node is not None
        output_node.model.output_connection_created(conn)
        input_node.model.input_connection_created(conn)

    def _send_connection_deleted_to_nodes(self, conn: Connection):
        """
        Send connection deleted to nodes

        Parameters
        ----------
        conn : Connection
        """
        input_node, output_node = conn.nodes
        assert input_node is not None
        assert output_node is not None
        output_node.model.output_connection_deleted(conn)
        input_node.model.input_connection_deleted(conn)

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
            yield node.model

    def iterate_over_node_data_dependent_order(self):
        """
        Generator: Iterate over node data dependent order
        """
        visited_nodes = []

        # A leaf node is a node with no input ports, or all possible input ports empty
        def is_node_leaf(node, model):
            for port in node[PortType.input].values():
                if not port.connections:
                    return False

            return True

        # Iterate over "leaf" nodes
        for node in self._nodes.values():
            model = node.model
            if is_node_leaf(node, model):
                yield model
                visited_nodes.append(node)

        def are_node_inputs_visited_before(node, model):
            for port in node[PortType.input].values():
                for conn in port.connections:
                    other = conn.get_node(PortType.output)
                    if visited_nodes and other == visited_nodes[-1]:
                        return False
            return True

        # Iterate over dependent nodes
        while len(self._nodes) != len(visited_nodes):
            for node in self._nodes.values():
                if node in visited_nodes and node is not visited_nodes[-1]:
                    continue

                model = node.model
                if are_node_inputs_visited_before(node, model):
                    yield model
                    visited_nodes.append(node)

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

    def remove_node(self, node: Node):
        """
        Remove node

        Parameters
        ----------
        node : Node
        """
        self.node_deleted.emit(node)
        for conn in list(node.state.all_connections):
            self.delete_connection(conn)

        node._cleanup()
        del self._nodes[node.id]

    def _restore_node(self, node_json: dict) -> Node:
        """
        Restore a node from a state dictionary

        Parameters
        ----------
        node_json : dict

        Returns
        -------
        value : Node
        """
        with self._new_node_context(node_json["model"]["name"]) as node:
            ...

        return node

    @contextlib.contextmanager
    def _new_node_context(self, data_model_name):
        'Context manager: creates Node/yields it, handling necessary Signals'
        data_model = self._registry.create(data_model_name)
        if not data_model:
            raise ValueError("No registered model with name {}"
                             "".format(data_model_name))

        node = Node(data_model)
        yield node
        self._nodes[node.id] = node
        self.node_created.emit(node)

    def restore_node(self, node_json: dict) -> Node:
        """
        Restore a node from a state dictionary

        Parameters
        ----------
        node_json : dict

        Returns
        -------
        value : Node
        """
        with self._new_node_context(node_json["model"]["name"]) as node:
            node.__setstate__(node_json)

        return node

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


class FlowScene(QGraphicsScene, FlowSceneModel, QObject):
    # Re-implement Signals from FlowSceneModel due to limitations of PyQt:
    connection_created = Signal(Connection)
    connection_deleted = Signal(Connection)
    node_created = Signal(Node)
    node_deleted = Signal(Node)
    # End of re-implemented signals

    connection_hover_left = Signal(Connection)
    connection_hovered = Signal(Connection, QPoint)

    #  Node has been added to the scene.
    #  Connect to self signal if need a correct position of node.
    node_placed = Signal(Node)
    node_context_menu = Signal(Node, QPointF)
    node_double_clicked = Signal(Node)
    node_hover_left = Signal(Node)
    node_hovered = Signal(Node, QPoint)
    node_moved = Signal(Node, QPointF)

    def __init__(self, registry=None, style=None, parent=None,
                 allow_node_creation=True, allow_node_deletion=True):
        '''
        Create a new flow scene

        Parameters
        ----------
        registry : DataModelRegistry, optional
        style : StyleCollection, optional
        parent : QObject, optional
        '''
        super().__init__(registry=registry, parent=parent)

        if style is None:
            style = style_module.default_style

        self._style = style
        self.allow_node_deletion = allow_node_creation
        self.allow_node_creation = allow_node_deletion

        self.setItemIndexMethod(QGraphicsScene.NoIndex)

    def _cleanup(self):
        self.clear_scene()

    def __del__(self):
        try:
            self._cleanup()
        except Exception:
            ...

    @property
    def allow_node_creation(self):
        return self._allow_node_creation

    @allow_node_creation.setter
    def allow_node_creation(self, allow):
        self._allow_node_creation = bool(allow)

    @property
    def allow_node_deletion(self):
        return self._allow_node_deletion

    @allow_node_deletion.setter
    def allow_node_deletion(self, allow):
        self._allow_node_deletion = bool(allow)

    @property
    def style_collection(self) -> style_module.StyleCollection:
        'The style collection for the scene'
        return self._style

    def locate_node_at(self, point, transform):
        return locate_node_at(point, self, transform)

    def create_connection(self, port_a: Port, port_b: Port = None, *,
                          converter: TypeConverter = None) -> Connection:
        """
        Create a connection

        Parameters
        ----------
        port_a : Port
            The first port, either input or output
        port_b : Port, optional
            The second port, opposite of the type of port_a
        converter : TypeConverter, optional
            The type converter to use for data propagation

        Returns
        -------
        value : Connection
        """
        connection = Connection(port_a=port_a, port_b=port_b, style=self._style)
        if port_a is not None:
            port_a.add_connection(connection)
        if port_b is not None:
            port_b.add_connection(connection)

        cgo = ConnectionGraphicsObject(self, connection)
        # after self function connection points are set to node port
        connection.graphics_object = cgo
        self._connections.append(connection)

        if not port_a or not port_b:
            # This connection isn't truly created yet. It's only partially
            # created.  Thus, don't send the connection_created(...) signal.
            connection.connection_completed.connect(self.connection_created.emit)
        else:
            in_port, out_port = connection.ports
            out_port.node.on_data_updated(out_port)
            self.connection_created.emit(connection)

        return connection

    def create_connection_by_index(
            self, node_in: Node, port_index_in: int,
            node_out: Node, port_index_out: int,
            converter: TypeConverter) -> Connection:
        """
        Create connection

        Parameters
        ----------
        node_in : Node
        port_index_in : int
        node_out : Node
        port_index_out : int
        converter : TypeConverter

        Returns
        -------
        value : Connection
        """
        port_in = node_in[PortType.input][port_index_in]
        port_out = node_out[PortType.output][port_index_out]
        return self.create_connection(port_out, port_in, converter=converter)

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

        connection = self.create_connection_by_index(
            node_in, port_index_in,
            node_out, port_index_out,
            converter=get_converter())

        # Note: the connection_created(...) signal has already been sent by
        # create_connection(...)
        return connection

    def create_node(self, data_model: NodeDataModel) -> Node:
        """
        Create a node in the scene

        Parameters
        ----------
        data_model : NodeDataModel

        Returns
        -------
        value : Node
        """
        with self._new_node_context(data_model.name) as node:
            ngo = NodeGraphicsObject(self, node)
            node.graphics_object = ngo

        return node

    def restore_node(self, node_json: dict) -> Node:
        """
        Restore a node from a state dictinoary

        Parameters
        ----------
        node_json : dict

        Returns
        -------
        value : Node
        """
        # NOTE: Overrides FlowSceneModel.restore_node
        with self._new_node_context(node_json["model"]["name"]) as node:
            node.graphics_object = NodeGraphicsObject(self, node)
            node.__setstate__(node_json)
        return node

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
            node.position = (pos_x * scale, pos_y * scale)

    def selected_nodes(self) -> list:
        """
        Selected nodes

        Returns
        -------
        value : list of Node
        """
        return [item.node for item in self.selectedItems()
                if isinstance(item, NodeGraphicsObject)]
