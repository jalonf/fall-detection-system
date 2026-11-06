from peewee import Model

from src.database.database_manager import db_connection


class BaseModel(Model):
    """Base class that assigns the database to all models."""
    class Meta:
        database = db_connection