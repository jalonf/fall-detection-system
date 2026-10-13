from pathlib import Path

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.dtos.registration_data import RegistrationData
from src.views.components.login_form import LoginForm
from src.views.components.pose_backdrop import PoseBackdrop
from src.views.components.register_form import RegisterForm
from src.views.components.toast import Toast

APP_NAME = "Name"
APP_TAGLINE = "Fall Detection System"


class AuthView(QWidget):
    """
    Main authentication view controller.
    Acts as a container and manages transition animations between
    login and registration form components.
    """

    login_requested = Signal(str, str)
    register_requested = Signal(RegistrationData)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("authScreen")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.effect_out = None
        self.effect_in = None
        self.anim_out = None
        self.anim_in = None
        self._switching = False

        # Floating notification (success / info / warning / error). `banner_label`
        # is kept as an alias of its message label for backwards compatibility.
        self.toast = Toast(self)
        self.banner_label: QLabel = self.toast.message_label

        self._build_ui()

    def _build_ui(self):
        """Constructs and organizes the comprehensive layout for branding and authentication panels."""
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ---- Left: brand surface (paints the fall-sequence illustration itself) ----
        left_area = PoseBackdrop()
        left_layout = QVBoxLayout(left_area)
        left_layout.setContentsMargins(64, 56, 56, 48)
        left_layout.setSpacing(0)

        lockup = QHBoxLayout()
        lockup.setSpacing(12)
        brand_mark = QLabel()
        brand_mark.setObjectName("authBrandMark")

        # FIX: assets and auth_view.py are in the same 'views' folder
        base_dir = Path(__file__).resolve().parent
        logo_path = base_dir / "assets" / "logo.png"
        logo_pixmap = QPixmap(str(logo_path))
        
        logo_escaled = logo_pixmap.scaled(
            85, 85, 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        brand_mark.setPixmap(logo_escaled)
        brand_mark.setFixedSize(85, 85)
        brand_mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand_title = QLabel(APP_NAME)
        brand_title.setObjectName("authBrandName")
        lockup.addWidget(brand_mark)
        lockup.addWidget(brand_title)
        lockup.addStretch()
        left_layout.addLayout(lockup)
        left_layout.addSpacing(48)

        brand_subtitle = QLabel("Pose Analytics & Fall Detection System")
        brand_subtitle.setObjectName("brandHeadline")
        brand_subtitle.setWordWrap(True)
        brand_subtitle.setMaximumWidth(460)
        brand_subtitle.setAlignment(Qt.AlignmentFlag.AlignLeft)
        left_layout.addWidget(brand_subtitle)
        left_layout.addSpacing(14)

        brand_desc = QLabel(
            "An enterprise-grade computer vision platform designed for continuous safety monitoring, "
            "leveraging spatial-temporal graph neural networks and MediaPipe pipelines."
        )
        brand_desc.setObjectName("brandDesc")
        brand_desc.setWordWrap(True)
        brand_desc.setMaximumWidth(440)
        brand_desc.setAlignment(Qt.AlignmentFlag.AlignLeft)
        left_layout.addWidget(brand_desc)

        left_layout.addStretch(1)

        tech_pill = QLabel("Powered by MediaPipe & PySide6")
        tech_pill.setObjectName("techPill")
        left_layout.addWidget(tech_pill, 0, Qt.AlignmentFlag.AlignLeft)

        # ---- Right: form panel ----
        right_panel = QFrame()
        right_panel.setObjectName("authPanel")
        right_panel.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        right_panel.setFixedWidth(600)

        self.panel_layout = QVBoxLayout(right_panel)
        self.panel_layout.setContentsMargins(56, 36, 46, 24)
        self.panel_layout.setSpacing(12)

        self.stacked = QStackedWidget()

        self.login_form = LoginForm()
        self.register_form = RegisterForm()

        self.login_form.switch_page_requested.connect(lambda: self._switch_page(1))
        self.register_form.switch_page_requested.connect(lambda: self._switch_page(0))

        self.login_form.login_requested.connect(self.login_requested.emit)
        self.register_form.register_requested.connect(self.register_requested.emit)

        self.stacked.addWidget(self.login_form)
        self.stacked.addWidget(self.register_form)

        self.panel_layout.addWidget(self.stacked, 1)

        footer = QLabel(APP_TAGLINE)
        footer.setObjectName("authFooter")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.panel_layout.addWidget(footer)

        root.addWidget(left_area, 1)
        root.addWidget(right_panel, 0)

    def _switch_page(self, target_index):
        """Executes smooth opacity fade-out and fade-in transitions between sub-forms."""
        if self._switching or self.stacked.currentIndex() == target_index:
            return
        self._switching = True

        current_widget = self.stacked.currentWidget()
        self.effect_out = QGraphicsOpacityEffect(current_widget)
        current_widget.setGraphicsEffect(self.effect_out)

        self.anim_out = QPropertyAnimation(self.effect_out, b"opacity")
        self.anim_out.setDuration(120)
        self.anim_out.setStartValue(1.0)
        self.anim_out.setEndValue(0.0)
        self.anim_out.setEasingCurve(QEasingCurve.Type.InOutQuad)

        def on_fade_in_finished(widget):
            widget.setGraphicsEffect(None)  # type: ignore
            self._switching = False

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

            self.anim_in.finished.connect(lambda: on_fade_in_finished(next_widget))
            self.anim_in.start()

        self.anim_out.finished.connect(on_fade_out_finished)
        self.anim_out.start()

    def resizeEvent(self, event):
        """Keeps the floating toast anchored if the window is resized."""
        super().resizeEvent(event)
        if self.toast.isVisible():
            self.toast.reposition()

    def _show_banner(self, message: str, is_error: bool = True):
        """Shows the floating toast: error (red) or success (green accent)."""
        self.toast.show_message("error" if is_error else "success", message)

    def _hide_banner(self):
        """Hides the floating toast cleanly."""
        self.toast.dismiss()

    def show_error(self, message: str):
        """Triggers the display of a styled error toast notification."""
        self._show_banner(message, is_error=True)

    def show_success(self, message: str):
        """Triggers the display of a styled success toast notification."""
        self._show_banner(message, is_error=False)

    def show_info(self, message: str):
        """Displays a neutral informational toast."""
        self.toast.show_message("info", message)

    def show_warning(self, message: str):
        """Displays a warning toast."""
        self.toast.show_message("warning", message)