import uuid

from qtpy.QtCore import QObject, QPointF, Property

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
        self._uid = str(uuid.uuid4())
        self._style = data_model.node_style
        self._state = NodeState(self._node_data_model)
        self._geometry = NodeGeometry(self._node_data_model)
        self._graphics_obj = None
        self._geometry.recalculate_size()

        # propagate data: model => node
        self._node_data_model.data_updated.connect(self.on_data_updated)
        self._node_data_model.embedded_widget_size_updated.connect(self.on_node_size_updated)

    def _cleanup(self):
        if self._graphics_obj is not None:
            self._graphics_obj._cleanup()
            self._graphics_obj = None
            self._geometry = None

    def __del__(self):
        try:
            self._cleanup()
        except Exception:
            ...

    def __getstate__(self) -> dict:
        """
        Save

        Returns
        -------
        value : dict
        """
        return {
            "id": self._uid,
            "model": self._node_data_model.__getstate__(),
            "position": {"x": self._graphics_obj.pos().x(),
                         "y": self._graphics_obj.pos().y()}
        }

    def __setstate__(self, state: dict):
        """
        Restore

        Parameters
        ----------
        state : dict
        """
        self._uid = state["id"]
        pos = state["position"]
        point = QPointF(pos["x"], pos["y"])
        self._graphics_obj.setPos(point)
        self._node_data_model.__setstate__(state["model"])

    @property
    def id(self) -> str:
        """
        Node unique identifier (uuid)

        Returns
        -------
        value : str
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
        transform = self._graphics_obj.sceneTransform()
        inverted, invertible = transform.inverted()
        if invertible:
            pos = inverted.map(scene_point)
            self._geometry.dragging_position = pos
        self._graphics_obj.update()
        self._state.set_reaction(ReactToConnectionState.reacting,
                                 reacting_port_type, reacting_data_type)

    def reset_reaction_to_connection(self):
        self._state.set_reaction(ReactToConnectionState.not_reacting)
        self._graphics_obj.update()

    @Property(NodeGraphicsObject)
    def graphics_object(self) -> NodeGraphicsObject:
        """
        Node graphics object

        Returns
        -------
        value : NodeGraphicsObject
        """
        return self._graphics_obj

    @graphics_object.setter
    def graphics_object(self, graphics: NodeGraphicsObject):
        """
        Set graphics object

        Parameters
        ----------
        graphics : NodeGraphicsObject
        """
        self._graphics_obj = graphics
        self._geometry.recalculate_size()

    @property
    def geometry(self) -> NodeGeometry:
        """
        Node geometry

        Returns
        -------
        value : NodeGeometry
        """
        return self._geometry

    @property
    def state(self) -> NodeState:
        """
        Node state

        Returns
        -------
        value : NodeState
        """
        return self._state

    @property
    def data(self) -> NodeDataModel:
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
        self._graphics_obj.set_geometry_changed()
        self._geometry.recalculate_size()
        self._graphics_obj.update()
        self._graphics_obj.move_connections()

    def on_data_updated(self, index: PortIndex):
        """
        Fetches data from model's OUT #index port and propagates it to the connection

        Parameters
        ----------
        index : PortIndex
        """
        node_data = self._node_data_model.out_data(index)
        connections = self._state.connections(PortType.output, index)
        for c in connections:
            c.propagate_data(node_data)

    def on_node_size_updated(self):
        """
        update the graphic part if the size of the embeddedwidget changes
        """
        widget = self.data.embedded_widget()
        if widget:
            widget.adjustSize()

        self.geometry.recalculate_size()
        for conn in self.state.all_connections:
            conn.graphics_object.move()
