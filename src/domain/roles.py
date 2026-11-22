"""User roles (role-based access: one users table, one role per account).

Every account, administrators included, is a row of the `user` table: they all sign in the same way and
share the e-mail uniqueness and the password hashing. What changes with the role is the screen and what
the account may do. The table only accepts the roles below (see `User.role`).

Signing up only offers the monitoring roles. Administrators are the application's testers: they have no
patient and are created from the command line (`python -m src.create_admin`), so nobody can give themselves
the administrator screen from the sign-up form.
"""

CAREGIVER = "Family / Caregiver"
MEDICAL_STAFF = "Medical Staff"
ADMINISTRATOR = "Administrator"

# Every valid role (the values stored in the database).
ROLES = (CAREGIVER, MEDICAL_STAFF, ADMINISTRATOR)
# Roles that can be chosen when signing up.
SIGNUP_ROLES = (CAREGIVER, MEDICAL_STAFF)


def is_admin(user) -> bool:
    """True when `user` (a User row, or anything with a `role`) is an administrator."""
    return getattr(user, "role", None) == ADMINISTRATOR
