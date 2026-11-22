"""Top bar of the monitoring screens.

The screen's title and today's date on the left; the signed-in user on the right, as a
button that opens the account menu (Sign out).
"""

from __future__ import annotations

from PySide6.QtCore import (
    QDate,
    QDateTime,
    QLocale,
    QPoint,
    QRect,
    QSize,
    Qt,
    QTime,
    QTimer,
    Signal,
    Slot,
)
from PySide6.QtGui import QColor, QFontMetrics, QPainter
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMenu,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.views import icons
from src.views.components.common.painting import IconView
from src.views.strings import Monitor
from src.views.theme import (
    Colors,
    Size,
    Space,
    Type,
    make_label,
    make_tabular_label,
    set_props,
)

_LOCALE = QLocale(QLocale.Language.English)
_ACCOUNT_HEIGHT = 44
_IDENTITY_WIDTH = 200


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


class Avatar(QWidget):
    """32 px circle with the user's initials."""
    def __init__(self, name: str, parent: QWidget | None = None):
        super().__init__(parent)
        self._initials = initials(name)
        self.setFixedSize(32, 32)
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


class AccountButton(QPushButton):
    """The signed-in user (avatar, name, role and a chevron) as one button that opens the account menu.

    The menu opens under the button, as wide as it, and holds "Sign out" (also Ctrl+Shift+Q on the
    monitoring screen). It works from the keyboard too: Tab to the button, Enter or Space to open it,
    the arrows to move and Enter to choose.
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

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 0, 10, 0)
        layout.setSpacing(Space.S2)
        layout.addWidget(Avatar(user_name or "?"), 0, Qt.AlignmentFlag.AlignVCenter)
        identity = QVBoxLayout()
        identity.setContentsMargins(0, 0, 0, 0)
        identity.setSpacing(0)
        identity.addStretch(1)
        for text, role, tone in ((user_name, "body-strong", None), (user_role, "caption", "secondary")):
            label = make_label("", role, tone)
            metrics = QFontMetrics(Type.font(role))
            label.setText(metrics.elidedText(text or "", Qt.TextElideMode.ElideRight, _IDENTITY_WIDTH))
            label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
            identity.addWidget(label)
        identity.addStretch(1)
        layout.addLayout(identity)
        layout.addSpacing(Space.S1)
        layout.addWidget(IconView("chevron-down", Colors.N500, 16), 0, Qt.AlignmentFlag.AlignVCenter)
        for child in self.findChildren(QWidget):      # the whole button takes the clicks
            child.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.menu = QMenu(self)
        self.menu.setAccessibleName(Monitor.ACCOUNT_MENU)
        # The text after the tab is drawn right-aligned, as the shortcut hint of a menu item.
        self.sign_out_action = self.menu.addAction(icons.icon("log-out", Colors.N700, 16),
                                                   f"{Monitor.SIGN_OUT}\t{Monitor.SIGN_OUT_SHORTCUT}")
        self.sign_out_action.triggered.connect(self.sign_out_requested)
        self.menu.aboutToShow.connect(self._on_menu_shown)
        self.menu.aboutToHide.connect(self._on_menu_hidden)
        self.clicked.connect(self.open_menu)

    def sizeHint(self) -> QSize:
        """Preferred size: its content's width and the fixed height."""
        return QSize(self.layout().sizeHint().width(), _ACCOUNT_HEIGHT)

    def minimumSizeHint(self) -> QSize:
        """The button never shrinks below its preferred size."""
        return self.sizeHint()

    @Slot()
    def open_menu(self) -> None:
        """Shows the menu right under the button, right-aligned with it.

        It is at least as wide as the button, so a wider menu grows to the left instead of past
        the window's edge.
        """
        self.menu.setMinimumWidth(self.width())
        width = max(self.width(), self.menu.sizeHint().width())
        self.menu.popup(self.mapToGlobal(QPoint(self.width() - width, self.height() + Space.S1)))

    @Slot()
    def _on_menu_shown(self) -> None:
        set_props(self, open=True)        # keeps the pressed look while the menu is open

    @Slot()
    def _on_menu_hidden(self) -> None:
        set_props(self, open=False)


class Topbar(QWidget):
    """Top bar: title and date, and the account button.

    Signals:
        sign_out_clicked: The user chose Sign out in the account menu.
    """
    sign_out_clicked = Signal()

    def __init__(self, section: str, user_name: str, user_role: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("Topbar")
        self.setFixedHeight(Size.TOPBAR)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(Space.S6, 0, Space.S6, 1)
        layout.setSpacing(0)

        # Left: what this screen is (e.g. "Administration Monitoring") and, under it, today's date.
        heading = QVBoxLayout()
        heading.setContentsMargins(0, 0, 0, 0)
        heading.setSpacing(0)
        heading.addStretch(1)
        self.title = make_label(section, "title-md")
        heading.addWidget(self.title)
        self.clock = make_tabular_label("", "caption", "secondary", sample=_widest_clock_sample())
        heading.addWidget(self.clock)
        heading.addStretch(1)
        layout.addLayout(heading)
        layout.addStretch(1)

        # Right: the signed-in user; clicking it opens the account menu (Sign out).
        self.account = AccountButton(user_name, user_role)
        self.account.sign_out_requested.connect(self.sign_out_clicked)
        layout.addWidget(self.account, 0, Qt.AlignmentFlag.AlignVCenter)

        self._clock_timer = QTimer(self)
        self._clock_timer.setSingleShot(True)
        self._clock_timer.timeout.connect(self._tick)
        self._tick()

    @Slot()
    def _tick(self) -> None:
        """Updates the clock and schedules the next update at the start of the next minute."""
        now = QDateTime.currentDateTime()
        self.clock.setText(_LOCALE.toString(now, Monitor.CLOCK_FORMAT))
        time = now.time()
        self._clock_timer.start((60 - time.second()) * 1000 - time.msec() + 5)

    def sizeHint(self) -> QSize:
        """Preferred size of the bar."""
        return QSize(1120, Size.TOPBAR)

    def paintEvent(self, event) -> None:
        """Paints the white bar and its bottom border."""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(Colors.N0))
        painter.fillRect(QRect(0, self.height() - 1, self.width(), 1), QColor(Colors.N200))
