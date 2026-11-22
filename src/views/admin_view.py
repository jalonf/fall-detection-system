"""Administration screen, for the application's testers.

Administrators have no patient. In the context strip, where the patient would be, they choose a test
profile: the camera settings and fall model of a risk level. Everything runs in test mode
(`AdminController`): falls are shown and logged, but never stored or e-mailed. The screen also analyses
video files and shows the pose analysis panel (`skeleton_panel`, fed directly by `AdminController`).

Contract, on top of BaseMonitorView's: `test_profile()` returns the chosen risk level ("LOW", "MEDIUM"
or "HIGH"); the controller reads it when the camera starts.
"""

from __future__ import annotations

import os

from PySide6.QtCore import Slot
from PySide6.QtWidgets import QVBoxLayout, QWidget

from src.views.base_monitor_view import RUNNING, BaseMonitorView, SourceInfo
from src.views.components.common.inputs import Combo
from src.views.components.monitor.context_bar import ContextBar
from src.views.components.monitor.skeleton_panel import SkeletonPanel
from src.views.strings import Monitor
from src.workers.strategies import RISK_LEVELS, strategy_for

SETTINGS_TEST_PROFILE = "admin/test_profile"
DEFAULT_TEST_PROFILE = "HIGH"      # the strictest profile, as for a patient whose level is unknown


class _ProfileCombo(Combo):
    """The test-profile selector: locked while a run is going, like the camera selector."""

    def set_state(self, state: str) -> None:
        self.setEnabled(state not in RUNNING)


class AdminView(BaseMonitorView):
    SECTION = Monitor.SECTION_ADMIN
    CAN_ANALYSE_FILES = True

    def __init__(self, user_name: str = "", user_role: str = "", parent: QWidget | None = None):
        super().__init__(user_name, user_role, patient_name=None, risk_level=None, parent=parent)

    # ------------------------------------------------------------------ contract
    def test_profile(self) -> str:
        """Risk level whose camera settings and model the next camera run uses."""
        return RISK_LEVELS[self.profile_combo.currentIndex()]

    # ------------------------------------------------------------------ construction
    def _make_context_bar(self, patient_name: str | None, risk_level: str | None) -> ContextBar:
        self.profile_combo = _ProfileCombo([Monitor.TEST_PROFILES[level] for level in RISK_LEVELS], size="sm",
                                           width=136, accessible_name=Monitor.TEST_PROFILE_COMBO)
        self.profile_combo.setToolTip(Monitor.TEST_PROFILE_TIP)
        saved = str(self._settings.value(SETTINGS_TEST_PROFILE, DEFAULT_TEST_PROFILE))
        self.profile_combo.setCurrentIndex(RISK_LEVELS.index(saved if saved in RISK_LEVELS else DEFAULT_TEST_PROFILE))
        self._stateful.append(self.profile_combo)
        return ContextBar(None, None, profile_selector=self.profile_combo)

    def _build_side_panels(self, layout: QVBoxLayout) -> None:
        self.skeleton_panel = SkeletonPanel()
        layout.addWidget(self.skeleton_panel)
        self._stateful.append(self.skeleton_panel)

    def _connect_extras(self) -> None:
        self.video_panel.file_chosen.connect(self._start_file)
        self._shortcut(("Ctrl+O",), self.video_panel.choose_file)
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
        strategy = strategy_for(level)
        spec = Monitor.CAMERA_SPEC.format(width=strategy.width, height=strategy.height, fps=strategy.fps)
        self._set_camera_profile(spec, Monitor.CAMERA_SPEC_TEST_TIP.format(level=level))

    # ------------------------------------------------------------------ user actions
    @Slot(str)
    def _start_file(self, path: str) -> None:
        self._start(SourceInfo("file", os.path.basename(path), path))
