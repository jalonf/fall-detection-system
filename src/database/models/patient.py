import datetime

from peewee import CharField, DateTimeField, ForeignKeyField, TextField, Model
from src.database.core.database_manager import db
from src.database.models.user import User
class BaseModel(Model):
    """Base class that assigns the database to all models."""
    class Meta:
        database = db

class Patient(BaseModel):
    """Model for the patient table"""
    caregiver_id = ForeignKeyField(User, backref="patients", on_delete="CASCADE")
    name = CharField()
    medical_notes = TextField()
    created_at = DateTimeField(default=datetime.datetime.now)