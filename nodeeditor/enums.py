from enum import IntEnum


class NodeValidationState(IntEnum):
    Valid = 0
    Warning = 1
    Error = 2


class PortType(IntEnum):
    none = 0
    In = 1
    Out = 2


class ConnectionPolicy(IntEnum):
    One = 0
    Many = 1


class ReactToConnectionState(IntEnum):
    REACTING = 0
    NOT_REACTING = 1
