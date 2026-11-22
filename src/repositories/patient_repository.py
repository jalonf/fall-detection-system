"""Database access for patients."""

import logging

from src.database.models.patient import Patient

logger = logging.getLogger(__name__)


class PatientRepository:
    """Handles all database operations for the patients (1:1 current, ready for 1:N)."""

    def create_patient(self, user, name, risk_level, medical_notes=None):
        """Saves a new patient linked to the caregiver."""
        try:
            logger.info("Attempting to create new patient with name: %s", name)
            notes = medical_notes.strip() if medical_notes else None
            
            patient = Patient.create(
                caregiver_id=user,
                name=name,
                medical_notes=notes,
                risk_level=risk_level
            )
            logger.info("Patient successfully created with name: %s", patient.name)
            return patient
        except Exception as e:  # noqa: BLE001
            logger.error("Could not create patient with name %s: %s", name, e)
            return None

    def get_patient_by_caregiver(self, caregiver_id):
        """Returns the patient of a caregiver, or None.

        There is one patient per caregiver today (1:1), so the first match is returned; this is
        the place to change when a caregiver can have several patients (1:N).

        Args:
            caregiver_id: The caregiver (a User or its id).
        """
        logger.debug("Querying patient for caregiver ID: %s", caregiver_id)
        patient = Patient.select().where(Patient.caregiver_id == caregiver_id).first()
        if patient is None:
            logger.debug("No patient found for caregiver ID: %s", caregiver_id)
        return patient
