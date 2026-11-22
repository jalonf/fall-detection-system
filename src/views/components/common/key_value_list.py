"""Key / value rows of 32 px, painted, so updating a value never relayouts."""

from __future__ import annotations

from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QSizePolicy, QWidget

from src.views.strings import EM_DASH
from src.views.theme import Colors, Type

ROW = 32
_TONES = {None: Colors.N900, "danger": Colors.R700}


class KeyValueList(QWidget):
    def __init__(self, rows: list[tuple[str, str]], parent: QWidget | None = None):
        super().__init__(parent)
        self._keys = [key for key, _ in rows]
        self._labels = dict(rows)
        self._values: dict[str, str | None] = {key: None for key in self._keys}
        self._tones: dict[str, str | None] = {key: None for key in self._keys}
        self.setFixedHeight(ROW * len(rows))
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._describe()

    def set_value(self, key: str, text: str | None, *, tone: str | None = None) -> None:
        if self._values[key] == text and self._tones[key] == tone:
            return
        self._values[key] = text
        self._tones[key] = tone
        row = self._keys.index(key)
        self.update(QRect(0, row * ROW, self.width(), ROW))
        self._describe()

    def value(self, key: str) -> str | None:
        return self._values[key]

    def _describe(self) -> None:
        parts = [f"{self._labels[key]}: {self._values[key] or EM_DASH}" for key in self._keys]
        self.setAccessibleDescription("; ".join(parts))

    def sizeHint(self) -> QSize:
        return QSize(280, ROW * len(self._keys))

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        label_font = Type.font("body")
        value_font = Type.font("body-strong", tabular=True)
        divider = QColor(Colors.N150)
        width = self.width()
        for row, key in enumerate(self._keys):
            top = row * ROW
            painter.setFont(label_font)
            painter.setPen(QColor(Colors.N600))
            label_rect = QRect(0, top, width // 2, ROW)
            painter.drawText(label_rect, int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                             self._labels[key])
            label_width = painter.fontMetrics().horizontalAdvance(self._labels[key])

            value = self._values[key]
            painter.setFont(value_font)
            if value is None:
                painter.setPen(QColor(Colors.N500))
                value = EM_DASH
            else:
                painter.setPen(QColor(_TONES.get(self._tones[key], Colors.N900)))
            available = width - label_width - 16
            shown = painter.fontMetrics().elidedText(value, Qt.TextElideMode.ElideMiddle, max(0, available))
            painter.drawText(QRect(0, top, width, ROW), int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
                             shown)
            if row < len(self._keys) - 1:
                painter.fillRect(QRect(0, top + ROW - 1, width, 1), divider)
