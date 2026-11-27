"""Monitoring page of the administration screen, for the application's testers.

Administrators have no patient. In the context strip, where the patient would be, they choose a test
profile: the camera settings and fall model of a risk level. Everything runs in test mode
(`AdminController`): falls are shown and logged, but never stored or e-mailed. The screen also analyses
video files and shows the pose analysis panel (`skeleton_panel`, fed directly by `AdminController`).
The top bar around it belongs to the dashboard (`AdminDashboardView`).

Contract, on top of BaseMonitorView's: the signal `upload_requested(str)` (a video file to analyse),
`test_profile()`, the chosen risk level ("LOW", "MEDIUM" or "HIGH") the controller reads when the
camera starts, and `show_pose(skeleton, telemetry)` for every processed frame.
"""

from __future__ import annotations

import os

from PySide6.QtCore import Signal, Slot
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QVBoxLayout

from src.domain.monitoring_profiles import RISK_LEVELS, strategy_for
from src.dtos.telemetry import Telemetry
from src.strings import Monitor, risk_level_label
from src.views.base_monitor_view import BaseMonitorView, SourceInfo, camera_spec
from src.views.components.common.badge import Badge
from src.views.components.common.inputs import Combo
from src.views.components.common.shortcuts import add_shortcut
from src.views.components.monitor.context_bar import ContextBar
from src.views.components.monitor.skeleton_panel import SkeletonPanel
from src.views.monitor_state import RUNNING

SETTINGS_TEST_PROFILE = "admin/test_profile"
DEFAULT_TEST_PROFILE = "HIGH"      # the strictest profile, as for a patient whose level is unknown


class _ProfileCombo(Combo):
    """The test-profile selector: locked while a run is going, like the camera selector."""

    def set_state(self, state: str) -> None:
        self.setEnabled(state not in RUNNING)


class AdminView(BaseMonitorView):
    """Monitoring page of the administrators (testers), in test mode.

    Signals:
        upload_requested(str): Analyse the video file at this path.
    """
    upload_requested = Signal(str)

    CAN_ANALYSE_FILES = True

    # ------------------------------------------------------------------ contract
    def test_profile(self) -> str:
        """Risk level whose camera settings and model the next camera run uses."""
        return RISK_LEVELS[self.profile_combo.currentIndex()]

    def show_pose(self, skeleton: QImage, telemetry: Telemetry) -> None:
        """Shows the pose analysis of a processed frame (the skeleton image and the telemetry)."""
        self.skeleton_panel.update_frame(skeleton)
        self.skeleton_panel.update_telemetry(telemetry)

    # ------------------------------------------------------------------ construction
    def _make_context_bar(self) -> ContextBar:
        self.profile_combo = _ProfileCombo([Monitor.TEST_PROFILES[level] for level in RISK_LEVELS], size="sm",
                                           width=136, accessible_name=Monitor.TEST_PROFILE_COMBO)
        self.profile_combo.setToolTip(Monitor.TEST_PROFILE_TIP)
        saved = str(self._settings.value(SETTINGS_TEST_PROFILE, DEFAULT_TEST_PROFILE))
        self.profile_combo.setCurrentIndex(RISK_LEVELS.index(saved if saved in RISK_LEVELS else DEFAULT_TEST_PROFILE))
        self._stateful.append(self.profile_combo)
        test_badge = Badge(Monitor.TEST_MODE_BADGE, "info")
        test_badge.setToolTip(Monitor.TEST_MODE_TIP)
        return ContextBar(Monitor.STRIP_TEST_PROFILE, self.profile_combo, test_badge)

    def _build_side_panels(self, layout: QVBoxLayout) -> None:
        self.skeleton_panel = SkeletonPanel()
        layout.addWidget(self.skeleton_panel)
        self._stateful.append(self.skeleton_panel)

    def _connect_extras(self) -> None:
        self.video_panel.file_chosen.connect(self._start_file)
        add_shortcut(self, ("Ctrl+O",), self.video_panel.choose_file)
        self.profile_combo.currentIndexChanged.connect(self._on_test_profile_changed)
        self._show_test_profile()

    # ------------------------------------------------------------------ test profile
    @Slot(int)
    def _on_test_profile_changed(self, _index: int) -> None:
        self._settings.setValue(SETTINGS_TEST_PROFILE, self.test_profile())
        self._show_test_profile()

    def _show_test_profile(self) -> None:
        """The strip shows the resolution and frame rate the chosen profile opens the camera with."""
        level = self.test_profile()
        self._set_camera_profile(camera_spec(strategy_for(level)), Monitor.CAMERA_SPEC_TEST_TIP.format(level=risk_level_label(level)))

    # ------------------------------------------------------------------ user actions
    @Slot(str)
    def _start_file(self, path: str) -> None:
        self._start(SourceInfo("file", os.path.basename(path), path))

    def _request_source(self, source: SourceInfo) -> None:
        if source.kind == "file":
            self.upload_requested.emit(str(source.arg))
        else:
            super()._request_source(source)
