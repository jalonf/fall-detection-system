"""Monitoring page of caregivers and medical staff: the shared monitoring page with a patient selector.

The session card starts with the patient selector. The chosen patient's risk level sets the camera
settings and the fall model of the next run. While a monitoring runs the selector is locked, so the
patient being monitored cannot change.

The page does not know where the patients come from: the dashboard (`CaregiverDashboardView`) hands it
the list shown on the Patients page through `set_patients`.

Contract, on top of BaseMonitorView's: `selected_patient_id()` (read by the controller when the camera
starts) and `set_patients(list)`.
"""

from __future__ import annotations

from PySide6.QtCore import Slot

from src.dtos.patient_summary import PatientSummary
from src.views.base_monitor_view import BaseMonitorView, camera_profile
from src.views.components.common.badge import Badge, risk_badge
from src.views.components.common.inputs import Combo
from src.views.components.monitor.context_bar import ContextBar
from src.views.monitor_state import RUNNING, MonitorState
from src.views.strings import Monitor

SETTINGS_PATIENT = "monitor/patient"
_PATIENT_COMBO_WIDTH = 220


class MonitorView(BaseMonitorView):
    """Monitoring page of caregivers and medical staff (see the module docstring)."""

    CAN_ANALYSE_FILES = False

    # ------------------------------------------------------------------ construction
    def _make_context_bar(self) -> ContextBar:
        self._levels: dict[int, str] = {}
        self.patient_combo = Combo(size="sm", width=_PATIENT_COMBO_WIDTH, accessible_name=Monitor.PATIENT_COMBO)
        self.patient_combo.setToolTip(Monitor.PATIENT_COMBO_TIP)
        self.risk_badge = Badge("", "neutral")
        return ContextBar(Monitor.STRIP_PATIENT, self.patient_combo, self.risk_badge)

    def _connect_extras(self) -> None:
        self.patient_combo.currentIndexChanged.connect(self._on_patient_chosen)
        self.set_patients([])

    # ------------------------------------------------------------------ state
    def _set_state(self, state: MonitorState) -> None:
        super()._set_state(state)
        self._refresh_lock()

    def _refresh_lock(self) -> None:
        """The selector only changes with patients to choose from and no monitoring running."""
        self.patient_combo.setEnabled(self.has_patients() and self.state() not in RUNNING)

    # ------------------------------------------------------------------ patients
    def selected_patient_id(self) -> int | None:
        """Id of the patient the next run monitors, or None when there are none."""
        return self.patient_combo.currentData()

    def has_patients(self) -> bool:
        """True when there is at least one patient to monitor."""
        return self.patient_combo.count() > 0

    @Slot(list)
    def set_patients(self, patients: list[PatientSummary]) -> None:
        """Refills the selector, keeping the chosen patient (or the one chosen last time) if still there.

        Args:
            patients: The caregiver's patients, oldest first.
        """
        current = self.patient_combo.currentData()
        wanted = current if current is not None else self._settings.value(SETTINGS_PATIENT, None, int)
        self.patient_combo.blockSignals(True)
        self.patient_combo.clear()
        for patient in patients:
            self.patient_combo.addItem(patient.name, patient.id)
        index = self.patient_combo.findData(wanted) if wanted is not None else -1
        self.patient_combo.setCurrentIndex(index if index >= 0 else 0 if patients else -1)
        self.patient_combo.blockSignals(False)
        self._levels = {patient.id: patient.risk_level for patient in patients}
        self._refresh_lock()
        self._on_patient_chosen()

    @Slot()
    def _on_patient_chosen(self, *_args) -> None:
        """Shows the chosen patient's risk badge and camera settings, and remembers the choice."""
        patient_id = self.patient_combo.currentData()
        level = self._levels.get(patient_id) if patient_id is not None else None
        if level is not None:
            self.risk_badge.set_badge(*risk_badge(level))
            self._settings.setValue(SETTINGS_PATIENT, patient_id)
        self.risk_badge.setVisible(level is not None)
        self._set_camera_profile(*camera_profile(level))
