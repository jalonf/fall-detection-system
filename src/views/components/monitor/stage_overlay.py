"""Overlay at the top of the stage: the source bar (40 px, only with an image or while starting) with
the source's icon and name. The monitoring status is not repeated here: the session card shows it.
It never takes mouse input."""

from __future__ import annotations

from PySide6.QtCore import QRect, QRectF, Qt
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPixmap
from PySide6.QtWidgets import QWidget

from src.views import icons
from src.views.theme import Colors, Type, qcolor

BAR = 40
_PADDING = 12


class StageOverlay(QWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._kind = "camera"
        self._label = ""
        self._bar = False
        self._gradient: QPixmap | None = None

    # ------------------------------------------------------------------ API
    def set_source(self, kind: str, label: str) -> None:
        if (kind, label) != (self._kind, self._label):
            self._kind, self._label = kind, label
            self.update(0, 0, self.width(), BAR)

    def set_bar(self, visible: bool) -> None:
        if visible != self._bar:
            self._bar = visible
            self.update(0, 0, self.width(), BAR)

    # ------------------------------------------------------------------ painting
    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._gradient = None

    def _gradient_pixmap(self) -> QPixmap:
        dpr = self.devicePixelRatioF()
        if self._gradient is None or self._gradient.devicePixelRatio() != dpr:
            pixmap = QPixmap(max(1, round(self.width() * dpr)), round(BAR * dpr))
            pixmap.setDevicePixelRatio(dpr)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            gradient = QLinearGradient(0, 0, 0, BAR)
            gradient.setColorAt(0.0, qcolor(Colors.S900, 0.7))
            gradient.setColorAt(1.0, qcolor(Colors.S900, 0.0))
            painter.fillRect(QRect(0, 0, self.width(), BAR), gradient)
            painter.end()
            self._gradient = pixmap
        return self._gradient

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        if self._bar:
            self._paint_bar(painter)

    def _paint_bar(self, painter: QPainter) -> None:
        painter.drawPixmap(0, 0, self._gradient_pixmap())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setFont(Type.font("overline"))
        metrics = painter.fontMetrics()

        # Source icon and name.
        icon_name = "film" if self._kind == "file" else "camera"
        painter.drawPixmap(_PADDING, (BAR - 16) // 2,
                           icons.icon_pixmap(icon_name, Colors.S100, 16, self.devicePixelRatioF()))
        text_x = _PADDING + 16 + 8
        available = max(0, self.width() - text_x - _PADDING)
        label = metrics.elidedText(self._label.upper(), Qt.TextElideMode.ElideMiddle, available)
        painter.setPen(QColor(Colors.S100))
        painter.drawText(QRectF(text_x, 0, available, BAR),
                         int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), label)
