"""Base class of the Peewee models."""

from peewee import Model

from src.database.connection import db


class BaseModel(Model):
    """Base class that assigns the database to all models."""
    class Meta:
        """Peewee options: every model is stored in the application's database."""
        database = db