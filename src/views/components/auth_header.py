from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class AuthHeader(QWidget):
    """Shared heading for the login and registration forms: a title and a subtitle."""

    def __init__(self, title: str, subtitle: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.title = QLabel(title)
        self.title.setObjectName("formTitle")
        self.title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.title)
        layout.addSpacing(8)

        self.subtitle = QLabel(subtitle)
        self.subtitle.setObjectName("formSubtitle")
        self.subtitle.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.subtitle)
