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

from src.views.theme import Space

_PLACEHOLDER = "Awaiting pose stream"
_POSE_VIEW_HEIGHT = 196


class SkeletonPanel(QFrame):
    """Pose-estimation preview plus live inference telemetry."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("panel")

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
        value = QLabel("--")
        value.setObjectName("metricValue")
        value.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        column.addWidget(cap)
        column.addWidget(value)
        parent_layout.addLayout(column, 1)
        return value

    def update_frame(self, qimage):
        pixmap = QPixmap.fromImage(qimage)
        self.view.setPixmap(pixmap.scaled(
            self.view.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        ))

    def update_telemetry(self, data: dict):
        if not data:
            self.lbl_inf.setText("--")
            self.lbl_cent.setText("--")
            self.lbl_conf.setText("--")
            self.conf_bar.setValue(0)
            return

        inf = data.get('inference_ms', 0.0)
        cent = data.get('centroid_y')
        conf = data.get('confidence', 0.0)

        self.lbl_inf.setText(f"{inf:.1f} ms")
        self.lbl_cent.setText(f"{cent:.3f}" if cent is not None else "--")
        self.lbl_conf.setText(f"{int(conf*100)}%")
        self.conf_bar.setValue(max(0, min(100, int(conf * 100))))

    def clear_video(self):
        self.view.clear()
        self.view.setText(_PLACEHOLDER)
        self.update_telemetry({})
