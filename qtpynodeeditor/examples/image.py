import logging

from qtpy import QtCore, QtGui, QtWidgets
from qtpy.QtCore import Qt

import qtpynodeeditor
from qtpynodeeditor import NodeData, NodeDataModel, NodeDataType, PortType


class PixmapData(NodeData):
    data_type = NodeDataType(id='Pixmap', name='PixmapData')

    def __init__(self, pixmap):
        self.pixmap = pixmap


class ImageLoaderModel(NodeDataModel):
    caption = 'Image Source'
    num_ports = {PortType.input: 0,
                 PortType.output: 1,
                 }
    data_type = PixmapData

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pixmap = None
        self._label = QtWidgets.QLabel('Click to load image')
        self._label.setAlignment(Qt.AlignVCenter | Qt.AlignCenter)

        font = self._label.font()
        font.setBold(True)
        font.setItalic(True)
        self._label.setFont(font)

        self._label.setFixedSize(200, 200)
        self._label.installEventFilter(self)

    def eventFilter(self, obj, event):
        label = getattr(self, "_label", None)

        if label is None or obj is not label:
            return False

        def set_pixmap():
            w, h = label.width(), label.height()
            label.setPixmap(self._pixmap.scaled(w, h, Qt.KeepAspectRatio))

        if event.type() == QtCore.QEvent.MouseButtonPress:
            file_name, _ = QtWidgets.QFileDialog.getOpenFileName(
                None, "Open Image", QtCore.QDir.homePath(),
                "Image files (*.png *.jpg *.bmp)")
            try:
                self._pixmap = QtGui.QPixmap(file_name)
            except Exception as ex:
                print(f'Failed to load image {file_name}: {ex}')
                return False

            set_pixmap()
            self.data_updated.emit(0)
            return True

        elif event.type() == QtCore.QEvent.Resize:
            if self._pixmap is not None:
                set_pixmap()

        return False

    def resizable(self):
        return True

    def out_data(self, port):
        return PixmapData(self._pixmap)

    def embedded_widget(self):
        return self._label


class ImageShowModel(NodeDataModel):
    caption = 'Image Display'
    num_ports = {PortType.input: 1,
                 PortType.output: 1,
                 }
    data_type = PixmapData

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._node_data = None
        self._label = QtWidgets.QLabel('Image will appear here')
        self._label.setAlignment(Qt.AlignVCenter | Qt.AlignCenter)

        font = self._label.font()
        font.setBold(True)
        font.setItalic(True)
        self._label.setFont(font)

        self._label.setFixedSize(200, 200)
        self._label.installEventFilter(self)

    def resizable(self):
        return True

    def eventFilter(self, obj, event):
        if obj is self._label and event.type() == QtCore.QEvent.Resize:
            if (self._node_data and
                    self._node_data.data_type == PixmapData.data_type and
                    self._node_data.pixmap):
                w, h = self._label.width(), self._label.height()
                pixmap = self._node_data.pixmap
                self._label.setPixmap(pixmap.scaled(w, h, Qt.KeepAspectRatio))

        return False

    def set_in_data(self, node_data, port):
        self._node_data = node_data
        if (self._node_data and
                self._node_data.data_type == PixmapData.data_type and
                self._node_data.pixmap):
            w, h = self._label.width(), self._label.height()
            pixmap = node_data.pixmap.scaled(w, h, Qt.KeepAspectRatio)
        else:
            pixmap = QtGui.QPixmap()

        self._label.setPixmap(pixmap)
        self.data_updated.emit(0)

    def out_data(self, port):
        return self._node_data

    def embedded_widget(self):
        return self._label


def main(app):
    registry = qtpynodeeditor.DataModelRegistry()
    registry.register_model(ImageShowModel, category='My Category')
    registry.register_model(ImageLoaderModel, category='My Category')
    scene = qtpynodeeditor.FlowScene(registry=registry)

    view = qtpynodeeditor.FlowView(scene)
    view.setWindowTitle("Image example")
    view.resize(800, 600)

    node_loader = scene.create_node(ImageLoaderModel)
    node_show = scene.create_node(ImageShowModel)

    scene.create_connection(
        node_loader[PortType.output][0],
        node_show[PortType.input][0],
    )

    return scene, view, [node_loader, node_show]


if __name__ == '__main__':
    logging.basicConfig(level='DEBUG')
    app = QtWidgets.QApplication([])
    scene, view, nodes = main(app)
    view.show()
    app.exec_()
