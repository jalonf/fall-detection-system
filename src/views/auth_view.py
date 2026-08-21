from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QStackedWidget, QGraphicsOpacityEffect
)

from src.views.components.login_form import LoginForm
from src.views.components.register_form import RegisterForm

APP_NAME = "Safeguard"
APP_TAGLINE = "Fall Detection System"

class AuthView(QWidget):
    """
    Main authentication view controller.
    Acts as a container and manages transition animations between 
    login and registration form components.
    """
    
    login_requested = Signal(str, str)
    register_requested = Signal(str, str, str, str, str, str)

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

        # Left clean typographic branding area with serious enterprise nomenclature
        left_area = QFrame()
        left_layout = QVBoxLayout(left_area)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.setContentsMargins(70, 0, 70, 0)
        
        brand_title = QLabel("Safeguard")
        brand_title.setStyleSheet("font-size: 54px; font-weight: 900; color: #111827; letter-spacing: -1.5px; background: transparent;")
        brand_title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # Subtle accent divider line
        divider = QFrame()
        divider.setFixedWidth(48)
        divider.setFixedHeight(4)
        divider.setStyleSheet("background-color: #1E3A8A; border: none; border-radius: 2px;")
        
        brand_subtitle = QLabel("Pose Analytics & Fall Detection System")
        brand_subtitle.setStyleSheet("font-size: 18px; font-weight: 700; color: #1E3A8A; letter-spacing: -0.5px; background: transparent;")
        brand_subtitle.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        brand_desc = QLabel(
            "An enterprise-grade computer vision platform designed for continuous safety monitoring, "
            "leveraging spatial-temporal graph neural networks and MediaPipe pipelines."
        )
        brand_desc.setWordWrap(True)
        brand_desc.setStyleSheet("font-size: 13px; font-weight: 400; color: #4B5563; line-height: 1.6; background: transparent;")
        brand_desc.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        tech_pill = QLabel("Powered by MediaPipe & PySide6")
        tech_pill.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.6);
            color: #374151;
            padding: 8px 16px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        """)

        left_layout.addWidget(brand_title)
        left_layout.addSpacing(4)
        left_layout.addWidget(divider)
        left_layout.addSpacing(14)
        left_layout.addWidget(brand_subtitle)
        left_layout.addSpacing(10)
        left_layout.addWidget(brand_desc)
        left_layout.addSpacing(24)
        left_layout.addWidget(tech_pill, 0, Qt.AlignmentFlag.AlignLeft)

        # Right form panel with balanced proportions
        right_panel = QFrame()
        right_panel.setObjectName("glassPanel")
        right_panel.setFixedWidth(500)
        
        panel_layout = QVBoxLayout(right_panel)
        panel_layout.setContentsMargins(60, 0, 60, 0)
        panel_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.stacked = QStackedWidget()
        
        self.login_form = LoginForm()
        self.register_form = RegisterForm()

        self.login_form.switch_page_requested.connect(lambda: self._switch_page(1))
        self.register_form.switch_page_requested.connect(lambda: self._switch_page(0))
        
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
        self.anim_out.setDuration(120)
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
            self.anim_in.setDuration(120)
            self.anim_in.setStartValue(0.0)
            self.anim_in.setEndValue(1.0)
            self.anim_in.setEasingCurve(QEasingCurve.Type.InOutQuad)
            
            self.anim_in.finished.connect(lambda: next_widget.setGraphicsEffect(None))  # type: ignore
            self.anim_in.start()

        self.anim_out.finished.connect(on_fade_out_finished)
        self.anim_out.start()