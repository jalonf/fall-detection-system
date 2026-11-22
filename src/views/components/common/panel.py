"""Panel: N0 surface, N200 border, radius 8, a 48 px header and an optional 56 px footer."""

from __future__ import annotations

import math

from PySide6.QtCore import QEvent, QRect, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QRegion
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from src.views.components.common.painting import crisp
from src.views.theme import Colors, Radius, Size, Space, make_label


class Panel(QWidget):
    """Container with a title, an optional subtitle / counter and an actions slot on the right.

    The body has 16 px of padding, or none when `flush` (video stage, tables). A flush body that
    reaches the bottom corners is masked to the rounded border.
    """

    def __init__(self, title: str, *, subtitle: str = "", flush: bool = False, footer: bool = False,
                 parent: QWidget | None = None):
        super().__init__(parent)
        self._flush = flush
        self._has_footer = footer

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
        if flush and not footer:
            self.body.installEventFilter(self)

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
    def set_title(self, title: str) -> None:
        self.title_label.setText(title)

    def set_subtitle(self, text: str) -> None:
        if text != self.subtitle_label.text():
            self.subtitle_label.setText(text)

    def add_action(self, widget: QWidget) -> None:
        self._actions.addWidget(widget, 0, Qt.AlignmentFlag.AlignVCenter)

    def body_layout(self) -> QVBoxLayout:
        return self._body_layout

    def footer_layout(self) -> QHBoxLayout:
        assert self._footer_layout is not None, "the panel was created without a footer"
        return self._footer_layout

    # ------------------------------------------------------------------ painting
    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor(Colors.N200), 1))
        painter.setBrush(QColor(Colors.N0))
        painter.drawRoundedRect(crisp(QRectF(self.rect())), Radius.R_LG, Radius.R_LG)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        divider = QColor(Colors.N150)
        painter.fillRect(QRect(1, self.header.geometry().bottom() + 1, self.width() - 2, 1), divider)
        if self.footer is not None:
            painter.fillRect(QRect(1, self.footer.geometry().top() - 1, self.width() - 2, 1), divider)

    def eventFilter(self, watched, event) -> bool:
        if watched is self.body and event.type() == QEvent.Type.Resize:
            self._mask_body()
        return False

    def _mask_body(self) -> None:
        """Clips the flush body to the inside of the rounded bottom corners."""
        width, height = self.body.width(), self.body.height()
        if width <= 0 or height <= 0:
            return
        radius = Radius.R_LG - 1
        region = QRegion(0, 0, width, max(0, height - radius))
        for row in range(radius):
            y = height - radius + row
            dy = row + 0.5
            inset = radius - math.sqrt(max(0.0, radius * radius - dy * dy))
            inset = math.ceil(inset)
            region += QRegion(inset, y, max(0, width - 2 * inset), 1)
        self.body.setMask(region)
