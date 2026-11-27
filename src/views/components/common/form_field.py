"""Form field: label, control and a help or error message."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from src.strings import Common
from src.views.components.common.painting import IconView
from src.views.theme import Colors, make_label, set_props


class FieldMessage(QWidget):
    """Help text (N600) or an error (alert-circle 12 + R700) under a control, 6 px below it."""

    def __init__(self, help_text: str = "", parent: QWidget | None = None):
        super().__init__(parent)
        self._help = help_text
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 6, 0, 0)
        layout.setSpacing(6)
        self._icon = IconView("alert-circle", Colors.R700, 12)
        icon_box = QVBoxLayout()
        icon_box.setContentsMargins(0, 2, 0, 0)
        icon_box.addWidget(self._icon)
        icon_box.addStretch(1)
        layout.addLayout(icon_box)
        self._text = make_label("", "caption", "secondary", wrap=True)
        self._text.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        layout.addWidget(self._text, 1)
        self.set_error(None)

    def set_error(self, message: str | None) -> None:
        """Shows an error, or the help text when there is none.

        Args:
            message: The error, or None / an empty string for no error.
        """
        error = bool(message)
        self._icon.setVisible(error)
        text = message if error else self._help
        self._text.setText(text or "")
        set_props(self._text, tone="danger" if error else "secondary")
        self.setVisible(bool(text))

    def text(self) -> str:
        """Returns the text shown, or an empty string when the message is hidden."""
        parent = self.parentWidget()
        shown = self.isVisibleTo(parent) if parent is not None else not self.isHidden()
        return self._text.text() if shown else ""


class FormField(QWidget):
    """Label (body-strong N700), the control 6 px below and the message 6 px below that.

    `set_error(msg)` marks the control invalid (R600 border and focus ring) and shows `msg`;
    an empty string marks it invalid without a message; None clears the error.
    """

    def __init__(self, label: str, control: QWidget, *, help_text: str = "", optional: bool = False,
                 parent: QWidget | None = None):
        super().__init__(parent)
        self.control = control
        self._help = help_text
        self._invalid = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(8)
        self.label: QLabel = make_label(label, "body-strong", "body")
        self.label.setBuddy(control)
        header.addWidget(self.label)
        header.addStretch(1)
        if optional:
            header.addWidget(make_label(Common.OPTIONAL, "caption", "tertiary"))
        layout.addLayout(header)
        layout.addSpacing(6)
        layout.addWidget(control)
        self._message = FieldMessage(help_text)
        layout.addWidget(self._message)

        if not control.accessibleName():
            control.setAccessibleName(label)
        if help_text:
            control.setAccessibleDescription(help_text)

    def set_error(self, message: str | None) -> None:
        """Marks the control invalid and shows a message, or clears the error.

        Args:
            message: The error; an empty string marks it invalid without a message; None clears it.
        """
        self._invalid = message is not None
        set_invalid = getattr(self.control, "set_invalid", None)     # the inputs that paint their own border
        if callable(set_invalid):
            set_invalid(self._invalid)
        else:
            set_props(self.control, invalid=self._invalid)
        self._message.set_error(message or None)
        self.control.setAccessibleDescription(message or self._help)

    def has_error(self) -> bool:
        """True while the field is marked invalid."""
        return self._invalid
