"""FallSense logo mark: a minimal pose pictogram (head, spine, hips, legs as landmarks and links).

It is painted with antialiasing straight onto its parent, never on a filled box, so it always takes
the exact background of the screen it sits on.
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

from src.views.theme import Colors

TONES = {
    "on-dark": (Colors.P200, Colors.N0),     # links, nodes
    "on-light": (Colors.P600, Colors.P700),
}


def paint_logo_mark(painter: QPainter, origin: QPointF, size: float, tone: str = "on-light") -> None:
    """Draws the mark in a `size` x `size` square whose top-left corner is `origin`."""
    link, node = TONES[tone]
    unit = size / 24.0

    def at(x: float, y: float) -> QPointF:
        return QPointF(origin.x() + x * unit, origin.y() + y * unit)

    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(QColor(link), max(1.25, 1.6 * unit))
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawEllipse(at(12, 5.2), 3.0 * unit, 3.0 * unit)           # head
    painter.drawLine(at(12, 8.8), at(12, 14.2))                          # spine
    painter.drawLine(at(12, 10.6), at(6.6, 13.4))                        # arms
    painter.drawLine(at(12, 10.6), at(17.4, 13.4))
    painter.drawLine(at(12, 14.2), at(7.6, 21.0))                        # legs
    painter.drawLine(at(12, 14.2), at(16.4, 21.0))

    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(node))
    for x, y, r in ((12, 10.6, 1.6), (12, 14.2, 1.9), (6.6, 13.4, 1.3), (17.4, 13.4, 1.3),
                    (7.6, 21.0, 1.4), (16.4, 21.0, 1.4)):
        painter.drawEllipse(at(x, y), r * unit, r * unit)
    painter.restore()


class LogoMark(QWidget):
    def __init__(self, size: int = 24, tone: str = "on-light", parent: QWidget | None = None):
        super().__init__(parent)
        self._size = size
        self._tone = tone
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def sizeHint(self) -> QSize:
        return QSize(self._size, self._size)

    def paintEvent(self, event) -> None:
        paint_logo_mark(QPainter(self), QPointF(0, 0), self._size, self._tone)
