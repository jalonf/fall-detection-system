import datetime
from peewee import Model, CharField, DateTimeField

from src.database.core.databaseManager import db

class BaseModel(Model):
    """Base class that assigns the database to all models."""
    class Meta:
        database = db

class User(BaseModel):
    """Model for the users table."""
    name = CharField()
    email = CharField(unique=True) 
    phone = CharField(null=True)
    password = CharField()
    role = CharField()
    created_at = DateTimeField(default=datetime.datetime.now)