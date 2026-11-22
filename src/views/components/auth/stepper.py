"""Stepper of the sign-up form: five 24 px nodes joined by 2 px connectors, labels below."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from src.views import icons
from src.views.theme import Colors, Type

_NODE = 24
_HEIGHT = 48
_LABEL_TOP = 28


class Stepper(QWidget):
    step_clicked = Signal(int)

    def __init__(self, labels: tuple[str, ...], parent: QWidget | None = None):
        super().__init__(parent)
        self._labels = labels
        self._current = 0
        self._completed = 0      # steps 0 .. completed-1 have been validated
        self.setFixedHeight(_HEIGHT)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMouseTracking(True)
        self._describe()

    def set_current(self, index: int) -> None:
        self._current = index
        self._describe()
        self.update()

    def set_completed(self, count: int) -> None:
        self._completed = count
        self.update()

    def current(self) -> int:
        return self._current

    def completed(self) -> int:
        return self._completed

    def _describe(self) -> None:
        self.setAccessibleName(f"Step {self._current + 1} of {len(self._labels)}: {self._labels[self._current]}")

    # ------------------------------------------------------------------ geometry
    def _column(self) -> float:
        return self.width() / len(self._labels)

    def _center(self, index: int) -> QPointF:
        return QPointF(self._column() * (index + 0.5), _NODE / 2)

    def _index_at(self, x: float) -> int:
        return max(0, min(len(self._labels) - 1, int(x // self._column())))

    def _clickable(self, index: int) -> bool:
        return self.isEnabled() and index != self._current and index < self._completed

    def mouseMoveEvent(self, event) -> None:
        index = self._index_at(event.position().x())
        self.setCursor(Qt.CursorShape.PointingHandCursor if self._clickable(index) else Qt.CursorShape.ArrowCursor)

    def mousePressEvent(self, event) -> None:
        index = self._index_at(event.position().x())
        if self._clickable(index):
            self.step_clicked.emit(index)

    def sizeHint(self) -> QSize:
        return QSize(600, _HEIGHT)

    # ------------------------------------------------------------------ painting
    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        count = len(self._labels)
        radius = _NODE / 2

        for index in range(count - 1):
            start = self._center(index)
            end = self._center(index + 1)
            done = index < self._completed and index + 1 <= max(self._completed, self._current)
            painter.fillRect(QRectF(start.x() + radius + 4, radius - 1, end.x() - start.x() - _NODE - 8, 2),
                             QColor(Colors.P600 if done else Colors.N200))

        for index, label in enumerate(self._labels):
            center = self._center(index)
            node = QRectF(center.x() - radius, 0, _NODE, _NODE)
            current = index == self._current
            done = index < self._completed and not current
            if done:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(Colors.P600))
                painter.drawEllipse(node)
                pixmap = icons.icon_pixmap("check", Colors.N0, 16, self.devicePixelRatioF())
                painter.drawPixmap(QPointF(center.x() - 8, radius - 8), pixmap)
            else:
                width = 2 if current else 1
                painter.setPen(QPen(QColor(Colors.P600 if current else Colors.N300), width))
                painter.setBrush(QColor(Colors.N0))
                painter.drawEllipse(node.adjusted(width / 2, width / 2, -width / 2, -width / 2))
                painter.setFont(Type.font("caption-strong"))
                painter.setPen(QColor(Colors.P600 if current else Colors.N500))
                painter.drawText(node, int(Qt.AlignmentFlag.AlignCenter), str(index + 1))

            painter.setFont(Type.font("caption-strong" if current else "caption"))
            painter.setPen(QColor(Colors.N900 if current else Colors.N700 if done else Colors.N600))
            painter.drawText(QRectF(center.x() - self._column() / 2, _LABEL_TOP, self._column(), 16),
                             int(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter), label)
