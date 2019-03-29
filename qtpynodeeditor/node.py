import uuid

from qtpy.QtCore import QObject, QPointF, Property, QSizeF

from .enums import ReactToConnectionState
from .base import NodeBase, Serializable
from .node_data import NodeData, NodeDataModel, NodeDataType
from .node_geometry import NodeGeometry
from .node_graphics_object import NodeGraphicsObject
from .node_state import NodeState
from .port import PortType, Port
from .style import NodeStyle


class Node(QObject, Serializable, NodeBase):
    def __init__(self, data_model: NodeDataModel):
        '''
        A single Node in the scene

        Parameters
        ----------
        data_model : NodeDataModel
        '''
        super().__init__()
        self._model = data_model
        self._uid = str(uuid.uuid4())
        self._style = data_model.node_style
        self._state = NodeState(self)
        self._geometry = NodeGeometry(self)
        self._graphics_obj = None
        self._geometry.recalculate_size()

        # propagate data: model => node
        self._model.data_updated.connect(self._on_port_index_data_updated)
        self._model.embedded_widget_size_updated.connect(self.on_node_size_updated)

    def __getitem__(self, key):
        return self._state[key]

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
            "model": self._model.__getstate__(),
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
        if self._graphics_obj:
            pos = state["position"]
            self.position = (pos["x"], pos["y"])
        self._model.__setstate__(state["model"])

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
    def model(self) -> NodeDataModel:
        """
        Node data model

        Returns
        -------
        value : NodeDataModel
        """
        return self._model

    def propagate_data(self, node_data: NodeData, input_port: Port):
        """
        Propagates incoming data to the underlying model.

        Parameters
        ----------
        node_data : NodeData
        input_port : int
        """
        if input_port.node is not self:
            raise ValueError('Port does not belong to this Node')
        elif input_port.port_type != PortType.input:
            raise ValueError('Port is not an input port')

        self._model.set_in_data(node_data, input_port)

        # Recalculate the nodes visuals. A data change can result in the node
        # taking more space than before, so self forces a recalculate+repaint
        # on the affected node
        self._graphics_obj.set_geometry_changed()
        self._geometry.recalculate_size()
        self._graphics_obj.update()
        self._graphics_obj.move_connections()

    def _on_port_index_data_updated(self, port_index: int):
        """
        Data has been updated on this Node's output port port_index;
        propagate it to any connections.

        Parameters
        ----------
        index : int
        """
        port = self[PortType.output][port_index]
        self.on_data_updated(port)

    def on_data_updated(self, port: Port):
        """
        Fetches data from model's output port and propagates it along the
        connection

        Parameters
        ----------
        port : Port
        """
        node_data = port.data
        for conn in port.connections:
            conn.propagate_data(node_data)

    def on_node_size_updated(self):
        """
        update the graphic part if the size of the embeddedwidget changes
        """
        widget = self.model.embedded_widget()
        if widget:
            widget.adjustSize()

        self.geometry.recalculate_size()
        for conn in self.state.all_connections:
            conn.graphics_object.move()

    @property
    def size(self) -> QSizeF:
        """
        Get the node size

        Parameters
        ----------
        node : Node

        Returns
        -------
        value : QSizeF
        """
        return self._geometry.size

    @property
    def position(self) -> QPointF:
        """
        Get the node position

        Parameters
        ----------
        node : Node

        Returns
        -------
        value : QPointF
        """
        return self._graphics_obj.pos()

    @position.setter
    def position(self, pos):
        if not isinstance(pos, QPointF):
            px, py = pos
            pos = QPointF(px, py)

        self._graphics_obj.setPos(pos)
        self._graphics_obj.move_connections()

    @property
    def style(self) -> NodeStyle:
        'Node style'
        return self._style

    @property
    def state(self) -> NodeState:
        """
        Node state

        Returns
        -------
        value : NodeState
        """
        return self._state
