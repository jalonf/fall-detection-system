from html import escape

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QWidget

from src.views.theme import APP_NAME_ACCENT, Colors


def paint_brand_mark(painter: QPainter, size: float) -> None:
    """
    Draws the logo in a `size` x `size` square: a white detection reticle (four corner
    brackets around a dot, a target locked by a camera) on a rounded blue tile. The
    reticle is the same one that frames the video stage and the "Fall detected" box.
    """
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(Colors.PRIMARY))
    painter.drawRoundedRect(QRectF(0, 0, size, size), size * 0.24, size * 0.24)

    white = QColor(Colors.ON_PRIMARY)
    pen = QPen(white, max(1.2, size * 0.07))
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    near, far, arm = size * 0.25, size * 0.75, size * 0.16
    for cx, cy, dx, dy in (
        (near, near, 1, 1), (far, near, -1, 1),
        (near, far, 1, -1), (far, far, -1, -1),
    ):
        corner = QPainterPath()
        corner.moveTo(QPointF(cx + dx * arm, cy))
        corner.lineTo(QPointF(cx, cy))
        corner.lineTo(QPointF(cx, cy + dy * arm))
        painter.drawPath(corner)

    radius = size * 0.085
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(white)
    painter.drawEllipse(QPointF(size / 2, size / 2), radius, radius)


def brand_icon() -> QIcon:
    """The logo as an application icon (window title bar and taskbar)."""
    icon = QIcon()
    for size in (16, 24, 32, 48, 64, 128, 256):
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        paint_brand_mark(painter, float(size))
        painter.end()
        icon.addPixmap(pixmap)
    return icon


class _BrandMark(QWidget):
    """The logo as a widget of a fixed size."""

    def __init__(self, size: int, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)

    def paintEvent(self, event):
        painter = QPainter(self)
        paint_brand_mark(painter, float(self.width()))
        painter.end()


class Wordmark(QWidget):
    """
    Identity of the application: the logo and the name, whose ending ("Sense") is drawn
    in the accent colour, with an optional caption after a hairline
    ("FallSense | Administrator Control Panel"). Nothing is loaded from image files, so
    it renders crisply at any scale.

    `large=True` is the version used on the sign-in screen.
    """

    def __init__(self, name: str, caption: str = "", large: bool = False, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16 if large else 10)

        layout.addWidget(_BrandMark(56 if large else 24), 0, Qt.AlignmentFlag.AlignVCenter)

        self.name_label = QLabel(self._two_tone(name))
        self.name_label.setTextFormat(Qt.TextFormat.RichText)
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

    @staticmethod
    def _two_tone(name: str) -> str:
        """Rich text of the name with its accent ending in the primary colour."""
        if not name.endswith(APP_NAME_ACCENT) or name == APP_NAME_ACCENT:
            return escape(name)
        base = name[: -len(APP_NAME_ACCENT)]
        return f'{escape(base)}<span style="color: {Colors.PRIMARY};">{escape(APP_NAME_ACCENT)}</span>'
