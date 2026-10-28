from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap

from src.views.theme import Colors


def paint_brand_mark(painter: QPainter, size: float) -> None:
    """
    Draws the logo in a `size` x `size` square: a white detection reticle (four corner
    brackets around a dot, a target locked by a camera) on a rounded blue tile. The
    reticle is the same one that frames the video stage and the "Fall detected" box.
    """
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(Colors.PRIMARY))
    painter.drawRoundedRect(QRectF(0, 0, size, size), size * 0.24, size * 0.24)

    white = QColor(Colors.ON_PRIMARY)
    pen = QPen(white, max(1.2, size * 0.07))
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    near, far, arm = size * 0.25, size * 0.75, size * 0.16
    for cx, cy, dx, dy in (
        (near, near, 1, 1), (far, near, -1, 1),
        (near, far, 1, -1), (far, far, -1, -1),
    ):
        corner = QPainterPath()
        corner.moveTo(QPointF(cx + dx * arm, cy))
        corner.lineTo(QPointF(cx, cy))
        corner.lineTo(QPointF(cx, cy + dy * arm))
        painter.drawPath(corner)

    radius = size * 0.085
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(white)
    painter.drawEllipse(QPointF(size / 2, size / 2), radius, radius)


def brand_icon() -> QIcon:
    """The logo as an application icon (window title bar and taskbar)."""
    icon = QIcon()
    for size in (16, 24, 32, 48, 64, 128, 256):
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        paint_brand_mark(painter, float(size))
        painter.end()
        icon.addPixmap(pixmap)
    return icon
