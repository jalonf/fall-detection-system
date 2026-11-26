"""Controller of the Patients page: lists, adds and deletes the caregiver's patients."""

import logging

from PySide6.QtCore import QObject, Slot

from src.ai.risk_assessor import RiskAssessor
from src.dtos.patient_form_data import PatientFormData
from src.repositories.patient_repository import PatientRepository

logger = logging.getLogger(__name__)

# Used when the risk level cannot be calculated: the strictest monitoring.
FALLBACK_RISK_LEVEL = "HIGH"


class PatientsController(QObject):
    """Handles the Patients page (`PatientsPage`) of a caregiver.

    Like the other controllers it lives in the GUI thread and answers each request synchronously.
    Each new patient's risk level is calculated here from their health questionnaire.

    Args:
        page: The Patients page whose requests it handles.
        caregiver: The signed-in caregiver; they only ever see and change their own patients.
    """

    def __init__(self, page, caregiver):
        super().__init__()
        self.page = page
        self.caregiver = caregiver
        self.patient_repo = PatientRepository()
        self.risk_assessor = RiskAssessor()
        self.page.add_requested.connect(self.add_patient)
        self.page.delete_requested.connect(self.delete_patient)

    def refresh(self) -> None:
        """Loads the caregiver's patients into the page."""
        self.page.set_patients(self.patient_repo.get_summaries(self.caregiver))

    def _assess_risk(self, answers: dict[str, float]) -> str:
        """Risk level of the patient. If it cannot be calculated, the strictest monitoring is used."""
        try:
            return self.risk_assessor.assess(answers).level
        except Exception:   # whatever the cause (missing model, bad answers), the patient is still added
            logger.exception("The risk level could not be calculated; using %s to be safe", FALLBACK_RISK_LEVEL)
            return FALLBACK_RISK_LEVEL

    @Slot(object)      # PatientFormData (a Python object, as in PatientsPage.add_requested)
    def add_patient(self, data: PatientFormData) -> None:
        """Calculates the new patient's risk level and saves them."""
        risk_level = self._assess_risk(data.risk_answers)
        patient = self.patient_repo.create_patient(self.caregiver, data.name, risk_level, data.medical_notes)
        if patient is None:
            self.page.show_error("The patient could not be saved. Please try again.")
            return
        logger.info("Patient added with risk level %s", risk_level)
        self.refresh()
        self.page.show_patient_added(patient.name, risk_level)

    @Slot(int)
    def delete_patient(self, patient_id: int) -> None:
        """Deletes one of the caregiver's patients and their stored falls."""
        patient = self.patient_repo.get_patient(patient_id, self.caregiver)
        name = patient.name if patient is not None else ""
        if not self.patient_repo.delete_patient(patient_id, self.caregiver):
            self.page.show_error("The patient could not be deleted. Please try again.")
            return
        self.refresh()
        self.page.show_patient_deleted(name)
