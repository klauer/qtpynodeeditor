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
        points_c1_c2

        Returns
        -------
        value : pair<QPointF, QPointF
        """
        x_distance = self._in.x() - self._out.x()

        # double yDistance = _in.y() - _out.y() - 100;
        default_offset = 200
        minimum = min((default_offset, abs(x_distance)))
        vertical_offset = 0
        ratio1 = 0.5
        if x_distance <= 0:
            vertical_offset = -minimum
            ratio1 = 1.0

        # double verticalOffset2 = vertical_offset;
        # if (x_distance <= 0)
        # verticalOffset2 = qMin(default_offset, std::abs(yDistance));
        # auto sign = [](double d) { return d > 0.0 ? +1.0 : -1.0; };

        # verticalOffset2 = 0.0;
        c1 = QPointF(self._out.x() + minimum * ratio1, self._out.y() + vertical_offset)
        c2 = QPointF(self._in.x() - minimum * ratio1, self._in.y() + vertical_offset)
        return c1, c2

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
