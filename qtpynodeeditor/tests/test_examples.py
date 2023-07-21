import pytest
from qtpy import QtCore, QtGui

from qtpynodeeditor import examples


@pytest.fixture(scope='function',
                params=['style', 'calculator', 'connection_colors', 'image'])
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
        print(node.size)
        node.position = node.position

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
        widget = node.model.embedded_widget()
        if widget is not None:
            if hasattr(widget, 'setText'):
                widget.setText('0.0')


class MySceneEvent(QtGui.QMouseEvent):
    last_pos = QtCore.QPoint(0, 0)
    scene_pos = QtCore.QPoint(0, 0)

    def lastPos(self):
        return self.last_pos

    def screenPos(self):
        return self.scene_pos

    def scenePos(self):
        return self.scene_pos


def test_smoke_mouse(qtbot, nodes):
    for node in nodes:
        ngo = node.graphics_object
        # TODO qtbot doesn't work with QGraphicsObjects
        # qtbot.mouseClick(ngo)

        ev = MySceneEvent(QtCore.QEvent.MouseButtonPress, QtCore.QPointF(0, 0),
                          QtCore.Qt.LeftButton, QtCore.Qt.LeftButton,
                          QtCore.Qt.NoModifier)

        if node.model.num_ports['input']:
            pos = node.geometry.port_scene_position('input', 0)
        else:
            pos = node.geometry.port_scene_position('output', 0)

        ev.scene_pos = QtCore.QPoint(int(pos.x()), int(pos.y()))
        ev.last_pos = QtCore.QPoint(int(pos.x()), int(pos.y()))

        if node.model.resizable():
            # Other case will try to propagate to mouseMoveEvent
            node.state.resizing = True
            ngo.mouseMoveEvent(ev)

        ngo.mousePressEvent(ev)
        ngo.hoverEnterEvent(ev)
        ngo.hoverMoveEvent(ev)
        ngo.hoverLeaveEvent(ev)


def test_save_and_load(scene):
    scene.__setstate__(scene.__getstate__())
