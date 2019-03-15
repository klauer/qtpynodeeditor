from qtpy.QtCore import QPoint, Qt, QLineF, QSize
from qtpy.QtGui import QPainter, QPainterPath, QPainterPathStroker, QIcon, QPen


from .enums import PortType
from .connection_geometry import ConnectionGeometry
from .style import StyleCollection


use_debug_drawing = False


def cubic_path(geom):
    source = geom.source()
    sink = geom.sink()
    c1, c2 = geom.points_c1_c2()

    # cubic spline
    cubic = QPainterPath(source)

    cubic.cubicTo(c1, c2, sink)
    return cubic


def debug_drawing(painter, connection):
    geom = connection.connection_geometry()

    source = geom.source()
    sink = geom.sink()

    c1, c2 = geom.points_c1_c2()

    painter.setPen(Qt.red)
    painter.setBrush(Qt.red)

    painter.drawLine(QLineF(source, c1))
    painter.drawLine(QLineF(c1, c2))
    painter.drawLine(QLineF(c2, sink))
    painter.drawEllipse(c1, 3, 3)
    painter.drawEllipse(c2, 3, 3)

    painter.setBrush(Qt.NoBrush)

    painter.drawPath(cubic_path(geom))
    painter.setPen(Qt.yellow)

    painter.drawRect(geom.boundingRect())


def draw_sketch_line(painter, connection):
    state = connection.connection_state()

    if state.requires_port():
        connection_style = StyleCollection.connection_style()

        p = QPen()
        p.setWidth(connection_style.construction_line_width())
        p.setColor(connection_style.construction_color())
        p.setStyle(Qt.DashLine)

        painter.setPen(p)
        painter.setBrush(Qt.NoBrush)

        geom = connection.connection_geometry()

        cubic = cubic_path(geom)
        # cubic spline
        painter.drawPath(cubic)


def draw_hovered_or_selected(painter, connection):
    geom = connection.connection_geometry()
    hovered = geom.hovered()

    graphics_object = connection.get_connection_graphics_object()
    selected = graphics_object.isSelected()

    # drawn as a fat background
    if hovered or selected:
        p = QPen()

        connection_style = StyleCollection.connection_style()
        line_width = connection_style.line_width()

        p.setWidth(2 * line_width)
        p.setColor((connection_style.selected_halo_color() if selected else connection_style.hovered_color()))

        painter.setPen(p)
        painter.setBrush(Qt.NoBrush)

        # cubic spline
        cubic = cubic_path(geom)
        painter.drawPath(cubic)


def draw_normal_line(painter, connection):
    state = connection.connection_state()

    if state.requires_port():
        return

    # colors

    connection_style = StyleCollection.connection_style()

    normal_color_out = connection_style.normal_color()
    normal_color_in = connection_style.normal_color()
    selected_color = connection_style.selected_color()

    gradient_color = False
    if connection_style.use_data_defined_colors():
        data_type_out = connection.data_type(PortType.Out)
        data_type_in = connection.data_type(PortType.In)

        gradient_color = data_type_out.id != data_type_in.id

        normal_color_out = connection_style.normal_color(data_type_out.id)
        normal_color_in = connection_style.normal_color(data_type_in.id)
        selected_color = normal_color_out.darker(200)

    # geometry
    geom = connection.connection_geometry()
    line_width = connection_style.line_width()

    # draw normal line
    p = QPen()
    p.setWidth(line_width)

    graphics_object = connection.get_connection_graphics_object()
    selected = graphics_object.isSelected()

    cubic = cubic_path(geom)
    if gradient_color:
        painter.setBrush(Qt.NoBrush)

        c = normal_color_out
        if selected:
            c = c.darker(200)

        p.setColor(c)
        painter.setPen(p)

        segments = 60

        for i in range(segments):
            ratio_prev = float(i) / segments
            ratio = float(i + 1) / segments

            if i == segments / 2:
                c = normal_color_in
                if selected:
                    c = c.darker(200)

                p.setColor(c)
                painter.setPen(p)

            painter.drawLine(cubic.pointAtPercent(ratio_prev), cubic.pointAtPercent(ratio))

        icon = QIcon(":convert.png")

        pixmap = icon.pixmap(QSize(22, 22))
        painter.drawPixmap(cubic.pointAtPercent(0.50) - QPoint(pixmap.width() / 2, pixmap.height() / 2), pixmap)
    else:
        p.setColor(normal_color_out)

        if selected:
            p.setColor(selected_color)

        painter.setPen(p)
        painter.setBrush(Qt.NoBrush)

        painter.drawPath(cubic)


class ConnectionPainter:
    @staticmethod
    def paint(painter: QPainter, connection):  # connection : Connection):
        """
        paint

        Parameters
        ----------
        painter : QPainter
        connection : Connection
        """
        draw_hovered_or_selected(painter, connection)
        draw_sketch_line(painter, connection)
        draw_normal_line(painter, connection)
        if use_debug_drawing:
            debug_drawing(painter, connection)

        # draw end points
        geom = connection.connection_geometry()
        source = geom.source()
        sink = geom.sink()
        connection_style = StyleCollection.connection_style()
        point_diameter = connection_style.point_diameter()
        painter.setPen(connection_style.construction_color())
        painter.setBrush(connection_style.construction_color())
        point_radius = point_diameter / 2.0
        painter.drawEllipse(source, point_radius, point_radius)
        painter.drawEllipse(sink, point_radius, point_radius)

    @staticmethod
    def get_painter_stroke(geom: ConnectionGeometry) -> QPainterPath:
        """
        get_painter_stroke

        Parameters
        ----------
        geom : ConnectionGeometry

        Returns
        -------
        value : QPainterPath
        """
        cubic = cubic_path(geom)
        source = geom.source()
        result = QPainterPath(source)
        segments = 20

        for i in range(segments):
            ratio = float(i + 1) / segments
            result.lineTo(cubic.pointAtPercent(ratio))

        stroker = QPainterPathStroker()
        stroker.setWidth(10.0)
        return stroker.createStroke(result)
