"""Callout: an inline message box (info or danger) with an icon, used in place of toasts."""

from __future__ import annotations

from PySide6.QtCore import QRectF
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from src.views.components.common.painting import IconView, crisp
from src.views.theme import Colors, Radius, Space, make_label, set_props

KINDS = {
    # fill, border, icon, icon colour, text tone
    "info": (Colors.P50, Colors.P200, "info", Colors.P600, "info"),
    "danger": (Colors.R50, Colors.R200, "alert-circle", Colors.R600, "danger"),
}


class Callout(QWidget):
    """Inline message box with an icon, used instead of a toast.

    Args:
        text: Message.
        kind: "info" or "danger".
        parent: Parent widget.
    """
    def __init__(self, text: str = "", kind: str = "info", parent: QWidget | None = None):
        super().__init__(parent)
        self._kind = kind
        layout = QHBoxLayout(self)
        layout.setContentsMargins(Space.S3, Space.S3, Space.S3, Space.S3)
        layout.setSpacing(Space.S2)
        icon_box = QVBoxLayout()
        icon_box.setContentsMargins(0, 2, 0, 0)
        self._icon = IconView(KINDS[kind][2], KINDS[kind][3], 16)
        icon_box.addWidget(self._icon)
        icon_box.addStretch(1)
        layout.addLayout(icon_box)
        self._label = make_label(text, "body", KINDS[kind][4], wrap=True)
        layout.addWidget(self._label, 1)
        self.setAccessibleName(text)

    def set_message(self, text: str, kind: str | None = None) -> None:
        """Changes the message and, optionally, the kind.

        Args:
            text: The new message.
            kind: "info" or "danger"; None keeps the current one.
        """
        if kind and kind != self._kind:
            self._kind = kind
            self._icon.set_icon(KINDS[kind][2], KINDS[kind][3])
            set_props(self._label, tone=KINDS[kind][4])
        self._label.setText(text)
        self.setAccessibleName(text)
        self.update()

    def text(self) -> str:
        """Returns the message shown."""
        return self._label.text()

    def paintEvent(self, event) -> None:
        """Paints the filled box with its border."""
        fill, border = KINDS[self._kind][:2]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QColor(border))
        painter.setBrush(QColor(fill))
        painter.drawRoundedRect(crisp(QRectF(self.rect())), Radius.R_MD, Radius.R_MD)
