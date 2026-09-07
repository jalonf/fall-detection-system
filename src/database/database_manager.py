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
    connection: SqliteDatabase | None = None
    
    def __new__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super().__new__(cls)
            cls.instance.configure()

        return cls.instance

    def configure(self):
        """Configures the path and prepares the connection object."""
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        
        db_file = project_root / 'app.db'
        
        db_exists = db_file.exists()
        if db_exists:
            logger.info("Existing database detected at: %s", db_file)
        else:
            logger.info("Database file not found. A new database will be created from scratch at: %s", db_file)
        
        self.connection = SqliteDatabase(str(db_file), check_same_thread=False)

    def init_tables(self, models: list):
        """
        Connects to the database and creates the necessary tables safely,
        then closes the connection to release the file.
        """
        if self.connection is not None:
            logger.info("Connecting to the database to initialize tables...")
            self.connection.connect()
            
            tables_exist = all(model.table_exists() for model in models)
            
            # The create_tables method executes "CREATE TABLE IF NOT EXISTS" under the hood.
            self.connection.create_tables(models)
            self.connection.close()
            
            if tables_exist:
                logger.info("Database schema verified. All tables are ready.")
            else:
                logger.info("New database tables created successfully.")
        else:
            logger.error("Attempted to initialize tables but there is no active database connection.")


databaseManager = DatabaseManager()
db = databaseManager.connection