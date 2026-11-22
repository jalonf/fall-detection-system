"""Brand panel of the sign-in screens.

Composition, top to bottom: the logo lockup; the message (overline, headline, lead); a live-stage
card with the 33-landmark MediaPipe Pose figure as the product's visual signature; and the three
things FallSense does for the caregiver. Everything is painted on the panel's own background.
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import (
    QColor,
    QLinearGradient,
    QPainter,
    QPen,
    QPixmap,
    QRadialGradient,
)
from PySide6.QtWidgets import (
    QHBoxLayout,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from src.views import icons
from src.views.components.common.logo_mark import LogoMark
from src.views.components.common.painting import Divider, IconView
from src.views.strings import Brand
from src.views.theme import Colors, Radius, Space, Type, make_label, mix, qcolor

_PADDING_X = 48
_PADDING_Y = 44

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


def paint_pose_figure(painter: QPainter, rect: QRectF, bracket: QColor) -> None:
    """Draws the 33-landmark figure fitted (aspect kept) and centred in `rect`, framed by
    detection brackets like the ones the app draws around the person."""
    scale = min(rect.width() / _BOX_W, rect.height() / _BOX_H)
    left = rect.center().x() - _BOX_W * scale / 2
    top = rect.center().y() - _BOX_H * scale / 2
    points = [QPointF(left + x * scale, top + y * scale) for x, y in POSE_LANDMARKS]

    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    xs = [point.x() for point in points]
    ys = [point.y() for point in points]
    frame = QRectF(min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)).adjusted(
        -12 * scale, -7 * scale, 12 * scale, 5 * scale)
    arm = min(frame.width(), frame.height()) * 0.14
    pen = QPen(bracket, 1.5)
    pen.setCapStyle(Qt.PenCapStyle.SquareCap)
    painter.setPen(pen)
    for corner, dx, dy in ((frame.topLeft(), 1, 1), (frame.topRight(), -1, 1),
                           (frame.bottomLeft(), 1, -1), (frame.bottomRight(), -1, -1)):
        painter.drawLine(corner, QPointF(corner.x() + dx * arm, corner.y()))
        painter.drawLine(corner, QPointF(corner.x(), corner.y() + dy * arm))

    line = QPen(qcolor(Colors.P200, 0.65), max(1.25, 0.8 * scale))
    line.setCapStyle(Qt.PenCapStyle.RoundCap)
    thin = QPen(qcolor(Colors.P200, 0.5), 1.0)
    for start, end in POSE_CONNECTIONS:
        painter.setPen(thin if start in _SMALL and end in _SMALL else line)
        painter.drawLine(points[start], points[end])

    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(qcolor(Colors.N0, 0.85))
    for index in _SMALL:
        painter.drawEllipse(points[index], max(1.1, 0.55 * scale), max(1.1, 0.55 * scale))
    painter.setPen(QPen(QColor(Colors.N0), max(1.0, 0.55 * scale)))
    painter.setBrush(QColor(Colors.S900))
    for index, point in enumerate(points):
        if index not in _SMALL:
            radius = max(2.2, 1.5 * scale)
            painter.drawEllipse(point, radius, radius)
    painter.restore()


class LiveCard(QWidget):
    """A small picture of the live stage: camera bar with the LIVE pill, and the pose figure."""

    HEADER = 36

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(150)
        self.setMaximumHeight(460)
        self._cache: QPixmap | None = None
        self._cache_key: tuple | None = None

    def sizeHint(self) -> QSize:
        return QSize(360, 280)

    def paintEvent(self, event) -> None:
        dpr = self.devicePixelRatioF()
        key = (self.width(), self.height(), dpr)
        if self._cache is None or self._cache_key != key:
            pixmap = QPixmap(max(1, round(self.width() * dpr)), max(1, round(self.height() * dpr)))
            pixmap.setDevicePixelRatio(dpr)
            pixmap.fill(Qt.GlobalColor.transparent)
            self._paint(QPainter(pixmap), dpr)
            self._cache, self._cache_key = pixmap, key
        QPainter(self).drawPixmap(0, 0, self._cache)

    def _paint(self, painter: QPainter, dpr: float) -> None:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        card = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        painter.setPen(QPen(qcolor(Colors.P200, 0.16), 1))
        painter.setBrush(qcolor(Colors.S900, 0.72))
        painter.drawRoundedRect(card, Radius.R_LG, Radius.R_LG)

        # Camera bar, as in the monitoring screen's stage overlay.
        painter.drawPixmap(14, (self.HEADER - 16) // 2, icons.icon_pixmap("camera", Colors.S100, 16, dpr))
        painter.setFont(Type.font("overline"))
        painter.setPen(QColor(Colors.S100))
        painter.drawText(QRectF(38, 0, 160, self.HEADER), int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                         Brand.CARD_SOURCE)
        metrics = painter.fontMetrics()
        pill_width = 8 + 6 + 6 + metrics.horizontalAdvance(Brand.CARD_LIVE) + 8
        pill = QRectF(self.width() - 12 - pill_width, (self.HEADER - 20) / 2, pill_width, 20)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 0, 0, 115))
        painter.drawRoundedRect(pill, Radius.R_SM, Radius.R_SM)
        painter.setBrush(QColor(Colors.G500))
        painter.drawEllipse(QPointF(pill.left() + 11, pill.center().y()), 3, 3)
        painter.setPen(QColor(Colors.N0))
        painter.drawText(QRectF(pill.left() + 20, pill.top(), pill_width - 20, pill.height()),
                         int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), Brand.CARD_LIVE)
        painter.fillRect(QRectF(1, self.HEADER, self.width() - 2, 1), qcolor(Colors.P200, 0.10))

        # Stage body: faint grid and the figure.
        body = QRectF(1, self.HEADER + 1, self.width() - 2, self.height() - self.HEADER - 2)
        painter.save()
        painter.setClipRect(body)
        grid = qcolor(Colors.P200, 0.05)
        step = 20
        x = body.left() + step
        while x < body.right():
            painter.fillRect(QRectF(x, body.top(), 1, body.height()), grid)
            x += step
        y = body.top() + step
        while y < body.bottom():
            painter.fillRect(QRectF(body.left(), y, body.width(), 1), grid)
            y += step
        painter.restore()
        paint_pose_figure(painter, body.adjusted(16, 18, -16, -14), qcolor(Colors.G500, 0.85))
        painter.end()


def _block() -> QWidget:
    """Container for a group of texts that keeps its natural height (it never stretches)."""
    block = QWidget()
    block.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
    layout = QVBoxLayout(block)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    return block


class BrandPanel(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)
        self._background: QPixmap | None = None
        self._background_key: tuple | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(_PADDING_X, _PADDING_Y, _PADDING_X, _PADDING_Y)
        layout.setSpacing(0)

        # The text blocks never grow: spare height goes to the card first, then to the gap below it.
        message = _block()
        message_layout = message.layout()
        lockup = QHBoxLayout()
        lockup.setSpacing(10)
        lockup.addWidget(LogoMark(28, "on-dark"))
        lockup.addWidget(make_label(Brand.WORDMARK, "title-md", "on-brand"))
        lockup.addStretch(1)
        message_layout.addLayout(lockup)
        message_layout.addSpacing(Space.S10)
        message_layout.addWidget(make_label(Brand.OVERLINE, "overline", "on-brand-muted"))
        message_layout.addSpacing(Space.S3)
        headline = make_label(Brand.HEADLINE, "display", "on-brand", wrap=True)
        headline.setMaximumWidth(460)
        message_layout.addWidget(headline)
        message_layout.addSpacing(Space.S3)
        lead = make_label(Brand.PARAGRAPH, "lead", "on-brand-soft", wrap=True)
        lead.setMaximumWidth(460)
        message_layout.addWidget(lead)
        layout.addWidget(message)
        layout.addSpacing(28)

        self.card = LiveCard()
        layout.addWidget(self.card, 1)       # takes the free height first, up to its maximum
        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        layout.addSpacing(28)

        features = _block()
        features_layout = features.layout()
        hairline = qcolor(Colors.P200, 0.14).name(QColor.NameFormat.HexArgb)
        for index, (icon, title, detail) in enumerate(Brand.FEATURES):
            if index:
                features_layout.addSpacing(Space.S3)
                features_layout.addWidget(Divider(hairline))
                features_layout.addSpacing(Space.S3)
            row = QHBoxLayout()
            row.setSpacing(Space.S3)
            icon_box = QVBoxLayout()
            icon_box.setContentsMargins(0, 2, 0, 0)
            icon_box.addWidget(IconView(icon, Colors.P200, 16))
            icon_box.addStretch(1)
            row.addLayout(icon_box)
            text = QVBoxLayout()
            text.setSpacing(2)
            text.addWidget(make_label(title, "body-strong", "on-brand"))
            text.addWidget(make_label(detail, "caption", "on-brand-muted", wrap=True))
            row.addLayout(text, 1)
            features_layout.addLayout(row)
        layout.addWidget(features)

    def set_target_width(self, width: int) -> None:
        if width != self.width():
            self.setFixedWidth(width)

    def _background_pixmap(self) -> QPixmap:
        dpr = self.devicePixelRatioF()
        glow_centre = QRectF(self.card.geometry()).center()
        key = (self.width(), self.height(), dpr, glow_centre.x(), glow_centre.y())
        if self._background is None or self._background_key != key:
            pixmap = QPixmap(max(1, round(self.width() * dpr)), max(1, round(self.height() * dpr)))
            pixmap.setDevicePixelRatio(dpr)
            painter = QPainter(pixmap)
            depth = QLinearGradient(0, 0, 0, self.height())
            depth.setColorAt(0.0, QColor(Colors.BRAND))
            depth.setColorAt(1.0, mix(Colors.BRAND, Colors.S900, 0.55))
            painter.fillRect(QRectF(0, 0, self.width(), self.height()), depth)
            radius = max(self.width(), self.height()) * 0.55
            glow = QRadialGradient(glow_centre, radius)
            glow.setColorAt(0.0, qcolor(Colors.P600, 0.30))
            glow.setColorAt(1.0, qcolor(Colors.P600, 0.0))
            painter.fillRect(QRectF(0, 0, self.width(), self.height()), glow)
            painter.end()
            self._background, self._background_key = pixmap, key
        return self._background

    def paintEvent(self, event) -> None:
        QPainter(self).drawPixmap(0, 0, self._background_pixmap())
