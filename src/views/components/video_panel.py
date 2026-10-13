import time

from PySide6.QtCore import QEvent, QSize, Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.views.components.status_chip import StatusChip
from src.views.icons import icon
from src.views.theme import Colors, set_prop


class VideoPanel(QFrame):
    """Component for the live camera feed and stream controls with a professional layout."""

    start_requested = Signal(int)
    upload_requested = Signal(str)
    stop_requested = Signal()
    notify_requested = Signal()

    def __init__(self, user_role="Family / Caregiver", parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("panel")
        self.user_role = user_role
        self._current_pixmap = None
        self._monitoring = False
        self._last_frame_ts = None
        self._fps = 0.0
        self._meta_ts = 0.0
        self._build_ui()

    # ------------------------------------------------------------------ build
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(14)

        # ---- Header ----
        header_row = QHBoxLayout()
        header_row.setSpacing(12)

        header = QVBoxLayout()
        header.setSpacing(2)
        header_title = QLabel("Live Camera Feed & Analysis")
        header_title.setObjectName("cardTitle")
        header_sub = QLabel("Real-time pose tracking and fall detection stream")
        header_sub.setObjectName("cardSubtitle")
        header.addWidget(header_title)
        header.addWidget(header_sub)
        header_row.addLayout(header)
        header_row.addStretch()

        self.meta_label = QLabel("")
        self.meta_label.setObjectName("streamMeta")
        header_row.addWidget(self.meta_label)

        self.live_chip = StatusChip(tone="light", text="Offline", state="idle")
        header_row.addWidget(self.live_chip)
        layout.addLayout(header_row)

        # ---- Video stage ----
        self.video_stage = QFrame()
        self.video_stage.setObjectName("stage")
        self.video_stage.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.video_stage.setProperty("alert", "off")
        self.video_stage.installEventFilter(self)
        stage_layout = QVBoxLayout(self.video_stage)
        stage_layout.setContentsMargins(6, 6, 6, 6)

        self.video_label = QLabel()
        self.video_label.setObjectName("videoFrame")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(1, 1)
        self.video_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.video_label.setText(self._video_placeholder())
        stage_layout.addWidget(self.video_label)
        layout.addWidget(self.video_stage, 1)

        # High-contrast fall alert, floated over the top of the stage (not in the layout).
        self.fall_banner = QFrame(self.video_stage)
        self.fall_banner.setObjectName("fallBanner")
        self.fall_banner.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.fall_banner.setProperty("pulse", "off")
        banner_layout = QHBoxLayout(self.fall_banner)
        banner_layout.setContentsMargins(14, 9, 18, 9)
        banner_layout.setSpacing(10)
        banner_icon = QLabel()
        banner_icon.setPixmap(icon("warning", "#FFFFFF", 20).pixmap(QSize(20, 20)))
        self.fall_banner_text = QLabel("")
        self.fall_banner_text.setObjectName("fallBannerText")
        banner_layout.addWidget(banner_icon)
        banner_layout.addWidget(self.fall_banner_text)
        self.fall_banner.hide()

        # ---- Controls ----
        controls_container = QWidget()
        controls = QHBoxLayout(controls_container)
        controls.setContentsMargins(0, 2, 0, 0)
        controls.setSpacing(10)

        cam_label = QLabel("Source")
        cam_label.setObjectName("fieldLabel")

        self.camera_select = QComboBox()
        self.camera_select.addItems(["Camera 0 (Built-in)", "Camera 1 (USB)", "IP Stream"])
        self.camera_select.setFixedHeight(38)
        self.camera_select.setFixedWidth(184)
        self.camera_select.setCursor(Qt.CursorShape.PointingHandCursor)

        controls.addWidget(cam_label)
        controls.addWidget(self.camera_select)

        if self.user_role == "Administrator":
            controls.addSpacing(6)

            self.btn_upload = QPushButton("Upload Video")
            self.btn_upload.setObjectName("ghost")
            self.btn_upload.setFixedHeight(38)
            self.btn_upload.setMinimumWidth(130)
            self.btn_upload.setCursor(Qt.CursorShape.PointingHandCursor)
            self.btn_upload.setIcon(icon("upload", Colors.PRIMARY, 16))
            self.btn_upload.setIconSize(QSize(16, 16))
            self.btn_upload.clicked.connect(self._open_file_dialog)
            controls.addWidget(self.btn_upload)

            self.btn_notify = QPushButton("Send Test Alert")
            self.btn_notify.setObjectName("ghost")
            self.btn_notify.setFixedHeight(38)
            self.btn_notify.setMinimumWidth(145)
            self.btn_notify.setCursor(Qt.CursorShape.PointingHandCursor)
            self.btn_notify.setIcon(icon("bell", Colors.PRIMARY, 16))
            self.btn_notify.setIconSize(QSize(16, 16))
            self.btn_notify.clicked.connect(self.notify_requested.emit)
            controls.addWidget(self.btn_notify)

        controls.addStretch()

        self.btn_stop = QPushButton("Stop Monitoring")
        self.btn_stop.setObjectName("danger")
        self.btn_stop.setFixedHeight(38)
        self.btn_stop.setMinimumWidth(150)
        self.btn_stop.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_stop.setIcon(icon("stop", "#FFFFFF", 16, "#C5CFE3"))
        self.btn_stop.setIconSize(QSize(16, 16))
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_requested.emit)

        self.btn_start = QPushButton("Start Detection")
        self.btn_start.setObjectName("primary")
        self.btn_start.setFixedHeight(38)
        self.btn_start.setMinimumWidth(160)
        self.btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_start.setIcon(icon("play", "#FFFFFF", 16, "#A3AEC4"))
        self.btn_start.setIconSize(QSize(16, 16))
        self.btn_start.clicked.connect(lambda: self.start_requested.emit(self.camera_select.currentIndex()))

        controls.addWidget(self.btn_stop)
        controls.addWidget(self.btn_start)

        layout.addWidget(controls_container)

    def _open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Video for Fall Analysis",
            "",
            "Video Files (*.mp4 *.avi *.mov *.mkv)"
        )
        if file_path:
            self.upload_requested.emit(file_path)

    def _video_placeholder(self):
        return (
            "<div style='text-align:center;'>"
            "<b style='color:#D5DEF2; font-size:16px;'>Stream offline</b><br/><br/>"
            "<span style='color:#8A9CC0; font-size:13px;'>Select a source and start detection to begin analysis</span>"
            "</div>"
        )

    # ----------------------------------------------------------------- frames
    def update_frame(self, qimage):
        self._current_pixmap = QPixmap.fromImage(qimage)
        self._render_pixmap()
        self._update_stream_meta(qimage.width(), qimage.height())

    def _render_pixmap(self):
        if self._current_pixmap is None or self._current_pixmap.isNull():
            return
        scaled = self._current_pixmap.scaled(
            self.video_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.video_label.setPixmap(scaled)

    def _update_stream_meta(self, width: int, height: int):
        """Presentation-only readout of resolution and smoothed frame rate."""
        now = time.monotonic()
        if self._last_frame_ts is not None:
            delta = now - self._last_frame_ts
            if delta > 0:
                instant = 1.0 / delta
                self._fps = instant if self._fps == 0.0 else self._fps * 0.9 + instant * 0.1
        self._last_frame_ts = now

        if now - self._meta_ts >= 0.5:
            self._meta_ts = now
            self.meta_label.setText(f"{width}×{height}   {self._fps:.0f} fps")

    def clear_video(self):
        self._current_pixmap = None
        self._last_frame_ts = None
        self._fps = 0.0
        self._meta_ts = 0.0
        self.meta_label.setText("")
        self.video_label.clear()
        self.video_label.setText(self._video_placeholder())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._render_pixmap()

    # ---------------------------------------------------------------- alert banner
    def eventFilter(self, obj, event):
        if obj is self.video_stage and event.type() == QEvent.Type.Resize:
            self._position_fall_banner()
        return super().eventFilter(obj, event)

    def _position_fall_banner(self):
        self.fall_banner.adjustSize()
        x = max((self.video_stage.width() - self.fall_banner.width()) // 2, 0)
        self.fall_banner.move(x, 18)

    def show_fall_banner(self, message: str):
        """Presentation-only: surfaces the alert message over the video."""
        self.fall_banner_text.setText(message)
        self._position_fall_banner()
        self.fall_banner.show()
        self.fall_banner.raise_()

    # ------------------------------------------------------------------ state
    def _sync_chip(self):
        if self._monitoring:
            self.live_chip.set_state("active", "Live")
        else:
            self.live_chip.set_state("idle", "Offline")

    def set_monitoring_state(self, active: bool):
        self._monitoring = active
        self.btn_start.setEnabled(not active)
        if hasattr(self, "btn_upload"):
            self.btn_upload.setEnabled(not active)
        self.btn_stop.setEnabled(active)
        self.camera_select.setEnabled(not active)
        self._sync_chip()

    def set_alert_state(self, pulse_state: bool):
        set_prop(self.video_stage, "alert", "on" if pulse_state else "dim")
        set_prop(self.fall_banner, "pulse", "on" if pulse_state else "off")
        self.live_chip.set_state("alert", "Fall alert")

    def reset_alert_state(self):
        set_prop(self.video_stage, "alert", "off")
        set_prop(self.fall_banner, "pulse", "off")
        self.fall_banner.hide()
        self._sync_chip()
