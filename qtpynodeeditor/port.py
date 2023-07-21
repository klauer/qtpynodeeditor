import typing

from qtpy.QtCore import QObject, Signal

from .enums import ConnectionPolicy, PortType

if typing.TYPE_CHECKING:
    from .connection import Connection  # noqa


def opposite_port(port: PortType) -> PortType:
    """
    Get the opposite port of `port`.

    Parameters
    ----------
    port : PortType
    """
    return {PortType.input: PortType.output,
            PortType.output: PortType.input}.get(port, PortType.none)


class Port(QObject):
    """

    Signals
    -------
    connection_created : Signal(Connection)
    connection_deleted : Signal(Connection)
    data_updated : Signal(QObject)
    data_invalidated : Signal(QObject)
    """

    connection_created = Signal(object)
    connection_deleted = Signal(object)
    data_updated = Signal(QObject)
    data_invalidated = Signal(QObject)
    _connections: list['Connection']

    def __init__(self, node, *, port_type: PortType, index: int):
        super().__init__(parent=node)
        self.node = node
        self.port_type = port_type
        self.index = index
        self._connections = []
        self.opposite_port = {PortType.input: PortType.output,
                              PortType.output: PortType.input}[self.port_type]

    @property
    def connections(self):
        return list(self._connections)

    @property
    def model(self):
        'The data model associated with the Port'
        return self.node.model

    @property
    def data(self):
        'The NodeData associated with the Port, if an output port'
        if self.port_type == PortType.input:
            # return self.model.in_data(self.index)
            # TODO
            return
        else:
            return self.model.out_data(self.index)

    @property
    def can_connect(self):
        'Can this port be connected to?'
        return (not self._connections or
                self.connection_policy == ConnectionPolicy.many)

    @property
    def caption(self):
        'Data model-specified caption for the port'
        return self.model.port_caption[self.port_type][self.index]

    @property
    def caption_visible(self):
        'Show the data model-specified caption?'
        return self.model.port_caption_visible[self.port_type][self.index]

    @property
    def data_type(self):
        'The NodeData type associated with the Port'
        return self.model.data_type[self.port_type][self.index]

    @property
    def display_text(self):
        'The text to show on the label caption'
        return (self.caption
                if self.caption_visible
                else self.data_type.name)

    @property
    def connection_policy(self):
        'The connection policy (one/many) for the port'
        if self.port_type == PortType.input:
            return ConnectionPolicy.one
        else:
            return self.model.port_out_connection_policy(self.index)

    def add_connection(self, connection: 'Connection'):
        'Add a Connection to the Port'
        if connection in self._connections:
            raise ValueError('Connection already in list')

        self._connections.append(connection)
        self.connection_created.emit(connection)

    def remove_connection(self, connection: 'Connection'):
        'Remove a Connection from the Port'
        try:
            self._connections.remove(connection)
        except ValueError:
            # TODO: should not be reaching this
            ...
        else:
            self.connection_deleted.emit(connection)

    @property
    def scene_position(self):
        '''
        The position in the scene of the Port

        Returns
        -------
        value : QPointF

        See also
        --------
        get_mapped_scene_position
        '''
        return self.node.geometry.port_scene_position(self.port_type,
                                                      self.index)

    def get_mapped_scene_position(self, transform):
        """
        Node port scene position after a transform

        Parameters
        ----------
        port_type : PortType
        port_index : int

        Returns
        -------
        value : QPointF
        """
        ngo = self.node.graphics_object
        return ngo.sceneTransform().map(self.scene_position)

    def __repr__(self):
        return (f'<{self.__class__.__name__} port_type={self.port_type} '
                f'index={self.index} connections={len(self._connections)}>')
