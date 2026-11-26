"""Entry point of the application: logging, theme, database and the main window."""

import logging
import os
import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMainWindow

from src.ai import preload
from src.database.connection import init_tables
from src.database.models.fall_event import FallEvent
from src.database.models.patient import Patient
from src.database.models.user import User
from src.navigation.coordinator import AppCoordinator
from src.views import icons
from src.views.theme import APP_NAME, ThemeManager

os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
logger = logging.getLogger(__name__)

PRELOAD_DELAY_MS = 300


class MainWindow(QMainWindow):
    """The application window. Which screen it shows is decided by `AppCoordinator`."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(1120, 720)
        self.resize(1280, 820)
        logger.info("Initializing application main window...")
        self.coordinator = AppCoordinator(self)

    def start(self) -> None:
        """Shows the window and its first screen, then loads the AI libraries in the background."""
        self.showMaximized()
        self.coordinator.start()
        # Once the sign-in screen has been painted: by the time the user starts a monitoring, the
        # several seconds of importing TensorFlow and MediaPipe have passed while they signed in.
        QTimer.singleShot(PRELOAD_DELAY_MS, preload.start)

    def closeEvent(self, event):
        """Lets a running video thread release the camera before the window (and its thread objects) go away."""
        self.coordinator.shutdown()
        super().closeEvent(event)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] [%(threadName)s] %(name)s: %(message)s",   # which thread wrote it
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("app.log", encoding="utf-8")
        ]
    )

    logger.info("Starting application execution...")
    if sys.platform == "win32":
        # Its own taskbar entry: without an AppUserModelID, Windows groups the window under python.exe
        # and shows Python's icon instead of the application's.
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_NAME)
    app = QApplication(sys.argv)
    app.setOrganizationName(APP_NAME)        # where QSettings() keeps the interface's preferences
    app.setApplicationName(APP_NAME)

    ThemeManager.setup_theme(app)
    app.setWindowIcon(icons.app_icon())      # the window's title bar and the taskbar

    init_tables([User, Patient, FallEvent])

    window = MainWindow()
    window.start()

    logger.info("Application main event loop started.")
    exit_code = app.exec()
    logger.info("Application shutting down with exit code: %d", exit_code)
    sys.exit(exit_code)
