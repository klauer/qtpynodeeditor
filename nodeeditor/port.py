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
    return {PortType.In: PortType.Out,
            PortType.Out: PortType.In}.get(port, PortType.none)
