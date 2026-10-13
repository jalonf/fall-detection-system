from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from src.views.theme import Colors


class AuthHeader(QWidget):
    """
    Shared heading for the login and registration forms: a two-tone title
    (the accent word picks up the brand blue) and a subtitle.

    `icon_name` is accepted for API stability but no icon is drawn.
    """

    def __init__(self, icon_name: str, lead: str, accent: str, subtitle: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.title = QLabel(f"{lead} <span style='color:{Colors.PRIMARY};'>{accent}</span>")
        self.title.setObjectName("formTitle")
        self.title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.title)
        layout.addSpacing(8)

        self.subtitle = QLabel(subtitle)
        self.subtitle.setObjectName("formSubtitle")
        self.subtitle.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.subtitle)
