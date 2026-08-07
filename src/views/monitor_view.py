from PySide6.QtCore import Qt, QTime, QTimer
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QComboBox, QListWidget, QListWidgetItem, QSizePolicy
)
from src.views.theme import apply_shadow, Colors

APP_NAME = "EXAMPLE"
APP_TAGLINE = "Fall Detection System"

class MonitorView(QWidget):
    """
    View responsible for rendering the real-time monitoring interface, 
    including the live camera feed, system status cards, control buttons, 
    and event logs.
    """
    def __init__(self, user_name="User", on_start=None, on_stop=None, on_logout=None, parent=None):
        """
        Args:
            user_name (str): Name of the logged-in user displayed on the top bar.
            on_start (callable): Callback function triggered when monitoring starts.
            on_stop (callable): Callback function triggered when monitoring stops.
            on_logout (callable): Callback function triggered when the user signs out.
            parent (QWidget): Parent widget.
        """
        super().__init__(parent)
        self.setObjectName("monitorScreen")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.user_name = user_name
        self.on_start = on_start
        self.on_stop = on_stop
        self.on_logout = on_logout
        self._is_monitoring = False
        self._current_pixmap = None
        
        self.alert_timer = QTimer(self)
        self.alert_timer.timeout.connect(self._pulse_alert)
        self._pulse_state = False
        
        self._build_ui()

    def _build_ui(self):
        """Builds the main layout containing the top bar, video stream, and sidebar panel."""
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_topbar())

        body_wrapper = QWidget()
        body_wrapper.setObjectName("monitorBody")
        body_layout = QHBoxLayout(body_wrapper)
        body_layout.setContentsMargins(36, 30, 36, 34)
        body_layout.setSpacing(26)

        video_area = QWidget()
        video_layout = QVBoxLayout(video_area)
        video_layout.setContentsMargins(0, 0, 0, 0)
        video_layout.addWidget(self._build_main_video_card(), 1)
        body_layout.addWidget(video_area, 1)

        sidebar_panel = QWidget()
        sidebar_panel.setFixedWidth(352)
        sidebar_panel.setLayout(self._build_sidebar())
        body_layout.addWidget(sidebar_panel, 0)

        root.addWidget(body_wrapper, 1)

    def _build_topbar(self):
        """Builds the application header bar featuring the logo, status indicator, user info, and sign-out button."""
        bar = QFrame()
        bar.setObjectName("topbar")
        bar.setFixedHeight(70)

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(36, 0, 36, 0)
        layout.setSpacing(0)

        logo_mark = QLabel(APP_NAME[0].upper())
        logo_mark.setObjectName("brandMark")
        logo_mark.setFixedSize(36, 36)
        logo_mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_mark.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        brand_text = QVBoxLayout()
        brand_text.setSpacing(1)
        brand_text.setContentsMargins(0, 0, 0, 0)
        logo = QLabel(APP_NAME)
        logo.setObjectName("appTitle")
        tagline = QLabel(APP_TAGLINE)
        tagline.setObjectName("appSubtitle")
        brand_text.addWidget(logo)
        brand_text.addWidget(tagline)

        layout.addWidget(logo_mark)
        layout.addSpacing(12)
        layout.addLayout(brand_text)
        layout.addStretch()

        self.status_badge = QFrame()
        self.status_badge.setObjectName("statusBadgeIdle")
        badge_layout = QHBoxLayout(self.status_badge)
        badge_layout.setContentsMargins(12, 0, 14, 0)
        badge_layout.setSpacing(8)
        self.status_dot = QFrame()
        self.status_dot.setObjectName("statusDot")
        self.status_dot.setFixedSize(8, 8)
        self.status_dot.setStyleSheet("background-color: #94A3B8; border-radius: 4px;")
        self.status_label = QLabel("Idle")
        self.status_label.setObjectName("statusText")
        self.status_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #64748B; background: transparent;")
        badge_layout.addWidget(self.status_dot)
        badge_layout.addWidget(self.status_label)
        layout.addWidget(self.status_badge)

        sep = QFrame()
        sep.setObjectName("topbarSep")
        sep.setFixedSize(1, 26)
        layout.addSpacing(18)
        layout.addWidget(sep)
        layout.addSpacing(18)

        avatar = QLabel(self.user_name[0].upper() if self.user_name else "U")
        avatar.setObjectName("avatar")
        avatar.setFixedSize(32, 32)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        user_lbl = QLabel(self.user_name)
        user_lbl.setObjectName("userName")

        layout.addWidget(avatar)
        layout.addSpacing(10)
        layout.addWidget(user_lbl)
        layout.addSpacing(24)

        self.btn_logout = QPushButton("Sign Out")
        self.btn_logout.setObjectName("ghost")
        self.btn_logout.setFixedHeight(34)
        self.btn_logout.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_logout.clicked.connect(lambda: self.on_logout() if self.on_logout else None)
        layout.addWidget(self.btn_logout)
        return bar

    def _build_main_video_card(self):
        """Builds the main video frame card along with source selection dropdown and control buttons."""
        card = QFrame()
        card.setObjectName("panel")
        apply_shadow(card, blur=32, y=8, alpha=10)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(26, 24, 26, 22)
        layout.setSpacing(18)

        header = QVBoxLayout()
        header.setSpacing(3)
        header_title = QLabel("Live Camera Feed")
        header_title.setObjectName("cardTitle")
        header_sub = QLabel("Real-time pose tracking and fall analysis")
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

        line = QFrame()
        line.setObjectName("divider")
        line.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(line)

        controls = QHBoxLayout()
        controls.setSpacing(14)

        cam_label = QLabel("Source")
        cam_label.setObjectName("fieldLabel")

        self.camera_select = QComboBox()
        self.camera_select.addItems(["Camera 0 (Built-in)", "Camera 1 (USB)", "IP Stream"])
        self.camera_select.setFixedHeight(42)
        self.camera_select.setFixedWidth(210)
        self.camera_select.setCursor(Qt.CursorShape.PointingHandCursor)

        controls.addWidget(cam_label)
        controls.addWidget(self.camera_select)
        controls.addStretch()

        self.btn_stop = QPushButton("Stop Monitoring")
        self.btn_stop.setObjectName("ghost")
        self.btn_stop.setFixedHeight(44)
        self.btn_stop.setMinimumWidth(150)
        self.btn_stop.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._handle_stop)

        self.btn_start = QPushButton("Start Detection")
        self.btn_start.setObjectName("primary")
        self.btn_start.setFixedHeight(44)
        self.btn_start.setMinimumWidth(170)
        self.btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_start.clicked.connect(self._handle_start)

        controls.addWidget(self.btn_stop)
        controls.addWidget(self.btn_start)

        layout.addLayout(controls)
        return card

    def _build_sidebar(self):
        """Builds the sidebar containing statistics cards, system status overview, and the event log."""
        sidebar = QVBoxLayout()
        sidebar.setContentsMargins(0, 0, 0, 0)
        sidebar.setSpacing(18)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(16)
        stats_row.addWidget(self._stat_card("0", "FALLS TODAY", "stat_falls", Colors.DANGER))
        stats_row.addWidget(self._stat_card("00:00", "SESSION UPTIME", "stat_time", Colors.PRIMARY))
        sidebar.addLayout(stats_row)

        self.status_card = QFrame()
        self.status_card.setObjectName("statusCardNormal")
        apply_shadow(self.status_card, blur=28, y=6, alpha=9)

        sc_layout = QVBoxLayout(self.status_card)
        sc_layout.setContentsMargins(22, 20, 22, 20)
        sc_layout.setSpacing(8)

        sc_title = QLabel("SYSTEM STATUS")
        sc_title.setObjectName("sectionTitle")
        sc_layout.addWidget(sc_title)

        self.detection_status = QLabel("Idle")
        self.detection_status.setObjectName("detectionStatus")
        self.detection_status.setStyleSheet("font-size: 23px; font-weight: 800; color: #475569; letter-spacing: -0.4px; background: transparent;")
        sc_layout.addWidget(self.detection_status)

        self.detection_detail = QLabel("System is ready. Awaiting video stream.")
        self.detection_detail.setObjectName("detectionDetail")
        self.detection_detail.setWordWrap(True)
        sc_layout.addWidget(self.detection_detail)
        sidebar.addWidget(self.status_card)

        log_card = QFrame()
        log_card.setObjectName("panel")
        apply_shadow(log_card, blur=28, y=6, alpha=9)
        log_wrapper = QVBoxLayout(log_card)
        log_wrapper.setContentsMargins(20, 18, 20, 18)
        log_wrapper.setSpacing(12)

        log_header = QHBoxLayout()
        log_title = QLabel("EVENT LOG")
        log_title.setObjectName("sectionTitle")
        log_header.addWidget(log_title)
        log_header.addStretch()

        clear_btn = QPushButton("Clear log")
        clear_btn.setObjectName("subtle")
        clear_btn.setFixedHeight(24)
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self._clear_events)
        log_header.addWidget(clear_btn)
        log_wrapper.addLayout(log_header)

        self.event_list = QListWidget()
        self.event_list.setObjectName("eventLog")
        self.event_list.setMinimumHeight(200)
        self.event_list.setSpacing(4)
        log_wrapper.addWidget(self.event_list, 1)

        sidebar.addWidget(log_card, 1)
        self._refresh_empty_log_hint()
        return sidebar

    def _stat_card(self, value, label, attr_name, accent_color):
        """Helper method to generate a styled metric statistics card."""
        card = QFrame()
        card.setObjectName("statCard")
        card.setFixedHeight(85)
        card.setStyleSheet(f"QFrame#statCard {{ border-left: 4px solid {accent_color}; }}")
        
        apply_shadow(card, blur=16, y=4, alpha=5)

        col = QVBoxLayout(card)
        col.setContentsMargins(20, 14, 18, 14)
        col.setSpacing(2)

        val = QLabel(value)
        val.setStyleSheet("font-size: 26px; font-weight: 800; color: #0F172A; background: transparent; border: none;")

        lbl = QLabel(label)
        lbl.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748B; letter-spacing: 0.5px; background: transparent; border: none;")

        col.addWidget(val)
        col.addWidget(lbl)
        col.addStretch()

        setattr(self, attr_name, val)
        return card

    def _video_placeholder(self):
        """Returns the HTML-formatted placeholder text shown when the camera is offline."""
        return (
            "<div style='text-align:center;'>"
            "<b style='color:#475569; font-size:18px;'>Camera Offline</b><br/><br/>"
            "<span style='color:#64748B; font-size:14px;'>Awaiting video stream connection...</span>"
            "</div>"
        )

    def update_video_frame(self, qimage):
        """Updates the current video frame pixmap and triggers rendering."""
        self._current_pixmap = QPixmap.fromImage(qimage)
        self._render_video_pixmap()

    def _render_video_pixmap(self):
        """Scales and renders the current video frame while preserving aspect ratio."""
        pixmap = getattr(self, "_current_pixmap", None)
        if pixmap is None or pixmap.isNull():
            return
        scaled = pixmap.scaled(
            self.video_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.video_label.setPixmap(scaled)

    def resizeEvent(self, event):
        """Handles widget resizing to dynamically readjust the video frame scale."""
        super().resizeEvent(event)
        self._render_video_pixmap()

    def clear_video(self):
        """Clears the current video pixmap and restores the offline placeholder."""
        self._current_pixmap = None
        self.video_label.setPixmap(QPixmap())
        self.video_label.setText(self._video_placeholder())

    def set_monitoring_state(self, active: bool):
        """Toggles the UI elements and status text based on whether monitoring is active."""
        self._is_monitoring = active
        self.btn_start.setEnabled(not active)
        self.btn_stop.setEnabled(active)
        self.camera_select.setEnabled(not active)

        if active:
            self.status_dot.setStyleSheet(f"background-color: {Colors.PRIMARY}; border-radius: 4px;")
            self.status_label.setText("Monitoring")
            self.status_label.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {Colors.PRIMARY}; background: transparent;")
            self._swap_object_name(self.status_badge, "statusBadgeActive")

            self.detection_status.setText("Analyzing...")
            self.detection_status.setStyleSheet("font-size: 23px; font-weight: 800; color: #2563EB; letter-spacing: -0.4px; background: transparent;")
            self.detection_detail.setText("AI processing active. Looking for anomalies.")
            self._swap_object_name(self.status_card, "statusCardNormal")
        else:
            self.status_dot.setStyleSheet("background-color: #94A3B8; border-radius: 4px;")
            self.status_label.setText("Idle")
            self.status_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #64748B; background: transparent;")
            self._swap_object_name(self.status_badge, "statusBadgeIdle")

            self.detection_status.setText("Idle")
            self.detection_status.setStyleSheet("font-size: 23px; font-weight: 800; color: #475569; letter-spacing: -0.4px; background: transparent;")
            self.detection_detail.setText("System is ready. Awaiting video stream.")

    def trigger_fall_alert(self, message="Possible fall detected"):
        """Triggers visual emergency warning states across UI components upon a fall detection event."""
        self.detection_status.setText("CRITICAL ALERT")
        self.detection_detail.setText(message)
        
        self._swap_object_name(self.video_label, "videoFrameAlert")
        self._swap_object_name(self.status_badge, "statusBadgeAlert")
        self._swap_object_name(self.status_card, "statusCardAlert")
        
        self.add_event("ALERT", message)
        
        self._pulse_state = False
        self.alert_timer.start(350)
        
        QTimer.singleShot(4000, self.clear_alert)

    def _pulse_alert(self):
        """Alternates styling states to create a pulsing blinking effect during a critical alert."""
        self._pulse_state = not self._pulse_state
        
        if self._pulse_state:
            color = Colors.DANGER 
            self._swap_object_name(self.video_label, "videoFrameAlert")
        else:
            color = "#7F1D1D" 
            self._swap_object_name(self.video_label, "videoFrameAlertDim") 
            
        self.detection_status.setStyleSheet(f"font-size: 23px; font-weight: 800; color: {color}; letter-spacing: -0.4px; background: transparent;")
        self.status_dot.setStyleSheet(f"background-color: {color}; border-radius: 4px;")
        self.status_label.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {color}; background: transparent;")

    def clear_alert(self):
        """Stops the alert pulsing animation and restores standard monitoring visual themes."""
        self.alert_timer.stop()
        self._swap_object_name(self.video_label, "videoFrame")
        self.set_monitoring_state(self._is_monitoring)

    def add_event(self, event_type: str, message: str):
        """Appends a new formatted event entry to the log list widget."""
        if getattr(self, "_empty_hint_active", False):
            self.event_list.clear()
            self._empty_hint_active = False

        timestamp = QTime.currentTime().toString("HH:mm:ss")
        item = QListWidgetItem(f"[{timestamp}]  {event_type}  —  {message}")
        if event_type == "ALERT":
            item.setForeground(QColor(Colors.DANGER))
        elif event_type == "INFO":
            item.setForeground(QColor(Colors.PRIMARY))
        else:
            item.setForeground(QColor(Colors.TEXT_MUTED))
        self.event_list.insertItem(0, item)

    def _clear_events(self):
        """Clears all records from the event log."""
        self.event_list.clear()
        self._refresh_empty_log_hint()

    def _refresh_empty_log_hint(self):
        """Inserts a default placeholder instruction inside the event log when empty."""
        self.event_list.clear()
        hint = QListWidgetItem("No events recorded in this session.")
        hint.setForeground(QColor(Colors.TEXT_SUBTLE))
        hint.setFlags(Qt.ItemFlag.NoItemFlags)
        self.event_list.addItem(hint)
        self._empty_hint_active = True

    def update_stat(self, attr_name: str, value: str):
        """Safely updates a target numeric tracking label value by its attribute name."""
        widget = getattr(self, attr_name, None)
        if widget:
            widget.setText(value)

    def _swap_object_name(self, widget, name: str):
        """Helper to safely modify an element's object name and force QSS style re-evaluation."""
        widget.setObjectName(name)
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    def _handle_start(self):
        """Handles the start monitoring action button press."""
        camera_index = self.camera_select.currentIndex()
        self.set_monitoring_state(True)
        self.add_event("INFO", f"Stream connected (Source {camera_index})")
        if self.on_start:
            self.on_start(camera_index=camera_index)

    def _handle_stop(self):
        """Handles the stop monitoring action button press."""
        self.set_monitoring_state(False)
        self.add_event("INFO", "Stream disconnected")
        self.clear_video()
        if self.on_stop:
            self.on_stop()


