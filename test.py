import logging

import qtpy
from qtpy import QtCore, QtWidgets

import nodeeditor
from nodeeditor import FlowViewStyle, NodeStyle, ConnectionStyle, StyleCollection
from nodeeditor import NodeData, NodeDataType, NodeDataModel


style_json = '''
    {
      "FlowViewStyle": {
        "BackgroundColor": [255, 255, 240],
        "FineGridColor": [245, 245, 230],
        "CoarseGridColor": [235, 235, 220]
      },
      "NodeStyle": {
        "NormalBoundaryColor": "darkgray",
        "SelectedBoundaryColor": "deepskyblue",
        "GradientColor0": "mintcream",
        "GradientColor1": "mintcream",
        "GradientColor2": "mintcream",
        "GradientColor3": "mintcream",
        "ShadowColor": [200, 200, 200],
        "FontColor": [10, 10, 10],
        "FontColorFaded": [100, 100, 100],
        "ConnectionPointColor": "white",
        "PenWidth": 2.0,
        "HoveredPenWidth": 2.5,
        "ConnectionPointDiameter": 10.0,
        "Opacity": 1.0
      },
      "ConnectionStyle": {
        "ConstructionColor": "gray",
        "NormalColor": "black",
        "SelectedColor": "gray",
        "SelectedHaloColor": "deepskyblue",
        "HoveredColor": "deepskyblue",

        "LineWidth": 3.0,
        "ConstructionLineWidth": 2.0,
        "PointDiameter": 10.0,

        "UseDataDefinedColors": false
      }
  }
'''



class MyNodeData(NodeData):
    _type = NodeDataType('MyNodeData', 'My Node Data')


class MyDataModel(NodeDataModel):
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


logging.basicConfig(level='DEBUG')
app = QtWidgets.QApplication([])

style = StyleCollection.from_json(style_json)
model = MyDataModel(style=style)

registry = nodeeditor.DataModelRegistry()
registry.register_model(model, category='My Category')
scene = nodeeditor.FlowScene(registry=registry)

view = nodeeditor.FlowView(scene)
view.setWindowTitle("Style example")
view.resize(800, 600)
view.show()

node1 = scene.create_node(model)
node2 = scene.create_node(model)
scene.create_connection(
    node_in=node1, port_index_in=1,
    node_out=node2, port_index_out=2,
    converter=None
)

from nodeeditor import PortType

# dtype = model.data_type(PortType.In, 0)
# node1.react_to_possible_connection(
#     reacting_port_type=PortType.In,
#     reacting_data_type=model.data_type,
#     scene_point=qtpy.QtCore.QPointF(0, 0),
# )

app.exec_()
