import logging
from pathlib import Path

from peewee import SqliteDatabase

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Class in charge of managing the SQLite connection.
    It is implemented as a Singleton to ensure a single global connection.
    """
    instance = None
    connection: SqliteDatabase
    
    def __new__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super().__new__(cls)
            cls.instance.configure()

        return cls.instance

    def configure(self):
        """Configures the path and prepares the connection object."""
        project_root = Path(__file__).resolve().parents[2]

        db_file = project_root / 'app.db'
        
        db_exists = db_file.exists()
        if db_exists:
            logger.info("Existing database detected at: %s", db_file)
        else:
            logger.info("Database file not found. A new database will be created from scratch at: %s", db_file)
        
        self.connection = SqliteDatabase(
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

        with self.connection.connection_context():
            tables_exist = all(model.table_exists() for model in models)
            self.connection.create_tables(models)

        if tables_exist:
            logger.info("Database schema verified. All tables are ready.")
        else:
            logger.info("New database tables created successfully.")


databaseManager = DatabaseManager()
db = databaseManager.connection