"""The SQLite connection shared by the whole application.

A module is created only once per program, so `db` is already the single shared connection
object (a module-level singleton): no class is needed to guarantee it. Peewee keeps one real
connection per thread behind it, opened on demand.
"""

import logging

from peewee import SqliteDatabase

from src.paths import DATABASE_FILE

logger = logging.getLogger(__name__)

# WAL journaling (readers do not block the writer), foreign keys, and a 5 s wait when the file is busy.
db = SqliteDatabase(str(DATABASE_FILE), pragmas={"journal_mode": "wal", "foreign_keys": 1, "busy_timeout": 5000})


def init_tables(models: list) -> None:
    """Creates the tables that do not exist yet, closing the connection afterwards.

    Args:
        models: The Peewee model classes.
    """
    new_file = not DATABASE_FILE.exists()
    with db.connection_context():
        db.create_tables(models)
    if new_file:
        logger.info("New database created at: %s", DATABASE_FILE)
    else:
        logger.info("Database ready at: %s", DATABASE_FILE)
