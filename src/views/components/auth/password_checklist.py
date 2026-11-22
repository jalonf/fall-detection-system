"""Password requirements in a 2 x 2 grid, updated as the user types."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, Slot
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from src.domain import password_policy
from src.views import icons
from src.views.strings import Register
from src.views.theme import Colors, Type

_ROW = 20
_GAP = 4


class PasswordChecklist(QWidget):
    """The four password requirements, each ticked as soon as it is met."""
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._met = dict.fromkeys((key for key, _ in Register.CHECKLIST), False)
        self.setFixedHeight(2 * _ROW + _GAP)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._describe()

    @staticmethod
    def requirements(password: str) -> dict[str, bool]:
        """The shared rules (also used by `python -m src.create_admin`)."""
        return password_policy.requirements(password)

    @Slot(str)
    def set_password(self, password: str) -> None:
        """Updates the ticks for the password being typed.

        Args:
            password: The text of the password field.
        """
        met = self.requirements(password)
        if met != self._met:
            self._met = met
            self._describe()
            self.update()

    def is_satisfied(self) -> bool:
        """True when every requirement is met."""
        return all(self._met.values())

    def _describe(self) -> None:
        parts = [f"{label}: {'met' if self._met[key] else 'missing'}" for key, label in Register.CHECKLIST]
        self.setAccessibleDescription("; ".join(parts))

    def sizeHint(self) -> QSize:
        """Preferred size: two rows of requirements."""
        return QSize(600, 2 * _ROW + _GAP)

    def paintEvent(self, event) -> None:
        """Paints the 2 x 2 grid of requirements: tick or empty circle, and label."""
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
