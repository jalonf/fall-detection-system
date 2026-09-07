
from peewee import Model

from src.database.core.database_manager import db


class BaseModel(Model):
    """Base class that assigns the database to all models."""
    class Meta:
        database = db