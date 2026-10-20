import logging
import os
import sys

from PySide6.QtWidgets import QApplication, QMainWindow

from src.controllers.admin_controller import AdminController
from src.controllers.auth_controller import AuthController
from src.controllers.monitor_controller import MonitorController
from src.database.database_manager import databaseManager
from src.database.models.fall_event import FallEvent
from src.database.models.patient import Patient
from src.database.models.user import User
from src.router.router import ViewRouter
from src.views.admin_view import AdminView
from src.views.auth_view import AuthView
from src.views.components.wordmark import brand_icon
from src.views.monitor_view import MonitorView
from src.views.theme import APP_NAME, ThemeManager

os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(1120, 720)
        self.resize(1280, 820)
        
        self.monitor_view = None
        self.monitor_controller = None
        
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
        """Transitions the interface to the monitoring module, selecting AdminView or MonitorView based on user role."""
        logger.info("Transitioning to dashboard for user: %s (Role: %s)", user.name, user.role)
        
        patient = self.auth_controller.user_repo.get_patient_by_user(user)
        
        # Check user role and instantiate the corresponding view and controller dynamically
        role_str = str(getattr(user, 'role', '')).strip().lower()
        if role_str in ["admin", "administrator"]:
            logger.info("Instantiating AdminView and AdminController for administrator role.")
            self.monitor_view = AdminView(user_name=user.name, user_role=user.role)
            self.monitor_controller = AdminController(
                view=self.monitor_view,
                current_user=user,
                patient=patient,
                on_logout_callback=self.handle_logout
            )
        else:
            logger.info("Instantiating MonitorView and MonitorController for standard user role.")
            self.monitor_view = MonitorView(user_name=user.name, user_role=user.role)
            self.monitor_controller = MonitorController(
                view=self.monitor_view,
                current_user=user,
                patient=patient,
                on_logout_callback=self.handle_logout
            )
        
        self.router.add_view(self.monitor_view)
        self.router.navigate_to(self.monitor_view)

    def handle_logout(self):
        logger.info("Logout requested. Stopping camera worker and cleaning up monitor/admin view...")
        if self.monitor_controller and hasattr(self.monitor_controller, "stop_camera"):
            self.monitor_controller.stop_camera()
        
        def cleanup_monitor():
            if self.monitor_view:
                self.router.remove_view(self.monitor_view)
                self.monitor_view.deleteLater()
                self.monitor_view = None
            self.monitor_controller = None
            logger.info("Dashboard module successfully cleaned up and unloaded.")

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
    app.setWindowIcon(brand_icon())

    databaseManager.init_tables([User, Patient, FallEvent])
    
    window = MainWindow()
    window.showMaximized()
    
    logger.info("Application main event loop started.")
    exit_code = app.exec()
    logger.info("Application shutting down with exit code: %d", exit_code)
    sys.exit(exit_code)