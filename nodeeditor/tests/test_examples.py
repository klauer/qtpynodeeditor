from nodeeditor import examples


def test_smoke_style(qtbot, qapp):
    scene, view, nodes = examples.style.main(qapp)
    qtbot.addWidget(view)


def test_smoke_calculator(qtbot, qapp):
    scene, view, nodes = examples.calculator.main(qapp)
    qtbot.addWidget(view)

    def visitor(node):
        print(node, node.number if hasattr(node, 'number') else '')

    print('Node data iterator')
    print('------------------')
    scene.iterate_over_node_data(visitor)

    print('Node data dependent iterator')
    print('----------------------------')
    scene.iterate_over_node_data_dependent_order(visitor)
