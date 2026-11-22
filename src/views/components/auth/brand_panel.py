"""Brand panel of the sign-in screens: what FallSense does for the caregiver."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from src.views.components.common.painting import IconView
from src.views.strings import Brand
from src.views.theme import Colors, Space, make_label

_PADDING = 48
_DOT_STEP = 24


class BrandPanel(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._grid: QPixmap | None = None
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(_PADDING, _PADDING, _PADDING, _PADDING)
        layout.setSpacing(0)

        wordmark = QHBoxLayout()
        wordmark.setSpacing(Space.S2)
        wordmark.addWidget(IconView("shield", Colors.P200, 20))
        wordmark.addWidget(make_label(Brand.WORDMARK, "title-md", "on-brand"))
        wordmark.addStretch(1)
        layout.addLayout(wordmark)
        layout.addStretch(1)

        content = QWidget()
        content.setMaximumWidth(440)
        column = QVBoxLayout(content)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(0)
        column.addWidget(make_label(Brand.HEADLINE, "display", "on-brand", wrap=True))
        column.addSpacing(Space.S3)
        column.addWidget(make_label(Brand.PARAGRAPH, "lead", "on-brand-soft", wrap=True))
        column.addSpacing(Space.S8)
        for index, (icon, title, detail) in enumerate(Brand.FEATURES):
            if index:
                column.addSpacing(Space.S4)
            row = QHBoxLayout()
            row.setSpacing(Space.S3)
            icon_box = QVBoxLayout()
            icon_box.setContentsMargins(0, 0, 0, 0)
            icon_box.addWidget(IconView(icon, Colors.P200, 20))
            icon_box.addStretch(1)
            row.addLayout(icon_box)
            text = QVBoxLayout()
            text.setSpacing(0)
            text.addWidget(make_label(title, "body-strong", "on-brand"))
            text.addWidget(make_label(detail, "caption", "on-brand-muted", wrap=True))
            row.addLayout(text, 1)
            column.addLayout(row)
        layout.addWidget(content, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)

    def set_target_width(self, width: int) -> None:
        if width != self.width():
            self.setFixedWidth(width)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._grid = None

    def _dot_grid(self) -> QPixmap:
        dpr = self.devicePixelRatioF()
        if self._grid is None or self._grid.devicePixelRatio() != dpr:
            pixmap = QPixmap(round(self.width() * dpr), round(self.height() * dpr))
            pixmap.setDevicePixelRatio(dpr)
            pixmap.fill(QColor(Colors.BRAND))
            painter = QPainter(pixmap)
            dot = QColor(Colors.N0)
            dot.setAlphaF(0.06)
            for x in range(_DOT_STEP // 2, self.width(), _DOT_STEP):
                for y in range(_DOT_STEP // 2, self.height(), _DOT_STEP):
                    painter.fillRect(x, y, 1, 1, dot)
            painter.end()
            self._grid = pixmap
        return self._grid

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self._dot_grid())
