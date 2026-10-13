from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel

from src.views.theme import set_prop


class StatusChip(QFrame):
    """
    Compact pill showing a coloured dot and a short status text.

    `tone` is kept for API compatibility and `state` is
    one of "idle", "active" or "alert". All colours live in style.qss.
    """

    def __init__(self, tone: str = "light", text: str = "", state: str = "idle", parent=None):
        super().__init__(parent)
        self.setObjectName("statusChip")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedHeight(28)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(11, 0, 13, 0)
        layout.setSpacing(8)

        self._dot = QFrame()
        self._dot.setObjectName("chipDot")
        self._dot.setFixedSize(8, 8)

        self._text = QLabel(text)
        self._text.setObjectName("chipText")

        layout.addWidget(self._dot)
        layout.addWidget(self._text)

        for widget in (self, self._dot, self._text):
            widget.setProperty("tone", tone)
            widget.setProperty("state", state)

    def set_state(self, state: str, text: str | None = None):
        for widget in (self, self._dot, self._text):
            set_prop(widget, "state", state)
        if text is not None:
            self._text.setText(text)
