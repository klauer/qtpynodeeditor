from enum import Enum


class NodeValidationState(str, Enum):
    valid = 'valid'
    warning = 'warning'
    error = 'error'


class PortType(str, Enum):
    none = 'none'
    input = 'input'
    output = 'output'


class ConnectionPolicy(str, Enum):
    one = 'one'
    many = 'many'


class ReactToConnectionState(str, Enum):
    reacting = 'reacting'
    not_reacting = 'not_reacting'
