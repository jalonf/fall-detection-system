"""Spinner painting: a 270-degree arc with a 2 px stroke, rotated by an endless animation."""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt, QVariantAnimation
from PySide6.QtGui import QColor, QPainter, QPen


def paint_arc(painter: QPainter, rect: QRectF, angle: float, color: str, stroke: float = 2.0) -> None:
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(QColor(color), stroke)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    inset = stroke / 2 + 0.5
    painter.drawArc(rect.adjusted(inset, inset, -inset, -inset), round((90 - angle) * 16), -270 * 16)
    painter.restore()


def make_rotation(parent, slot) -> QVariantAnimation:
    """Endless 0-360 rotation, one turn per second, calling `slot(angle)`."""
    animation = QVariantAnimation(parent)
    animation.setStartValue(0.0)
    animation.setEndValue(360.0)
    animation.setDuration(1000)
    animation.setLoopCount(-1)
    animation.valueChanged.connect(slot)
    return animation
