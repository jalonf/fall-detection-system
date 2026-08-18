from peewee import SqliteDatabase
from pathlib import Path

class DatabaseManager:
    """
    Class in charge of managing the SQLite connection.
    It is implemented as a Singleton to ensure a single global connection.
    """
    instance = None
    connection: SqliteDatabase | None = None
    
    def __new__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super(DatabaseManager, cls).__new__(cls)
            cls.instance.configure()

        return cls.instance

    def configure(self):
        """Configures the path and prepares the connection object."""
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        
        db_file = project_root / 'app.db'
        
        self.connection = SqliteDatabase(str(db_file), check_same_thread=False)

    def init_tables(self, models: list):
        """
        Connects to the database and creates the necessary tables safely,
        then closes the connection to release the file.
        """
        if self.connection is not None:
            self.connection.connect()
            # The create_tables method executes "CREATE TABLE IF NOT EXISTS" under the hood.
            self.connection.create_tables(models)
            self.connection.close()
            print("Database initialized successfully.")
        else:
            print("Error: Attempted to initialize tables but there is no connection.")


databaseManager = DatabaseManager()
db = databaseManager.connection