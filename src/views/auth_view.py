from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.dtos.registration_data import RegistrationData
from src.views.components.login_form import LoginForm
from src.views.components.pose_backdrop import PoseBackdrop
from src.views.components.register_form import RegisterForm
from src.views.components.toast import Toast
from src.views.components.wordmark import Wordmark
from src.views.theme import APP_NAME, Size, apply_shadow

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

        # ---- Left: brand copy on the canvas, with the fall-sequence figure below it ----
        left_area = QWidget()
        left_area.setObjectName("brandPanel")
        left_layout = QVBoxLayout(left_area)
        left_layout.setContentsMargins(64, 56, 36, 44)
        left_layout.setSpacing(0)

        left_layout.addWidget(Wordmark(APP_NAME, large=True), 0, Qt.AlignmentFlag.AlignLeft)
        left_layout.addSpacing(44)

        brand_subtitle = QLabel("Pose Analytics & Fall Detection System")
        brand_subtitle.setObjectName("brandHeadline")
        brand_subtitle.setWordWrap(True)
        brand_subtitle.setMaximumWidth(460)
        brand_subtitle.setAlignment(Qt.AlignmentFlag.AlignLeft)
        left_layout.addWidget(brand_subtitle)
        left_layout.addSpacing(14)

        brand_desc = QLabel(
            "An enterprise-grade computer vision platform designed for continuous safety monitoring, "
            "leveraging gated recurrent unit neural networks and MediaPipe pipelines."
        )
        brand_desc.setObjectName("brandDesc")
        brand_desc.setWordWrap(True)
        brand_desc.setMaximumWidth(440)
        brand_desc.setAlignment(Qt.AlignmentFlag.AlignLeft)
        left_layout.addWidget(brand_desc)

        left_layout.addSpacing(28)

        # The figure plate takes the remaining height and resizes with the window.
        self.pose_figure = PoseBackdrop()
        left_layout.addWidget(self.pose_figure, 1)
        left_layout.addSpacing(22)

        tech_pill = QLabel("Powered by MediaPipe & PySide6")
        tech_pill.setObjectName("techPill")
        left_layout.addWidget(tech_pill, 0, Qt.AlignmentFlag.AlignLeft)

        # ---- Right: floating form card ----
        right_area = QWidget()
        right_area.setObjectName("authRight")
        right_area.setMinimumWidth(Size.AUTH_PANEL_MIN)
        right_area.setMaximumWidth(Size.AUTH_PANEL_MAX)
        right_area.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        right_layout = QGridLayout(right_area)
        right_layout.setContentsMargins(20, 28, 32, 28)

        # The shadow lives on a childless plate stacked *behind* the card. Putting the
        # effect on the card itself would nest it with the opacity effect that
        # `_switch_page` applies to the forms inside, which Qt does not support well.
        shadow_plate = QFrame()
        shadow_plate.setObjectName("authShadow")
        shadow_plate.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        apply_shadow(shadow_plate, blur=40, y=10, alpha=38)
        right_layout.addWidget(shadow_plate, 0, 0)

        right_panel = QFrame()
        right_panel.setObjectName("authCard")
        right_panel.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        right_layout.addWidget(right_panel, 0, 0)

        self.panel_layout = QVBoxLayout(right_panel)
        self.panel_layout.setContentsMargins(44, 36, 36, 22)
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

        self._brand_area = left_area
        root.addWidget(left_area, 5)
        root.addWidget(right_area, 4)

    @staticmethod
    def _release_effect(widget: QWidget) -> None:
        """Turns off the fade effect once a transition ends.

        ``setGraphicsEffect`` does not accept ``None`` in the PySide6 stubs, so the effect
        is disabled instead; the widget then paints normally and the next transition
        replaces the (disabled) effect.
        """
        effect = widget.graphicsEffect()
        if effect is not None:
            effect.setEnabled(False)

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
            self._release_effect(widget)
            self._switching = False

        def on_fade_out_finished():
            self._release_effect(current_widget)
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

    def showEvent(self, event):
        """Starts with the caret in the e-mail field instead of a focused button."""
        super().showEvent(event)
        if self.stacked.currentIndex() == 0:
            self.login_form.login_email.setFocus(Qt.FocusReason.OtherFocusReason)

    def resizeEvent(self, event):
        """Keeps the floating toast anchored and drops the brand surface on narrow windows."""
        super().resizeEvent(event)
        self._brand_area.setVisible(self.width() >= 900)
        if self.toast.isVisible():
            self.toast.reposition()

    def _show_banner(self, message: str, is_error: bool = True):
        """Shows the floating toast: error (red) or success (green accent)."""
        self.toast.show_message("error" if is_error else "success", message)

    def show_error(self, message: str):
        """Triggers the display of a styled error toast notification."""
        self._show_banner(message, is_error=True)

    def show_success(self, message: str):
        """Triggers the display of a styled success toast notification."""
        self._show_banner(message, is_error=False)
