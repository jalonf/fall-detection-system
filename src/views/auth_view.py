from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QStackedWidget, QGraphicsOpacityEffect
)

from src.views.components.login_form import LoginForm
from src.views.components.register_form import RegisterForm

APP_NAME = "EXAMPLE"
APP_TAGLINE = "Fall Detection System"

class AuthView(QWidget):
    """
    Main authentication view controller.
    Acts as a container and manages the transition animations between 
    the login and registration form components.
    """
    
    # Main view exposes signals to the controller
    login_requested = Signal(str, str, bool)
    register_requested = Signal(str, str, str, str, str, str, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("authScreen")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        
        self.effect_out = None
        self.effect_in = None
        self.anim_out = None
        self.anim_in = None
        
        self._build_ui()

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        left_area = QFrame()
        left_layout = QVBoxLayout(left_area)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        brand_title = QLabel("TFG")
        brand_title.setStyleSheet("font-size: 72px; font-weight: 900; color: #0F172A; letter-spacing: -2px;")
        brand_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        brand_subtitle = QLabel("Real-Time Fall Detection System")
        brand_subtitle.setStyleSheet("font-size: 20px; font-weight: 500; color: #334155; letter-spacing: -0.5px;")
        brand_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        tech_pill = QLabel("Powered by MediaPipe & PySide6")
        tech_pill.setStyleSheet("""
            background-color: rgba(255,255,255,0.4);
            color: #475569;
            padding: 8px 16px;
            border-radius: 16px;
            font-size: 13px;
            font-weight: 600;
        """)
        tech_pill.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        left_layout.addWidget(brand_title)
        left_layout.addSpacing(4)
        left_layout.addWidget(brand_subtitle)
        left_layout.addSpacing(24)
        left_layout.addWidget(tech_pill, 0, Qt.AlignmentFlag.AlignHCenter)

        right_panel = QFrame()
        right_panel.setObjectName("glassPanel")
        right_panel.setFixedWidth(520) 
        
        panel_layout = QVBoxLayout(right_panel)
        panel_layout.setContentsMargins(60, 0, 60, 0)
        panel_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.stacked = QStackedWidget()
        
        self.login_form = LoginForm()
        self.register_form = RegisterForm()

        # INTERNAL CONNECTIONS: 
        # 1. Connect page switch links
        self.login_form.switch_page_requested.connect(lambda: self._switch_page(1))
        self.register_form.switch_page_requested.connect(lambda: self._switch_page(0))
        
        # 2. Redirect internal form signals to the exterior view signals
        self.login_form.login_requested.connect(self.login_requested.emit)
        self.register_form.register_requested.connect(self.register_requested.emit)

        self.stacked.addWidget(self.login_form)
        self.stacked.addWidget(self.register_form)
        
        panel_layout.addWidget(self.stacked)

        root.addWidget(left_area, 1)    
        root.addWidget(right_panel, 0)  

    def _switch_page(self, target_index):
        if self.stacked.currentIndex() == target_index:
            return
            
        current_widget = self.stacked.currentWidget()
        self.effect_out = QGraphicsOpacityEffect(current_widget)
        current_widget.setGraphicsEffect(self.effect_out)
        
        self.anim_out = QPropertyAnimation(self.effect_out, b"opacity")
        self.anim_out.setDuration(150)
        self.anim_out.setStartValue(1.0)
        self.anim_out.setEndValue(0.0)
        self.anim_out.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        def on_fade_out_finished():
            current_widget.setGraphicsEffect(None)  # type: ignore
            self.stacked.setCurrentIndex(target_index)
            
            next_widget = self.stacked.currentWidget()
            self.effect_in = QGraphicsOpacityEffect(next_widget)
            next_widget.setGraphicsEffect(self.effect_in)
            
            self.anim_in = QPropertyAnimation(self.effect_in, b"opacity")
            self.anim_in.setDuration(150)
            self.anim_in.setStartValue(0.0)
            self.anim_in.setEndValue(1.0)
            self.anim_in.setEasingCurve(QEasingCurve.Type.InOutQuad)
            
            self.anim_in.finished.connect(lambda: next_widget.setGraphicsEffect(None))  # type: ignore
            self.anim_in.start()

        self.anim_out.finished.connect(on_fade_out_finished)
        self.anim_out.start()