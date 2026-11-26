"""Heading of the sign-in and sign-up pages: an icon tile, then the title and its subtitle.

The tile (48 px, P50 fill, P600 icon, the controls' barely softened corner) gives each page its own
mark without adding colour or height. It has no border on purpose: the buttons and inputs of the
form below are bordered boxes, and a bordered tile would read as one more control to click. It is
centred on the two lines of text beside it.
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from src.views import icons
from src.views.theme import Colors, Radius, Space, Type, make_label, set_props

TILE = 48
_ICON = 24
WIDE_PAGE = 960   # from this page width on (wide screens), the title is set larger


class IconTile(QWidget):
    """48 px square with an icon, the mark of a page's heading.

    Args:
        icon: Name of the icon (see `icons.ICONS`).
        parent: Parent widget.
    """
    def __init__(self, icon: str, parent: QWidget | None = None):
        super().__init__(parent)
        self._icon = icon
        self.setFixedSize(TILE, TILE)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def paintEvent(self, event) -> None:
        """Paints the P50 square and the icon centred on it."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(Colors.P50))
        painter.drawRoundedRect(QRectF(self.rect()), Radius.R_MD, Radius.R_MD)
        offset = (TILE - _ICON) / 2
        painter.drawPixmap(QPointF(offset, offset), icons.icon_pixmap(self._icon, Colors.P600, _ICON,
                                                                      self.devicePixelRatioF()))


class PageHeading(QWidget):
    """Icon tile, then the title (title-lg, or display on wide screens) with the subtitle under it.

    Args:
        icon: Name of the tile's icon.
        title: The page's title.
        subtitle: One line under it.
        parent: Parent widget.
    """

    def __init__(self, icon: str, title: str, subtitle: str, parent: QWidget | None = None):
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(Space.S4)
        row.addWidget(IconTile(icon), 0, Qt.AlignmentFlag.AlignVCenter)

        text = QVBoxLayout()
        text.setContentsMargins(0, 0, 0, 0)
        text.setSpacing(Space.S1)
        self.title = make_label(title, "title-lg")
        self.subtitle = make_label(subtitle, "body", "secondary", wrap=True)
        text.addWidget(self.title)
        text.addWidget(self.subtitle)
        row.addLayout(text, 1)

    def fit_to(self, page_width: int) -> None:
        """Sets the title one step larger (display) when the page is wide, back otherwise.

        Args:
            page_width: Width of the page the heading is on.
        """
        role = "display" if page_width >= WIDE_PAGE else "title-lg"
        if self.title.property("type") != role:
            set_props(self.title, type=role)
            self.title.setMinimumHeight(Type.line_height(role))
