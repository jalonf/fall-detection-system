"""Panel: square N0 surface, N200 border, a 48 px N50 header band and an optional 56 px footer."""

from __future__ import annotations

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from src.views.theme import Colors, Size, Space, make_label


class Panel(QWidget):
    """Container with a title, an optional subtitle / counter and an actions slot on the right.

    The body has 16 px of padding, or none when `flush` (video stage, tables).
    """

    def __init__(self, title: str, *, subtitle: str = "", flush: bool = False, footer: bool = False,
                 parent: QWidget | None = None):
        super().__init__(parent)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(1, 1, 1, 1)
        outer.setSpacing(0)

        self.header = QWidget()
        self.header.setFixedHeight(Size.PANEL_HEADER - 1)
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(Space.S4 - 1, 0, Space.S4 - 1, 0)
        header_layout.setSpacing(0)
        self.title_label: QLabel = make_label(title, "title-sm")
        header_layout.addWidget(self.title_label)
        header_layout.addSpacing(Space.S2)
        self.subtitle_label: QLabel = make_label(subtitle, "caption", "tertiary")
        header_layout.addWidget(self.subtitle_label, 0, Qt.AlignmentFlag.AlignVCenter)
        header_layout.addStretch(1)
        self._actions = QHBoxLayout()
        self._actions.setContentsMargins(0, 0, 0, 0)
        self._actions.setSpacing(Space.S2)
        header_layout.addLayout(self._actions)
        outer.addWidget(self.header)
        outer.addSpacing(1)   # header divider

        self.body = QWidget()
        self._body_layout = QVBoxLayout(self.body)
        padding = 0 if flush else Space.S4 - 1
        self._body_layout.setContentsMargins(padding, 0 if flush else Space.S4, padding, padding)
        self._body_layout.setSpacing(0)
        outer.addWidget(self.body, 1)

        self.footer: QWidget | None = None
        self._footer_layout: QHBoxLayout | None = None
        if footer:
            outer.addSpacing(1)   # footer divider
            self.footer = QWidget()
            self.footer.setFixedHeight(Size.PANEL_FOOTER - 1)
            self._footer_layout = QHBoxLayout(self.footer)
            self._footer_layout.setContentsMargins(Space.S4 - 1, 0, Space.S4 - 1, 0)
            self._footer_layout.setSpacing(0)
            outer.addWidget(self.footer)

    # ------------------------------------------------------------------ API

    def set_subtitle(self, text: str) -> None:
        """Changes the text next to the title.

        Args:
            text: The new subtitle (or counter).
        """
        if text != self.subtitle_label.text():
            self.subtitle_label.setText(text)

    def add_action(self, widget: QWidget) -> None:
        """Adds a widget to the right of the header.

        Args:
            widget: Button, combo or label.
        """
        self._actions.addWidget(widget, 0, Qt.AlignmentFlag.AlignVCenter)

    def body_layout(self) -> QVBoxLayout:
        """Returns the layout where the panel's content goes."""
        return self._body_layout

    def footer_layout(self) -> QHBoxLayout:
        """Returns the footer's layout (the panel must be created with `footer=True`)."""
        assert self._footer_layout is not None, "the panel was created without a footer"
        return self._footer_layout

    # ------------------------------------------------------------------ painting
    def paintEvent(self, event) -> None:
        """Paints the surface, the header band and the borders (filled, so they stay crisp at any scale)."""
        painter = QPainter(self)
        rect = self.rect()
        painter.fillRect(rect, QColor(Colors.N200))
        painter.fillRect(rect.adjusted(1, 1, -1, -1), QColor(Colors.N0))
        header_bottom = self.header.geometry().bottom() + 1
        painter.fillRect(QRect(1, 1, rect.width() - 2, header_bottom - 1), QColor(Colors.N50))
        painter.fillRect(QRect(1, header_bottom, rect.width() - 2, 1), QColor(Colors.N200))
        if self.footer is not None:
            painter.fillRect(QRect(1, self.footer.geometry().top() - 1, rect.width() - 2, 1), QColor(Colors.N150))
