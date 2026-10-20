from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QSizePolicy,
    QVBoxLayout,
)

from src.views.theme import Space, set_prop

_PLACEHOLDER = "Awaiting pose stream"
_POSE_VIEW_HEIGHT = 196

# Readout shown while a metric has no value: an em dash that keeps the unit in place, so the
# layout and meaning of each metric stay stable between "no data" and "live".
_EMPTY_INFERENCE = "\u2014 ms"
_EMPTY_CENTROID = "\u2014"
_EMPTY_CONFIDENCE = "\u2014 %"


class SkeletonPanel(QFrame):
    """Pose-estimation preview plus live inference telemetry."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("panel")
        self._streaming = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(*Space.PANEL)
        layout.setSpacing(12)

        title = QLabel("Pose telemetry")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        # The preview keeps a fixed height and fills the (fixed-width) sidebar, so
        # incoming frames never trigger a dynamic re-layout.
        stage = QFrame()
        stage.setObjectName("stage")
        stage.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        stage_layout = QVBoxLayout(stage)
        stage_layout.setContentsMargins(4, 4, 4, 4)

        self.view = QLabel()
        self.view.setObjectName("poseView")
        self.view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.view.setMinimumSize(1, _POSE_VIEW_HEIGHT)
        self.view.setMaximumHeight(_POSE_VIEW_HEIGHT)
        self.view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.view.setText(_PLACEHOLDER)
        stage_layout.addWidget(self.view)
        layout.addWidget(stage)

        metrics = QHBoxLayout()
        metrics.setContentsMargins(2, 4, 2, 0)
        metrics.setSpacing(12)

        self.lbl_inf = self._metric(metrics, "Inference")
        self.lbl_cent = self._metric(metrics, "Centroid Y")
        self.lbl_conf = self._metric(metrics, "Confidence")
        layout.addLayout(metrics)

        self.conf_bar = QProgressBar()
        self.conf_bar.setObjectName("confBar")
        self.conf_bar.setRange(0, 100)
        self.conf_bar.setValue(0)
        self.conf_bar.setTextVisible(False)
        self.conf_bar.setFixedHeight(4)
        layout.addWidget(self.conf_bar)

        self.update_telemetry({})

    def _metric(self, parent_layout, caption: str) -> QLabel:
        column = QVBoxLayout()
        column.setSpacing(2)
        column.setContentsMargins(0, 0, 0, 0)

        cap = QLabel(caption)
        cap.setObjectName("metricCaption")
        value = QLabel(_EMPTY_CENTROID)
        value.setProperty("empty", "true")
        value.setObjectName("metricValue")
        value.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        column.addWidget(cap)
        column.addWidget(value)
        parent_layout.addLayout(column, 1)
        return value

    def set_streaming(self, active: bool):
        """Presentation-only: late frames queued after a stop are ignored."""
        self._streaming = active

    def update_frame(self, qimage):
        if not self._streaming:
            return
        pixmap = QPixmap.fromImage(qimage)
        self.view.setPixmap(pixmap.scaled(
            self.view.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        ))

    @staticmethod
    def _show(label: QLabel, text: str | None, empty_text: str):
        """Shows `text`, or the quiet empty readout (muted, regular weight) when it is None."""
        label.setText(empty_text if text is None else text)
        set_prop(label, "empty", "true" if text is None else "false")

    def update_telemetry(self, data: dict):
        if data and not self._streaming:
            return
        if not data:
            self._show(self.lbl_inf, None, _EMPTY_INFERENCE)
            self._show(self.lbl_cent, None, _EMPTY_CENTROID)
            self._show(self.lbl_conf, None, _EMPTY_CONFIDENCE)
            self.conf_bar.setValue(0)
            return

        inf = data.get('inference_ms', 0.0)
        cent = data.get('centroid_y')
        conf = data.get('confidence', 0.0)

        self._show(self.lbl_inf, f"{inf:.1f} ms", _EMPTY_INFERENCE)
        self._show(self.lbl_cent, f"{cent:.3f}" if cent is not None else None, _EMPTY_CENTROID)
        self._show(self.lbl_conf, f"{int(conf*100)}%", _EMPTY_CONFIDENCE)
        self.conf_bar.setValue(max(0, min(100, int(conf * 100))))

    def clear_video(self):
        self.view.clear()
        self.view.setText(_PLACEHOLDER)
        self.update_telemetry({})
