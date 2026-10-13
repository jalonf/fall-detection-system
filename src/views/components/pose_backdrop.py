import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontMetrics,
        QPainter,
    QPainterPath,
    QPen,
    QTextOption,
)
from PySide6.QtWidgets import QWidget

# Standing pose in normalised coordinates: x is relative to the spine,
# y runs from the top of the head (0) to the ground (1).
_JOINTS = {
    "head": (0.0, 0.065),
    "chin": (0.0, 0.113),
    "neck": (0.0, 0.15),
    "sh_l": (-0.09, 0.18),
    "sh_r": (0.09, 0.18),
    "el_l": (-0.13, 0.32),
    "el_r": (0.13, 0.32),
    "wr_l": (-0.14, 0.46),
    "wr_r": (0.14, 0.46),
    "mid_hip": (0.0, 0.53),
    "hip_l": (-0.055, 0.53),
    "hip_r": (0.055, 0.53),
    "kn_l": (-0.065, 0.75),
    "kn_r": (0.065, 0.75),
    "an_l": (-0.065, 0.97),
    "an_r": (0.065, 0.97),
}

_BONES = [
    ("chin", "neck"),
    ("neck", "sh_l"), ("neck", "sh_r"),
    ("sh_l", "el_l"), ("el_l", "wr_l"),
    ("sh_r", "el_r"), ("el_r", "wr_r"),
    ("neck", "mid_hip"),
    ("sh_l", "hip_l"), ("sh_r", "hip_r"), ("hip_l", "hip_r"),
    ("hip_l", "kn_l"), ("kn_l", "an_l"),
    ("hip_r", "kn_r"), ("kn_r", "an_r"),
]

_NO_DOT = {"head", "chin"}
_FEET_Y = 0.97
_HEAD_RADIUS = 0.048

# (progress along the sequence, rotation in degrees, limb spread, opacity)
_POSES = [
    (0.0, 0.0, 0.0, 90),
    (0.5, 34.0, 0.6, 165),
    (1.0, 84.0, 1.4, 255),
]

_GHOST = (86, 124, 190)     # soft blue strokes for the 'before' frames
_ALERT = (212, 61, 61)      # the single alert colour


def _local(name: str, height: float, spread: float) -> QPointF:
    x, y = _JOINTS[name]
    if name.startswith(("el", "wr")):
        x *= 1.0 + spread
    elif name.startswith(("kn", "an")):
        x *= 1.0 + spread * 0.8
    return QPointF(x * height, (y - _FEET_Y) * height)


def _world(pivot: QPointF, angle_deg: float, point: QPointF) -> QPointF:
    rad = math.radians(angle_deg)
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    return QPointF(
        pivot.x() + point.x() * cos_a - point.y() * sin_a,
        pivot.y() + point.x() * sin_a + point.y() * cos_a,
    )


class PoseBackdrop(QWidget):
    """
    Branding surface for the authentication screen. Paints a soft blue-tinted
    field with a measurement grid and a three-step fall sequence rendered as
    pose-estimation skeletons — the exact signal the product watches for.
    Child widgets (brand copy) are laid out on top by the owner.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("brandSurface")

    # ------------------------------------------------------------------ paint
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = float(self.width()), float(self.height())
        self._paint_field(painter, w, h)
        self._paint_sequence(painter, w, h)
        painter.end()

    def _paint_field(self, painter: QPainter, w: float, h: float):
        # Flat, softly tinted surface (no gradient) with a faint measurement grid.
        painter.fillRect(QRectF(0, 0, w, h), QColor("#EEF3FA"))

        painter.setPen(QPen(QColor(61, 111, 190, 22), 1))
        step = 48
        x = 0
        while x < w:
            painter.drawLine(QPointF(x, 0), QPointF(x, h))
            x += step
        y = 0
        while y < h:
            painter.drawLine(QPointF(0, y), QPointF(w, y))
            y += step

    def _paint_sequence(self, painter: QPainter, w: float, h: float):
        body_h = max(90.0, min(h * 0.32, w * 0.30))
        floor_y = h * 0.80
        x_start = w * 0.14 + body_h * 0.2
        x_end = max(w * 0.92 - body_h, x_start + body_h * 1.2)

        # Ground line
        painter.setPen(QPen(QColor(61, 111, 190, 70), 1.2))
        painter.drawLine(QPointF(w * 0.10, floor_y), QPointF(w * 0.94, floor_y))

        head_trace = []
        final_points = []

        for progress, angle, spread, alpha in _POSES:
            is_final = progress >= 1.0
            pivot_x = x_start + (x_end - x_start) * progress
            pivot_y = floor_y - 0.11 * body_h * math.sin(math.radians(angle))
            pivot = QPointF(pivot_x, pivot_y)

            base = _ALERT if is_final else _GHOST
            line_color = QColor(base[0], base[1], base[2], alpha)
            self._draw_pose(painter, pivot, angle, body_h, spread, line_color, is_final)

            head_trace.append(_world(pivot, angle, _local("head", body_h, spread)))
            if is_final:
                final_points = [
                    _world(pivot, angle, _local(name, body_h, spread))
                    for name in _JOINTS
                ]

        self._draw_trace(painter, head_trace)
        if final_points:
            self._draw_detection_box(painter, final_points, body_h)

    def _draw_pose(self, painter, pivot, angle, body_h, spread, color, emphasised):
        painter.save()
        painter.translate(pivot)
        painter.rotate(angle)

        pen = QPen(color, 2.4 if emphasised else 2.0)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        for a, b in _BONES:
            painter.drawLine(_local(a, body_h, spread), _local(b, body_h, spread))

        head = _local("head", body_h, spread)
        radius = _HEAD_RADIUS * body_h
        painter.drawEllipse(head, radius, radius)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        dot = 3.6 if emphasised else 3.0
        for name in _JOINTS:
            if name in _NO_DOT or name == "mid_hip":
                continue
            painter.drawEllipse(_local(name, body_h, spread), dot, dot)

        painter.restore()

    def _draw_trace(self, painter, head_trace):
        if len(head_trace) < 3:
            return
        p0, p1, p2 = head_trace
        control = QPointF(2 * p1.x() - 0.5 * (p0.x() + p2.x()),
                          2 * p1.y() - 0.5 * (p0.y() + p2.y()))
        path = QPainterPath(p0)
        path.quadTo(control, p2)
        pen = QPen(QColor(_GHOST[0], _GHOST[1], _GHOST[2], 130), 1.5, Qt.PenStyle.DotLine)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)

    def _draw_detection_box(self, painter, points, body_h):
        pad = 16.0
        head_pad = _HEAD_RADIUS * body_h
        left = min(p.x() for p in points) - pad - head_pad
        right = max(p.x() for p in points) + pad + head_pad
        top = min(p.y() for p in points) - pad - head_pad
        bottom = max(p.y() for p in points) + pad

        color = QColor(_ALERT[0], _ALERT[1], _ALERT[2])
        pen = QPen(color, 2.0)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        arm = 16.0
        for cx, cy, dx, dy in (
            (left, top, 1, 1), (right, top, -1, 1),
            (left, bottom, 1, -1), (right, bottom, -1, -1),
        ):
            corner = QPainterPath()
            corner.moveTo(cx + dx * arm, cy)
            corner.lineTo(cx, cy)
            corner.lineTo(cx, cy + dy * arm)
            painter.drawPath(corner)

        # Label tag
        font = QFont()
        font.setFamilies(["Segoe UI", "Inter", "Helvetica Neue", "sans-serif"])
        font.setPixelSize(11)
        font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(font)
        text = "Fall detected"
        metrics = QFontMetrics(font)
        tag_w = metrics.horizontalAdvance(text) + 18
        tag_h = 20.0
        tag = QRectF(left, top - tag_h - 6, tag_w, tag_h)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawRoundedRect(tag, 5, 5)
        painter.setPen(QColor("#FFFFFF"))
        painter.drawText(tag, text, QTextOption(Qt.AlignmentFlag.AlignCenter))
