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

    def set_required_port(self, end: PortType):
        """
        set_required_port

        Parameters
        ----------
        end : PortType
        """
        self._required_port = end

    def required_port(self) -> PortType:
        """
        required_port

        Returns
        -------
        value : PortType
        """
        return self._required_port

    def requires_port(self) -> bool:
        """
        requires_port

        Returns
        -------
        value : bool
        """
        return self._required_port != PortType.none

    def set_no_required_port(self):
        self._required_port = PortType.none

    def interact_with_node(self, node: Node):
        """
        interact_with_node

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
        set_last_hovered_node

        Parameters
        ----------
        node : Node
        """
        self._last_hovered_node = node

    def last_hovered_node(self) -> Node:
        """
        last_hovered_node

        Returns
        -------
        value : Node
        """
        return self._last_hovered_node

    def reset_last_hovered_node(self):
        if self._last_hovered_node:
            self._last_hovered_node.reset_reaction_to_connection()
        self._last_hovered_node = None
