import unittest.mock

import pytest
import qtpy.QtCore

import qtpynodeeditor as nodeeditor
from qtpynodeeditor import PortType


class MyNodeData(nodeeditor.NodeData):
    data_type = nodeeditor.NodeDataType('MyNodeData', 'My Node Data')


class MyOtherNodeData(nodeeditor.NodeData):
    data_type = nodeeditor.NodeDataType('MyOtherNodeData', 'My Other Node Data')


class BasicDataModel(nodeeditor.NodeDataModel):
    name = 'MyDataModel'
    caption = 'Caption'
    caption_visible = True
    num_ports = {'input': 3,
                 'output': 3
                 }
    data_type = MyNodeData.data_type

    def model(self):
        return 'MyDataModel'

    def out_data(self, port_index):
        return MyNodeData()

    def set_in_data(self, node_data, port):
        ...

    def embedded_widget(self):
        return None


class BasicOtherDataModel(nodeeditor.NodeDataModel):
    name = 'MyOtherDataModel'
    caption = 'Caption'
    caption_visible = True
    num_ports = {'input': 1,
                 'output': 1
                 }
    data_type = MyOtherNodeData.data_type


# @pytest.mark.parametrize("model_class", [...])
@pytest.fixture(scope='function')
def model():
    return BasicDataModel


@pytest.fixture(scope='function')
def other_model():
    return BasicOtherDataModel


@pytest.fixture(scope='function')
def registry(model, other_model):
    registry = nodeeditor.DataModelRegistry()
    registry.register_model(model, category='My Category')
    registry.register_model(other_model, category='My Category')
    return registry


@pytest.fixture(scope='function')
def scene(qapp, registry):
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
    assert node in scene.nodes.values()
    assert node.id in scene.nodes

    assert scene.allow_node_creation
    assert scene.allow_node_deletion


def test_selected_nodes(scene, model):
    node = scene.create_node(model)
    node.graphics_object.setSelected(True)
    assert scene.selected_nodes() == [node]


def test_create_connection(scene, view, model):
    node1 = scene.create_node(model)
    node2 = scene.create_node(model)
    scene.create_connection(node2[PortType.output][2],
                            node1[PortType.input][1],
                            )

    view.update()

    assert len(scene.connections) == 1
    all_c1 = node1.state.all_connections
    assert len(all_c1) == 1
    all_c2 = node1.state.all_connections
    assert len(all_c2) == 1
    assert all_c1 == all_c2

    conn, = all_c1
    # conn_state = conn.state
    in_node = conn.get_node(PortType.input)
    in_port = conn.get_port_index(PortType.input)
    out_node = conn.get_node(PortType.output)
    out_port = conn.get_port_index(PortType.output)
    assert in_node == node1
    assert in_port == 1
    assert out_node == node2
    assert out_port == 2

    scene.delete_connection(conn)
    assert len(scene.connections) == 0
    all_c1 = node1.state.all_connections
    assert len(all_c1) == 0
    all_c2 = node1.state.all_connections
    assert len(all_c2) == 0


def test_create_connection_with_converter(scene, view, model, other_model):
    node1 = scene.create_node(model)
    node2 = scene.create_node(other_model)

    # Converter not registerd, must raise Exception
    with pytest.raises(nodeeditor.ConnectionDataTypeFailure):
        scene.create_connection(node1[PortType.output][0], node2[PortType.input][0])

    # Wrong converter, must fail
    converter = nodeeditor.type_converter.TypeConverter(MyOtherNodeData.data_type,
                                                        MyNodeData.data_type,
                                                        lambda x: None)
    scene.registry.register_type_converter(MyNodeData.data_type, MyOtherNodeData.data_type, converter)
    with pytest.raises(nodeeditor.ConnectionDataTypeFailure):
        scene.create_connection(node1[PortType.output][0], node2[PortType.input][0])

    # Correct converter registered, must pass
    converter = nodeeditor.type_converter.TypeConverter(MyNodeData.data_type,
                                                        MyOtherNodeData.data_type,
                                                        lambda x: None)
    scene.registry.register_type_converter(MyNodeData.data_type, MyOtherNodeData.data_type, converter)
    scene.create_connection(node1[PortType.output][0], node2[PortType.input][0])


def test_clear_scene(scene, view, model):
    node1 = scene.create_node(model)
    node2 = scene.create_node(model)
    scene.create_connection(node2[PortType.output][2],
                            node1[PortType.input][1],
                            )

    scene.clear_scene()

    assert len(scene.nodes) == 0
    assert len(scene.connections) == 0
    all_c1 = node1.state.all_connections
    assert len(all_c1) == 0
    all_c2 = node1.state.all_connections
    assert len(all_c2) == 0


def test_get_and_set_state(scene, model):
    node1 = scene.create_node(model)
    node2 = scene.create_node(model)
    scene.create_connection(node2[PortType.output][2],
                            node1[PortType.input][1],
                            )
    state = scene.__getstate__()
    scene.__setstate__(state)

    assert scene.__getstate__() == state


def test_save_load(tmp_path, scene, view, model):
    node1 = scene.create_node(model)
    node2 = scene.create_node(model)

    created_nodes = (node1, node2)

    assert len(scene.nodes) == len(created_nodes)

    for node in created_nodes:
        assert node in scene.nodes.values()
        assert node.id in scene.nodes

    fname = tmp_path / 'temp.flow'
    scene.save(fname)
    scene.load(fname)

    assert len(scene.nodes) == len(created_nodes)

    for node in created_nodes:
        assert node not in scene.nodes.values()
        assert node.id in scene.nodes


@pytest.mark.parametrize('reset, port_type',
                         [(True, 'input'),
                          (False, 'output')])
def test_smoke_reacting(scene, view, model, reset, port_type):
    node = scene.create_node(model)
    dtype = node.model.data_type[port_type][0]
    node.react_to_possible_connection(
        reacting_port_type=port_type,
        reacting_data_type=dtype,
        scene_point=qtpy.QtCore.QPointF(0, 0),
    )
    view.update()
    if reset:
        node.reset_reaction_to_connection()


def test_smoke_node_size_updated(scene, view, model):
    node = scene.create_node(model)
    node.on_node_size_updated()
    view.update()


def test_connection_cycles(scene, view, model):
    node1 = scene.create_node(model)
    node2 = scene.create_node(model)
    node3 = scene.create_node(model)
    scene.create_connection(node1[PortType.output][0],
                            node2[PortType.input][0])
    scene.create_connection(node2[PortType.output][0],
                            node3[PortType.input][0])

    # node1 -> node2 -> node3

    # Test with a fully-specified connection: try to connect node3->node1
    with pytest.raises(nodeeditor.ConnectionCycleFailure):
        scene.create_connection(node3[PortType.output][0],
                                node1[PortType.input][0])

    # Test with a half-specified connection: start with node3
    conn = scene.create_connection(node3[PortType.output][0])
    # and then pretend the user attempts to connect it to node1:
    interaction = nodeeditor.NodeConnectionInteraction(
        node=node1, connection=conn, scene=scene)

    assert interaction.creates_cycle


def test_smoke_connection_interaction(scene, view, model):
    node1 = scene.create_node(model)
    node2 = scene.create_node(model)
    conn = scene.create_connection(node1[PortType.output][0])
    interaction = nodeeditor.NodeConnectionInteraction(
        node=node2, connection=conn, scene=scene)

    node_scene_transform = node2.graphics_object.sceneTransform()
    pos = node2.geometry.port_scene_position(PortType.input, 0,
                                             node_scene_transform)

    conn.geometry.set_end_point(PortType.input, pos)

    with pytest.raises(nodeeditor.ConnectionPointFailure):
        interaction.can_connect()

    conn.geometry.set_end_point(PortType.output, pos)
    with pytest.raises(nodeeditor.ConnectionPointFailure):
        interaction.can_connect()

    assert interaction.node_port_is_empty(PortType.input, 0)
    assert interaction.connection_required_port == PortType.input

    # TODO node still not on it?
    interaction.can_connect = lambda: (node1.state[PortType.input][0], None)

    assert interaction.try_connect()

    interaction.disconnect(PortType.output)
    interaction.connection_end_scene_position(PortType.input)
    interaction.node_port_scene_position(PortType.input, 0)
    interaction.node_port_under_scene_point(PortType.input, qtpy.QtCore.QPointF(0, 0))


def test_connection_interaction_wrong_data_type(scene, view, model, other_model):
    node1 = scene.create_node(model)
    node2 = scene.create_node(other_model)
    conn = scene.create_connection(node1[PortType.output][0])
    interaction = nodeeditor.NodeConnectionInteraction(
        node=node2, connection=conn, scene=scene)

    node_scene_transform = node2.graphics_object.sceneTransform()
    pos = node2.geometry.port_scene_position(PortType.input, 0, node_scene_transform)

    conn.geometry.set_end_point(PortType.input, conn.graphics_object.mapFromScene(pos))
    with pytest.raises(nodeeditor.ConnectionDataTypeFailure):
        interaction.can_connect()


def test_locate_node(scene, view, model):
    node = scene.create_node(model)
    assert scene.locate_node_at(node.position, view.transform()) == node


def test_view_scale(scene, view, model):
    node1 = scene.create_node(model)
    node2 = scene.create_node(model)
    scene.create_connection(node2[PortType.output][2],
                            node1[PortType.input][1],
                            )

    view.scale_up()
    view.scale_down()


def test_view_delete_selected(scene, view, model):
    node1 = scene.create_node(model)
    node2 = scene.create_node(model)
    conn = scene.create_connection(node2[PortType.output][2],
                                   node1[PortType.input][1])
    node1.graphics_object.setSelected(True)
    conn.graphics_object.setSelected(True)
    node2.graphics_object.setSelected(True)
    view.delete_selected()

    assert node1 not in scene.nodes.values()
    assert node2 not in scene.nodes.values()
    assert conn not in scene.connections


def test_smoke_view_context_menu(qtbot, view):
    view.generate_context_menu(qtpy.QtCore.QPoint(0, 0))


def test_smoke_repr(scene, view, model):
    node1 = scene.create_node(model)
    node2 = scene.create_node(model)
    print()
    print('node1', node1)
    print('node2', node2)
    ports = (node2[PortType.output][2], node1[PortType.input][1])
    print()
    print('ports', ports)
    conn = scene.create_connection(*ports)
    print()
    print('connection', conn)


def test_smoke_scene_signal_connections(scene, view, model):
    mock = unittest.mock.Mock()
    scene.connection_created.connect(mock)

    node1 = scene.create_node(model)
    node2 = scene.create_node(model)
    conn = scene.create_connection(node2[PortType.output][2],
                                   node1[PortType.input][1])
    assert mock.call_count == 1

    mock = unittest.mock.Mock()
    scene.connection_deleted.connect(mock)

    node1 = scene.create_node(model)
    node2 = scene.create_node(model)
    scene.delete_connection(conn)
    assert mock.call_count == 1


def test_smoke_scene_signal_nodes(scene, view, model):
    mock = unittest.mock.Mock()
    scene.node_created.connect(mock)
    node1 = scene.create_node(model)
    node2 = scene.create_node(model)
    assert mock.call_count == 2

    mock = unittest.mock.Mock()
    scene.node_deleted.connect(mock)
    scene.remove_node(node1)
    scene.remove_node(node2)
    assert mock.call_count == 2
