"""Controller of the caregivers' and medical staff's monitoring page."""

import logging

from PySide6.QtCore import Slot

from src.controllers.base_monitor_controller import BaseMonitorController
from src.repositories.patient_repository import PatientRepository

logger = logging.getLogger(__name__)


class MonitorController(BaseMonitorController):
    """Monitoring controller of caregivers and medical staff.

    It uses the shared workflow for the patient chosen in the view: the camera follows that
    patient's risk level, and each fall is stored for them and e-mailed to the user. The patient is
    read from the database when monitoring starts, not every time the selector changes. The patients
    themselves are managed by `PatientsController`, on the Patients page.

    Args:
        view: The MonitorView (monitoring page) it drives.
        current_user: The signed-in caregiver.
    """

    def __init__(self, view, current_user):
        super().__init__(view, current_user, patient=None)
        self.patient_repo = PatientRepository()

    @Slot(int)
    def start_camera(self, camera_index):
        """Starts monitoring the patient chosen in the view (never without one: nothing could be stored)."""
        if self.video_thread is None:      # the patient never changes while a monitoring runs
            patient_id = self.view.selected_patient_id()
            self.patient = None if patient_id is None else self.patient_repo.get_patient(patient_id, self.user)
        if self.patient is None:
            logger.warning("Monitoring not started: the user has no patient selected")
            return
        super().start_camera(camera_index)
