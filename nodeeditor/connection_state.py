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

    @property
    def required_port(self) -> PortType:
        """
        Required port

        Returns
        -------
        value : PortType
        """
        return self._required_port

    @required_port.setter
    def required_port(self, end: PortType):
        self._required_port = PortType(end)

    @property
    def requires_port(self) -> bool:
        """
        Requires port

        Returns
        -------
        value : bool
        """
        return self._required_port != PortType.none

    def interact_with_node(self, node: Node):
        """
        Interact with node

        Parameters
        ----------
        node : Node
        """
        if node:
            self._last_hovered_node = node
        else:
            self.reset_last_hovered_node()

    def set_last_hovered_node(self, node: Node):
        """
        Set last hovered node

        Parameters
        ----------
        node : Node
        """
        self._last_hovered_node = node

    def last_hovered_node(self) -> Node:
        """
        Last hovered node

        Returns
        -------
        value : Node
        """
        return self._last_hovered_node

    def reset_last_hovered_node(self):
        if self._last_hovered_node:
            self._last_hovered_node.reset_reaction_to_connection()
            self._last_hovered_node = None
