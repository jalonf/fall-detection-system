"""Pose analysis panel (administrators), under the video: the skeleton image and, beside it,
the model's telemetry.

`AdminController` calls `update_frame` and `update_telemetry` directly for every frame. Frames
are ignored while monitoring is stopped; telemetry is only stored and painted at 4 Hz.
"""

from __future__ import annotations

from PySide6.QtCore import QRect, QRectF, Qt, QTimer, Slot
from PySide6.QtGui import QColor, QImage, QPainter, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QWidget

from src.views.components.common.metric_tile import MetricTile
from src.views.components.common.painting import crisp
from src.views.components.common.panel import Panel
from src.views.components.monitor.video_widget import VideoWidget
from src.views.strings import Pose
from src.views.theme import Colors, Radius, Space, Type

VIEW_HEIGHT = 128
VIEW_WIDTH = 200
_GRID = 24
STOPPED = ("idle", "error", "finished")


class SkeletonView(VideoWidget):
    """Skeleton image on the exact stage colour, so the worker's background blends in. The
    grid is only drawn while empty ("No signal"); with an image the background stays plain."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(Colors.STAGE, radius=Radius.R_MD, corner_color=Colors.N0, parent=parent)
        self.setFixedSize(VIEW_WIDTH, VIEW_HEIGHT)
        self._grid: QPixmap | None = None
        self.setAccessibleName(Pose.SKELETON)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._grid = None

    def _grid_pixmap(self) -> QPixmap:
        dpr = self.devicePixelRatioF()
        if self._grid is None or self._grid.devicePixelRatio() != dpr:
            pixmap = QPixmap(max(1, round(self.width() * dpr)), max(1, round(self.height() * dpr)))
            pixmap.setDevicePixelRatio(dpr)
            pixmap.fill(QColor(Colors.STAGE))
            painter = QPainter(pixmap)
            line = QColor(Colors.S800)
            for x in range(_GRID, self.width(), _GRID):
                painter.fillRect(x, 0, 1, self.height(), line)
            for y in range(_GRID, self.height(), _GRID):
                painter.fillRect(0, y, self.width(), 1, line)
            painter.end()
            self._grid = pixmap
        return self._grid

    def paint_empty(self, painter: QPainter) -> None:
        painter.drawPixmap(0, 0, self._grid_pixmap())
        painter.setFont(Type.font("body"))
        painter.setPen(QColor(Colors.S300))
        painter.drawText(self.rect(), int(Qt.AlignmentFlag.AlignCenter), Pose.NO_SIGNAL)

    def paint_overlay(self, painter: QPainter) -> None:
        painter.setFont(Type.font("overline"))
        painter.setPen(QColor(Colors.S300))
        painter.drawText(QRect(10, 10, self.width() - 20, 16),
                         int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), Pose.SKELETON)


class MetricStrip(QWidget):
    """Three metric tiles side by side in a bordered strip, separated by dividers."""

    def __init__(self, tiles: list[MetricTile], parent: QWidget | None = None):
        super().__init__(parent)
        self.tiles = tiles
        self.setFixedHeight(VIEW_HEIGHT)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(1)
        for tile in tiles:
            layout.addWidget(tile, 1)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QColor(Colors.N150))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(crisp(QRectF(self.rect())), Radius.R_MD, Radius.R_MD)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        for tile in self.tiles[1:]:
            painter.fillRect(QRect(tile.geometry().left() - 1, 1, 1, self.height() - 2), QColor(Colors.N150))


class SkeletonPanel(Panel):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(Pose.TITLE, subtitle=Pose.SUBTITLE, parent=parent)
        self._state = "idle"
        self._telemetry: dict = {}
        self.view = SkeletonView()
        self.inference = MetricTile(Pose.INFERENCE, "ms")
        self.confidence = MetricTile(Pose.CONFIDENCE, "%", bar=True)
        self.hip_height = MetricTile(Pose.HIP_HEIGHT, tooltip=Pose.HIP_HEIGHT_TIP)
        self.strip = MetricStrip([self.inference, self.confidence, self.hip_height])
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(Space.S4)
        row.addWidget(self.view)
        row.addWidget(self.strip, 1)
        self.body_layout().addLayout(row)

        self._timer = QTimer(self)
        self._timer.setInterval(250)
        self._timer.timeout.connect(self._render_telemetry)

    # ------------------------------------------------------------------ contract (AdminController)
    @Slot(QImage)
    def update_frame(self, qimage: QImage) -> None:
        if self._state in STOPPED:
            return
        self.view.set_image(qimage)

    @Slot(dict)
    def update_telemetry(self, data: dict) -> None:
        if self._state in STOPPED:
            return
        self._telemetry = data or {}

    # ------------------------------------------------------------------ state
    def set_state(self, state: str) -> None:
        self._state = state
        if state == "live":
            self._timer.start()
        else:
            self._timer.stop()
        if state in STOPPED:
            self._telemetry = {}
            self.view.clear()
            self._render_telemetry()

    @Slot()
    def _render_telemetry(self) -> None:
        data = self._telemetry
        inference = data.get("inference_ms")
        confidence = data.get("confidence")
        hip = data.get("centroid_y")
        self.inference.set_value(f"{inference:.1f}" if inference is not None else None)
        if confidence is not None:
            ratio = max(0.0, min(1.0, float(confidence)))
            self.confidence.set_value(f"{round(ratio * 100)}", ratio)
        else:
            self.confidence.set_value(None)
        self.hip_height.set_value(f"{float(hip):.3f}" if hip is not None else None)
