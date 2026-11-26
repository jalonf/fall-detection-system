"""Base class of the Peewee models."""

from peewee import AutoField, Model

from src.database.connection import db


class BaseModel(Model):
    """Base class that assigns the database to all models."""

    id = AutoField()      # the primary key Peewee would add anyway, declared so type checkers see it

    class Meta:
        """Peewee options: every model is stored in the application's database."""
        database = db