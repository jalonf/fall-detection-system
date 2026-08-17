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
        # En Python se recomienda usar 'is None' en lugar de '== None'
        if cls.instance is None:
            cls.instance = super(DatabaseManager, cls).__new__(cls)
            cls.instance.configure()

        return cls.instance

    def configure(self):
        """Configures the path and prepares the connection object."""
        rute_app = Path.home() / ".fall_detection_app"
        rute_app.mkdir(parents=True, exist_ok=True)
        self.connection = SqliteDatabase(str(rute_app / 'app.db'), check_same_thread=False)

    def init_tables(self, models: list):
        """
        Connects to the database and creates the necessary tables safely,
        then closes the connection to release the file.
        """
        if self.connection is not None:
            self.connection.connect()
            self.connection.create_tables(models)
            self.connection.close()
            print("Database initialized successfully.")
        else:
            print("Error: Attempted to initialize tables but there is no connection.")


databaseManager = DatabaseManager()
# OJO A ESTE CAMBIO: Tiene que ser la 'd' minúscula (la instancia), no la clase
db = databaseManager.connection