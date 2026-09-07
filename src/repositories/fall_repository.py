import logging

from src.database.models.fall_event import FallEvent

logger = logging.getLogger(__name__)


class FallRepository:
    """Handles all database operations for fall events and inference logs."""

    def create_fall_event(self, patient, prediction_probability, notification_sent=False, snapshot_path=None):
        """Saves a new fall event record linked to a patient."""
        try:
            logger.info("Attempting to create fall event for patient ID: %s with probability: %s", patient.id, prediction_probability)
            
            fall_event = FallEvent.create(
                patient_id=patient,
                prediction_probability=prediction_probability,
                notification_sent=notification_sent,
                snapshot_path=snapshot_path
            )
            logger.info("Fall event successfully created")
            return fall_event
        except Exception as e:  # noqa: BLE001
            logger.error("Could not create fall event for patient ID %s: %s", patient.id, e)
            return None

    def get_falls_by_patient(self, patient_id):
        """Retrieves all fall event records associated with a specific patient."""
        logger.debug("Querying fall events for patient ID: %s", patient_id)
        falls = list(FallEvent.select().where(FallEvent.patient_id == patient_id).order_by(FallEvent.timestamp.desc()))
        return falls