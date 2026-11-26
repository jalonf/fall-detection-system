"""Badge: 20 px tall, overline text on a tinted fill with a border of the same hue, painted.

The border keeps a badge readable on any surface, including the red card of a fall alert.
"""

from __future__ import annotations

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from src.views.components.common.painting import crisp
from src.views.strings import Monitor
from src.views.theme import Colors, Radius, Type

RISK_VARIANTS = {"LOW": "success", "MEDIUM": "warning", "HIGH": "danger"}


def risk_badge(level: str) -> tuple[str, str]:
    """Text and variant of a patient's risk badge.

    Args:
        level: "LOW", "MEDIUM" or "HIGH".

    Returns:
        ("HIGH RISK", "danger"), for example; an unknown level is neutral.
    """
    return Monitor.RISK_BADGE.format(level=level), RISK_VARIANTS.get(level, "neutral")


VARIANTS = {    # fill, border, text
    "neutral": (Colors.N100, Colors.N200, Colors.N700),
    "info": (Colors.P50, Colors.P200, Colors.P700),
    "success": (Colors.G50, Colors.G200, Colors.G700),
    "warning": (Colors.A50, Colors.A200, Colors.A700),
    "danger": (Colors.R50, Colors.R200, Colors.R700),
    "danger-solid": (Colors.R600, Colors.R600, Colors.N0),
}
HEIGHT = 20
_PADDING = 8


class Badge(QWidget):
    """Small painted label with a colour variant (neutral, info, success, warning, danger...).

    Args:
        text: Text, already in upper case.
        variant: Key of `VARIANTS`.
        parent: Parent widget.
    """
    def __init__(self, text: str = "", variant: str = "neutral", parent: QWidget | None = None):
        super().__init__(parent)
        self._text = text
        self._variant = variant
        self.setFixedHeight(HEIGHT)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setAccessibleName(text)

    def set_badge(self, text: str, variant: str) -> None:
        """Changes the text and the variant.

        Args:
            text: New text, in upper case.
            variant: Key of `VARIANTS`.
        """
        if (text, variant) == (self._text, self._variant):
            return
        width_changed = text != self._text
        self._text, self._variant = text, variant
        self.setAccessibleName(text)
        if width_changed:
            self.updateGeometry()
        self.update()

    def text(self) -> str:
        """Returns the badge's text."""
        return self._text

    @staticmethod
    def width_for(text: str) -> int:
        """Returns the width a badge needs for a text.

        Args:
            text: The badge's text.

        Returns:
            The width in pixels, padding included.
        """
        return QFontMetrics(Type.font("overline")).horizontalAdvance(text) + 2 * _PADDING

    def sizeHint(self) -> QSize:
        """Preferred size: the text's width and the fixed height."""
        return QSize(self.width_for(self._text), HEIGHT)

    def paintEvent(self, event) -> None:
        """Paints the badge (see `paint`)."""
        painter = QPainter(self)
        self.paint(painter, QRectF(self.rect()), self._text, self._variant)

    @staticmethod
    def paint(painter: QPainter, rect: QRectF, text: str, variant: str) -> None:
        """Paints a badge in `rect` (used by Badge and by the event log delegate)."""
        background, border, foreground = VARIANTS[variant]
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor(border), 1))
        painter.setBrush(QColor(background))
        painter.drawRoundedRect(crisp(rect), Radius.R_SM, Radius.R_SM)
        painter.setFont(Type.font("overline"))
        painter.setPen(QColor(foreground))
        painter.drawText(rect, int(Qt.AlignmentFlag.AlignCenter), text)
        painter.restore()
