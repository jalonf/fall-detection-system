"""Database access for patients."""

import logging
from collections.abc import Iterable
from typing import Any, cast

from peewee import JOIN, fn

from src.database.connection import db
from src.database.models.fall_event import FallEvent
from src.database.models.patient import Patient
from src.dtos.patient_summary import PatientSummary

logger = logging.getLogger(__name__)


class PatientRepository:
    """Handles all database operations for the patients. A caregiver can have any number of them (1:N).

    Every query that takes a patient id also takes the caregiver, so a caregiver can only read or
    delete their own patients.
    """

    def create_patient(self, caregiver, name, risk_level, medical_notes=None):
        """Saves a new patient linked to the caregiver.

        Args:
            caregiver: The caregiver (a User).
            name: Full name of the patient.
            risk_level: "LOW", "MEDIUM" or "HIGH".
            medical_notes: Optional notes.

        Returns:
            The new Patient, or None if it could not be saved.
        """
        try:
            notes = medical_notes.strip() if medical_notes else None
            patient = Patient.create(caregiver_id=caregiver, name=name, medical_notes=notes, risk_level=risk_level)
            logger.info("Patient %s created", patient.id)
            return patient
        except Exception as e:  # noqa: BLE001
            logger.error("Could not create the patient: %s", e)
            return None

    def get_patient(self, patient_id, caregiver):
        """Returns one of the caregiver's patients, or None (also when it belongs to someone else).

        Args:
            patient_id: Id of the patient.
            caregiver: The caregiver (a User or its id).
        """
        return Patient.get_or_none((Patient.id == patient_id) & (Patient.caregiver_id == caregiver))

    def get_summaries(self, caregiver) -> list[PatientSummary]:
        """Returns the caregiver's patients, oldest first, with how many falls each has stored.

        One query: the falls are counted with a LEFT JOIN, so patients without falls are included.

        Args:
            caregiver: The caregiver (a User or its id).
        """
        last_fall = fn.MAX(FallEvent.timestamp).python_value(FallEvent.timestamp.python_value)
        query = (Patient
                 .select(Patient, fn.COUNT(FallEvent.id).alias("fall_count"), last_fall.alias("last_fall_at"))
                 .join(FallEvent, JOIN.LEFT_OUTER, on=(FallEvent.patient_id == Patient.id))
                 .where(Patient.caregiver_id == caregiver)
                 .group_by(Patient.id)
                 .order_by(Patient.created_at, Patient.id))
        # Plain rows: the aggregates are not Patient attributes (Peewee is untyped, hence the cast).
        rows = cast("Iterable[dict[str, Any]]", query.dicts())
        return [
            PatientSummary(
                id=row["id"],
                name=row["name"],
                risk_level=row["risk_level"],
                medical_notes=row["medical_notes"] or "",
                added_at=row["created_at"],
                fall_count=row["fall_count"],
                last_fall_at=row["last_fall_at"],
            )
            for row in rows
        ]

    def delete_patient(self, patient_id, caregiver) -> bool:
        """Deletes one of the caregiver's patients together with their stored falls.

        Args:
            patient_id: Id of the patient.
            caregiver: The caregiver (a User or its id).

        Returns:
            True if it was deleted; False if it does not exist, is not theirs, or the database failed.
        """
        patient = self.get_patient(patient_id, caregiver)
        if patient is None:
            logger.warning("Patient %s not found for this caregiver; nothing deleted", patient_id)
            return False
        try:
            with db.atomic():
                patient.delete_instance(recursive=True)    # its FallEvent rows first, then the patient
            logger.info("Patient %s deleted with their falls", patient_id)
            return True
        except Exception as e:  # noqa: BLE001
            logger.error("Could not delete patient %s: %s", patient_id, e)
            return False
