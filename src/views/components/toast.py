from PySide6.QtCore import (
    QAbstractAnimation,
    QEasingCurve,
    QPoint,
    QPropertyAnimation,
    QSize,
    Qt,
    QTimer,
)
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from src.views.icons import icon
from src.views.theme import Colors, apply_shadow, set_prop

# kind -> (icon name, icon colour, default title, auto-dismiss in ms)
_KINDS = {
    "success": ("check", Colors.SUCCESS, "Success", 3000),
    "info": ("info", Colors.INFO, "Information", 3500),
    "warning": ("warning", Colors.WARNING, "Warning", 4500),
    "error": ("error", Colors.DANGER, "Something went wrong", 5000),
}


class Toast(QFrame):
    """
    Discreet floating notification for routine feedback (not for fall alerts,
    which use the dedicated high-contrast banner on the video stage).

    The toast is a child of the widget it floats over and is anchored to its
    top-right corner, where it never covers primary form controls.
    """

    WIDTH = 360
    MARGIN = 24
    SLIDE = 14

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("toast")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setProperty("kind", "info")
        self.hide()

        self._hiding = False
        self._generation = 0   # invalidates stale hide callbacks when a new toast arrives
        self._target = QPoint(0, 0)

        root = QHBoxLayout(self)
        root.setContentsMargins(14, 12, 10, 12)
        root.setSpacing(12)

        self.icon_label = QLabel()
        self.icon_label.setObjectName("toastIcon")
        self.icon_label.setProperty("kind", "info")
        self.icon_label.setFixedSize(32, 32)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.icon_label, 0, Qt.AlignmentFlag.AlignTop)

        text = QVBoxLayout()
        text.setContentsMargins(0, 0, 0, 0)
        text.setSpacing(2)
        self.title_label = QLabel()
        self.title_label.setObjectName("toastTitle")
        self.message_label = QLabel()
        self.message_label.setObjectName("toastMessage")
        self.message_label.setWordWrap(True)
        text.addWidget(self.title_label)
        text.addWidget(self.message_label)
        root.addLayout(text, 1)

        self.btn_close = QPushButton()
        self.btn_close.setObjectName("toastClose")
        self.btn_close.setFixedSize(24, 24)
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.setIcon(icon("close", Colors.TEXT_SUBTLE, 14))
        self.btn_close.setIconSize(QSize(14, 14))
        self.btn_close.setToolTip("Dismiss")
        self.btn_close.clicked.connect(self.dismiss)
        root.addWidget(self.btn_close, 0, Qt.AlignmentFlag.AlignTop)

        apply_shadow(self, blur=28, y=8, alpha=60)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.dismiss)

        self._anim = QPropertyAnimation(self, b"pos", self)
        self._anim.finished.connect(self._on_anim_finished)

    # ------------------------------------------------------------------ API
    def show_message(self, kind: str, message: str, title: str | None = None, duration: int | None = None):
        if kind not in _KINDS:
            kind = "info"
        icon_name, color, default_title, default_ms = _KINDS[kind]

        for widget in (self, self.icon_label):
            set_prop(widget, "kind", kind)
        self.icon_label.setPixmap(icon(icon_name, color, 18).pixmap(QSize(18, 18)))
        self.title_label.setText(title or default_title)
        self.message_label.setText(message)

        # Arm the auto-dismiss first so the toast always closes by itself,
        # even if something below were to fail.
        self._generation += 1
        self._timer.stop()
        self._timer.start(duration if duration is not None else default_ms)

        # Order matters: clear the flag *before* stopping a running animation.
        self._hiding = False
        self._anim.stop()

        self.reposition()
        start = self._target + QPoint(0, -self.SLIDE)
        self.move(start)
        self.show()
        self.raise_()

        self._anim.setDuration(200)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.setStartValue(start)
        self._anim.setEndValue(self._target)
        self._anim.start()

    def dismiss(self, *_):
        if self.isHidden() or self._hiding:
            return

        self._timer.stop()
        self._anim.stop()
        self._hiding = True

        self._anim.setDuration(150)
        self._anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self._anim.setStartValue(self.pos())
        self._anim.setEndValue(self._target + QPoint(0, -self.SLIDE))
        self._anim.start()

        # Safety net: hide for sure even if the animation never reports `finished`.
        generation = self._generation
        QTimer.singleShot(300, lambda: self._finish_hide(generation))

    def reposition(self):
        """Size the toast for its content and anchor it to the parent's top-right."""
        parent = self.parentWidget()
        if parent is None:
            return

        width = min(self.WIDTH, max(parent.width() - 2 * self.MARGIN, 200))
        self.setFixedWidth(width)

        layout = self.layout()
        if layout is not None:
            height = max(layout.totalHeightForWidth(width), layout.minimumSize().height(), 60)
        else:
            height = 60

        self.setFixedHeight(height)
        self._target = QPoint(parent.width() - width - self.MARGIN, self.MARGIN)

        if self.isVisible() and not self._hiding and self._anim.state() != QAbstractAnimation.State.Running:
            self.move(self._target)

    # ------------------------------------------------------------- internals
    def _on_anim_finished(self):
        if self._hiding:
            self._hiding = False
            self.hide()

    def _finish_hide(self, generation: int):
        # Ignore if a newer toast has been shown since this hide was scheduled.
        if generation == self._generation and self._hiding:
            self._hiding = False
            self.hide()