from qtpy.QtCore import QObject, QPointF, QUuid

from .enums import ReactToConnectionState
from .base import NodeBase
from .node_data import NodeData, NodeDataModel, NodeDataType
from .node_geometry import NodeGeometry
from .node_graphics_object import NodeGraphicsObject
from .node_state import NodeState
from .port import PortType, PortIndex
from .serializable import Serializable


class Node(QObject, Serializable, NodeBase):
    def __init__(self, data_model: NodeDataModel):
        '''
        A single Node in the scene

        Parameters
        ----------
        data_model : NodeDataModel
        '''
        super().__init__()
        self._node_data_model = data_model
        self._uid = QUuid.createUuid()
        self._style = data_model.node_style()
        self._node_state = NodeState(self._node_data_model)
        self._node_geometry = NodeGeometry(self._node_data_model)
        self._node_graphics_object = None
        self._node_geometry.recalculate_size()

        # propagate data: model => node
        self._node_data_model.data_updated.connect(self.on_data_updated)
        self._node_data_model.embedded_widget_size_updated.connect(self.on_node_size_updated)

    def _cleanup(self):
        if self._node_graphics_object is not None:
            self._node_graphics_object._cleanup()
            self._node_graphics_object = None
            self._node_geometry = None

    def __del__(self):
        try:
            self._cleanup()
        except Exception:
            ...

    def save(self) -> dict:
        """
        Save

        Returns
        -------
        value : dict
        """
        return {
            "id": self._uid.toString(),
            "model": self._node_data_model.save(),
            "position": {"x": self._node_graphics_object.pos().x(),
                         "y": self._node_graphics_object.pos().y()}
        }

    def restore(self, json: dict):
        """
        Restore

        Parameters
        ----------
        json : dict
        """
        self._uid = QUuid(json["id"])
        position_json = json["position"]
        point = QPointF(position_json["x"], position_json["y"])
        self._node_graphics_object.setPos(point)
        self._node_data_model.restore(json["model"])

    def id(self) -> QUuid:
        """
        Id

        Returns
        -------
        value : QUuid
        """
        return self._uid

    def react_to_possible_connection(self, reacting_port_type: PortType,
                                     reacting_data_type: NodeDataType,
                                     scene_point: QPointF
                                     ):
        """
        React to possible connection

        Parameters
        ----------
        port_type : PortType
        node_data_type : NodeDataType
        scene_point : QPointF
        """
        transform = self._node_graphics_object.sceneTransform()
        inverted, invertible = transform.inverted()
        if invertible:
            pos = inverted.map(scene_point)
            self._node_geometry.set_dragging_position(pos)
        self._node_graphics_object.update()
        self._node_state.set_reaction(ReactToConnectionState.reacting,
                                      reacting_port_type, reacting_data_type)

    def reset_reaction_to_connection(self):
        self._node_state.set_reaction(ReactToConnectionState.not_reacting)
        self._node_graphics_object.update()

    def node_graphics_object(self) -> NodeGraphicsObject:
        """
        Node graphics object

        Returns
        -------
        value : NodeGraphicsObject
        """
        return self._node_graphics_object

    def set_graphics_object(self, graphics: NodeGraphicsObject):
        """
        Set graphics object

        Parameters
        ----------
        graphics : NodeGraphicsObject
        """
        self._node_graphics_object = graphics
        self._node_geometry.recalculate_size()

    def node_geometry(self) -> NodeGeometry:
        """
        Node geometry

        Returns
        -------
        value : NodeGeometry
        """
        return self._node_geometry

    def node_state(self) -> NodeState:
        """
        Node state

        Returns
        -------
        value : NodeState
        """
        return self._node_state

    def node_data_model(self) -> NodeDataModel:
        """
        Node data model

        Returns
        -------
        value : NodeDataModel
        """
        return self._node_data_model

    def propagate_data(self, node_data: NodeData, in_port_index: PortIndex):
        """
        Propagates incoming data to the underlying model.

        Parameters
        ----------
        node_data : NodeData
        in_port_index : PortIndex
        """
        self._node_data_model.set_in_data(node_data, in_port_index)

        # Recalculate the nodes visuals. A data change can result in the node
        # taking more space than before, so self forces a recalculate+repaint
        # on the affected node
        self._node_graphics_object.set_geometry_changed()
        self._node_geometry.recalculate_size()
        self._node_graphics_object.update()
        self._node_graphics_object.move_connections()

    def on_data_updated(self, index: PortIndex):
        """
        Fetches data from model's OUT #index port and propagates it to the connection

        Parameters
        ----------
        index : PortIndex
        """
        node_data = self._node_data_model.out_data(index)
        connections = self._node_state.connections(PortType.output, index)
        for c in connections:
            c.propagate_data(node_data)

    def on_node_size_updated(self):
        """
        update the graphic part if the size of the embeddedwidget changes
        """
        widget = self.node_data_model().embedded_widget()
        if widget:
            widget.adjustSize()

        self.node_geometry().recalculate_size()
        for conn in self.node_state().all_connections:
            conn.get_connection_graphics_object().move()
