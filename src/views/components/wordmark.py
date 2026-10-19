from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QWidget


class Wordmark(QWidget):
    """
    Typographic identity of the application: a short accent bar and the name, with an
    optional caption after a hairline ("Name | Administrator Control Panel"). No image
    asset is involved, so it renders crisply at any scale and in any theme.

    `large=True` is the version used on the sign-in screen.
    """

    def __init__(self, name: str, caption: str = "", large: bool = False, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12 if large else 10)

        bar = QFrame()
        bar.setObjectName("wordmarkBar")
        bar.setFixedSize(3, 26 if large else 18)
        layout.addWidget(bar, 0, Qt.AlignmentFlag.AlignVCenter)

        self.name_label = QLabel(name)
        self.name_label.setObjectName("wordmarkLarge" if large else "wordmark")
        layout.addWidget(self.name_label, 0, Qt.AlignmentFlag.AlignVCenter)

        self.caption_label = None
        if caption:
            divider = QFrame()
            divider.setObjectName("wordmarkDivider")
            divider.setFixedSize(1, 16)
            layout.addSpacing(4)
            layout.addWidget(divider, 0, Qt.AlignmentFlag.AlignVCenter)
            layout.addSpacing(4)

            self.caption_label = QLabel(caption)
            self.caption_label.setObjectName("wordmarkCaption")
            layout.addWidget(self.caption_label, 0, Qt.AlignmentFlag.AlignVCenter)
