"""Brand panel of the sign-in screens.

Composition: a message block in the app's own type scale (overline, headline, lead), the three
things the app does, and the project credit at the bottom. Behind it, cropped
by the right and bottom edges, a large and faint MediaPipe Pose figure (33 landmarks and their
connections) gives the screen its character. Everything is painted on the panel's own background.
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QLinearGradient, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QSizePolicy, QVBoxLayout, QWidget

from src.views.components.common.painting import IconView
from src.views.strings import Brand
from src.views.theme import Colors, Space, make_label, mix, qcolor

_PADDING_X = 48
_PADDING_Y = 40
_TEXT_WIDTH = 440

# A relaxed standing pose in a 100 x 160 box, facing the viewer (the person's left is on the right).
POSE_LANDMARKS: tuple[tuple[float, float], ...] = (
    (50.0, 12.0),                                    # 0 nose
    (52.2, 9.6), (53.8, 9.4), (55.4, 9.7),           # 1-3 left eye inner, eye, outer
    (47.8, 9.6), (46.2, 9.4), (44.6, 9.7),           # 4-6 right eye inner, eye, outer
    (58.0, 11.5), (42.0, 11.5),                      # 7-8 ears
    (52.0, 15.6), (48.0, 15.6),                      # 9-10 mouth
    (62.0, 28.0), (38.0, 28.5),                      # 11-12 shoulders
    (67.0, 47.0), (33.5, 47.5),                      # 13-14 elbows
    (69.5, 65.0), (31.0, 66.0),                      # 15-16 wrists
    (71.5, 71.0), (29.0, 72.0),                      # 17-18 pinkies
    (70.0, 72.5), (30.5, 73.5),                      # 19-20 index fingers
    (67.0, 69.5), (33.5, 70.0),                      # 21-22 thumbs
    (57.0, 80.0), (43.0, 80.5),                      # 23-24 hips
    (58.5, 112.0), (42.0, 112.5),                    # 25-26 knees
    (59.5, 145.0), (40.5, 145.0),                    # 27-28 ankles
    (58.0, 150.0), (42.0, 150.0),                    # 29-30 heels
    (64.5, 152.0), (35.5, 152.0),                    # 31-32 foot index
)

# MediaPipe Pose connections (POSE_CONNECTIONS).
POSE_CONNECTIONS: tuple[tuple[int, int], ...] = (
    (0, 1), (1, 2), (2, 3), (3, 7), (0, 4), (4, 5), (5, 6), (6, 8), (9, 10),
    (11, 12), (11, 13), (13, 15), (15, 17), (15, 19), (15, 21), (17, 19),
    (12, 14), (14, 16), (16, 18), (16, 20), (16, 22), (18, 20),
    (11, 23), (12, 24), (23, 24), (23, 25), (24, 26), (25, 27), (26, 28),
    (27, 29), (28, 30), (29, 31), (30, 32), (27, 31), (28, 32),
)
_SMALL = set(range(1, 11)) | set(range(17, 23)) | set(range(29, 33))   # face, hands and feet


def paint_background_figure(painter: QPainter, width: float, height: float) -> None:
    """Paints the faint MediaPipe pose figure behind the brand panel's text.

    The shoulders are about a quarter of the panel wide, centred at 80 % of the width with
    the head near the top, so the legs run off the bottom edge.

    Args:
        painter: Painter of the panel's background pixmap.
        width: Panel width.
        height: Panel height.
    """
    scale = width / 96.0
    origin_x = width * 0.80 - 50.0 * scale
    origin_y = height * 0.20 - 12.0 * scale
    points = [QPointF(origin_x + x * scale, origin_y + y * scale) for x, y in POSE_LANDMARKS]

    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    line = QPen(qcolor(Colors.P200, 0.17), 1.5)
    line.setCapStyle(Qt.PenCapStyle.RoundCap)
    thin = QPen(qcolor(Colors.P200, 0.14), 1.0)
    for start, end in POSE_CONNECTIONS:
        painter.setPen(thin if start in _SMALL and end in _SMALL else line)
        painter.drawLine(points[start], points[end])
    painter.setBrush(Qt.BrushStyle.NoBrush)
    for index, point in enumerate(points):
        small = index in _SMALL
        painter.setPen(QPen(qcolor(Colors.P200, 0.24 if small else 0.30), 1.0 if small else 1.5))
        radius = 2.0 if small else 3.5
        painter.drawEllipse(point, radius, radius)
    painter.restore()


def _feature(icon: str, title: str, detail: str) -> QHBoxLayout:
    row = QHBoxLayout()
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(Space.S4)
    icon_box = QVBoxLayout()
    icon_box.setContentsMargins(0, 0, 0, 0)
    icon_box.addWidget(IconView(icon, Colors.N0, 20))
    icon_box.addStretch(1)
    row.addLayout(icon_box)
    text = QVBoxLayout()
    text.setContentsMargins(0, 0, 0, 0)
    text.setSpacing(Space.S1)
    text.addWidget(make_label(title, "title-sm", "on-brand"))
    text.addWidget(make_label(detail, "body", "on-brand-muted", wrap=True))
    row.addLayout(text, 1)
    return row


class BrandPanel(QWidget):
    """Left half of the sign-in screens: the message, the three features and the credits."""
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)
        self._background: QPixmap | None = None
        self._background_key: tuple | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(_PADDING_X, _PADDING_Y, _PADDING_X, _PADDING_Y)
        layout.setSpacing(0)
        layout.addStretch(2)

        content = QWidget()
        content.setMaximumWidth(_TEXT_WIDTH)
        content.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        column = QVBoxLayout(content)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(0)
        column.addWidget(make_label(Brand.OVERLINE, "overline", "on-brand-muted"))
        column.addSpacing(Space.S3)
        column.addWidget(make_label(Brand.HEADLINE, "display", "on-brand", wrap=True))
        column.addSpacing(Space.S3)
        column.addWidget(make_label(Brand.PARAGRAPH, "lead", "on-brand-soft", wrap=True))
        column.addSpacing(Space.S10)
        for index, (icon, title, detail) in enumerate(Brand.FEATURES):
            if index:
                column.addSpacing(Space.S6)
            column.addLayout(_feature(icon, title, detail))
        layout.addWidget(content)      # fills the width up to its maximum, so wrapped text gets its full height

        layout.addStretch(3)
        layout.addWidget(make_label(Brand.FOOTER, "caption", "on-brand-muted"))

    def set_target_width(self, width: int) -> None:
        """Fixes the panel's width (the sign-in screen gives it 40 % of the window).

        Args:
            width: Width in pixels.
        """
        if width != self.width():
            self.setFixedWidth(width)

    def sizeHint(self) -> QSize:
        """Preferred size of the panel."""
        return QSize(520, 720)

    def _background_pixmap(self) -> QPixmap:
        dpr = self.devicePixelRatioF()
        key = (self.width(), self.height(), dpr)
        if self._background is None or self._background_key != key:
            pixmap = QPixmap(max(1, round(self.width() * dpr)), max(1, round(self.height() * dpr)))
            pixmap.setDevicePixelRatio(dpr)
            painter = QPainter(pixmap)
            depth = QLinearGradient(0, 0, 0, self.height())
            depth.setColorAt(0.0, mix(Colors.BRAND, Colors.S900, 0.35))
            depth.setColorAt(1.0, mix(Colors.BRAND, Colors.P800, 0.45))
            painter.fillRect(QRectF(0, 0, self.width(), self.height()), depth)
            paint_background_figure(painter, self.width(), self.height())
            painter.end()
            self._background, self._background_key = pixmap, key
        return self._background

    def paintEvent(self, event) -> None:
        """Paints the cached background: gradient and pose figure."""
        QPainter(self).drawPixmap(0, 0, self._background_pixmap())
