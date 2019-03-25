import pytest
from qtpynodeeditor import examples


@pytest.fixture(scope='function',
                params=['style', 'calculator', 'connection_colors'])
def example(qtbot, qapp, request):
    example_module = getattr(examples, request.param)
    scene, view, nodes = example_module.main(qapp)
    qtbot.addWidget(view)
    yield scene, view, nodes


@pytest.fixture(scope='function')
def scene(example):
    return example[0]


@pytest.fixture(scope='function')
def view(example):
    return example[1]


@pytest.fixture(scope='function')
def nodes(example):
    return example[2]


def test_smoke_example(example):
    ...


def test_iterate(scene):
    for node in scene.iterate_over_nodes():
        scene.get_node_size(node)
        scene.set_node_position(node, scene.get_node_position(node))

    print('Node data iterator')
    print('------------------')
    for data in scene.iterate_over_node_data():
        print(data, data.number if hasattr(data, 'number') else '')

    print('Node data dependent iterator')
    print('----------------------------')
    for data in scene.iterate_over_node_data_dependent_order():
        print(data, data.number if hasattr(data, 'number') else '')


def test_smoke_zero_inputs(scene, example):
    for node in scene.iterate_over_nodes():
        widget = node.data.embedded_widget()
        if widget is not None:
            if hasattr(widget, 'setText'):
                widget.setText('0.0')


def test_save_and_load(scene):
    scene.__setstate__(scene.__getstate__())
