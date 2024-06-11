import typing

from qtpy.QtCore import QObject, Signal

from .enums import ConnectionPolicy, PortType

if typing.TYPE_CHECKING:
    from .connection import Connection  # noqa


class Spacer(QObject):
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

    def __init__(self, node, *, spacer_type: PortType, index: int):
        super().__init__(parent=node)
        self.node = node
        self.spacer_type = spacer_type
        self.index = index

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
    def text(self):
        'Data model-specified caption for the spacer'
        return self.model.spacers[self.spacer_type][self.index]

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
        return self.node.geometry.spacer_scene_position(self.spacer_type,
                                                        self.index,
                                                        self.model.spacers)

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
