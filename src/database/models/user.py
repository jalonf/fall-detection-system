import datetime

from peewee import CharField, DateTimeField

from src.database.models.base_model import BaseModel


class User(BaseModel):
    """Model for the users table."""
    name = CharField()
    email = CharField(unique=True) 
    phone = CharField(null=True)
    password = CharField()
    role = CharField()
    created_at = DateTimeField(default=datetime.datetime.now)