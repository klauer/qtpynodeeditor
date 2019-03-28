from .base import ConnectionBase
from .enums import PortType


# TODO
PortIndex = int


INVALID = -1


class Port:
    def __init__(self, type_, index):
        self.type = type_
        self.index = index

    @property
    def index_is_valid(self):
        return self.index != INVALID

    @property
    def port_type_is_valid(self):
        return self.type != PortType.none


def opposite_port(port: PortType):
    return {PortType.input: PortType.output,
            PortType.output: PortType.input}.get(port, PortType.none)


class NodePort:
    def __init__(self, node, *, port_type: PortType, index: PortIndex):
        self.node = node
        self.port_type = port_type
        self.index = index
        self.connections = []
        self.opposite_port = {PortType.input: PortType.output,
                              PortType.output: PortType.input}[self.port_type]

    def add_connection(self, connection: ConnectionBase):
        self.connections.append(connection)

    def remove_connection(self, connection: ConnectionBase):
        try:
            self.connections.remove(connection)
        except ValueError:
            # TODO: should not be reaching this
            ...
