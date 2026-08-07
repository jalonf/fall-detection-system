from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QLineEdit, QCheckBox, QStackedWidget, QScrollArea, QComboBox,
    QGraphicsOpacityEffect
)
from src.views.theme import apply_shadow, Colors

APP_NAME = "EXAMPLE"
APP_TAGLINE = "Fall Detection System"

class AuthView(QWidget):
    """
    View responsible for rendering the authentication interface, 
    including login and registration forms with smooth page transitions.
    """
    login_email: QLineEdit
    login_password: QLineEdit
    reg_name: QLineEdit
    reg_phone: QLineEdit
    reg_email: QLineEdit
    reg_password: QLineEdit
    reg_confirm: QLineEdit
    
    effect_out: QGraphicsOpacityEffect
    effect_in: QGraphicsOpacityEffect
    anim_out: QPropertyAnimation
    anim_in: QPropertyAnimation

    def __init__(self, on_login_attempt=None, on_register_attempt=None, parent=None):
        """
        Args:
            on_login_attempt (callable): Callback function for submitting login data.
            on_register_attempt (callable): Callback function for submitting registration data.
            parent (QWidget): Parent widget.
        """
        super().__init__(parent)
        self.setObjectName("authScreen")
        
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        
        self.on_login_attempt = on_login_attempt
        self.on_register_attempt = on_register_attempt
        
        self._build_ui()

    def _build_ui(self):
        """Builds the main authentication layout featuring the branding panel and form container."""
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
        self.stacked.addWidget(self._wrap_scroll(self._login_page()))
        self.stacked.addWidget(self._register_page())
        
        panel_layout.addWidget(self.stacked)

        root.addWidget(left_area, 1)    
        root.addWidget(right_panel, 0)  

    def _switch_page(self, target_index):
        """Animates a smooth opacity cross-fade transition between the login and registration pages."""
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

    def _wrap_scroll(self, inner):
        """Wraps a page widget inside a clean, borderless scroll area."""
        scroll = QScrollArea()
        scroll.setObjectName("authScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.viewport().setAutoFillBackground(False)
        scroll.setWidget(inner)
        return scroll

    def _login_page(self):
        """Constructs and returns the login form page widget."""
        page = QWidget()
        page.setObjectName("authPage")
        layout = QVBoxLayout(page)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addStretch(1)

        title = QLabel("Welcome back")
        title.setObjectName("formTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        layout.addSpacing(8)

        sub = QLabel("Sign in to your account to continue")
        sub.setObjectName("formSubtitle")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sub)
        layout.addSpacing(32) 

        layout.addLayout(self._field("Email address", "login_email", "name@example.com"))
        layout.addSpacing(16)
        layout.addLayout(self._field("Password", "login_password", "••••••••", password=True))
        layout.addSpacing(16)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        self.remember = QCheckBox("Remember me")
        forgot = QLabel("Forgot password?")
        forgot.setObjectName("link")
        forgot.setCursor(Qt.CursorShape.PointingHandCursor)
        row.addWidget(self.remember)
        row.addStretch()
        row.addWidget(forgot)
        layout.addLayout(row)
        layout.addSpacing(28)

        self.btn_login = QPushButton("Sign In")
        self.btn_login.setObjectName("success")
        self.btn_login.setFixedHeight(46)
        self.btn_login.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_login.clicked.connect(self._handle_login)
        layout.addWidget(self.btn_login)
        layout.addSpacing(24)

        layout.addWidget(self._divider("or continue with"))
        layout.addSpacing(24)
        layout.addWidget(self._social_btn("Continue with Google", icon="G"))
        layout.addSpacing(32)

        switch = QHBoxLayout()
        switch.setAlignment(Qt.AlignmentFlag.AlignCenter)
        switch.setSpacing(6)
        q = QLabel("Don't have an account?")
        q.setStyleSheet("color: #64748B; font-size: 13px;")
        link = QLabel("Sign up")
        link.setObjectName("link")
        link.setCursor(Qt.CursorShape.PointingHandCursor)
        
        link.mousePressEvent = lambda e: self._switch_page(1)
        
        switch.addWidget(q)
        switch.addWidget(link)
        layout.addLayout(switch)
        
        layout.addStretch(1) 
        
        return page

    def _register_page(self):
        """Constructs and returns the registration form page widget."""
        inner = QWidget()
        inner.setObjectName("authPage")
        form = QVBoxLayout(inner)
        form.setContentsMargins(0, 40, 0, 40) 
        form.setSpacing(0)

        form.addStretch(1)

        title = QLabel("Create an account")
        title.setObjectName("formTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        form.addWidget(title)
        form.addSpacing(8)

        sub = QLabel("Set up your monitoring access")
        sub.setObjectName("formSubtitle")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        form.addWidget(sub)
        form.addSpacing(32)

        two_col = QHBoxLayout()
        two_col.setSpacing(16) 
        left = QVBoxLayout()
        left.addLayout(self._field("Full Name", "reg_name", "John Doe"))
        right = QVBoxLayout()
        right.addLayout(self._field("Phone", "reg_phone", "+1 234 567 8900"))
        two_col.addLayout(left, 1)
        two_col.addLayout(right, 1)
        form.addLayout(two_col)
        form.addSpacing(16)

        form.addLayout(self._field("Email address", "reg_email", "name@example.com"))
        form.addSpacing(16)

        two_col2 = QHBoxLayout()
        two_col2.setSpacing(16)
        l2 = QVBoxLayout()
        l2.addLayout(self._field("Password", "reg_password", "••••••••", password=True))
        r2 = QVBoxLayout()
        r2.addLayout(self._field("Confirm", "reg_confirm", "••••••••", password=True))
        two_col2.addLayout(l2, 1)
        two_col2.addLayout(r2, 1)
        form.addLayout(two_col2)
        form.addSpacing(16)

        role_label = QLabel("User Role")
        role_label.setObjectName("fieldLabel")
        form.addWidget(role_label)
        form.addSpacing(6)
        self.reg_role = QComboBox()
        self.reg_role.addItems(["Family / Caregiver", "Medical Staff", "Administrator"])
        self.reg_role.setFixedHeight(44)
        form.addWidget(self.reg_role)
        form.addSpacing(20)

        self.terms = QCheckBox("I accept the Terms of Use & Privacy Policy")
        form.addWidget(self.terms)
        form.addSpacing(28)

        self.btn_register = QPushButton("Create account")
        self.btn_register.setObjectName("success")
        self.btn_register.setFixedHeight(46)
        self.btn_register.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_register.clicked.connect(self._handle_register)
        form.addWidget(self.btn_register)
        form.addSpacing(24)

        switch = QHBoxLayout()
        switch.setAlignment(Qt.AlignmentFlag.AlignCenter)
        switch.setSpacing(6)
        q = QLabel("Already have an account?")
        q.setStyleSheet("color: #64748B; font-size: 13px;")
        link = QLabel("Sign in")
        link.setObjectName("link")
        link.setCursor(Qt.CursorShape.PointingHandCursor)
        
        link.mousePressEvent = lambda e: self._switch_page(0)
        
        switch.addWidget(q)
        switch.addWidget(link)
        form.addLayout(switch)
        
        form.addStretch(1)

        return self._wrap_scroll(inner)

    def _field(self, label_text, attr_name, placeholder, password=False):
        """Helper method to generate a uniform input field layout with a label and text box."""
        col = QVBoxLayout()
        col.setSpacing(6)
        col.setContentsMargins(0, 0, 0, 0)
        lbl = QLabel(label_text)
        lbl.setObjectName("fieldLabel")
        col.addWidget(lbl)
        edit = QLineEdit()
        edit.setPlaceholderText(placeholder)
        edit.setFixedHeight(44)
        if password:
            edit.setEchoMode(QLineEdit.EchoMode.Password)
        setattr(self, attr_name, edit)
        col.addWidget(edit)
        return col

    def _divider(self, text):
        """Creates a horizontal separator line with a centered text label."""
        w = QWidget()
        row = QHBoxLayout(w)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(12)
        left = QFrame()
        left.setObjectName("divider")
        left.setFrameShape(QFrame.Shape.HLine)
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #94A3B8; font-size: 12px; font-weight: 500;")
        right = QFrame()
        right.setObjectName("divider")
        right.setFrameShape(QFrame.Shape.HLine)
        row.addWidget(left, 1)
        row.addWidget(lbl)
        row.addWidget(right, 1)
        return w

    def _social_btn(self, text, icon="G"):
        """Generates a styled alternative login/social button."""
        btn = QPushButton(f"  {icon}    {text}")
        btn.setObjectName("ghost")
        btn.setFixedHeight(44)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        return btn

    def _handle_login(self):
        """Extracts login form data and triggers the login attempt callback."""
        if self.on_login_attempt:
            self.on_login_attempt(
                email=self.login_email.text().strip(),
                password=self.login_password.text(),
                remember=self.remember.isChecked(),
            )

    def _handle_register(self):
        """Extracts registration form data and triggers the register attempt callback."""
        if self.on_register_attempt:
            self.on_register_attempt(
                name=self.reg_name.text().strip(),
                email=self.reg_email.text().strip(),
                phone=self.reg_phone.text().strip(),
                password=self.reg_password.text(),
                confirm=self.reg_confirm.text(),
                role=self.reg_role.currentText(),
                terms=self.terms.isChecked(),
            )