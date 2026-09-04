import logging
import sys

from PySide6.QtWidgets import QApplication, QMainWindow

from src.controllers.auth_controller import AuthController
from src.controllers.monitor_controller import MonitorController
from src.database.core.database_manager import databaseManager
from src.database.models.user import User
from src.router.router import ViewRouter
from src.views.auth_view import AuthView
from src.views.monitor_view import MonitorView
from src.views.theme import ThemeManager

logger = logging.getLogger(__name__)


class ExampleApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EXAMPLE")
        self.setMinimumSize(1120, 720)
        self.resize(1280, 820)
        
        logger.info("Initializing application main window...")
        self.router = ViewRouter(self)
        self.init_auth_module()

    def init_auth_module(self):
        logger.info("Initializing authentication module...")
        self.auth_view = AuthView()
        self.auth_controller = AuthController(
            view=self.auth_view, 
            on_auth_success=self.show_monitor_module
        )
        
        self.router.add_view(self.auth_view)
        self.router.navigate_to(self.auth_view)

    def show_monitor_module(self, user):
        """Transitions the interface to the real-time monitoring dashboard module passing the user entity."""
        logger.info("Transitioning to monitor module for user: %s (Role: %s)", user.name, user.role)
        self.monitor_view = MonitorView(user_name=user.name, user_role=user.role)
        
        self.monitor_controller = MonitorController(
            view=self.monitor_view,
            current_user=user,
            on_logout_callback=self.handle_logout
        )
        
        self.router.add_view(self.monitor_view)
        self.router.navigate_to(self.monitor_view)

    def handle_logout(self):
        logger.info("Logout requested. Stopping camera worker and cleaning up monitor view...")
        self.monitor_controller.stop_camera()
        
        def cleanup_monitor():
            self.router.remove_view(self.monitor_view)
            self.monitor_view.deleteLater()
            self.monitor_view = None
            self.monitor_controller = None
            logger.info("Monitor module successfully cleaned up and unloaded.")

        self.router.navigate_to(self.auth_view, on_finish_callback=cleanup_monitor)


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

    databaseManager.init_tables([User])
    
    window = ExampleApp()
    window.showMaximized()
    
    logger.info("Application main event loop started.")
    exit_code = app.exec()
    logger.info("Application shutting down with exit code: %d", exit_code)
    sys.exit(exit_code)