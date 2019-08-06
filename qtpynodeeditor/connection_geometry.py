from qtpy.QtCore import QPointF, QRectF

from .port import PortType


class ConnectionGeometry:
    def __init__(self, style):
        # local object coordinates
        self._in = QPointF(0, 0)
        self._out = QPointF(0, 0)
        # self._animationPhase = 0
        self._line_width = 3.0
        self._hovered = False
        self._point_diameter = style.connection.point_diameter

    def get_end_point(self, port_type: PortType) -> QPointF:
        """
        Get end point

        Parameters
        ----------
        port_type : PortType

        Returns
        -------
        value : QPointF
        """
        assert port_type != PortType.none
        return (self._out if port_type == PortType.output
                else self._in
                )

    def set_end_point(self, port_type: PortType, point: QPointF):
        """
        Set end point

        Parameters
        ----------
        port_type : PortType
        point : QPointF
        """
        if port_type == PortType.output:
            self._out = point
        elif port_type == PortType.input:
            self._in = point
        else:
            raise ValueError(port_type)

    def move_end_point(self, port_type: PortType, offset: QPointF):
        """
        Move end point

        Parameters
        ----------
        port_type : PortType
        offset : QPointF
        """
        if port_type == PortType.output:
            self._out += offset
        elif port_type == PortType.input:
            self._in += offset
        else:
            raise ValueError(port_type)

    @property
    def bounding_rect(self) -> QRectF:
        """
        Bounding rect

        Returns
        -------
        value : QRectF
        """
        c1, c2 = self.points_c1_c2()
        basic_rect = QRectF(self._out, self._in).normalized()
        c1c2_rect = QRectF(c1, c2).normalized()

        common_rect = basic_rect.united(c1c2_rect)
        corner_offset = QPointF(self._point_diameter, self._point_diameter)
        common_rect.setTopLeft(common_rect.topLeft() - corner_offset)
        common_rect.setBottomRight(common_rect.bottomRight() + 2 * corner_offset)
        return common_rect

    def points_c1_c2(self) -> tuple:
        """
        Connection points (c1, c2)

        Returns
        -------
        c1: QPointF
            The first point
        c2: QPointF
            The second point
        """
        x_distance = self._in.x() - self._out.x()

        default_offset = 200.0
        x_offset = min((default_offset, abs(x_distance)))
        y_offset = 0

        x_ratio = 0.5
        if x_distance <= 0:
            y_distance = self._in.y() - self._out.y() + 20
            y_direction = (-1.0 if y_distance < 0 else 1.0)
            y_offset = y_direction * min((default_offset, abs(y_distance)))
            x_ratio = 1.0

        x_offset *= x_ratio
        return (
            QPointF(self._out.x() + x_offset,
                    self._out.y() + y_offset),

            QPointF(self._in.x() - x_offset,
                    self._in.y() - y_offset)
        )

    @property
    def source(self) -> QPointF:
        """
        Source

        Returns
        -------
        value : QPointF
        """
        return self._out

    @property
    def sink(self) -> QPointF:
        """
        Sink

        Returns
        -------
        value : QPointF
        """
        return self._in

    def line_width(self) -> float:
        """
        Line width

        Returns
        -------
        value : double
        """
        return self._line_width

    @property
    def hovered(self) -> bool:
        """
        Hovered

        Returns
        -------
        value : bool
        """
        return self._hovered

    @hovered.setter
    def hovered(self, hovered: bool):
        self._hovered = hovered
