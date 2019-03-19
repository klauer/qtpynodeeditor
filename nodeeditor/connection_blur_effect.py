from qtpy.QtCore import Qt
from qtpy.QtGui import QPainter
from qtpy.QtWidgets import QGraphicsBlurEffect


from .connection import Connection
from .connection_painter import ConnectionPainter
from .connection_graphics_object import ConnectionGraphicsObject


from qtpy.QtWidgets import QGraphicsBlurEffect


class ConnectionBlurEffect(QGraphicsBlurEffect):
    def __init__(self, item: ConnectionGraphicsObject):
        """
        Connection blur effect

        Parameters
        ----------
        item : ConnectionGraphicsObject
        """
        super().__init__(item)

    def draw(self, painter: QPainter):
        """
        Draw

        Parameters
        ----------
        painter : QPainter
        """
        super().draw(painter)

        # ConnectionPainter.paint(painter,
        # _object.connection_geometry(),
        # _object.connection_state())
        # _item.paint(painter, None, None)
