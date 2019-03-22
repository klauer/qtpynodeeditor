from qtpy.QtCore import QPointF
from nodeeditor import examples


def test_smoke_style(qtbot, qapp):
    scene, view, nodes = examples.style.main(qapp)
    qtbot.addWidget(view)

    for node in scene.iterate_over_nodes():
        scene.get_node_size(node)
        scene.set_node_position(node, QPointF(0.0, 0.0))


def test_smoke_calculator(qtbot, qapp):
    scene, view, nodes = examples.calculator.main(qapp)
    qtbot.addWidget(view)

    print('Node data iterator')
    print('------------------')
    for data in scene.iterate_over_node_data():
        print(data, data.number if hasattr(data, 'number') else '')

    print('Node data dependent iterator')
    print('----------------------------')
    for data in scene.iterate_over_node_data_dependent_order():
        print(data, data.number if hasattr(data, 'number') else '')
