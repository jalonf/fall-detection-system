import datetime

from peewee import CharField, DateTimeField, ForeignKeyField, TextField

from src.database.models.base_model import BaseModel
from src.database.models.user import User


class Patient(BaseModel):
    """Model for the patient table"""
    caregiver_id = ForeignKeyField(User, backref="patients", on_delete="CASCADE")
    name = CharField()
    medical_notes = TextField()
    created_at = DateTimeField(default=datetime.datetime.now)