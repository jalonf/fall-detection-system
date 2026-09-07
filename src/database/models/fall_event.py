import datetime

from peewee import BooleanField, CharField, DateTimeField, FloatField, ForeignKeyField

from src.database.models.base_model import BaseModel
from src.database.models.patient import Patient


class FallEvent(BaseModel):
    """Model for logging model prediction and notifications."""
    patient_id = ForeignKeyField(Patient, backref="falls", on_delete="CASCADE")
    timestamp = DateTimeField(default=datetime.datetime.now)
    prediction_probability = FloatField()
    notification_sent = BooleanField(default=False)
    snapshot_path = CharField(null=True)