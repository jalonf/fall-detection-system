"""Confirmation dialog: a 420 px card with title, body and Cancel + action, over a dimmed window.

It is drawn inside the window (a child overlay), not as a separate modal window: Qt would disable
the main window at the OS level and Windows then plays its "ding" whenever the user clicks it.
The overlay eats every click outside the card, keeps keyboard focus on its two buttons, and
`exec()` / `ask()` still wait for the answer. Esc cancels; Enter presses the focused button.

It fades in (the dimming and a snapshot of the card, which rises a few pixels) and fades out a
little faster. The answer never waits for the fade: `exec()` returns as soon as a button is pressed.
"""

from __future__ import annotations

from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QEvent,
    QEventLoop,
    QPropertyAnimation,
    QRect,
    QRectF,
    Qt,
    Slot,
)
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import (
    QAbstractButton,
    QApplication,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)

from src.views.components.common.button import Button
from src.views.components.common.painting import shadow_pixmap
from src.views.strings import Common
from src.views.theme import Colors, Motion, Radius, Space, make_label, qcolor

WIDTH = 420
_BLUR, _DY, _ALPHA = 24, 8, 0.16
_DIM = 0.32          # opacity of the dimming once fully shown
_RISE = 8            # the card rises this far while it fades in


class ConfirmDialog(QWidget):
    """Confirmation drawn inside the window over a dimmed background.

    Args:
        parent: Any widget of the window it covers.
        title: Question asked.
        body: Explanation under the title.
        action: Text of the confirm button.
        destructive: Red confirm button, and the focus starts on Cancel.
    """
    def __init__(self, parent: QWidget, title: str, body: str, action: str, *, destructive: bool = False):
        window = parent.window()
        super().__init__(window)
        self.hide()
        self._window = window
        self._accepted = False
        self._loop: QEventLoop | None = None
        self._previous_focus: QWidget | None = None
        self.setAccessibleName(title)
        self.setAccessibleDescription(body)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.card = QWidget(self)
        layout = self._card_layout = QVBoxLayout(self.card)
        layout.setContentsMargins(Space.S6, Space.S6, Space.S6, Space.S6)
        layout.setSpacing(0)
        self.title_label = make_label(title, "title-md", wrap=True)
        layout.addWidget(self.title_label)
        layout.addSpacing(Space.S2)
        self.body_label = make_label(body, "body", "body", wrap=True)
        layout.addWidget(self.body_label)
        layout.addSpacing(Space.S6)
        buttons = QHBoxLayout()
        buttons.setContentsMargins(0, 0, 0, 0)
        buttons.setSpacing(Space.S2)
        buttons.addStretch(1)
        self.cancel_button = Button(Common.CANCEL, "secondary", "md")
        self.action_button = Button(action, "danger" if destructive else "primary", "md")
        buttons.addWidget(self.cancel_button)
        buttons.addWidget(self.action_button)
        layout.addLayout(buttons)

        self.cancel_button.clicked.connect(self.reject)
        self.action_button.clicked.connect(self.accept)
        self._initial_focus = self.cancel_button if destructive else self.action_button
        self._delete_when_closed = False
        self._snapshot = QPixmap()
        self._shown = 0.0
        self._fade = QPropertyAnimation(self, b"shown", self)
        self._fade.finished.connect(self._on_fade_finished)
        window.installEventFilter(self)

    def _get_shown(self) -> float:
        return self._shown

    def _set_shown(self, value: float) -> None:
        self._shown = value
        self.update()

    shown = Property(float, _get_shown, _set_shown)

    # ------------------------------------------------------------------ API
    def open(self) -> None:
        """Fades the overlay in without waiting (`exec` waits for the answer)."""
        self._previous_focus = QApplication.focusWidget()
        self._place()
        self._snapshot = self.card.grab()
        self.card.hide()                 # the snapshot stands in for it while it fades in
        self.show()
        self.raise_()
        self.setFocus(Qt.FocusReason.OtherFocusReason)
        self._animate(1.0, Motion.BASE, Motion.OUT)

    def exec(self) -> bool:
        """Shows the overlay and waits; True when the user confirms."""
        self.open()
        self._loop = QEventLoop(self)
        self._loop.exec()
        self._loop = None
        return self._accepted

    @Slot()
    def accept(self) -> None:
        """Closes the dialog with a confirmation."""
        self._finish(True)

    @Slot()
    def reject(self) -> None:
        """Closes the dialog without confirming."""
        self._finish(False)

    @staticmethod
    def ask(parent: QWidget, title: str, body: str, action: str, *, destructive: bool = False) -> bool:
        """Asks for confirmation and returns the answer (the dialog deletes itself once faded out)."""
        dialog = ConfirmDialog(parent, title, body, action, destructive=destructive)
        dialog._delete_when_closed = True
        return dialog.exec()

    def _finish(self, accepted: bool) -> None:
        if not self.isVisible() or self.testAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents):
            return               # already answered: it is fading out
        self._accepted = accepted
        self._snapshot = self.card.grab()
        self.card.hide()
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)   # the window is usable at once
        if self._previous_focus is not None and self._previous_focus.isVisible():
            self._previous_focus.setFocus(Qt.FocusReason.OtherFocusReason)
        self._animate(0.0, Motion.FAST, Motion.IN)
        if self._loop is not None:
            self._loop.quit()

    def _animate(self, end: float, duration: int, curve) -> None:
        self._fade.stop()
        self._fade.setDuration(duration)
        self._fade.setEasingCurve(QEasingCurve(curve))
        self._fade.setStartValue(self._shown)
        self._fade.setEndValue(end)
        self._fade.start()

    @Slot()
    def _on_fade_finished(self) -> None:
        if self._shown >= 1.0:           # faded in: the real card takes over, with the focus
            self.card.show()
            self._snapshot = QPixmap()
            self._initial_focus.setFocus(Qt.FocusReason.OtherFocusReason)
            return
        self.hide()
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        if self._delete_when_closed:
            self.deleteLater()

    # ------------------------------------------------------------------ geometry
    def card_rect(self) -> QRect:
        """Returns the card's geometry, centred in the window."""
        height = self._card_layout.totalHeightForWidth(WIDTH)
        rect = QRect(0, 0, WIDTH, height)
        rect.moveCenter(self.rect().center())
        return rect

    def _place(self) -> None:
        self.setGeometry(self._window.rect())
        self.card.setGeometry(self.card_rect())
        self._card_layout.activate()     # laid out before the first snapshot, while still hidden

    def eventFilter(self, watched, event) -> bool:
        """Keeps the overlay covering the window when the window is resized."""
        if watched is self._window and event.type() == QEvent.Type.Resize and self.isVisible():
            self._place()
        return False

    # ------------------------------------------------------------------ input: the overlay is modal
    def mousePressEvent(self, event) -> None:
        """Swallows clicks outside the card: the overlay is modal."""
        event.accept()

    def mouseReleaseEvent(self, event) -> None:
        """Swallows clicks outside the card: the overlay is modal."""
        event.accept()

    def wheelEvent(self, event) -> None:
        """Swallows scrolling: the content behind must not move."""
        event.accept()

    def keyPressEvent(self, event) -> None:
        """Esc cancels; Enter presses the focused button."""
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            focused = self.focusWidget()
            (focused if isinstance(focused, QAbstractButton) else self._initial_focus).click()
        event.accept()

    def focusNextPrevChild(self, next_child: bool) -> bool:
        """Tab moves between the two buttons only."""
        target = self.action_button if self.focusWidget() is self.cancel_button else self.cancel_button
        target.setFocus(Qt.FocusReason.TabFocusReason)
        return True

    # ------------------------------------------------------------------ painting
    def paintEvent(self, event) -> None:
        """Paints the dimmed background, the card's shadow and the card (its snapshot while fading)."""
        painter = QPainter(self)
        shown = self._shown
        painter.fillRect(self.rect(), qcolor(Colors.N900, _DIM * shown))
        card = self.card.geometry().translated(0, round(_RISE * (1.0 - shown)))
        dpr = round(self.devicePixelRatioF(), 2)
        painter.setOpacity(shown)
        painter.drawPixmap(card.left() - _BLUR, card.top() - _BLUR,
                           shadow_pixmap(card.width(), card.height(), Radius.R_LG, _BLUR, _DY, _ALPHA, dpr))
        painter.setPen(QColor(Colors.N200))
        painter.setBrush(QColor(Colors.N0))
        painter.drawRect(QRectF(card).adjusted(0.5, 0.5, -0.5, -0.5))
        if not self._snapshot.isNull():
            painter.drawPixmap(card.topLeft(), self._snapshot)
