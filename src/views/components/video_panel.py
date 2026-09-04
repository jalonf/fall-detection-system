from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QComboBox, QSizePolicy, QFileDialog, QWidget
)
from src.views.theme import apply_shadow

class VideoPanel(QFrame):
    """Component for the live camera feed and stream controls with a professional layout."""
    
    start_requested = Signal(int)
    upload_requested = Signal(str)
    stop_requested = Signal()
    
    def __init__(self, user_role="Family / Caregiver", parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("panel")
        self.user_role = user_role
        self._current_pixmap = None
        apply_shadow(self, blur=10, y=2, alpha=7)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        header = QVBoxLayout()
        header.setSpacing(2)
        header_title = QLabel("Live Camera Feed & Analysis")
        header_title.setObjectName("cardTitle")
        header_sub = QLabel("Real-time pose tracking and fall detection stream")
        header_sub.setObjectName("cardSubtitle")
        header.addWidget(header_title)
        header.addWidget(header_sub)
        layout.addLayout(header)

        self.video_label = QLabel()
        self.video_label.setObjectName("videoFrame")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(1, 1)
        self.video_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.video_label.setText(self._video_placeholder())
        layout.addWidget(self.video_label, 1)

        controls_container = QWidget()
        controls = QHBoxLayout(controls_container)
        controls.setContentsMargins(0, 4, 0, 0)
        controls.setSpacing(12)

        cam_label = QLabel("Source:")
        cam_label.setObjectName("fieldLabel")

        self.camera_select = QComboBox()
        self.camera_select.addItems(["Camera 0 (Built-in)", "Camera 1 (USB)", "IP Stream"])
        self.camera_select.setFixedHeight(36)
        self.camera_select.setFixedWidth(170)
        self.camera_select.setCursor(Qt.CursorShape.PointingHandCursor)

        controls.addWidget(cam_label)
        controls.addWidget(self.camera_select)

        if self.user_role == "Administrator":
            self.btn_upload = QPushButton("Upload Video")
            self.btn_upload.setObjectName("ghost")
            self.btn_upload.setFixedHeight(36)
            self.btn_upload.setMinimumWidth(115)
            self.btn_upload.setCursor(Qt.CursorShape.PointingHandCursor)
            self.btn_upload.clicked.connect(self._open_file_dialog)
            controls.addWidget(self.btn_upload)

        controls.addStretch()

        self.btn_stop = QPushButton("Stop Monitoring")
        self.btn_stop.setObjectName("ghost")
        self.btn_stop.setFixedHeight(36)
        self.btn_stop.setMinimumWidth(135)
        self.btn_stop.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_requested.emit)

        self.btn_start = QPushButton("Start Detection")
        self.btn_start.setObjectName("primary")
        self.btn_start.setFixedHeight(36)
        self.btn_start.setMinimumWidth(145)
        self.btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
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
            "<b style='color:#94A3B8; font-size:15px;'>Stream Offline</b><br/><br/>"
            "<span style='color:#64748B; font-size:13px;'>Select a source or start detection to begin analysis</span>"
            "</div>"
        )

    def update_frame(self, qimage):
        self._current_pixmap = QPixmap.fromImage(qimage)
        self._render_pixmap()

    def _render_pixmap(self):
        if self._current_pixmap is None or self._current_pixmap.isNull():
            return
        scaled = self._current_pixmap.scaled(
            self.video_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.video_label.setPixmap(scaled)

    def clear_video(self):
        self._current_pixmap = None
        self.video_label.setPixmap(QPixmap())
        self.video_label.setText(self._video_placeholder())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._render_pixmap()

    def set_monitoring_state(self, active: bool):
        self.btn_start.setEnabled(not active)
        if hasattr(self, "btn_upload"):
            self.btn_upload.setEnabled(not active)
        self.btn_stop.setEnabled(active)
        self.camera_select.setEnabled(not active)

    def set_alert_state(self, pulse_state: bool):
        if pulse_state:
            self._swap_object_name(self.video_label, "videoFrameAlert")
        else:
            self._swap_object_name(self.video_label, "videoFrameAlertDim")

    def reset_alert_state(self):
        self._swap_object_name(self.video_label, "videoFrame")

    def _swap_object_name(self, widget, name: str):
        widget.setObjectName(name)
        widget.style().unpolish(widget)
        widget.style().polish(widget)