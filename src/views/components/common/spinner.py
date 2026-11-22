"""Spinner: a 270-degree arc with a 2 px stroke that rotates while visible."""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt, QVariantAnimation, Slot
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

from src.views.theme import Colors


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


class Spinner(QWidget):
    def __init__(self, size: int = 16, color: str = Colors.P600, parent: QWidget | None = None):
        super().__init__(parent)
        self._color = color
        self._angle = 0.0
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._rotation = make_rotation(self, self._on_angle)

    def set_color(self, color: str) -> None:
        self._color = color
        self.update()

    @Slot("QVariant")
    def _on_angle(self, angle) -> None:
        self._angle = float(angle)
        self.update()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._rotation.start()

    def hideEvent(self, event) -> None:
        super().hideEvent(event)
        self._rotation.stop()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        paint_arc(painter, QRectF(self.rect()), self._angle, self._color)
