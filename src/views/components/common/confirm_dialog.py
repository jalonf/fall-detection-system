"""Confirmation dialog: 420 px card, title, body and Cancel + action buttons. Esc cancels."""

from __future__ import annotations

from PySide6.QtCore import QPoint, QRectF, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QDialog, QHBoxLayout, QVBoxLayout, QWidget

from src.views.components.common.button import Button
from src.views.components.common.painting import shadow_pixmap
from src.views.strings import Common
from src.views.theme import Colors, Radius, Space, make_label

WIDTH = 420
_BLUR, _DY, _ALPHA = 24, 8, 0.16


class ConfirmDialog(QDialog):
    def __init__(self, parent: QWidget, title: str, body: str, action: str, *, destructive: bool = False):
        super().__init__(parent, Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.setWindowTitle(title)
        self.setAccessibleName(title)
        self.setAccessibleDescription(body)

        margin_top, margin_bottom = _BLUR - _DY, _BLUR + _DY
        layout = QVBoxLayout(self)
        layout.setContentsMargins(_BLUR + Space.S6, margin_top + Space.S6, _BLUR + Space.S6, margin_bottom + Space.S6)
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
        self.cancel_button.setAutoDefault(True)
        self.action_button.setAutoDefault(True)
        self._initial_focus = self.cancel_button if destructive else self.action_button
        self._initial_focus.setDefault(True)
        self.setTabOrder(self.cancel_button, self.action_button)
        self.setFixedWidth(WIDTH + 2 * _BLUR)

    def card_rect(self) -> QRectF:
        return QRectF(_BLUR, _BLUR - _DY, WIDTH, self.height() - 2 * _BLUR)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.adjustSize()
        owner = self.parentWidget().window() if self.parentWidget() else None
        if owner is not None:
            center = owner.mapToGlobal(owner.rect().center())
            self.move(center - QPoint(self.width() // 2, self.height() // 2))
        self._initial_focus.setFocus(Qt.FocusReason.OtherFocusReason)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        card = self.card_rect()
        dpr = round(self.devicePixelRatioF(), 2)
        painter.drawPixmap(round(card.left()) - _BLUR, round(card.top()) - _BLUR,
                           shadow_pixmap(round(card.width()), round(card.height()), Radius.R_LG, _BLUR, _DY, _ALPHA, dpr))
        painter.setPen(QColor(Colors.N200))
        painter.setBrush(QColor(Colors.N0))
        painter.drawRoundedRect(card.adjusted(0.5, 0.5, -0.5, -0.5), Radius.R_LG, Radius.R_LG)

    @staticmethod
    def ask(parent: QWidget, title: str, body: str, action: str, *, destructive: bool = False) -> bool:
        """Shows the dialog modally; True when the user confirms."""
        dialog = ConfirmDialog(parent, title, body, action, destructive=destructive)
        accepted = dialog.exec() == QDialog.DialogCode.Accepted
        dialog.deleteLater()
        return accepted
