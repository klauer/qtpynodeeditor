import pytest
import qtpy.QtCore

import nodeeditor
from nodeeditor import PortType


class MyNodeData(nodeeditor.NodeData):
    data_type = nodeeditor.NodeDataType('MyNodeData', 'My Node Data')


class BasicDataModel(nodeeditor.NodeDataModel):
    name = 'MyDataModel'

    def model(self):
        return 'MyDataModel'

    def caption(self):
        return 'Caption'

    def n_ports(self, port_type):
        return 3

    def data_type(self, port_type, port_index):
        return MyNodeData.data_type

    def out_data(self, data):
        return MyNodeData()

    def set_in_data(self, node_data, port):
        ...

    def embedded_widget(self):
        return None

    # def node_style(self):
    #     return StyleCollection.instance().node_style()


# @pytest.mark.parametrize("model_class", [...])
@pytest.fixture(scope='function')
def model():
    return BasicDataModel


@pytest.fixture(scope='function')
def registry(model):
    registry = nodeeditor.DataModelRegistry()
    registry.register_model(model, category='My Category')
    return registry


@pytest.fixture(scope='function')
def scene(application, registry):
    return nodeeditor.FlowScene(registry=registry)


@pytest.fixture(scope='function')
def view(qtbot, scene):
    view = nodeeditor.FlowView(scene)
    qtbot.addWidget(view)
    view.setWindowTitle("nodeeditor test suite")
    view.resize(800, 600)
    view.show()
    return view


def test_instantiation(view):
    ...


def test_create_node(scene, model):
    node = scene.create_node(model)
    assert node in scene.nodes().values()
    assert node.id() in scene.nodes()


def test_selected_nodes(scene, model):
    node = scene.create_node(model)
    node.node_graphics_object().setSelected(True)
    assert scene.selected_nodes() == [node]


def test_create_connection(scene, view, model):
    node1 = scene.create_node(model)
    node2 = scene.create_node(model)
    scene.create_connection(
        node_in=node1, port_index_in=1,
        node_out=node2, port_index_out=2,
        converter=None
    )

    view.update()

    assert len(scene.connections()) == 1
    all_c1 = node1.node_state().all_connections
    assert len(all_c1) == 1
    all_c2 = node1.node_state().all_connections
    assert len(all_c2) == 1
    assert all_c1 == all_c2

    conn, = all_c1
    # conn_state = conn.connection_state()
    in_node = conn.get_node(PortType.input)
    in_port = conn.get_port_index(PortType.input)
    out_node = conn.get_node(PortType.output)
    out_port = conn.get_port_index(PortType.output)
    assert in_node == node1
    assert in_port == 1
    assert out_node == node2
    assert out_port == 2

    scene.delete_connection(conn)
    assert len(scene.connections()) == 0
    all_c1 = node1.node_state().all_connections
    assert len(all_c1) == 0
    all_c2 = node1.node_state().all_connections
    assert len(all_c2) == 0



def test_clear_scene(scene, view, model):
    node1 = scene.create_node(model)
    node2 = scene.create_node(model)
    scene.create_connection(
        node_in=node1, port_index_in=1,
        node_out=node2, port_index_out=2,
        converter=None
    )

    scene.clear_scene()

    assert len(scene.nodes()) == 0
    assert len(scene.connections()) == 0
    all_c1 = node1.node_state().all_connections
    assert len(all_c1) == 0
    all_c2 = node1.node_state().all_connections
    assert len(all_c2) == 0



def test_save_load(tmp_path, scene, view, model):
    node1 = scene.create_node(model)
    node2 = scene.create_node(model)

    created_nodes = (node1, node2)

    assert len(scene.nodes()) == len(created_nodes)

    for node in created_nodes:
        assert node in scene.nodes().values()
        assert node.id() in scene.nodes()

    fname = tmp_path / 'temp.flow'
    scene.save(fname)
    scene.load(fname)

    assert len(scene.nodes()) == len(created_nodes)

    for node in created_nodes:
        assert node not in scene.nodes().values()
        assert node.id() in scene.nodes()


def test_smoke_reacting(scene, view, model):
    node = scene.create_node(model)
    dtype = node.node_data_model().data_type(PortType.input, 0)
    node.react_to_possible_connection(
        reacting_port_type=PortType.input,
        reacting_data_type=dtype,
        scene_point=qtpy.QtCore.QPointF(0, 0),
    )
    view.update()
    node.reset_reaction_to_connection()


def test_smoke_node_size_updated(scene, view, model):
    node = scene.create_node(model)
    node.on_node_size_updated()
    view.update()
