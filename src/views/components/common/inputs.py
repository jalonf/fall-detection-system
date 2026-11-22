"""Text inputs and combo boxes of the design system."""

from __future__ import annotations

from PySide6.QtCore import QModelIndex, QRect, QSize, Qt, Slot
from PySide6.QtGui import QAction, QColor, QPainter
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QLineEdit,
    QListView,
    QRadioButton,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QWidget,
)

from src.dtos import password_policy
from src.views import icons
from src.views.strings import Common
from src.views.theme import Colors, Size, Type

_HEIGHT = {"sm": Size.H_SM, "md": Size.H_MD, "lg": Size.H_LG}


def _restyle_clear_button(edit: QLineEdit) -> None:
    action = edit.findChild(QAction, "_q_qlineeditclearaction")
    if action is not None:
        action.setIcon(icons.icon("x", Colors.N500, 16))
        action.setText(Common.CLEAR_TEXT)


def make_line_edit(placeholder: str = "", icon: str | None = None, *, clearable: bool = True,
                   size: str = "lg", parent: QWidget | None = None) -> QLineEdit:
    """Line edit with an optional leading icon and a clear button."""
    edit = QLineEdit(parent)
    edit.setPlaceholderText(placeholder)
    edit.setFixedHeight(_HEIGHT[size])
    if icon:
        edit.addAction(icons.icon(icon, Colors.N500, 16), QLineEdit.ActionPosition.LeadingPosition)
        edit.setProperty("leading", True)
    if clearable:
        edit.setClearButtonEnabled(True)
        _restyle_clear_button(edit)
    return edit


class PasswordEdit(QLineEdit):
    """Password field with a lock icon and a show / hide action.

    It takes at most 72 characters (a non-ASCII password can still pass 72 bytes: see
    `password_policy.too_long`).

    Args:
        placeholder: Placeholder text.
        size: sm, md or lg height.
        parent: Parent widget.
    """

    def __init__(self, placeholder: str = "", *, size: str = "lg", parent: QWidget | None = None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setFixedHeight(_HEIGHT[size])
        self.setMaxLength(password_policy.MAX_BYTES)
        self.setEchoMode(QLineEdit.EchoMode.Password)
        self.addAction(icons.icon("lock", Colors.N500, 16), QLineEdit.ActionPosition.LeadingPosition)
        self.setProperty("leading", True)
        self._toggle = self.addAction(icons.icon("eye", Colors.N500, 16), QLineEdit.ActionPosition.TrailingPosition)
        self._toggle.triggered.connect(self._on_toggle)
        self._revealed = False
        self._sync_toggle()

    def set_revealed(self, revealed: bool) -> None:
        """Shows or hides the password's characters.

        Args:
            revealed: True to show them.
        """
        self._revealed = revealed
        self.setEchoMode(QLineEdit.EchoMode.Normal if revealed else QLineEdit.EchoMode.Password)
        self._sync_toggle()

    def is_revealed(self) -> bool:
        """True while the characters are shown."""
        return self._revealed

    @Slot()
    def _on_toggle(self) -> None:
        self.set_revealed(not self._revealed)

    def _sync_toggle(self) -> None:
        name = "eye-off" if self._revealed else "eye"
        text = Common.HIDE_PASSWORD if self._revealed else Common.SHOW_PASSWORD
        self._toggle.setIcon(icons.icon(name, Colors.N500, 16))
        self._toggle.setText(text)
        self._toggle.setToolTip(text)


class CheckBox(QCheckBox):
    """Check box whose whole row is clickable."""

    def __init__(self, text: str, parent: QWidget | None = None):
        super().__init__(text, parent)
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.setMinimumHeight(Type.line_height("body"))

    def hitButton(self, pos) -> bool:
        """The whole row, label included, toggles the box."""
        return self.rect().contains(pos)


class RadioButton(QRadioButton):
    """Radio button whose whole row is clickable."""

    def __init__(self, text: str, parent: QWidget | None = None):
        super().__init__(text, parent)
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.setMinimumHeight(Type.line_height("body"))

    def hitButton(self, pos) -> bool:
        """The whole row, label included, checks the button."""
        return self.rect().contains(pos)


class ComboItemDelegate(QStyledItemDelegate):
    """Popup rows of 32 px: hover N100, the current item P50 / P700 with a check mark."""

    ROW = 32

    def __init__(self, combo: QComboBox):
        super().__init__(combo)
        self._combo = combo

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        """Every row of the popup is 32 px tall."""
        return QSize(option.rect.width(), self.ROW)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """Paints a popup row: hover fill, and the current item in P50 with a tick."""
        rect = option.rect
        current = index.row() == self._combo.currentIndex()
        hovered = bool(option.state & (QStyle.StateFlag.State_MouseOver | QStyle.StateFlag.State_Selected))
        painter.save()
        if current:
            painter.fillRect(rect, QColor(Colors.P100 if hovered else Colors.P50))
        elif hovered:
            painter.fillRect(rect, QColor(Colors.N100))
        font = Type.font("body-strong" if current else "body")
        painter.setFont(font)
        painter.setPen(QColor(Colors.P700 if current else Colors.N900))
        text_rect = rect.adjusted(12, 0, -36, 0)
        painter.drawText(text_rect, int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                         painter.fontMetrics().elidedText(index.data() or "", Qt.TextElideMode.ElideRight,
                                                          text_rect.width()))
        if current:
            pixmap = icons.icon_pixmap("check", Colors.P700, 16, painter.device().devicePixelRatioF())
            painter.drawPixmap(QRect(rect.right() - 12 - 16, rect.center().y() - 8, 16, 16), pixmap)
        painter.restore()


class Combo(QComboBox):
    """Combo box sized md (36) or sm (28) whose popup items follow the design system."""

    def __init__(self, items: list[str] | tuple[str, ...] = (), *, size: str = "md", width: int | None = None,
                 accessible_name: str = "", parent: QWidget | None = None):
        super().__init__(parent)
        self.setView(QListView())
        self.setItemDelegate(ComboItemDelegate(self))
        self.view().setMouseTracking(True)
        self.addItems(list(items))
        self.setFixedHeight(_HEIGHT[size])
        if width:
            self.setFixedWidth(width)
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        if accessible_name:
            self.setAccessibleName(accessible_name)
