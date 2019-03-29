from .node import Node
from .port import PortType


class ConnectionState:
    def __init__(self, port: PortType = None):
        self._required_port = port
        self._last_hovered_node = None

    def _cleanup(self):
        self.reset_last_hovered_node()

    def __del__(self):
        try:
            self._cleanup()
        except Exception:
            ...
