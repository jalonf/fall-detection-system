"""The SQLite connection shared by the whole application."""

import logging

from peewee import SqliteDatabase

from src.paths import DATABASE_FILE

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Owns the SQLite connection (a singleton: one global connection).

    The database uses WAL journaling, foreign keys and a 5 s busy timeout.
    """
    instance = None
    db_connection: SqliteDatabase
    
    def __new__(cls, *args, **kwargs):
        """Returns the only instance, creating and configuring it the first time."""
        if cls.instance is None:
            cls.instance = super().__new__(cls)
            cls.instance.configure()

        return cls.instance

    def configure(self):
        """Configures the path and prepares the connection object."""
        db_file = DATABASE_FILE

        db_exists = db_file.exists()
        if db_exists:
            logger.info("Existing database detected at: %s", db_file)
        else:
            logger.info("Database file not found. A new database will be created from scratch at: %s", db_file)
        
        self.db_connection = SqliteDatabase(
            str(db_file),
            pragmas={
                "journal_mode": "wal",
                "foreign_keys": 1,         
                "busy_timeout": 5000,      
            },
        )

    def init_tables(self, models: list):
        """Creates the necessary tables, closing the connection even if something fails."""
        logger.info("Connecting to the database to initialize tables...")

        with self.db_connection.connection_context():
            tables_exist = all(model.table_exists() for model in models)
            self.db_connection.create_tables(models)

        if tables_exist:
            logger.info("Database schema verified. All tables are ready.")
        else:
            logger.info("New database tables created successfully.")


databaseManager = DatabaseManager()
db_connection = databaseManager.db_connection