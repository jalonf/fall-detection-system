"""Overlay at the top of the stage: the source bar (40 px, only with an image or while starting).
It never takes mouse input."""

from __future__ import annotations

from PySide6.QtCore import QRect, QRectF, Qt
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPixmap
from PySide6.QtWidgets import QWidget

from src.views import icons
from src.views.strings import Monitor
from src.views.theme import Colors, Radius, Type, qcolor

BAR = 40
_PILL_HEIGHT = 20


class StageOverlay(QWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._kind = "camera"
        self._label = ""
        self._bar = False
        self._live = False
        self._gradient: QPixmap | None = None

    # ------------------------------------------------------------------ API
    def set_source(self, kind: str, label: str) -> None:
        if (kind, label) != (self._kind, self._label):
            self._kind, self._label = kind, label
            self.update(0, 0, self.width(), BAR)

    def set_bar(self, visible: bool, live: bool) -> None:
        if (visible, live) != (self._bar, self._live):
            self._bar, self._live = visible, live
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
        overline = Type.font("overline")
        painter.setFont(overline)
        metrics = painter.fontMetrics()

        # Right: LIVE / STANDBY pill.
        text = Monitor.OVERLAY_LIVE if self._live else Monitor.OVERLAY_STANDBY
        pill_width = 8 + 6 + 6 + metrics.horizontalAdvance(text) + 8
        pill = QRectF(self.width() - 12 - pill_width, (BAR - _PILL_HEIGHT) / 2, pill_width, _PILL_HEIGHT)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 0, 0, round(255 * 0.45)))
        painter.drawRoundedRect(pill, Radius.R_SM, Radius.R_SM)
        marker = QRectF(pill.left() + 8, pill.center().y() - 3, 6, 6)
        if self._live:
            painter.setBrush(QColor(Colors.G500))
            painter.drawEllipse(marker)
        else:
            painter.fillRect(marker, QColor(Colors.N400))
        painter.setPen(QColor(Colors.N0))
        painter.drawText(QRectF(marker.right() + 6, pill.top(), pill.right() - marker.right() - 6, pill.height()),
                         int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), text)

        # Left: source icon and name.
        icon_name = "film" if self._kind == "file" else "camera"
        painter.drawPixmap(12, (BAR - 16) // 2, icons.icon_pixmap(icon_name, Colors.S100, 16, self.devicePixelRatioF()))
        available = int(pill.left() - 12 - 16 - 8 - 16)
        label = metrics.elidedText(self._label.upper(), Qt.TextElideMode.ElideMiddle, max(0, available))
        painter.setPen(QColor(Colors.S100))
        painter.drawText(QRectF(12 + 16 + 8, 0, available, BAR),
                         int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), label)
