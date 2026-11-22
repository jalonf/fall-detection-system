"""Monitoring screen shared by MonitorView and AdminView.

Contract (used by `BaseMonitorController`): the signals `logout_requested`, `start_requested(int)`,
`stop_requested` and `upload_requested(str)`, and the methods `update_video_frame`, `clear_video`,
`set_monitoring_state`, `set_stopping`, `trigger_fall_alert` and `log_event`.

The state lives here only: `_set_state` is the single place that changes it and passes it on to
every component. The fall alert is an independent layer on top of it (`_alert_active`).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from PySide6.QtCore import (
    QElapsedTimer,
    QSettings,
    QSize,
    Qt,
    QTime,
    QTimer,
    Signal,
    Slot,
)
from PySide6.QtGui import QAction, QImage, QKeySequence
from PySide6.QtWidgets import QApplication, QHBoxLayout, QVBoxLayout, QWidget

from src.views.components.common.confirm_dialog import ConfirmDialog
from src.views.components.common.toast import ToastHost
from src.views.components.monitor.alert_pulse import AlertPulse
from src.views.components.monitor.context_bar import ContextBar
from src.views.components.monitor.event_log import EventLogPanel
from src.views.components.monitor.topbar import Topbar
from src.views.components.monitor.video_panel import VideoPanel
from src.views.strings import Monitor
from src.views.theme import Space
from src.workers.strategies import strategy_for


class MonitorState(StrEnum):
    """States of a monitoring run, shown by every component of the screen."""
    IDLE = "idle"
    STARTING = "starting"
    LIVE = "live"
    STOPPING = "stopping"
    ERROR = "error"
    FINISHED = "finished"


RUNNING = (MonitorState.STARTING, MonitorState.LIVE, MonitorState.STOPPING)
STOPPED = (MonitorState.IDLE, MonitorState.ERROR, MonitorState.FINISHED)


@dataclass(frozen=True)
class SourceInfo:
    """The video source of a run.

    Attributes:
        kind: "camera" or "file".
        label: What the interface shows: "Camera 0", "clip.mp4".
        arg: Camera index or file path, sent again by "Try again".
    """
    kind: str           # "camera" | "file"
    label: str          # what the interface shows: "Camera 0", "clip.mp4"
    arg: int | str      # camera index or file path, re-sent by "Try again"


def camera_profile(risk_level: str | None) -> tuple[str, str]:
    """Returns the camera settings shown for a risk level, and why.

    They are read from the workers' own strategies, so the interface always matches what runs.

    Args:
        risk_level: The patient's risk level, or None.

    Returns:
        The resolution and frame rate ("1280 × 720 · 15 fps") and its tooltip.
    """
    level = (risk_level or "").strip().upper()
    strategy = strategy_for(level or "LOW")
    spec = Monitor.CAMERA_SPEC.format(width=strategy.width, height=strategy.height, fps=strategy.fps)
    known = level in ("LOW", "MEDIUM", "HIGH")
    tip = (Monitor.CAMERA_SPEC_TIP if known else Monitor.CAMERA_SPEC_DEFAULT_TIP).format(level=strategy.name)
    return spec, tip


def format_duration(milliseconds: int) -> str:
    """Formats a duration as HH:MM:SS.

    Args:
        milliseconds: The duration (negative values count as 0).

    Returns:
        The text, e.g. "00:01:05".
    """
    seconds = max(0, milliseconds) // 1000
    return f"{seconds // 3600:02d}:{seconds // 60 % 60:02d}:{seconds % 60:02d}"


SIDE_MIN, SIDE_MAX, SIDE_SHARE = 380, 480, 0.27


class _SideColumn(QWidget):
    """Right column: pose analysis for administrators, then the event log.

    Its width follows the window: 27 % of it, between 380 and 480 px.
    """

    def sizeHint(self) -> QSize:
        return QSize(SIDE_MIN, 600)


class BaseMonitorView(QWidget):
    """Monitoring screen shared by MonitorView and AdminView.

    Signals:
        logout_requested: The user confirmed signing out.
        start_requested(int): Start the camera with this index.
        stop_requested: Stop the running source.
        upload_requested(str): Analyse the video file at this path (administrators).

    Args:
        user_name: Name of the signed-in user.
        user_role: Their role, shown under the name.
        patient_name: Name of their patient, or None.
        risk_level: The patient's risk level, or None.
        parent: Parent widget.
    """
    logout_requested = Signal()
    start_requested = Signal(int)
    stop_requested = Signal()
    upload_requested = Signal(str)

    SECTION = Monitor.SECTION_MONITORING
    CAN_ANALYSE_FILES = False

    def __init__(self, user_name: str = "", user_role: str = "", patient_name: str | None = None,
                 risk_level: str | None = None, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self._state = MonitorState.IDLE
        self._source: SourceInfo | None = None
        self._last_start: SourceInfo | None = None
        self._run_error: str | None = None
        self._stopped_by_user = False
        self._alert_active = False
        self._alert_count = 0
        self._signing_out = False
        self._elapsed = QElapsedTimer()
        self._frozen_ms: int | None = None
        self._run_started = False
        self._settings = QSettings("FallSense", "FallSense")
        self._stateful: list = []

        self._camera_spec, self._camera_tip = camera_profile(risk_level)
        self._build(user_name, user_role, patient_name, risk_level)

        self._duration_timer = QTimer(self)
        # 4 Hz, not 1 Hz: the clock starts with the timer, and a tick that fires a few ms early would
        # round down and keep the duration a whole second behind. The labels only change once a second.
        self._duration_timer.setInterval(250)
        self._duration_timer.timeout.connect(self._refresh_duration)
        self.pulse = AlertPulse(self)
        self.pulse.phase_changed.connect(self._on_pulse)

        self._toggle_action = self._shortcut(("Ctrl+Return", "Ctrl+Enter"), self._toggle_monitoring)
        self._ack_action = self._shortcut(("Esc",), self._acknowledge_alert)
        self._ack_action.setEnabled(False)
        self._shortcut(("Ctrl+L",), self.event_log.focus_events)
        self._shortcut(("Ctrl+Shift+Q",), self._request_sign_out)
        self._connect_extras()
        self._set_state(MonitorState.IDLE)

    # ------------------------------------------------------------------ construction
    def _build(self, user_name: str, user_role: str, patient_name: str | None, risk_level: str | None) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.topbar = Topbar(self.SECTION, user_name, user_role)
        self.topbar.sign_out_clicked.connect(self._request_sign_out)
        layout.addWidget(self.topbar)

        body = QWidget()
        body.setAutoFillBackground(True)      # N50 canvas (palette Window)
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(Space.S6, Space.S4, Space.S6, Space.S6)
        body_layout.setSpacing(Space.S4)
        layout.addWidget(body, 1)

        # Top: the session card (patient, camera, status, duration), a card like the panels below it.
        self.context_bar = self._make_context_bar(patient_name, risk_level)
        body_layout.addWidget(self.context_bar)      # full width, aligned with the panels below

        panels = QHBoxLayout()
        panels.setContentsMargins(0, 0, 0, 0)
        panels.setSpacing(Space.S4)
        body_layout.addLayout(panels, 1)

        # Left: the video, the full height of the body, so its stage stays close to the image's shape.
        self.video_panel = VideoPanel(can_analyse_files=self.CAN_ANALYSE_FILES)
        panels.addWidget(self.video_panel, 1)

        # Right: pose analysis for administrators, then the event log, which takes the rest.
        self.side = _SideColumn()
        self.side.setFixedWidth(SIDE_MIN)
        side_layout = QVBoxLayout(self.side)
        side_layout.setContentsMargins(0, 0, 0, 0)
        side_layout.setSpacing(Space.S4)
        self._build_side_panels(side_layout)
        self.event_log = EventLogPanel(self._settings)
        side_layout.addWidget(self.event_log, 1)
        panels.addWidget(self.side, 0)

        self.video_panel.start_clicked.connect(self._start_camera)
        self.video_panel.stop_clicked.connect(self._request_stop)
        self.video_panel.retry_clicked.connect(self._retry)
        self.video_panel.source_combo.currentIndexChanged.connect(self._refresh_source)
        self.context_bar.acknowledge_clicked.connect(self._acknowledge_alert)

    def _make_context_bar(self, patient_name: str | None, risk_level: str | None) -> ContextBar:
        """Hook: AdminView shows its test-profile selector instead of the patient."""
        return ContextBar(patient_name, risk_level)

    def _build_side_panels(self, layout: QVBoxLayout) -> None:
        """Hook: AdminView adds the pose analysis panel above the event log."""

    def _connect_extras(self) -> None:
        """Hook for AdminView's extra actions."""

    def _shortcut(self, keys: tuple[str, ...], slot) -> QAction:
        action = QAction(self)
        action.setShortcuts([QKeySequence(key) for key in keys])
        action.setShortcutContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        action.triggered.connect(slot)
        self.addAction(action)
        return action

    # ------------------------------------------------------------------ contract
    @Slot(QImage)
    def update_video_frame(self, qimage: QImage) -> None:
        """Shows a processed frame; the first one of a run switches the state to LIVE.

        Args:
            qimage: The frame with the person box and skeleton drawn on it.
        """
        if self._state in STOPPED:
            return       # frames that arrive after the run ended
        if self._state == MonitorState.STARTING:
            self._elapsed.start()      # the duration counts from the first frame, not from loading the models
            self._set_state(MonitorState.LIVE)
        self.video_panel.show_frame(qimage)

    @Slot()
    def clear_video(self) -> None:
        """Removes the image; the state (and the ERROR / FINISHED placeholder) stays until the next start."""
        self.video_panel.clear_frame()

    @Slot(bool)
    def set_monitoring_state(self, active: bool) -> None:
        """Starts a run (STARTING) or ends it (ERROR, FINISHED or IDLE).

        A camera that ends without Stop being pressed is reported as an error.

        Args:
            active: True when the controller started a source, False when it ended.
        """
        if active:
            self._run_error = None
            self._stopped_by_user = False
            self._run_started = True
            self._frozen_ms = None
            self._elapsed.invalidate()      # started by the first frame
            self.video_panel.set_run_error(None)
            self.video_panel.set_source(self._source)
            self._set_state(MonitorState.STARTING)
            return
        if self._state not in RUNNING:
            return
        self._freeze_duration()
        camera = self._source is not None and self._source.kind == "camera"
        if self._run_error is None and camera and not self._stopped_by_user:
            # A camera never ends on its own: if nobody pressed Stop, it was unplugged or stopped
            # delivering frames. Say so instead of looking like a normal stop.
            self._run_error = Monitor.CAMERA_LOST
            self.video_panel.set_run_error(self._run_error)
            self._add_event("ERROR", self._run_error)
            QApplication.alert(self.window(), 0)
        if self._run_error is not None:
            state = MonitorState.ERROR
        elif self._source is not None and self._source.kind == "file" and not self._stopped_by_user:
            state = MonitorState.FINISHED
        else:
            state = MonitorState.IDLE
        self._set_state(state)

    @Slot()
    def set_stopping(self) -> None:
        """Shows that the source is stopping (the user pressed Stop)."""
        if self._state not in RUNNING:
            return
        self._stopped_by_user = True
        self._freeze_duration()
        self._set_state(MonitorState.STOPPING)

    @Slot(str)
    def trigger_fall_alert(self, message: str) -> None:
        """Raises the fall alert: log entry, red session card, pulse and taskbar flash.

        Args:
            message: Description for the log, e.g. "Fall detected (87%)".
        """
        now = QTime.currentTime()
        self._add_event("ALERT", message, now)
        self._alert_count = self._alert_count + 1 if self._alert_active else 1
        self.context_bar.set_alert(True, self._alert_count)
        if not self._alert_active:
            self._alert_active = True
            self.pulse.start()
            self._ack_action.setEnabled(True)
        QApplication.alert(self.window(), 0)      # flashes the taskbar button; no sound

    @Slot(str, str)
    def log_event(self, event_type: str, message: str) -> None:
        """Adds the event to the log. Source errors also switch the stage to its error state."""
        kind = (event_type or "INFO").upper()
        self._add_event(kind, message)
        if kind == "ERROR":
            self._run_error = message
            self.video_panel.set_run_error(message)

    # ------------------------------------------------------------------ state
    def state(self) -> MonitorState:
        """Returns the current monitoring state."""
        return self._state

    def _set_state(self, state: MonitorState) -> None:
        self._state = state
        self._refresh_duration()
        self.context_bar.set_state(state)
        self._refresh_source()
        self.video_panel.set_state(state)
        for component in self._stateful:
            component.set_state(state)
        if state == MonitorState.LIVE:
            self._duration_timer.start()
        else:
            self._duration_timer.stop()

    @Slot()
    def _refresh_source(self, *_args) -> None:
        """The strip shows the running (or last) source; while stopped, the camera picked below."""
        source = self._source
        if source is None or self._state == MonitorState.IDLE:
            index = self.video_panel.camera_index()
            source = SourceInfo("camera", Monitor.CAMERA_LABEL.format(index=index), index)
        if source.kind == "file":
            self.context_bar.set_source(source.label, Monitor.FILE_SPEC, camera=False)
        else:
            self.context_bar.set_source(source.label, self._camera_spec, self._camera_tip)

    def _set_camera_profile(self, spec: str, tip: str) -> None:
        """Changes the camera settings shown in the strip (AdminView's test profile)."""
        self._camera_spec, self._camera_tip = spec, tip
        self._refresh_source()

    def _freeze_duration(self) -> None:
        if self._frozen_ms is None:
            live = self._state != MonitorState.STARTING and self._elapsed.isValid()
            self._frozen_ms = self._elapsed.elapsed() if live else 0      # stopped before the first frame: 0
        self._refresh_duration()

    @Slot()
    def _refresh_duration(self) -> None:
        if not self._run_started:
            text = None
        elif self._frozen_ms is not None:
            text = format_duration(self._frozen_ms)
        elif self._state == MonitorState.STARTING:
            text = format_duration(0)
        else:
            text = format_duration(self._elapsed.elapsed())
        self.context_bar.set_duration(text)
        self.video_panel.set_duration(text or "")

    def _add_event(self, kind: str, message: str, when: QTime | None = None) -> None:
        self.event_log.add_event(kind, message, when)

    # ------------------------------------------------------------------ user actions
    def _start(self, source: SourceInfo) -> None:
        if self._state in RUNNING:
            return
        self._source = source       # before emitting: the controller answers synchronously
        self._last_start = source
        if source.kind == "file":
            self.upload_requested.emit(str(source.arg))
        else:
            self.start_requested.emit(int(source.arg))

    @Slot(int)
    def _start_camera(self, index: int) -> None:
        self._start(SourceInfo("camera", Monitor.CAMERA_LABEL.format(index=index), index))

    @Slot()
    def _request_stop(self) -> None:
        if self._state in (MonitorState.STARTING, MonitorState.LIVE):
            self.stop_requested.emit()

    @Slot()
    def _retry(self) -> None:
        if self._last_start is not None:
            self._start(self._last_start)

    @Slot()
    def _toggle_monitoring(self) -> None:
        if self._state in STOPPED:
            self._start_camera(self.video_panel.camera_index())
        else:
            self._request_stop()

    @Slot()
    def _acknowledge_alert(self) -> None:
        if not self._alert_active:
            return
        self._alert_active = False
        self._ack_action.setEnabled(False)
        self._alert_count = 0
        self.pulse.stop()
        self.context_bar.set_alert(False)
        self._add_event("INFO", Monitor.ALERT_ACKNOWLEDGED)

    @Slot(float)
    def _on_pulse(self, phase: float) -> None:
        self.context_bar.set_pulse_phase(phase)

    @Slot()
    def _request_sign_out(self) -> None:
        if self._signing_out:
            return
        if self._state in RUNNING and not ConfirmDialog.ask(
                self, Monitor.CONFIRM_SIGN_OUT_TITLE, Monitor.CONFIRM_SIGN_OUT_BODY,
                Monitor.CONFIRM_SIGN_OUT_ACTION, destructive=True):
            return
        self._signing_out = True
        self.logout_requested.emit()

    # ------------------------------------------------------------------ events
    def resizeEvent(self, event) -> None:
        """Keeps the side column at 27 % of the width, between 380 and 480 px."""
        super().resizeEvent(event)
        width = max(SIDE_MIN, min(SIDE_MAX, round(self.width() * SIDE_SHARE)))
        if width != self.side.width():
            self.side.setFixedWidth(width)

    def showEvent(self, event) -> None:
        """Closes the sign-in toasts and takes the keyboard focus for the shortcuts."""
        super().showEvent(event)
        if not event.spontaneous():
            # The monitoring screen shows no toasts: the sign-in one ("Signed in · Opening your
            # dashboard…") has done its job once the dashboard is here.
            ToastHost.for_widget(self).dismiss_all()
            self.setFocus(Qt.FocusReason.OtherFocusReason)
