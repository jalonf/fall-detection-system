"""Badge: 20 px tall, overline text, painted."""

from __future__ import annotations

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFontMetrics, QPainter
from PySide6.QtWidgets import QSizePolicy, QWidget

from src.views.theme import Colors, Radius, Type

VARIANTS = {
    "neutral": (Colors.N100, Colors.N700),
    "info": (Colors.P50, Colors.P700),
    "success": (Colors.G50, Colors.G700),
    "warning": (Colors.A50, Colors.A700),
    "danger": (Colors.R50, Colors.R700),
    "danger-solid": (Colors.R600, Colors.N0),
}
HEIGHT = 20
_PADDING = 8


class Badge(QWidget):
    def __init__(self, text: str = "", variant: str = "neutral", parent: QWidget | None = None):
        super().__init__(parent)
        self._text = text
        self._variant = variant
        self.setFixedHeight(HEIGHT)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setAccessibleName(text)

    def set_badge(self, text: str, variant: str) -> None:
        if (text, variant) == (self._text, self._variant):
            return
        width_changed = text != self._text
        self._text, self._variant = text, variant
        self.setAccessibleName(text)
        if width_changed:
            self.updateGeometry()
        self.update()

    def text(self) -> str:
        return self._text

    @staticmethod
    def width_for(text: str) -> int:
        return QFontMetrics(Type.font("overline")).horizontalAdvance(text) + 2 * _PADDING

    def sizeHint(self) -> QSize:
        return QSize(self.width_for(self._text), HEIGHT)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        self.paint(painter, QRectF(self.rect()), self._text, self._variant)

    @staticmethod
    def paint(painter: QPainter, rect: QRectF, text: str, variant: str) -> None:
        """Paints a badge in `rect` (used by Badge and by the event log delegate)."""
        background, foreground = VARIANTS[variant]
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(background))
        painter.drawRoundedRect(rect, Radius.R_SM, Radius.R_SM)
        painter.setFont(Type.font("overline"))
        painter.setPen(QColor(foreground))
        painter.drawText(rect, int(Qt.AlignmentFlag.AlignCenter), text)
        painter.restore()
