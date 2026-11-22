"""Password requirements in a 2 x 2 grid, updated as the user types."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from src.views import icons
from src.views.strings import Register
from src.views.theme import Colors, Type

_ROW = 20
_GAP = 4


class PasswordChecklist(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._met = dict.fromkeys((key for key, _ in Register.CHECKLIST), False)
        self.setFixedHeight(2 * _ROW + _GAP)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._describe()

    @staticmethod
    def requirements(password: str) -> dict[str, bool]:
        return {
            "length": len(password) >= 8,
            "upper": any(char.isupper() for char in password),
            "number": any(char.isdigit() for char in password),
            "symbol": any(not char.isalnum() and not char.isspace() for char in password),
        }

    def set_password(self, password: str) -> None:
        met = self.requirements(password)
        if met != self._met:
            self._met = met
            self._describe()
            self.update()

    def is_satisfied(self) -> bool:
        return all(self._met.values())

    def _describe(self) -> None:
        parts = [f"{label}: {'met' if self._met[key] else 'missing'}" for key, label in Register.CHECKLIST]
        self.setAccessibleDescription("; ".join(parts))

    def sizeHint(self) -> QSize:
        return QSize(600, 2 * _ROW + _GAP)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setFont(Type.font("caption"))
        column = self.width() / 2
        dpr = self.devicePixelRatioF()
        for index, (key, label) in enumerate(Register.CHECKLIST):
            x = (index % 2) * column
            y = (index // 2) * (_ROW + _GAP)
            met = self._met[key]
            if met:
                painter.drawPixmap(QPointF(x, y + 2), icons.icon_pixmap("check", Colors.G600, 16, dpr))
            else:
                painter.setPen(QPen(QColor(Colors.N300), 1.25))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(QPointF(x + 8, y + _ROW / 2), 5, 5)
            painter.setPen(QColor(Colors.N700 if met else Colors.N600))
            painter.drawText(QRectF(x + 24, y, column - 24, _ROW),
                             int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), label)
