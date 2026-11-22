"""Brand panel of the sign-in screens: what FallSense does for the caregiver, with the app's
visual signature underneath — a MediaPipe Pose figure (33 landmarks and their connections)."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap, QRadialGradient
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from src.views.components.common.painting import IconView
from src.views.strings import Brand
from src.views.theme import Colors, Space, make_label, qcolor

_PADDING = 48
_DOT_STEP = 24
_MIN_FIGURE = 160          # below this height the figure is left out
_MAX_FIGURE = 440

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
_BOX_W, _BOX_H = 100.0, 160.0
_SMALL = set(range(1, 11)) | set(range(17, 23)) | set(range(29, 33))   # face, hands and feet


def paint_pose_figure(painter: QPainter, rect: QRectF) -> None:
    """Draws the 33-landmark figure fitted (aspect kept) and bottom-centred in `rect`."""
    scale = min(rect.width() / _BOX_W, rect.height() / _BOX_H)
    left = rect.center().x() - _BOX_W * scale / 2
    top = rect.bottom() - _BOX_H * scale
    points = [QPointF(left + x * scale, top + y * scale) for x, y in POSE_LANDMARKS]

    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Soft glow behind the torso, so the figure reads as a light source on the dark panel.
    centre = (points[11] + points[12] + points[23] + points[24]) / 4
    glow = QRadialGradient(centre, 70 * scale)
    glow.setColorAt(0.0, qcolor(Colors.P600, 0.35))
    glow.setColorAt(1.0, qcolor(Colors.P600, 0.0))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(glow)
    painter.drawEllipse(centre, 70 * scale, 70 * scale)

    # Detection frame: corner brackets around the person, as the app draws them on the video.
    xs = [point.x() for point in points]
    ys = [point.y() for point in points]
    frame = QRectF(min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)).adjusted(
        -10 * scale, -8 * scale, 10 * scale, 6 * scale)
    arm = min(frame.width(), frame.height()) * 0.12
    bracket = QPen(qcolor(Colors.P200, 0.35), 1.25)
    bracket.setCapStyle(Qt.PenCapStyle.FlatCap)
    painter.setPen(bracket)
    for corner, dx, dy in ((frame.topLeft(), 1, 1), (frame.topRight(), -1, 1),
                           (frame.bottomLeft(), 1, -1), (frame.bottomRight(), -1, -1)):
        painter.drawLine(corner, QPointF(corner.x() + dx * arm, corner.y()))
        painter.drawLine(corner, QPointF(corner.x(), corner.y() + dy * arm))

    line = QPen(qcolor(Colors.P200, 0.6), max(1.25, 0.8 * scale))
    line.setCapStyle(Qt.PenCapStyle.RoundCap)
    thin = QPen(qcolor(Colors.P200, 0.45), 1.0)
    for start, end in POSE_CONNECTIONS:
        painter.setPen(thin if start in _SMALL and end in _SMALL else line)
        painter.drawLine(points[start], points[end])

    # Body joints as rings; face, hand and foot landmarks as small solid dots.
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(qcolor(Colors.N0, 0.8))
    for index in _SMALL:
        painter.drawEllipse(points[index], max(1.1, 0.55 * scale), max(1.1, 0.55 * scale))
    painter.setPen(QPen(qcolor(Colors.N0, 0.95), max(1.0, 0.55 * scale)))
    painter.setBrush(QColor(Colors.BRAND))
    for index, point in enumerate(points):
        if index not in _SMALL:
            radius = max(2.2, 1.5 * scale)
            painter.drawEllipse(point, radius, radius)
    painter.restore()


class BrandPanel(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._background: QPixmap | None = None
        self._background_key: tuple | None = None
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
        layout.addSpacing(Space.S10)

        self.content = QWidget()
        self.content.setMaximumWidth(440)
        column = QVBoxLayout(self.content)
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
        layout.addWidget(self.content, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        layout.addStretch(1)      # the figure is painted in this space

    def set_target_width(self, width: int) -> None:
        if width != self.width():
            self.setFixedWidth(width)

    def figure_rect(self) -> QRectF:
        """Free space under the text, where the pose figure goes (empty when too small)."""
        top = self.content.geometry().bottom() + Space.S8
        bottom = self.height() - _PADDING
        free = bottom - top
        height = min(_MAX_FIGURE, free)
        if height < _MIN_FIGURE:
            return QRectF()
        return QRectF(_PADDING, top + (free - height) / 2, self.width() - 2 * _PADDING, height)

    def _background_pixmap(self) -> QPixmap:
        dpr = self.devicePixelRatioF()
        figure = self.figure_rect()
        key = (self.width(), self.height(), dpr, figure.top())
        if self._background is None or self._background_key != key:
            pixmap = QPixmap(max(1, round(self.width() * dpr)), max(1, round(self.height() * dpr)))
            pixmap.setDevicePixelRatio(dpr)
            pixmap.fill(QColor(Colors.BRAND))
            painter = QPainter(pixmap)
            dot = qcolor(Colors.N0, 0.06)
            for x in range(_DOT_STEP // 2, self.width(), _DOT_STEP):
                for y in range(_DOT_STEP // 2, self.height(), _DOT_STEP):
                    painter.fillRect(x, y, 1, 1, dot)
            if not figure.isEmpty():
                paint_pose_figure(painter, figure)
            painter.end()
            self._background = pixmap
            self._background_key = key
        return self._background

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self._background_pixmap())
