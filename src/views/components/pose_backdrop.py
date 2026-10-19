from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QFontMetrics,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QTextOption,
)
from PySide6.QtWidgets import QWidget

from src.views.components.pose_landmarks import (
    FRAME_LABELS,
    LANDMARK_COUNT,
    MINOR_LANDMARKS,
    POSE_CONNECTIONS,
    fall_sequence,
    mid_hip,
)
from src.views.theme import Colors, Radius, mono_font, ui_font, with_alpha

_GHOST_ALPHA = (95, 140, 190)     # earlier frames are fainter
_X_SPAN = 2.35                    # width of the sequence, in body heights

_GRID_MINOR = 20
_GRID_MAJOR_EVERY = 5
_RULER_X = 40.0                   # x of the height ruler; the ground line starts here
_PAD_TOP = 46                     # room for the figure caption
_PAD_BOTTOM = 40                  # room for the frame labels
_CAPTION = "Fall sequence  ·  MediaPipe Pose, 33 landmarks"


class PoseBackdrop(QWidget):
    """
    Figure plate for the authentication screen, drawn like an engineering report figure:
    a bordered sheet with a millimetre grid, a height ruler normalised to the person, and
    a four-frame fall rendered with the 33 MediaPipe Pose landmarks and the official
    POSE_CONNECTIONS, the exact signal the product watches for. The path of the hip
    centroid is traced through the frames and the last frame carries the detection box.

    The plate fills the widget, so the owner places it below the brand copy. It is fully
    static: nothing animates and it only repaints when resized.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(280)

        self._frames = fall_sequence()
        self._grid: QPixmap | None = None
        self._grid_key = None

    # ------------------------------------------------------------------ paint
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = float(self.width()), float(self.height())
        sheet = QRectF(0.5, 0.5, w - 1.0, h - 1.0)
        clip = QPainterPath()
        clip.addRoundedRect(sheet, Radius.LG, Radius.LG)

        # Everything inside the sheet is clipped to its rounded outline.
        painter.save()
        painter.setClipPath(clip)
        painter.fillRect(QRectF(0, 0, w, h), QColor(Colors.SURFACE))
        painter.drawPixmap(0, 0, self._grid_pixmap(int(w), int(h)))

        floor_y = h - _PAD_BOTTOM
        body_h = max(110.0, min((floor_y - _PAD_TOP) / 0.97, w * 0.78 / _X_SPAN))
        ruler_x = _RULER_X
        # Centre the sequence (it spans x = -0.07 .. 2.21 body heights around the pelvis of
        # the first frame), but never closer to the height ruler than a fixed gap.
        x0 = max(w * 0.5 - 1.07 * body_h, ruler_x + 52.0 + 0.07 * body_h)

        self._paint_caption(painter)
        self._paint_ruler(painter, ruler_x, floor_y, body_h)
        self._paint_sequence(painter, w, floor_y, body_h, x0)
        painter.restore()

        painter.setPen(QPen(QColor(Colors.BORDER_STRONG), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(sheet, Radius.LG, Radius.LG)
        painter.end()

    def _grid_pixmap(self, w: int, h: int) -> QPixmap:
        """Millimetre grid, cached per size and device pixel ratio."""
        dpr = self.devicePixelRatioF()
        key = (w, h, dpr)
        if self._grid is not None and self._grid_key == key:
            return self._grid

        pixmap = QPixmap(max(1, int(w * dpr)), max(1, int(h * dpr)))
        pixmap.setDevicePixelRatio(dpr)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        minor = QPen(with_alpha(Colors.BORDER, 150), 1)
        major = QPen(with_alpha(Colors.BORDER_STRONG, 120), 1)
        for index, x in enumerate(range(0, w + 1, _GRID_MINOR)):
            painter.setPen(major if index % _GRID_MAJOR_EVERY == 0 else minor)
            painter.drawLine(x, 0, x, h)
        for index, y in enumerate(range(0, h + 1, _GRID_MINOR)):
            painter.setPen(major if index % _GRID_MAJOR_EVERY == 0 else minor)
            painter.drawLine(0, y, w, y)
        painter.end()

        self._grid, self._grid_key = pixmap, key
        return pixmap

    @staticmethod
    def _paint_caption(painter: QPainter):
        font = mono_font(11)
        painter.setFont(font)
        painter.setPen(QColor(Colors.TEXT_MUTED))
        painter.drawText(QPointF(18, 28), _CAPTION)

    @staticmethod
    def _paint_ruler(painter: QPainter, x: float, floor_y: float, body_h: float):
        """Vertical scale normalised to the person's height (0 = ground, 1 = standing height)."""
        color = QColor(Colors.TEXT_SUBTLE)
        painter.setPen(QPen(color, 1.2))
        painter.drawLine(QPointF(x, floor_y), QPointF(x, floor_y - body_h))

        font = mono_font(10)
        painter.setFont(font)
        metrics = QFontMetrics(font)
        for i in range(5):
            value = i / 4.0
            y = floor_y - value * body_h
            length = 8.0 if i % 2 == 0 else 5.0
            painter.drawLine(QPointF(x, y), QPointF(x + length, y))
            if i % 2 == 0:
                label = f"{value:.1f}"
                label_w = metrics.horizontalAdvance(label)
                # Plate-coloured backing, so a grid line passing through the value never
                # strikes it out.
                painter.fillRect(
                    QRectF(x - label_w - 10, y - metrics.height() / 2.0, label_w + 8, metrics.height()),
                    QColor(Colors.SURFACE),
                )
                painter.drawText(
                    QPointF(x - label_w - 6, y + metrics.ascent() / 2 - 1),
                    label,
                )

    def _paint_sequence(self, painter: QPainter, w: float, floor_y: float, body_h: float, x0: float):
        def canvas(point):
            return QPointF(x0 + point[0] * body_h, floor_y - point[1] * body_h)

        # Ground line
        painter.setPen(QPen(QColor(Colors.BORDER_HOVER), 1.4))
        painter.drawLine(QPointF(_RULER_X, floor_y), QPointF(w - 14, floor_y))

        label_font = mono_font(10)
        centroids = []
        final_points = []
        last = len(self._frames) - 1

        for index, landmarks in enumerate(self._frames):
            points = [canvas(p) for p in landmarks]
            centroids.append(canvas(mid_hip(landmarks)))
            is_final = index == last
            if is_final:
                final_points = points

            alpha = 255 if is_final else _GHOST_ALPHA[index]
            color = with_alpha(Colors.DANGER if is_final else Colors.PRIMARY, alpha)
            self._draw_skeleton(painter, points, color, thick=is_final)

            # Frame label under the ground line, aligned with the pelvis.
            painter.setFont(label_font)
            painter.setPen(QColor(Colors.TEXT_MUTED))
            cx = centroids[-1].x()
            painter.drawLine(QPointF(cx, floor_y), QPointF(cx, floor_y + 5))
            painter.drawText(
                QRectF(cx - 30, floor_y + 7, 60, 16),
                FRAME_LABELS[index],
                QTextOption(Qt.AlignmentFlag.AlignCenter),
            )

        self._draw_centroid_trace(painter, centroids)
        if final_points:
            self._draw_detection_box(painter, final_points)

    @staticmethod
    def _draw_skeleton(painter: QPainter, points, color: QColor, thick: bool):
        """MediaPipe-style overlay: POSE_CONNECTIONS as lines, the 33 landmarks as dots."""
        pen = QPen(color, 2.0 if thick else 1.6)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for a, b in POSE_CONNECTIONS:
            painter.drawLine(points[a], points[b])

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        for i in range(LANDMARK_COUNT):
            radius = 1.7 if i in MINOR_LANDMARKS else 3.0
            painter.drawEllipse(points[i], radius, radius)

    @staticmethod
    def _draw_centroid_trace(painter: QPainter, centroids):
        """Dashed path of the hip centroid (the signal the detector follows) with a marker per frame."""
        if len(centroids) < 2:
            return
        pen = QPen(with_alpha(Colors.PRIMARY, 200), 1.2, Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        path = QPainterPath(centroids[0])
        for point in centroids[1:]:
            path.lineTo(point)
        painter.drawPath(path)

        painter.setPen(QPen(QColor(Colors.PRIMARY), 1.4))
        painter.setBrush(QColor(Colors.SURFACE))
        for point in centroids:
            painter.drawEllipse(point, 3.6, 3.6)

    @staticmethod
    def _draw_detection_box(painter: QPainter, points):
        pad = 14.0
        left = min(p.x() for p in points) - pad
        right = max(p.x() for p in points) + pad
        top = min(p.y() for p in points) - pad
        bottom = max(p.y() for p in points) + pad

        color = QColor(Colors.DANGER)
        pen = QPen(color, 1.8)
        pen.setCapStyle(Qt.PenCapStyle.SquareCap)
        pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        arm = 14.0
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
        font = ui_font(11, bold=True)
        painter.setFont(font)
        text = "Fall detected"
        tag_w = QFontMetrics(font).horizontalAdvance(text) + 18
        tag_h = 20.0
        tag = QRectF(left, top - tag_h - 4, tag_w, tag_h)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(Colors.DANGER_SOLID))
        painter.drawRoundedRect(tag, 3, 3)
        painter.setPen(QColor(Colors.TEXT_INVERSE))
        painter.drawText(tag, text, QTextOption(Qt.AlignmentFlag.AlignCenter))
