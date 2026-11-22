"""Confirmation dialog: a 420 px card with title, body and Cancel + action, over a dimmed window.

It is drawn inside the window (a child overlay), not as a separate modal window: Qt would disable
the main window at the OS level and Windows then plays its "ding" whenever the user clicks it.
The overlay eats every click outside the card, keeps keyboard focus on its two buttons, and
`exec()` / `ask()` still wait for the answer. Esc cancels; Enter presses the focused button.
"""

from __future__ import annotations

from PySide6.QtCore import QEvent, QEventLoop, QRect, QRectF, Qt, Slot
from PySide6.QtGui import QColor, QPainter
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
from src.views.theme import Colors, Radius, Space, make_label, qcolor

WIDTH = 420
_BLUR, _DY, _ALPHA = 24, 8, 0.16


class ConfirmDialog(QWidget):
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
        layout = QVBoxLayout(self.card)
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
        window.installEventFilter(self)

    # ------------------------------------------------------------------ API
    def open(self) -> None:
        """Shows the overlay without waiting (`exec` waits for the answer)."""
        self._previous_focus = QApplication.focusWidget()
        self._place()
        self.show()
        self.raise_()
        self._initial_focus.setFocus(Qt.FocusReason.OtherFocusReason)

    def exec(self) -> bool:
        """Shows the overlay and waits; True when the user confirms."""
        self.open()
        self._loop = QEventLoop(self)
        self._loop.exec()
        self._loop = None
        return self._accepted

    @Slot()
    def accept(self) -> None:
        self._finish(True)

    @Slot()
    def reject(self) -> None:
        self._finish(False)

    @staticmethod
    def ask(parent: QWidget, title: str, body: str, action: str, *, destructive: bool = False) -> bool:
        """Asks for confirmation and returns the answer."""
        dialog = ConfirmDialog(parent, title, body, action, destructive=destructive)
        accepted = dialog.exec()
        dialog.deleteLater()
        return accepted

    def _finish(self, accepted: bool) -> None:
        self._accepted = accepted
        self.hide()
        if self._previous_focus is not None and self._previous_focus.isVisible():
            self._previous_focus.setFocus(Qt.FocusReason.OtherFocusReason)
        if self._loop is not None:
            self._loop.quit()

    # ------------------------------------------------------------------ geometry
    def card_rect(self) -> QRect:
        height = self.card.layout().totalHeightForWidth(WIDTH)
        rect = QRect(0, 0, WIDTH, height)
        rect.moveCenter(self.rect().center())
        return rect

    def _place(self) -> None:
        self.setGeometry(self._window.rect())
        self.card.setGeometry(self.card_rect())

    def eventFilter(self, watched, event) -> bool:
        if watched is self._window and event.type() == QEvent.Type.Resize and self.isVisible():
            self._place()
        return False

    # ------------------------------------------------------------------ input: the overlay is modal
    def mousePressEvent(self, event) -> None:
        event.accept()

    def mouseReleaseEvent(self, event) -> None:
        event.accept()

    def wheelEvent(self, event) -> None:
        event.accept()

    def keyPressEvent(self, event) -> None:
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
        painter = QPainter(self)
        painter.fillRect(self.rect(), qcolor(Colors.N900, 0.32))
        card = self.card.geometry()
        dpr = round(self.devicePixelRatioF(), 2)
        painter.drawPixmap(card.left() - _BLUR, card.top() - _BLUR,
                           shadow_pixmap(card.width(), card.height(), Radius.R_LG, _BLUR, _DY, _ALPHA, dpr))
        painter.setPen(QColor(Colors.N200))
        painter.setBrush(QColor(Colors.N0))
        painter.drawRect(QRectF(card).adjusted(0.5, 0.5, -0.5, -0.5))
