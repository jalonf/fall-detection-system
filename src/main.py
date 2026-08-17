import sys
from pathlib import Path
from PySide6.QtCore import QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QGraphicsOpacityEffect

from src.database.core.databaseManager import databaseManager
from src.database.models.user import User

from src.views.auth_view import AuthView
from src.views.monitor_view import MonitorView 
from src.controllers.auth_controller import AuthController
from src.controllers.monitor_controller import MonitorController
from PySide6.QtWidgets import QLabel

STYLESHEET_PATH = Path(__file__).resolve().parent / "views" / "style.qss"

def load_stylesheet() -> str:
    try:
        return STYLESHEET_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"[WARN] No se pudo cargar la hoja de estilos ({STYLESHEET_PATH}): {exc}")
        return ""

def apply_light_theme(app: QApplication) -> None:
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#F8FAFC"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#334155"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#F1F5F9"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#334155"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#334155"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#2563EB"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor("#94A3B8"))
    app.setPalette(palette)
    app.setStyleSheet(load_stylesheet())

class ExampleApp(QMainWindow):
    effect_out: QGraphicsOpacityEffect
    effect_in: QGraphicsOpacityEffect
    anim_out: QPropertyAnimation
    anim_in: QPropertyAnimation

    def __init__(self):
        super().__init__()
        self.setWindowTitle("EXAMPLE")
        self.setMinimumSize(1120, 720)
        self.resize(1280, 820)

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.init_auth_module()

    def init_auth_module(self):
        self.auth_view = AuthView()
        self.auth_controller = AuthController(
            view=self.auth_view, 
            on_auth_success=self.show_monitor_module
        )
        self.stacked_widget.addWidget(self.auth_view)

    def show_monitor_module(self, user_email):
        user_name = user_email.split('@')[0].capitalize()
        
        self.monitor_view = MonitorView(user_name=user_name)
        self.monitor_controller = MonitorController(
            view=self.monitor_view,
            on_logout_callback=self.handle_logout
        )
        
        self.stacked_widget.addWidget(self.monitor_view)
        
        self._transition_between_widgets(self.auth_view, self.monitor_view)

    def handle_logout(self):
        self.monitor_controller.stop_camera()
        
        def cleanup_monitor():
            self.stacked_widget.removeWidget(self.monitor_view)
            self.monitor_view.deleteLater()
            self.monitor_view = None
            self.monitor_controller = None

        self._transition_between_widgets(self.monitor_view, self.auth_view, on_finish_callback=cleanup_monitor)


    def _transition_between_widgets(self, current_widget, next_widget, on_finish_callback=None):
        if current_widget == next_widget:
            return

        pixmap = current_widget.grab()

        self.overlay = QLabel(self)
        self.overlay.setPixmap(pixmap)
        self.overlay.resize(self.size())
        self.overlay.move(0, 0)
        self.overlay.show()
        self.overlay.raise_()

        self.stacked_widget.setCurrentWidget(next_widget)

        self.effect_out = QGraphicsOpacityEffect(self.overlay)
        self.overlay.setGraphicsEffect(self.effect_out)

        self.anim_out = QPropertyAnimation(self.effect_out, b"opacity")
        self.anim_out.setDuration(400)
        self.anim_out.setStartValue(1.0)
        self.anim_out.setEndValue(0.0)
        self.anim_out.setEasingCurve(QEasingCurve.Type.InOutQuad)

        def on_transition_finished():
            self.overlay.hide()
            self.overlay.deleteLater()
            
            if on_finish_callback:
                on_finish_callback()

        self.anim_out.finished.connect(on_transition_finished)
        self.anim_out.start()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_light_theme(app)
    databaseManager.init_tables([User])
    window = ExampleApp()
    window.showMaximized()
    sys.exit(app.exec())