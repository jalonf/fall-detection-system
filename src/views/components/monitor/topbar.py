"""Top bar of the dashboards.

Left: the application's mark, then the tabs (caregivers) or the page's title (administrators, who
have a single page). Right: today's date and time, and the signed-in user as a button that opens the
account menu (the user's role and Sign out). No internal names are shown: no product name, no role
under the user's name and no technical section names.

The current tab is underlined; the underline glides to the new tab instead of jumping to it.
"""

from __future__ import annotations

from PySide6.QtCore import (
    QDate,
    QDateTime,
    QLocale,
    QPoint,
    QRect,
    QRectF,
    QSize,
    Qt,
    QTime,
    QTimer,
    QVariantAnimation,
    Signal,
    Slot,
)
from PySide6.QtGui import QColor, QFontMetrics, QPainter
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QMenu,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
    QWidgetAction,
)

from src.views import icons
from src.views.components.common.painting import Divider, IconView
from src.views.strings import Monitor
from src.views.theme import (
    Colors,
    Motion,
    Size,
    Space,
    Type,
    make_label,
    make_tabular_label,
    set_props,
)

_LOCALE = QLocale(QLocale.Language.English)
_ACCOUNT_HEIGHT = 40
_NAME_WIDTH = 180          # longer names are elided
_MARK = 28
_INDICATOR = 2             # thickness of the current tab's underline


def initials(name: str) -> str:
    """Returns the initials shown in the avatar.

    Args:
        name: The user's full name.

    Returns:
        The first letters of the first two words, the first two letters of a single word, or "?".
    """
    words = [word for word in name.split() if word]
    if not words:
        return "?"
    if len(words) == 1:
        return words[0][:2].upper()
    return (words[0][0] + words[1][0]).upper()


def _widest_clock_sample() -> str:
    metrics = QFontMetrics(Type.font("caption", tabular=True))
    samples = []
    for month in range(1, 13):
        for day in (1, 7):     # every weekday name
            date = QDate(2024, month, 20 + day)
            samples.append(_LOCALE.toString(QDateTime(date, QTime(0, 0)), Monitor.CLOCK_FORMAT))
    return max(samples, key=metrics.horizontalAdvance)


class BrandMark(QWidget):
    """The application's logo (`icons.logo_pixmap`), in place of a written name."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedSize(_MARK, _MARK)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def paintEvent(self, event) -> None:
        """Paints the logo, rendered for the screen's pixel ratio."""
        QPainter(self).drawPixmap(0, 0, icons.logo_pixmap(_MARK, self.devicePixelRatioF()))


class Avatar(QWidget):
    """28 px circle with the user's initials."""

    def __init__(self, name: str, size: int = 28, parent: QWidget | None = None):
        super().__init__(parent)
        self._initials = initials(name)
        self.setFixedSize(size, size)
        self.setAccessibleName(name)

    def paintEvent(self, event) -> None:
        """Paints the circle and the initials."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(Colors.P100))
        painter.drawEllipse(self.rect())
        painter.setFont(Type.font("caption-strong"))
        painter.setPen(QColor(Colors.P700))
        painter.drawText(self.rect(), int(Qt.AlignmentFlag.AlignCenter), self._initials)


def _account_header(user_name: str, user_role: str) -> QWidget:
    """First row of the account menu: who is signed in, and as what (not clickable)."""
    header = QWidget()
    layout = QVBoxLayout(header)
    layout.setContentsMargins(Space.S3, Space.S2, Space.S6, Space.S2)
    layout.setSpacing(0)
    layout.addWidget(make_label(user_name, "body-strong"))
    if user_role:
        layout.addWidget(make_label(user_role, "caption", "secondary"))
    return header


class AccountButton(QPushButton):
    """The signed-in user (avatar, name and a chevron) as one button that opens the account menu.

    The menu opens under the button, right-aligned with it: who is signed in and their role, then
    "Sign out" (also Ctrl+Shift+Q). It works from the keyboard too: Tab to the button, Enter or Space
    to open it, the arrows to move and Enter to choose.
    """

    sign_out_requested = Signal()

    def __init__(self, user_name: str, user_role: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("AccountButton")
        self.setFixedHeight(_ACCOUNT_HEIGHT)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.setToolTip(Monitor.ACCOUNT_TIP)
        self.setAccessibleName(Monitor.ACCOUNT_NAME.format(name=user_name or "", role=user_role or ""))

        layout = self._layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 0, 8, 0)
        layout.setSpacing(Space.S2)
        layout.addWidget(Avatar(user_name or "?"), 0, Qt.AlignmentFlag.AlignVCenter)
        name = make_label("", "body-strong")
        name.setText(QFontMetrics(Type.font("body-strong")).elidedText(
            user_name or "", Qt.TextElideMode.ElideRight, _NAME_WIDTH))
        name.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        layout.addWidget(name, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(IconView("chevron-down", Colors.N500, 16), 0, Qt.AlignmentFlag.AlignVCenter)
        for child in self.findChildren(QWidget):      # the whole button takes the clicks
            child.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self._menu = QMenu(self)
        self._menu.setAccessibleName(Monitor.ACCOUNT_MENU)
        header = QWidgetAction(self._menu)
        header.setDefaultWidget(_account_header(user_name, user_role))
        header.setEnabled(False)
        self._menu.addAction(header)
        self._menu.addSeparator()
        # The text after the tab is drawn right-aligned, as the shortcut hint of a menu item.
        self.sign_out_action = self._menu.addAction(icons.icon("log-out", Colors.N700, 16),
                                                   f"{Monitor.SIGN_OUT}\t{Monitor.SIGN_OUT_SHORTCUT}")
        self.sign_out_action.triggered.connect(self.sign_out_requested)
        self._menu.aboutToShow.connect(lambda: set_props(self, open=True))   # keeps the pressed look
        self._menu.aboutToHide.connect(lambda: set_props(self, open=False))
        self.clicked.connect(self.open_menu)

    def sizeHint(self) -> QSize:
        """Preferred size: its content's width and the fixed height."""
        return QSize(self._layout.sizeHint().width(), _ACCOUNT_HEIGHT)

    def minimumSizeHint(self) -> QSize:
        """The button never shrinks below its preferred size."""
        return self.sizeHint()

    @Slot()
    def open_menu(self) -> None:
        """Shows the menu right under the button, right-aligned with it.

        It is at least as wide as the button, so a wider menu grows to the left instead of past
        the window's edge.
        """
        self._menu.setMinimumWidth(max(self.width(), 220))
        width = max(self.width(), self._menu.sizeHint().width())
        self._menu.popup(self.mapToGlobal(QPoint(self.width() - width, self.height() + Space.S1)))


class NavTab(QPushButton):
    """One tab of the top bar: its text. The underline of the current tab is painted by the bar."""

    def __init__(self, text: str, parent: QWidget | None = None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)      # repaint when the pointer enters or leaves
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.setFixedHeight(Size.TOPBAR - 1)
        width = QFontMetrics(Type.font("body-strong")).horizontalAdvance(text)
        self.setFixedWidth(width + 2 * Space.S4)

    def paintEvent(self, event) -> None:
        """Paints the text: N900 when current or hovered, N600 otherwise, N400 when locked."""
        painter = QPainter(self)
        current = self.isChecked()
        if not self.isEnabled():
            color = Colors.N400
        elif current or self.underMouse():
            color = Colors.N900
        else:
            color = Colors.N600
        painter.setFont(Type.font("body-strong" if current else "body"))
        painter.setPen(QColor(color))
        painter.drawText(self.rect(), int(Qt.AlignmentFlag.AlignCenter), self.text())
        if self.underMouse() and not current and self.isEnabled():
            painter.fillRect(QRect(Space.S2, self.height() - _INDICATOR, self.width() - 2 * Space.S2, _INDICATOR),
                             QColor(Colors.N200))
        if self.hasFocus():
            painter.setPen(QColor(Colors.P600))
            painter.drawRect(self.rect().adjusted(0, Space.S2, -1, -Space.S2 - 1))


class Topbar(QWidget):
    """Top bar: the mark, the tabs (or the page's title), the clock and the account button.

    Signals:
        sign_out_clicked: The user chose Sign out in the account menu.
        tab_changed(int): The user chose another tab.

    Args:
        user_name: Name of the signed-in user.
        user_role: Their role, shown in the account menu.
        parent: Parent widget.
        tabs: The tabs' names; none for a single page.
        title: The page's title, shown when there are no tabs.
    """
    sign_out_clicked = Signal()
    tab_changed = Signal(int)

    def __init__(self, user_name: str, user_role: str, parent: QWidget | None = None, *,
                 tabs: tuple[str, ...] = (), title: str = ""):
        super().__init__(parent)
        self.setObjectName("Topbar")
        self.setFixedHeight(Size.TOPBAR)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(Space.S6, 0, Space.S5, 1)
        layout.setSpacing(0)

        layout.addWidget(BrandMark(), 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addSpacing(Space.S5)
        layout.addWidget(Divider(Colors.N200, vertical=True, length=Space.S6), 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addSpacing(Space.S2)

        # Caregivers: the tabs, aligned with the bottom border. Administrators: the page's title.
        self.tabs: list[NavTab] = []
        self._tab_group = QButtonGroup(self)
        self._tab_group.setExclusive(True)
        for index, text in enumerate(tabs):
            tab = NavTab(text)
            self._tab_group.addButton(tab, index)
            self.tabs.append(tab)
            layout.addWidget(tab, 0, Qt.AlignmentFlag.AlignBottom)
        if self.tabs:
            self.tabs[0].setChecked(True)
            self._tab_group.idClicked.connect(self.tab_changed)
        else:
            layout.addSpacing(Space.S2)
            self.title = make_label(title, "title-sm")
            layout.addWidget(self.title, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addStretch(1)

        # Right: the date and time, then the signed-in user (the account menu).
        self.clock = make_tabular_label("", "caption", "secondary", sample=_widest_clock_sample())
        self.clock.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.clock, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addSpacing(Space.S4)
        layout.addWidget(Divider(Colors.N200, vertical=True, length=Space.S6), 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addSpacing(Space.S3)
        self.account = AccountButton(user_name, user_role)
        self.account.sign_out_requested.connect(self.sign_out_clicked)
        layout.addWidget(self.account, 0, Qt.AlignmentFlag.AlignVCenter)

        # The underline of the current tab, animated between tabs.
        self._indicator = QRectF()
        self._glide = QVariantAnimation(self)
        self._glide.setDuration(Motion.SLOW)
        self._glide.setEasingCurve(Motion.OUT)
        self._glide.valueChanged.connect(self._on_glide)

        self._clock_timer = QTimer(self)
        self._clock_timer.setSingleShot(True)
        self._clock_timer.timeout.connect(self._tick)
        self._tick()

    # ------------------------------------------------------------------ tabs
    def set_current_tab(self, index: int) -> None:
        """Marks a tab as the current one (without emitting `tab_changed`); the underline glides to it."""
        start = self._indicator_rect()
        self.tabs[index].setChecked(True)
        end = self._indicator_rect()
        if self.isVisible() and not start.isNull() and start != end:
            self._glide.stop()
            self._glide.setStartValue(start)
            self._glide.setEndValue(end)
            self._glide.start()
        else:
            self.update()

    def set_tab_enabled(self, index: int, enabled: bool, tooltip: str = "") -> None:
        """Enables or disables a tab; a disabled tab explains why in its tooltip."""
        tab = self.tabs[index]
        tab.setEnabled(enabled)
        tab.setToolTip("" if enabled else tooltip)

    def _indicator_rect(self) -> QRectF:
        """Where the underline of the current tab rests."""
        tab = self._tab_group.checkedButton()
        if tab is None:
            return QRectF()
        geometry = tab.geometry()
        return QRectF(geometry.left() + Space.S2, self.height() - 1 - _INDICATOR,
                      geometry.width() - 2 * Space.S2, _INDICATOR)

    @Slot("QVariant")
    def _on_glide(self, value) -> None:
        self._indicator = QRectF(value)
        self.update(0, self.height() - 1 - _INDICATOR, self.width(), _INDICATOR)

    # ------------------------------------------------------------------ clock
    @Slot()
    def _tick(self) -> None:
        """Updates the clock and schedules the next update at the start of the next minute."""
        now = QDateTime.currentDateTime()
        self.clock.setText(_LOCALE.toString(now, Monitor.CLOCK_FORMAT))
        time = now.time()
        self._clock_timer.start((60 - time.second()) * 1000 - time.msec() + 5)

    # ------------------------------------------------------------------ painting
    def sizeHint(self) -> QSize:
        """Preferred size of the bar."""
        return QSize(1120, Size.TOPBAR)

    def paintEvent(self, event) -> None:
        """Paints the white bar, its bottom border and the current tab's underline."""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(Colors.N0))
        painter.fillRect(QRect(0, self.height() - 1, self.width(), 1), QColor(Colors.N200))
        if self.tabs:
            gliding = self._glide.state() == QVariantAnimation.State.Running
            painter.fillRect(self._indicator if gliding else self._indicator_rect(), QColor(Colors.P600))
