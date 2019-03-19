import pytest
import tempfile

import nodeeditor
from nodeeditor import PortType


class MyNodeData(nodeeditor.NodeData):
    _type = nodeeditor.NodeDataType('MyNodeData', 'My Node Data')


class BasicDataModel(nodeeditor.NodeDataModel):
    def name(self):
        return 'MyDataModel'

    def model(self):
        return 'MyDataModel'

    def caption(self):
        return 'Caption'

    def save(self):
        return {'name': self.name()}

    def n_ports(self, port_type):
        return 3

    def data_type(self, port_type, port_index):
        return MyNodeData._type

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
    return BasicDataModel()


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
    print(view)
    ...


def test_create_node(scene, model):
    node = scene.create_node(model)
    assert node in scene.nodes().values()
    assert node.id() in scene.nodes()


def test_create_connection(scene, model):
    node1 = scene.create_node(model)
    node2 = scene.create_node(model)
    scene.create_connection(
        node_in=node1, port_index_in=1,
        node_out=node2, port_index_out=2,
        converter=None
    )
    assert len(scene.connections()) == 1
    all_c1 = node1.node_state().all_connections
    assert len(all_c1) == 1
    all_c2 = node1.node_state().all_connections
    assert len(all_c2) == 1
    assert all_c1 == all_c2

    conn, = all_c1
    # conn_state = conn.connection_state()
    in_node = conn.get_node(PortType.In)
    in_port = conn.get_port_index(PortType.In)
    out_node = conn.get_node(PortType.Out)
    out_port = conn.get_port_index(PortType.Out)
    assert in_node == node1
    assert in_port == 1
    assert out_node == node2
    assert out_port == 2


def test_save_load(scene, view, model):
    node1 = scene.create_node(model)
    node2 = scene.create_node(model)

    created_nodes = (node1, node2)

    assert len(scene.nodes()) == len(created_nodes)

    for node in created_nodes:
        assert node in scene.nodes().values()
        assert node.id() in scene.nodes()

    # with tempfile.NamedTemporaryFile(mode='wt') as f:
    fname = 'temp.flow'
    scene.save(fname)
    # f.flush()
    print(open(fname, 'rt').read())
    scene.load(fname)

    assert len(scene.nodes()) == len(created_nodes)

    for node in created_nodes:
        assert node not in scene.nodes().values()
        assert node.id() in scene.nodes()
