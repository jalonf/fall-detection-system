"""Pose analysis panel (administrators), at the top of the side column.

Top: the skeleton image the worker draws. Below: a telemetry table with one row per metric —
its name, the current value and a trend line of the last 30 seconds — so the model's behaviour
reads at a glance. The hip-height trend is drawn upside down (0 = top of the frame), so a fall
shows as the line dropping.

`AdminController` calls `update_frame` and `update_telemetry` directly for every frame. Frames
are ignored while monitoring is stopped; telemetry is only stored, then sampled and painted at
4 Hz while live. Everything on the right is painted, so updates never relayout.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field

from PySide6.QtCore import QEvent, QPointF, QRect, QRectF, QSize, Qt, QTimer, Slot
from PySide6.QtGui import (
    QColor,
    QFontMetrics,
    QImage,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import QSizePolicy, QToolTip, QWidget

from src.views.components.common.panel import Panel
from src.views.components.monitor.video_widget import VideoWidget
from src.views.strings import EM_DASH, Pose
from src.views.theme import Colors, Radius, Space, Type, make_label, qcolor

VIEW_HEIGHT = 140
ROW_HEIGHT = 38
HISTORY = 120                 # samples kept: 30 s at 4 Hz
_LABEL_WIDTH = 92
_VALUE_WIDTH = 80
STOPPED = ("idle", "error", "finished")


class SkeletonView(VideoWidget):
    """Skeleton image on the exact stage colour, so the worker's background blends in.

    Like the video stage, the background is plain; while empty it only says "No signal".
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(Colors.STAGE, radius=Radius.R_MD, corner_color=Colors.N0, parent=parent)
        self.setFixedHeight(VIEW_HEIGHT)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setAccessibleName(Pose.SKELETON)

    def paint_empty(self, painter: QPainter) -> None:
        """Paints "No signal" while there is no image."""
        painter.setFont(Type.font("body"))
        painter.setPen(QColor(Colors.S300))
        painter.drawText(self.rect(), int(Qt.AlignmentFlag.AlignCenter), Pose.NO_SIGNAL)

    def paint_overlay(self, painter: QPainter) -> None:
        """Paints the "SKELETON" caption."""
        painter.setFont(Type.font("overline"))
        painter.setPen(QColor(Colors.S300))
        painter.drawText(QRect(10, 10, self.width() - 20, 16),
                         int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), Pose.SKELETON)


@dataclass
class Metric:
    """One telemetry series: how to show its value and how to scale its trend."""

    key: str
    label: str
    unit: str
    format: Callable[[float], str]
    low: float = 0.0
    high: float | None = 1.0          # None: scale to the largest recent sample
    inverted: bool = False            # True: low values at the top of the trend
    warn_below: float | None = None   # the trend turns amber below this value
    tooltip: str = ""
    samples: deque = field(default_factory=lambda: deque(maxlen=HISTORY))

    @property
    def current(self) -> float | None:
        """The newest sample, or None."""
        return self.samples[-1] if self.samples else None

    def scale(self) -> tuple[float, float]:
        """Returns the trend's (low, high) range; with no `high`, it follows the largest recent sample."""
        if self.high is not None:
            return self.low, self.high
        values = [value for value in self.samples if value is not None]
        return self.low, max(20.0, max(values, default=0.0) * 1.25)


class TelemetryTable(QWidget):
    """Bordered table: one row per metric with name, value (and unit) and its trend line."""

    def __init__(self, metrics: list[Metric], parent: QWidget | None = None):
        super().__init__(parent)
        self.metrics = metrics
        self.setFixedHeight(ROW_HEIGHT * len(metrics) + 2)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMouseTracking(True)
        self._describe()

    def sizeHint(self) -> QSize:
        """Preferred size: one row per metric."""
        return QSize(340, ROW_HEIGHT * len(self.metrics) + 2)

    def push(self, values: dict[str, float | None]) -> None:
        """Adds one sample of every metric and repaints.

        Args:
            values: Metric key -> value (None leaves a gap in the trend).
        """
        for metric in self.metrics:
            metric.samples.append(values.get(metric.key))
        self._describe()
        self.update()

    def clear(self) -> None:
        """Removes every sample."""
        for metric in self.metrics:
            metric.samples.clear()
        self._describe()
        self.update()

    def _describe(self) -> None:
        parts = []
        for metric in self.metrics:
            value = metric.current
            shown = f"{metric.format(value)} {metric.unit}".strip() if value is not None else EM_DASH
            parts.append(f"{metric.label}: {shown}")
        self.setAccessibleDescription("; ".join(parts))

    # ------------------------------------------------------------------ geometry
    def _row(self, index: int) -> QRect:
        inner = self.rect().adjusted(1, 1, -1, -1)
        height = inner.height() / len(self.metrics)
        top = round(inner.top() + index * height)
        bottom = round(inner.top() + (index + 1) * height)
        return QRect(inner.left(), top, inner.width(), bottom - top)

    def event(self, event) -> bool:
        """Shows the tooltip of the metric under the pointer."""
        if event.type() == QEvent.Type.ToolTip:
            for index, metric in enumerate(self.metrics):
                if metric.tooltip and self._row(index).contains(event.pos()):
                    QToolTip.showText(event.globalPos(), metric.tooltip, self)
                    return True
            QToolTip.hideText()
            event.ignore()
            return True
        return super().event(event)

    # ------------------------------------------------------------------ painting
    def paintEvent(self, event) -> None:
        """Paints the table: name, value and trend of each metric."""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(Colors.N0))
        painter.setPen(QColor(Colors.N150))
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))
        for index, metric in enumerate(self.metrics):
            row = self._row(index)
            if index:
                painter.fillRect(QRect(row.left(), row.top(), row.width(), 1), QColor(Colors.N150))
            self._paint_row(painter, row, metric)

    def _paint_row(self, painter: QPainter, row: QRect, metric: Metric) -> None:
        x = row.left() + 12
        painter.setFont(Type.font("caption-strong"))
        painter.setPen(QColor(Colors.N600))
        painter.drawText(QRect(x, row.top(), _LABEL_WIDTH - 12, row.height()),
                         int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), metric.label)

        value_x = row.left() + _LABEL_WIDTH
        value = metric.current
        value_font = Type.font("metric", tabular=True)
        painter.setFont(value_font)
        if value is None:
            painter.setPen(QColor(Colors.N500))
            painter.drawText(QRect(value_x, row.top(), _VALUE_WIDTH, row.height()),
                             int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), EM_DASH)
        else:
            text = metric.format(value)
            painter.setPen(QColor(Colors.N900))
            painter.drawText(QRect(value_x, row.top(), _VALUE_WIDTH, row.height()),
                             int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), text)
            if metric.unit:
                metrics = QFontMetrics(value_font)
                baseline = row.top() + (row.height() + metrics.ascent() - metrics.descent()) / 2
                painter.setFont(Type.font("caption"))
                painter.setPen(QColor(Colors.N500))
                painter.drawText(QPointF(value_x + metrics.horizontalAdvance(text) + 4, baseline), metric.unit)

        trend = QRectF(value_x + _VALUE_WIDTH, row.top() + 8, row.right() - 12 - (value_x + _VALUE_WIDTH),
                       row.height() - 16)
        if trend.width() > 24:
            self._paint_trend(painter, trend, metric)

    def _paint_trend(self, painter: QPainter, area: QRectF, metric: Metric) -> None:
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        guide = QPen(QColor(Colors.N150), 1, Qt.PenStyle.DashLine)
        painter.setPen(guide)
        painter.drawLine(QPointF(area.left(), area.bottom() + 0.5), QPointF(area.right(), area.bottom() + 0.5))

        samples = list(metric.samples)
        if not any(value is not None for value in samples):
            painter.restore()
            return
        low, high = metric.scale()
        span = max(high - low, 1e-9)
        step = area.width() / (HISTORY - 1)
        start_x = area.right() - (len(samples) - 1) * step

        def point(index: int, value: float) -> QPointF:
            ratio = max(0.0, min(1.0, (value - low) / span))
            if not metric.inverted:
                ratio = 1.0 - ratio
            return QPointF(start_x + index * step, area.top() + ratio * area.height())

        current = metric.current
        warn = metric.warn_below is not None and current is not None and current < metric.warn_below
        color = Colors.A600 if warn else Colors.P600

        # Runs of consecutive samples (a missing value breaks the line).
        runs: list[list[QPointF]] = [[]]
        for index, value in enumerate(samples):
            if value is None:
                if runs[-1]:
                    runs.append([])
                continue
            runs[-1].append(point(index, value))
        line = QPen(QColor(color), 1.5)
        line.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        for run in runs:
            if len(run) < 2:
                continue
            area_path = QPainterPath(QPointF(run[0].x(), area.bottom()))
            for p in run:
                area_path.lineTo(p)
            area_path.lineTo(QPointF(run[-1].x(), area.bottom()))
            area_path.closeSubpath()
            painter.fillPath(area_path, qcolor(color, 0.10))
            line_path = QPainterPath(run[0])
            for p in run[1:]:
                line_path.lineTo(p)
            painter.setPen(line)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(line_path)
        last = runs[-1][-1] if runs[-1] else None
        if last is not None:
            painter.setPen(QPen(QColor(Colors.N0), 1.5))
            painter.setBrush(QColor(color))
            painter.drawEllipse(last, 3, 3)
        painter.restore()


class SkeletonPanel(Panel):
    """Pose analysis panel: the skeleton image and the telemetry table."""
    def __init__(self, parent: QWidget | None = None):
        super().__init__(Pose.TITLE, subtitle=Pose.SUBTITLE, parent=parent)
        self._state = "idle"
        self._telemetry: dict = {}
        self.add_action(make_label(Pose.TREND_WINDOW, "caption", "tertiary"))

        self.view = SkeletonView()
        self.metrics = [
            Metric("inference_ms", Pose.INFERENCE, "ms", lambda v: f"{v:.1f}", high=None),
            Metric("confidence", Pose.CONFIDENCE, "%", lambda v: f"{round(v * 100)}", warn_below=0.5),
            Metric("centroid_y", Pose.HIP_HEIGHT, "", lambda v: f"{v:.3f}", inverted=True,
                   tooltip=Pose.HIP_HEIGHT_TIP),
        ]
        self.table = TelemetryTable(self.metrics)
        body = self.body_layout()
        body.addWidget(self.view)
        body.addSpacing(Space.S3)
        body.addWidget(self.table)

        self._timer = QTimer(self)
        self._timer.setInterval(250)
        self._timer.timeout.connect(self._sample)

    # ------------------------------------------------------------------ contract (AdminController)
    @Slot(QImage)
    def update_frame(self, qimage: QImage) -> None:
        """Shows the skeleton image of the newest frame (ignored while stopped).

        Args:
            qimage: The skeleton cropped around the person.
        """
        if self._state in STOPPED:
            return
        self.view.set_image(qimage)

    @Slot(dict)
    def update_telemetry(self, data: dict) -> None:
        """Stores the newest telemetry; the trends sample it at 4 Hz.

        Args:
            data: inference_ms, confidence and centroid_y.
        """
        if self._state in STOPPED:
            return
        self._telemetry = data or {}

    # ------------------------------------------------------------------ state
    def set_state(self, state: str) -> None:
        """Follows the monitoring state: sample while live, clear when a run starts or ends.

        Args:
            state: The monitoring state.
        """
        previous, self._state = self._state, state
        if state == "live":
            self._timer.start()
        else:
            self._timer.stop()
        if state == "starting" or (state in STOPPED and previous not in STOPPED):
            self._telemetry = {}
            self.view.clear()
            self.table.clear()

    @Slot()
    def _sample(self) -> None:
        """Takes the latest telemetry into the trends (4 Hz, only while live)."""
        data = self._telemetry
        values: dict[str, float | None] = {}
        for metric in self.metrics:
            raw = data.get(metric.key)
            values[metric.key] = float(raw) if raw is not None else None
        if values.get("confidence") is not None:
            values["confidence"] = max(0.0, min(1.0, values["confidence"]))
        self.table.push(values)
