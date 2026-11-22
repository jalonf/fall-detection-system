"""Status indicator: shape + colour + text, so the state never depends on colour alone.

idle / finished: 8 px square N400 · starting: spinner P600 · stopping: spinner A600 ·
live: 8 px circle G600 (G500 on dark) · error: 12 px triangle R600 · alert: the triangle pulsing.
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, Slot
from PySide6.QtGui import QColor, QFontMetrics, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from src.views.components.common.spinner import make_rotation, paint_arc
from src.views.theme import Colors, Type, mix

_BOX = 12
_GAP = 8


def paint_triangle(painter: QPainter, rect: QRectF, color: QColor, mark: QColor) -> None:
    """Filled warning triangle with an exclamation mark, fitted in `rect`."""
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    w, h = rect.width(), rect.height()
    path = QPainterPath()
    path.moveTo(rect.left() + w / 2, rect.top() + 0.5)
    path.lineTo(rect.right() - 0.25, rect.bottom() - 0.75)
    path.lineTo(rect.left() + 0.25, rect.bottom() - 0.75)
    path.closeSubpath()
    painter.setPen(QPen(color, 1.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    painter.setBrush(color)
    painter.drawPath(path)
    pen = QPen(mark, max(1.2, w / 9), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    cx = rect.left() + w / 2
    painter.drawLine(QPointF(cx, rect.top() + h * 0.38), QPointF(cx, rect.top() + h * 0.62))
    painter.drawPoint(QPointF(cx, rect.top() + h * 0.80))
    painter.restore()


class StatusIndicator(QWidget):
    KINDS = ("idle", "starting", "live", "stopping", "error", "finished", "alert")

    def __init__(self, *, on_dark: bool = False, reserve: tuple[str, ...] = (), parent: QWidget | None = None):
        super().__init__(parent)
        self._on_dark = on_dark
        self._kind = "idle"
        self._text = ""
        self._phase = 0.0
        self._angle = 0.0
        self._rotation = make_rotation(self, self._on_angle)
        metrics = QFontMetrics(Type.font("body-strong"))
        self._reserved = max((metrics.horizontalAdvance(text) for text in reserve), default=0)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(Type.line_height("body-strong"))

    def set_status(self, kind: str, text: str) -> None:
        self._kind = kind
        self._text = text
        self.setAccessibleName(text)
        if kind in ("starting", "stopping") and self.isVisible():
            self._rotation.start()
        else:
            self._rotation.stop()
        self.updateGeometry()
        self.update()

    def kind(self) -> str:
        return self._kind

    def text(self) -> str:
        return self._text

    def set_pulse_phase(self, phase: float) -> None:
        if self._kind == "alert":
            self._phase = phase
            self.update(self._indicator_rect().toAlignedRect().adjusted(-1, -1, 1, 1))

    @Slot("QVariant")
    def _on_angle(self, angle) -> None:
        self._angle = float(angle)
        self.update(self._indicator_rect().toAlignedRect().adjusted(-1, -1, 1, 1))

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if self._kind in ("starting", "stopping"):
            self._rotation.start()

    def hideEvent(self, event) -> None:
        super().hideEvent(event)
        self._rotation.stop()

    def sizeHint(self) -> QSize:
        metrics = QFontMetrics(Type.font("body-strong"))
        text_width = max(metrics.horizontalAdvance(self._text), self._reserved)
        return QSize(_BOX + _GAP + text_width + 1, Type.line_height("body-strong"))

    def _indicator_rect(self) -> QRectF:
        return QRectF(0, (self.height() - _BOX) / 2, _BOX, _BOX)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        box = self._indicator_rect()
        kind = self._kind
        if kind in ("idle", "finished"):
            painter.fillRect(QRectF(box.center().x() - 4, box.center().y() - 4, 8, 8), QColor(Colors.N400))
        elif kind == "live":
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(Colors.G500 if self._on_dark else Colors.G600))
            painter.drawEllipse(box.center(), 4, 4)
        elif kind in ("starting", "stopping"):
            color = Colors.P600 if kind == "starting" else Colors.A600
            if self._on_dark:
                color = Colors.S100
            paint_arc(painter, box, self._angle, color, 1.75)
        elif kind == "error":
            paint_triangle(painter, box, QColor(Colors.R600), QColor(Colors.N0))
        elif kind == "alert":
            paint_triangle(painter, box, mix(Colors.R600, Colors.R300, self._phase), QColor(Colors.N0))

        painter.setFont(Type.font("body-strong"))
        painter.setPen(QColor(Colors.S100 if self._on_dark else Colors.N900))
        painter.drawText(QRectF(_BOX + _GAP, 0, self.width() - _BOX - _GAP, self.height()),
                         int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), self._text)
