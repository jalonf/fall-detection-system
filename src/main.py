import logging
import os
import sys

from PySide6.QtWidgets import QApplication, QMainWindow

from src.database.database_manager import databaseManager
from src.database.models.fall_event import FallEvent
from src.database.models.patient import Patient
from src.database.models.user import User
from src.navigation.coordinator import AppCoordinator
from src.views.theme import APP_NAME, ThemeManager

os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """The application window. Which screen it shows is decided by `AppCoordinator`."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(1120, 720)
        self.resize(1280, 820)
        logger.info("Initializing application main window...")
        self.coordinator = AppCoordinator(self)

    def closeEvent(self, event):
        """Lets a running worker release the camera before the window (and its thread objects) go away."""
        self.coordinator.shutdown()
        super().closeEvent(event)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("app.log", encoding="utf-8")
        ]
    )

    logger.info("Starting application execution...")
    app = QApplication(sys.argv)

    ThemeManager.setup_theme(app)

    databaseManager.init_tables([User, Patient, FallEvent])

    window = MainWindow()
    window.showMaximized()

    logger.info("Application main event loop started.")
    exit_code = app.exec()
    logger.info("Application shutting down with exit code: %d", exit_code)
    sys.exit(exit_code)
