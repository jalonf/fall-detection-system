"""Live video panel: the stage (video or placeholder, with the source overlay) and the source controls."""

from __future__ import annotations

from itertools import pairwise

from PySide6.QtCore import QSize, Signal, Slot
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QFileDialog, QSizePolicy, QStackedLayout, QWidget

from src.views.components.common.button import make_button
from src.views.components.common.inputs import Combo
from src.views.components.common.panel import Panel
from src.views.components.monitor.stage_overlay import BAR, StageOverlay
from src.views.components.monitor.stage_placeholder import StagePlaceholder
from src.views.components.monitor.video_widget import VideoWidget
from src.views.strings import Monitor
from src.views.theme import Space, make_label

RUNNING = ("starting", "live", "stopping")
STOPPED = ("idle", "error", "finished")


class Stage(QWidget):
    """Full-bleed dark area. A stacked layout switches video / placeholder; the overlay is a free
    child on top. Its size hint never changes, so frames never relayout."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.video = VideoWidget()
        self.placeholder = StagePlaceholder()
        self._stack = QStackedLayout(self)
        self._stack.setContentsMargins(0, 0, 0, 0)
        self._stack.addWidget(self.video)
        self._stack.addWidget(self.placeholder)
        self._stack.setCurrentWidget(self.placeholder)
        self.overlay = StageOverlay(self)

    def sizeHint(self) -> QSize:
        return QSize(640, 360)

    def minimumSizeHint(self) -> QSize:
        return QSize(320, 180)

    def show_video(self, visible: bool) -> None:
        target = self.video if visible else self.placeholder
        if self._stack.currentWidget() is not target:
            self._stack.setCurrentWidget(target)
            self.overlay.raise_()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.overlay.setGeometry(0, 0, self.width(), BAR)   # only the top bar repaints with each frame
        self.overlay.raise_()


class VideoPanel(Panel):
    start_clicked = Signal(int)       # camera index (the position in the source combo)
    stop_clicked = Signal()
    file_chosen = Signal(str)
    retry_clicked = Signal()

    def __init__(self, *, can_analyse_files: bool, parent: QWidget | None = None):
        super().__init__(Monitor.LIVE_VIDEO, subtitle=Monitor.SUBTITLE_IDLE, flush=True, footer=True, parent=parent)
        self.setMinimumHeight(340)
        self._state = "idle"
        self._source = None
        self._error: str | None = None
        self._duration = ""

        self.stage = Stage()
        self.body_layout().addWidget(self.stage)
        self.stage.placeholder.retry_clicked.connect(self.retry_clicked)

        footer = self.footer_layout()
        footer.addWidget(make_label(Monitor.SOURCE, "body", "secondary"))
        footer.addSpacing(Space.S2)
        self.source_combo = Combo(Monitor.CAMERAS, size="md", width=200, accessible_name=Monitor.SOURCE_COMBO)
        footer.addWidget(self.source_combo)
        footer.addStretch(1)

        self.analyse_button = None
        if can_analyse_files:
            self.analyse_button = make_button(Monitor.ANALYSE_VIDEO, "secondary", "md", "upload",
                                              tooltip=Monitor.ANALYSE_VIDEO_TIP)
            self.analyse_button.clicked.connect(self.choose_file)
            footer.addWidget(self.analyse_button)
            footer.addSpacing(Space.S2)

        self.primary = make_button(Monitor.START, "primary", "md", "play", tooltip=Monitor.START_TIP)
        self.primary.reserve_width(Monitor.START, Monitor.STOP, Monitor.STOPPING)
        self.primary.setMinimumWidth(176)
        self.primary.clicked.connect(self._on_primary)
        footer.addWidget(self.primary)

        order = [self.source_combo] + ([self.analyse_button] if self.analyse_button else []) + [self.primary]
        for first, second in pairwise(order):
            self.setTabOrder(first, second)

    # ------------------------------------------------------------------ API
    def set_source(self, source) -> None:
        """`source` is a SourceInfo (kind, label, arg) or None."""
        self._source = source
        if source is not None:
            self.stage.overlay.set_source(source.kind, source.label)
            if source.kind == "camera" and isinstance(source.arg, int):
                self.source_combo.setCurrentIndex(source.arg)

    def set_run_error(self, message: str | None) -> None:
        self._error = message

    def set_duration(self, text: str) -> None:
        self._duration = text

    def set_state(self, state: str) -> None:
        self._state = state
        label = self._source.label if self._source is not None else ""
        subtitles = {
            "idle": Monitor.SUBTITLE_IDLE,
            "error": Monitor.SUBTITLE_ERROR,
            "finished": Monitor.SUBTITLE_FINISHED.format(label=label),
        }
        self.set_subtitle(subtitles.get(state, Monitor.SUBTITLE_RUNNING.format(label=label)))

        running = state in RUNNING
        self.source_combo.setEnabled(not running)
        if self.analyse_button is not None:
            self.analyse_button.setEnabled(not running)

        if state == "stopping":
            self.primary.set_loading(True, Monitor.STOPPING)
        else:
            self.primary.set_loading(False)
            if running:
                self.primary.setText(Monitor.STOP)
                self.primary.set_variant("danger")
                self.primary.set_icon_name("stop")
                self.primary.setToolTip(Monitor.STOP_TIP)
            else:
                self.primary.setText(Monitor.START)
                self.primary.set_variant("primary")
                self.primary.set_icon_name("play")
                self.primary.setToolTip(Monitor.START_TIP)

        self.stage.placeholder.show_state(state, error=self._error, label=label, duration=self._duration)
        self._refresh_stage()

    def show_frame(self, image: QImage) -> None:
        first = not self.stage.video.has_image()
        self.stage.video.set_image(image)
        if first:
            self._refresh_stage()

    def clear_frame(self) -> None:
        self.stage.video.clear()
        self._refresh_stage()

    def camera_index(self) -> int:
        return self.source_combo.currentIndex()

    @Slot()
    def choose_file(self) -> None:
        if self._state in RUNNING:
            return
        path, _ = QFileDialog.getOpenFileName(self, Monitor.FILE_DIALOG_TITLE, "", Monitor.FILE_DIALOG_FILTER)
        if path:
            self.file_chosen.emit(path)

    # ------------------------------------------------------------------ internals
    @Slot()
    def _on_primary(self) -> None:
        if self._state in STOPPED:
            self.start_clicked.emit(self.camera_index())
        elif self._state in ("starting", "live"):
            self.stop_clicked.emit()

    def _refresh_stage(self) -> None:
        has_image = self.stage.video.has_image()
        self.stage.show_video(has_image)
        self.stage.overlay.set_bar(has_image or self._state == "starting", self._state == "live")

