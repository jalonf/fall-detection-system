"""Metric tile: label, value with its unit and an optional 3 px bar. Painted, fixed size."""

from __future__ import annotations

from PySide6.QtCore import QRect, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QSizePolicy, QWidget

from src.views.strings import EM_DASH
from src.views.theme import Colors, Type


class MetricTile(QWidget):
    def __init__(self, label: str, unit: str = "", *, bar: bool = False, tooltip: str = "",
                 parent: QWidget | None = None):
        super().__init__(parent)
        self._label = label
        self._unit = unit
        self._bar = bar
        self._value: str | None = None
        self._ratio: float | None = None
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(62)
        if tooltip:
            self.setToolTip(tooltip)
            self.setAccessibleDescription(tooltip)
        self.setAccessibleName(label)

    def set_value(self, text: str | None, ratio: float | None = None) -> None:
        if text == self._value and ratio == self._ratio:
            return
        self._value = text
        self._ratio = ratio
        self.setAccessibleName(f"{self._label}: {text or EM_DASH} {self._unit if text else ''}".strip())
        self.update()

    def value(self) -> str | None:
        return self._value

    def sizeHint(self) -> QSize:
        return QSize(96, 62)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        x = 12
        width = self.width() - 2 * x
        painter.setFont(Type.font("caption-strong"))
        painter.setPen(QColor(Colors.N600))
        painter.drawText(QRect(x, 8, width, 16), int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                         self._label)

        value_rect = QRect(x, 24, width, 26)
        value_font = Type.font("metric", tabular=True)
        painter.setFont(value_font)
        if self._value is None:
            painter.setPen(QColor(Colors.N500))
            painter.drawText(value_rect, int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), EM_DASH)
        else:
            painter.setPen(QColor(Colors.N900))
            painter.drawText(value_rect, int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), self._value)
            if self._unit:
                advance = painter.fontMetrics().horizontalAdvance(self._value)
                ascent = painter.fontMetrics().ascent()
                baseline = value_rect.top() + (value_rect.height() - painter.fontMetrics().height()) / 2 + ascent
                painter.setFont(Type.font("caption"))
                painter.setPen(QColor(Colors.N500))
                painter.drawText(QRectF(x + advance + 4, baseline - painter.fontMetrics().ascent(), 40,
                                        painter.fontMetrics().height()),
                                 int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop), self._unit)

        if self._bar:
            track = QRect(x, 54, width, 3)
            painter.fillRect(track, QColor(Colors.N150))
            if self._ratio is not None:
                ratio = max(0.0, min(1.0, self._ratio))
                fill = Colors.A600 if ratio < 0.5 else Colors.P600
                painter.fillRect(QRect(x, 54, round(width * ratio), 3), QColor(fill))
