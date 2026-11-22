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
    QEvent,
    QSettings,
    QSize,
    Qt,
    QTime,
    QTimer,
    Signal,
    Slot,
)
from PySide6.QtGui import QAction, QImage, QKeySequence
from PySide6.QtWidgets import QApplication, QHBoxLayout, QSplitter, QVBoxLayout, QWidget

from src.views.components.common.confirm_dialog import ConfirmDialog
from src.views.components.common.painting import transparent_scroll_area
from src.views.components.common.toast import ToastHost
from src.views.components.monitor.alert_pulse import AlertPulse
from src.views.components.monitor.context_bar import ContextBar
from src.views.components.monitor.event_log import EventLogPanel
from src.views.components.monitor.session_panel import SessionPanel
from src.views.components.monitor.topbar import Topbar
from src.views.components.monitor.video_panel import VideoPanel
from src.views.strings import Monitor, Toasts, toast_rule_for
from src.views.theme import Space

TOAST_TOP_INSET = 108            # below the top bar (56) and the context bar (40), plus 12
SETTINGS_LOG_HEIGHT = "monitor/log_height"
_HANDLE = 8


class MonitorState(StrEnum):
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
    kind: str           # "camera" | "file"
    label: str          # what the interface shows: "Camera 0", "clip.mp4"
    arg: int | str      # camera index or file path, re-sent by "Try again"


def format_duration(milliseconds: int) -> str:
    seconds = max(0, milliseconds) // 1000
    return f"{seconds // 3600:02d}:{seconds // 60 % 60:02d}:{seconds % 60:02d}"


class _SideColumn(QWidget):
    """Holder of the side scroll area: 320-400 px wide, 352 preferred."""

    def sizeHint(self) -> QSize:
        return QSize(352, 400)


class BaseMonitorView(QWidget):
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
        self._signing_out = False
        self._falls = 0
        self._events = 0
        self._elapsed = QElapsedTimer()
        self._frozen_ms: int | None = None
        self._run_started = False
        self._error_toast = None
        self._settings = QSettings("FallSense", "FallSense")
        self._splitter_ready = False
        self._stateful: list = []

        self._build(user_name, user_role, patient_name, risk_level)

        self._duration_timer = QTimer(self)
        self._duration_timer.setInterval(1000)
        self._duration_timer.timeout.connect(self._refresh_duration)
        self.pulse = AlertPulse(self)
        self.pulse.phase_changed.connect(self._on_pulse)

        self._toggle_action = self._shortcut(("Ctrl+Return", "Ctrl+Enter"), self._toggle_monitoring)
        self._ack_action = self._shortcut(("Esc",), self._acknowledge_alert)
        self._ack_action.setEnabled(False)
        self._shortcut(("Ctrl+L",), self.event_log.focus_table)
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
        self.context_bar = ContextBar(patient_name, risk_level)
        layout.addWidget(self.context_bar)

        body = QWidget()
        body.setAutoFillBackground(True)      # N50 canvas (palette Window)
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(Space.S6, Space.S4, Space.S6, Space.S6)
        body_layout.setSpacing(Space.S4)
        layout.addWidget(body, 1)

        self.splitter = QSplitter(Qt.Orientation.Vertical)
        self.splitter.setHandleWidth(_HANDLE)
        self.splitter.setChildrenCollapsible(False)
        self.video_panel = VideoPanel(can_analyse_files=self.CAN_ANALYSE_FILES)
        self.event_log = EventLogPanel(self._settings)
        self.splitter.addWidget(self.video_panel)
        self.splitter.addWidget(self.event_log)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 0)
        self.splitter.splitterMoved.connect(self._on_splitter_moved)
        self.splitter.installEventFilter(self)
        body_layout.addWidget(self.splitter, 1)

        side = QWidget()
        side_layout = QVBoxLayout(side)
        side_layout.setContentsMargins(0, 0, 0, 0)
        side_layout.setSpacing(Space.S4)
        self._build_side_panels(side_layout)
        side_layout.addStretch(1)
        self.side_area = transparent_scroll_area(side)
        holder = _SideColumn()
        holder.setMinimumWidth(320)
        holder.setMaximumWidth(400)
        holder_layout = QVBoxLayout(holder)
        holder_layout.setContentsMargins(0, 0, 0, 0)
        holder_layout.addWidget(self.side_area)
        body_layout.addWidget(holder, 0)

        self.video_panel.start_clicked.connect(self._start_camera)
        self.video_panel.stop_clicked.connect(self._request_stop)
        self.video_panel.retry_clicked.connect(self._retry)
        self.video_panel.stage.banner.acknowledged.connect(self._acknowledge_alert)

    def _build_side_panels(self, layout: QVBoxLayout) -> None:
        """Hook: AdminView adds the pose analysis panel before the session panel."""
        self.session_panel = SessionPanel()
        layout.addWidget(self.session_panel)

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
        if self._state in STOPPED:
            return       # frames that arrive after the run ended
        if self._state == MonitorState.STARTING:
            self._set_state(MonitorState.LIVE)
        self.video_panel.show_frame(qimage)

    @Slot()
    def clear_video(self) -> None:
        """Removes the image; the state (and the ERROR / FINISHED placeholder) stays until the next start."""
        self.video_panel.clear_frame()

    @Slot(bool)
    def set_monitoring_state(self, active: bool) -> None:
        if active:
            self._run_error = None
            self._stopped_by_user = False
            self._run_started = True
            self._frozen_ms = None
            self._elapsed.start()
            self._dismiss_error_toast()
            self.video_panel.set_run_error(None)
            self.video_panel.set_source(self._source)
            self.context_bar.set_source(self._source.label if self._source else None)
            self.session_panel.set_source(self._source.label if self._source else None)
            self.session_panel.set_started(QTime.currentTime())
            self._set_state(MonitorState.STARTING)
            return
        if self._state not in RUNNING:
            return
        self._freeze_duration()
        if self._run_error is not None:
            state = MonitorState.ERROR
        elif self._source is not None and self._source.kind == "file" and not self._stopped_by_user:
            state = MonitorState.FINISHED
        else:
            state = MonitorState.IDLE
        self._set_state(state)

    @Slot()
    def set_stopping(self) -> None:
        if self._state not in RUNNING:
            return
        self._stopped_by_user = True
        self._freeze_duration()
        self._set_state(MonitorState.STOPPING)

    @Slot(str)
    def trigger_fall_alert(self, message: str) -> None:
        now = QTime.currentTime()
        self._falls += 1
        self.session_panel.set_falls(self._falls)
        self._add_event("ALERT", message, now)
        self.video_panel.show_alert(message, now)
        if not self._alert_active:
            self._alert_active = True
            self.context_bar.set_alert(True)
            self.pulse.start()
            self._ack_action.setEnabled(True)
        QApplication.alert(self.window(), 0)
        QApplication.beep()

    @Slot(str, str)
    def log_event(self, event_type: str, message: str) -> None:
        kind = (event_type or "INFO").upper()
        self._add_event(kind, message)
        label = self._source.label if self._source is not None else ""
        if kind == "ERROR":
            self._run_error = message
            self.video_panel.set_run_error(message)
            rule = toast_rule_for("ERROR", message)
            self._dismiss_error_toast()
            self._error_toast = ToastHost.for_widget(self).notify(
                rule.kind, rule.message.format(text=message), title=rule.title, duration_ms=0)
            return
        rule = toast_rule_for(kind, message)
        if rule is None:
            return     # the rest only goes to the log
        title = rule.title
        if rule.key == "Stream disconnected":
            if self._state == MonitorState.ERROR:
                return
            if self._state == MonitorState.FINISHED:
                title = Toasts.FINISHED_TITLE
        ToastHost.for_widget(self).notify(rule.kind, rule.message.format(source=label, text=message), title=title,
                                          duration_ms=0 if rule.persistent else None)

    # ------------------------------------------------------------------ state
    def state(self) -> MonitorState:
        return self._state

    def _set_state(self, state: MonitorState) -> None:
        self._state = state
        self._refresh_duration()
        self.context_bar.set_state(state)
        self.video_panel.set_state(state)
        for component in self._stateful:
            component.set_state(state)
        if state == MonitorState.LIVE:
            self._duration_timer.start()
        else:
            self._duration_timer.stop()

    def _freeze_duration(self) -> None:
        if self._frozen_ms is None and self._elapsed.isValid():
            self._frozen_ms = self._elapsed.elapsed()
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
        self.session_panel.set_duration(text)
        self.video_panel.set_duration(text or "")

    def _add_event(self, kind: str, message: str, when: QTime | None = None) -> None:
        self.event_log.add_event(kind, message, when)
        self._events += 1
        self.session_panel.set_events(self._events)

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
        self.pulse.stop()
        self.video_panel.clear_alert()
        self.context_bar.set_alert(False)
        self._add_event("INFO", Monitor.ALERT_ACKNOWLEDGED)

    @Slot(float)
    def _on_pulse(self, phase: float) -> None:
        self.video_panel.set_pulse_phase(phase)
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

    def _dismiss_error_toast(self) -> None:
        if self._error_toast is not None:
            ToastHost.for_widget(self).dismiss(self._error_toast)
            self._error_toast = None

    # ------------------------------------------------------------------ splitter
    def eventFilter(self, watched, event) -> bool:
        if watched is self.splitter and event.type() == QEvent.Type.Resize and not self._splitter_ready:
            height = self.splitter.height()
            if height > 0:
                self._splitter_ready = True
                saved = self._settings.value(SETTINGS_LOG_HEIGHT)
                try:
                    log_height = int(saved) if saved is not None else 0
                except (TypeError, ValueError):
                    log_height = 0
                if log_height <= 0:
                    log_height = max(176, min(280, round(height * 0.28)))
                log_height = min(log_height, max(176, height - _HANDLE - self.video_panel.minimumHeight()))
                self.splitter.setSizes([height - _HANDLE - log_height, log_height])
        return False

    @Slot(int, int)
    def _on_splitter_moved(self, _position: int, _index: int) -> None:
        self._settings.setValue(SETTINGS_LOG_HEIGHT, self.splitter.sizes()[1])

    # ------------------------------------------------------------------ events
    def showEvent(self, event) -> None:
        super().showEvent(event)
        if not event.spontaneous():
            ToastHost.for_widget(self).set_top_inset(TOAST_TOP_INSET)
            self.setFocus(Qt.FocusReason.OtherFocusReason)

    def hideEvent(self, event) -> None:
        super().hideEvent(event)
        if not event.spontaneous():
            self._dismiss_error_toast()
