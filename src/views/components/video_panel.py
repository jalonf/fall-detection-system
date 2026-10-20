from PySide6.QtCore import QEvent, QPointF, QSize, Qt, Signal
from PySide6.QtGui import QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QStackedLayout,
    QVBoxLayout,
    QWidget,
)

from src.views.components.status_chip import StatusChip
from src.views.icons import icon
from src.views.theme import (
    Colors,
    Size,
    Space,
    apply_shadow,
    set_prop,
    style_combo,
    with_alpha,
)

_PRIMARY_ACTION_WIDTH = 160


class _StagePlaceholder(QWidget):
    """
    Empty state of the video stage. Four corner brackets (the same detection
    reticle as the brand mark) frame the message so the stage reads as a camera
    that is simply waiting, not as a broken panel.
    """

    ARM = 22
    INSET = 18

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("streamPlaceholder")

        column = QVBoxLayout(self)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(6)
        column.setAlignment(Qt.AlignmentFlag.AlignCenter)

        glyph = QLabel()
        glyph.setAlignment(Qt.AlignmentFlag.AlignCenter)
        glyph.setPixmap(icon("camera", Colors.STAGE_TEXT_MUTED, 40).pixmap(QSize(40, 40)))
        title = QLabel("Stream offline")
        title.setObjectName("placeholderTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint = QLabel("Select a video source and press \u201cStart detection\u201d to begin the analysis")
        hint.setObjectName("placeholderHint")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)

        column.addWidget(glyph)
        column.addSpacing(6)
        column.addWidget(title)
        column.addWidget(hint)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        pen = QPen(with_alpha(Colors.STAGE_TEXT_MUTED, 120), 2.0)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        left, top = float(self.INSET), float(self.INSET)
        right, bottom = self.width() - self.INSET, self.height() - self.INSET
        arm = float(self.ARM)
        for cx, cy, dx, dy in (
            (left, top, 1, 1), (right, top, -1, 1),
            (left, bottom, 1, -1), (right, bottom, -1, -1),
        ):
            corner = QPainterPath()
            corner.moveTo(QPointF(cx + dx * arm, cy))
            corner.lineTo(QPointF(cx, cy))
            corner.lineTo(QPointF(cx, cy + dy * arm))
            painter.drawPath(corner)
        painter.end()


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
        self._monitoring = False
        self._controls_compact: bool | None = None
        self._build_ui()

    # ------------------------------------------------------------------ build
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(*Space.PANEL)
        layout.setSpacing(14)

        layout.addLayout(self._build_header())
        layout.addWidget(self._build_stage(), 1)
        self._build_fall_banner()

        divider = QFrame()
        divider.setObjectName("panelDivider")
        divider.setFixedHeight(1)
        layout.addWidget(divider)

        layout.addWidget(self._build_controls())

    def _build_header(self) -> QHBoxLayout:
        header_row = QHBoxLayout()
        header_row.setSpacing(12)

        header = QVBoxLayout()
        header.setSpacing(2)
        header_title = QLabel("Live camera feed")
        header_title.setObjectName("cardTitle")
        header_sub = QLabel("Real-time pose tracking and fall detection")
        header_sub.setObjectName("cardSubtitle")
        header.addWidget(header_title)
        header.addWidget(header_sub)
        header_row.addLayout(header)
        header_row.addStretch()

        self.live_chip = StatusChip(text="Offline", state="idle")
        header_row.addWidget(self.live_chip, 0, Qt.AlignmentFlag.AlignTop)
        return header_row

    def _build_stage(self) -> QFrame:
        self.video_stage = QFrame()
        self.video_stage.setObjectName("stage")
        self.video_stage.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.video_stage.setProperty("alert", "off")
        self.video_stage.installEventFilter(self)
        self.video_stage.setMinimumHeight(220)

        # The stage shows either the offline placeholder or the live frame.
        self.stage_stack = QStackedLayout(self.video_stage)
        self.stage_stack.setContentsMargins(6, 6, 6, 6)

        self.video_label = QLabel()
        self.video_label.setObjectName("videoFrame")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(1, 1)
        self.video_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.stage_stack.addWidget(_StagePlaceholder())
        self.stage_stack.addWidget(self.video_label)
        self.stage_stack.setCurrentIndex(0)
        return self.video_stage

    def _build_fall_banner(self):
        """High-contrast fall alert, floated over the top of the stage (not in the layout)."""
        self.fall_banner = QFrame(self.video_stage)
        self.fall_banner.setObjectName("fallBanner")
        self.fall_banner.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.fall_banner.setProperty("pulse", "off")
        banner_layout = QHBoxLayout(self.fall_banner)
        banner_layout.setContentsMargins(14, 9, 18, 9)
        banner_layout.setSpacing(10)
        banner_icon = QLabel()
        banner_icon.setPixmap(icon("warning", Colors.TEXT_INVERSE, 20).pixmap(QSize(20, 20)))
        self.fall_banner_text = QLabel("")
        self.fall_banner_text.setObjectName("fallBannerText")
        banner_layout.addWidget(banner_icon)
        banner_layout.addWidget(self.fall_banner_text)
        # Small floating element: safe to give it depth (see theme.apply_shadow).
        apply_shadow(self.fall_banner, blur=22, y=4, alpha=110)
        self.fall_banner.hide()

    @staticmethod
    def _action_button(text, kind, icon_name, icon_color, min_width) -> QPushButton:
        """Dashboard button: shared height, cursor and icon sizing."""
        button = QPushButton(text)
        button.setObjectName(kind)
        button.setFixedHeight(Size.CONTROL)
        button.setMinimumWidth(min_width)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setIcon(icon(icon_name, icon_color, 16))
        button.setIconSize(QSize(16, 16))
        return button

    @staticmethod
    def _group(spacing: int = 10) -> tuple[QWidget, QHBoxLayout]:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(spacing)
        return widget, layout

    def _build_controls(self) -> QWidget:
        """
        Three groups (source · admin tools · run controls) placed on a grid. When the
        panel is too narrow for one row, the admin tools drop to their own row instead
        of forcing the window wider (see `_update_controls_layout`).
        """
        self._controls = QWidget()
        self._controls_grid = QGridLayout(self._controls)
        self._controls_grid.setContentsMargins(0, 2, 0, 0)
        self._controls_grid.setHorizontalSpacing(12)
        self._controls_grid.setVerticalSpacing(10)

        # -- source selector
        self._source_group, source = self._group()
        cam_label = QLabel("Source")
        cam_label.setObjectName("fieldLabel")

        self.camera_select = QComboBox()
        self.camera_select.addItems(["Camera 0 (Built-in)", "Camera 1 (USB)"])
        self.camera_select.setFixedHeight(Size.CONTROL)
        self.camera_select.setFixedWidth(196)
        self.camera_select.setCursor(Qt.CursorShape.PointingHandCursor)
        style_combo(self.camera_select)

        source.addWidget(cam_label)
        source.addWidget(self.camera_select)

        # -- administrator tools
        self._tools_group = None
        if self.user_role == "Administrator":
            self._tools_group, tools = self._group(spacing=0)

            self.btn_upload = self._action_button(
                "Upload video", "ghost", "upload", Colors.ON_GHOST, 130
            )
            self.btn_upload.setToolTip("Analyse a video file instead of a live camera")
            self.btn_upload.clicked.connect(self._open_file_dialog)
            tools.addWidget(self.btn_upload)

        # -- run controls
        self._run_group, run = self._group()

        # One button for both actions: it starts detection while idle and stops it while
        # a stream is running (see `set_monitoring_state`). The signals are the same ones
        # the two former buttons emitted.
        self.btn_toggle = self._action_button(
            "Start detection", "toggle", "play", Colors.TEXT_MAIN, _PRIMARY_ACTION_WIDTH
        )
        self.btn_toggle.setProperty("running", "false")
        self.btn_toggle.setToolTip("Start fall detection on the selected source")
        self.btn_toggle.clicked.connect(self._on_toggle_clicked)
        run.addWidget(self.btn_toggle)

        self._update_controls_layout(force=True)
        return self._controls

    def _on_toggle_clicked(self):
        if self._monitoring:
            self.stop_requested.emit()
        else:
            self.start_requested.emit(self.camera_select.currentIndex())

    def _controls_needed_width(self) -> int:
        groups = [self._source_group, self._run_group]
        if self._tools_group is not None:
            groups.append(self._tools_group)
        spacing = self._controls_grid.horizontalSpacing() * (len(groups) - 1)
        return sum(g.sizeHint().width() for g in groups) + spacing

    def _update_controls_layout(self, force: bool = False):
        """Single row when it fits; admin tools on a second row when it does not."""
        available = self.width() - 2 * Space.PANEL_X
        compact = (
            self._tools_group is not None
            and available > 0
            and available < self._controls_needed_width()
        )
        if not force and compact == self._controls_compact:
            return
        self._controls_compact = compact

        grid = self._controls_grid
        for widget in (self._source_group, self._tools_group, self._run_group):
            if widget is not None:
                grid.removeWidget(widget)
        for column in range(4):
            grid.setColumnStretch(column, 0)

        if compact:
            grid.addWidget(self._source_group, 0, 0)
            grid.addWidget(self._run_group, 0, 2, Qt.AlignmentFlag.AlignRight)
            grid.addWidget(self._tools_group, 1, 0, 1, 3)
            grid.setColumnStretch(1, 1)
        else:
            grid.addWidget(self._source_group, 0, 0)
            if self._tools_group is not None:
                grid.addWidget(self._tools_group, 0, 1)
            grid.addWidget(self._run_group, 0, 3, Qt.AlignmentFlag.AlignRight)
            grid.setColumnStretch(2, 1)

    def _open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Video for Fall Analysis",
            "",
            "Video Files (*.mp4 *.avi *.mov *.mkv)"
        )
        if file_path:
            self.upload_requested.emit(file_path)

    # ----------------------------------------------------------------- frames
    def update_frame(self, qimage):
        # Frames queued by the worker can still arrive just after "Stop"; once monitoring
        # has ended they must not bring the last picture (and its stream readout) back.
        if not self._monitoring:
            return
        self._current_pixmap = QPixmap.fromImage(qimage)
        if self.stage_stack.currentWidget() is not self.video_label:
            self.stage_stack.setCurrentWidget(self.video_label)
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
        self.video_label.clear()
        self.stage_stack.setCurrentIndex(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._render_pixmap()
        self._update_controls_layout()

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
        self._apply_toggle(active)
        if hasattr(self, "btn_upload"):
            self.btn_upload.setEnabled(not active)
        self.camera_select.setEnabled(not active)
        self._sync_chip()

    def _apply_toggle(self, running: bool):
        """Start/stop button: light grey "Start detection" when idle, red "Stop monitoring" when running."""
        if running:
            self.btn_toggle.setText("Stop monitoring")
            self.btn_toggle.setIcon(icon("stop", Colors.TEXT_INVERSE, 16))
            self.btn_toggle.setToolTip("Stop the stream and the analysis")
        else:
            self.btn_toggle.setText("Start detection")
            self.btn_toggle.setIcon(icon("play", Colors.TEXT_MAIN, 16))
            self.btn_toggle.setToolTip("Start fall detection on the selected source")
        set_prop(self.btn_toggle, "running", "true" if running else "false")

    def set_alert_state(self, pulse_state: bool):
        set_prop(self.video_stage, "alert", "on" if pulse_state else "dim")
        set_prop(self.fall_banner, "pulse", "on" if pulse_state else "off")
        self.live_chip.set_state("alert", "Fall alert")

    def reset_alert_state(self):
        set_prop(self.video_stage, "alert", "off")
        set_prop(self.fall_banner, "pulse", "off")
        self.fall_banner.hide()
        self._sync_chip()
