import logging

from qtpy import QtWidgets

import qtpynodeeditor
from qtpynodeeditor import (NodeData, NodeDataType, NodeDataModel, PortType)


class MyNodeData(NodeData):
    data_type = NodeDataType(id='MyNodeData', name='My Node Data')


class SimpleNodeData(NodeData):
    data_type = NodeDataType(id='SimpleData', name='Simple Data')


class NaiveDataModel(NodeDataModel):
    name = 'NaiveDataModel'
    caption = 'Caption'
    caption_visible = True
    num_ports = {PortType.input: 2,
                 PortType.output: 2,
                 }

    def data_type(self, port_type, port_index):
        return {0: MyNodeData.data_type,
                1: SimpleNodeData.data_type}[port_index]

    def out_data(self, port_index):
        if port_index == 0:
            return MyNodeData()
        elif port_index == 1:
            return SimpleNodeData()

    def set_in_data(self, node_data, port):
        ...

    def embedded_widget(self):
        ...


def main(app):
    registry = qtpynodeeditor.DataModelRegistry()
    registry.register_model(NaiveDataModel, category='My Category')
    scene = qtpynodeeditor.FlowScene(registry=registry)

    connection_style = scene.style_collection.connection

    # Configure the style collection to use colors based on data types:
    connection_style.use_data_defined_colors = True

    view = qtpynodeeditor.FlowView(scene)
    view.setWindowTitle("Connection (data-defined) color example")
    view.resize(800, 600)

    node_a = scene.create_node(NaiveDataModel)
    node_b = scene.create_node(NaiveDataModel)

    scene.create_connection(
        node_out=node_a, port_index_out=0,
        node_in=node_b, port_index_in=0,
        converter=None
    )

    scene.create_connection(
        node_out=node_a, port_index_out=1,
        node_in=node_b, port_index_in=1,
        converter=None
    )

    return scene, view, [node_a, node_b]


if __name__ == '__main__':
    logging.basicConfig(level='DEBUG')
    app = QtWidgets.QApplication([])
    scene, view, nodes = main(app)
    view.show()
    app.exec_()
