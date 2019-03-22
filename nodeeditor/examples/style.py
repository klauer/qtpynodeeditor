import logging

from qtpy import QtWidgets

import nodeeditor
from nodeeditor import NodeData, NodeDataType, NodeDataModel, StyleCollection


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
    data_type = NodeDataType(id='MyNodeData', name='My Node Data')


class MyDataModel(NodeDataModel):
    name = 'MyDataModel'

    def model(self):
        return 'MyDataModel'

    def caption(self):
        return 'Caption'

    def save(self):
        return {'name': self.name}

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


logging.basicConfig(level='DEBUG')
app = QtWidgets.QApplication([])

style = StyleCollection.from_json(style_json)
# style = StyleCollection()

registry = nodeeditor.DataModelRegistry()
registry.register_model(MyDataModel, category='My Category', style=style)
scene = nodeeditor.FlowScene(registry=registry)

view = nodeeditor.FlowView(scene)
view.setWindowTitle("Style example")
view.resize(800, 600)
view.show()

node = scene.create_node(MyDataModel)

app.exec_()
