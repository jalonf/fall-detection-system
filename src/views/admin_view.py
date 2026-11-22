"""Administration screen: everything in the monitoring screen, plus video-file analysis and the
pose analysis panel (`skeleton_panel`, fed directly by `AdminController`)."""

from __future__ import annotations

import os

from PySide6.QtCore import Slot
from PySide6.QtWidgets import QVBoxLayout

from src.views.base_monitor_view import BaseMonitorView, SourceInfo
from src.views.components.monitor.skeleton_panel import SkeletonPanel
from src.views.strings import Monitor


class AdminView(BaseMonitorView):
    SECTION = Monitor.SECTION_ADMIN
    CAN_ANALYSE_FILES = True

    def _build_below_video(self, layout: QVBoxLayout) -> None:
        self.skeleton_panel = SkeletonPanel()
        layout.addWidget(self.skeleton_panel)
        self._stateful.append(self.skeleton_panel)

    def _connect_extras(self) -> None:
        self.video_panel.file_chosen.connect(self._start_file)
        self._shortcut(("Ctrl+O",), self.video_panel.choose_file)

    @Slot(str)
    def _start_file(self, path: str) -> None:
        self._start(SourceInfo("file", os.path.basename(path), path))
