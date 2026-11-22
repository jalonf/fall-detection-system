import datetime

from peewee import CharField, Check, DateTimeField

from src.database.models.base_model import BaseModel
from src.dtos.roles import ROLES, is_admin

# SQL list of the valid roles, for the table's CHECK constraint ('Family / Caregiver', 'Medical Staff', ...).
_ROLE_VALUES = ", ".join("'" + role.replace("'", "''") + "'" for role in ROLES)


class User(BaseModel):
    """Model for the users table: every account, whatever its role (see `src/dtos/roles.py`).

    The role is checked twice: here before saving, and by a CHECK constraint in tables created from
    now on, so not even a direct SQL insert can store an unknown role.
    """
    name = CharField()
    email = CharField(unique=True)
    phone = CharField(null=True)
    password = CharField()
    role = CharField(choices=[(role, role) for role in ROLES], constraints=[Check(f"role IN ({_ROLE_VALUES})")])
    created_at = DateTimeField(default=datetime.datetime.now)

    @property
    def is_admin(self) -> bool:
        return is_admin(self)

    def save(self, *args, **kwargs):
        if self.role not in ROLES:
            raise ValueError(f"Unknown user role: {self.role!r}")
        return super().save(*args, **kwargs)
