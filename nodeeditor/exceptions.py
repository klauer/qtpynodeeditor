class NodeConnectionFailure(Exception):
    ...


class ConnectionRequiresPortFailure(NodeConnectionFailure):
    'A port is required'
    ...


class ConnectionSelfFailure(NodeConnectionFailure):
    'Cannot connect a node to itself'
    ...


class ConnectionPointFailure(NodeConnectionFailure):
    'Connection point is not on top of the node port'
    ...


class ConnectionPortNotEmptyFailure(NodeConnectionFailure):
    'Port should be empty'
    ...
