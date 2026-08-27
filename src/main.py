# main.py
import sys
from PySide6.QtWidgets import QApplication, QMainWindow

from src.router.router import ViewRouter
from src.views.theme import ThemeManager 

from src.database.core.databaseManager import databaseManager
from src.database.models.user import User

from src.views.auth_view import AuthView
from src.views.monitor_view import MonitorView 
from src.controllers.auth_controller import AuthController
from src.controllers.monitor_controller import MonitorController

class ExampleApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EXAMPLE")
        self.setMinimumSize(1120, 720)
        self.resize(1280, 820)

        self.router = ViewRouter(self)
        self.init_auth_module()

    def init_auth_module(self):
        self.auth_view = AuthView()
        self.auth_controller = AuthController(
            view=self.auth_view, 
            on_auth_success=self.show_monitor_module
        )
        
        self.router.add_view(self.auth_view)
        self.router.navigate_to(self.auth_view)

    def show_monitor_module(self, user):
        """Transitions the interface to the real-time monitoring dashboard module passing the user entity."""
        self.monitor_view = MonitorView(user_name=user.name, user_role=user.role)
        
        self.monitor_controller = MonitorController(
            view=self.monitor_view,
            current_user=user,
            on_logout_callback=self.handle_logout
        )
        
        self.router.add_view(self.monitor_view)
        self.router.navigate_to(self.monitor_view)

    def handle_logout(self):
        self.monitor_controller.stop_camera()
        
        def cleanup_monitor():
            self.router.remove_view(self.monitor_view)
            self.monitor_view.deleteLater()
            self.monitor_view = None
            self.monitor_controller = None

        self.router.navigate_to(self.auth_view, on_finish_callback=cleanup_monitor)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    ThemeManager.setup_theme(app)

    databaseManager.init_tables([User])
    
    window = ExampleApp()
    window.showMaximized()
    sys.exit(app.exec())