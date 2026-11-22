"""Top bar: wordmark and section on the left; clock, user and sign out on the right."""

from __future__ import annotations

from PySide6.QtCore import (
    QDate,
    QDateTime,
    QLocale,
    QRect,
    QSize,
    Qt,
    QTime,
    QTimer,
    Signal,
    Slot,
)
from PySide6.QtGui import QColor, QFontMetrics, QPainter
from PySide6.QtWidgets import QHBoxLayout, QSizePolicy, QVBoxLayout, QWidget

from src.views.components.common.button import make_button
from src.views.components.common.painting import Divider
from src.views.strings import Monitor
from src.views.theme import (
    APP_NAME,
    Colors,
    Size,
    Space,
    Type,
    make_label,
    make_tabular_label,
)

_LOCALE = QLocale(QLocale.Language.English)


def initials(name: str) -> str:
    words = [word for word in name.split() if word]
    if not words:
        return "?"
    if len(words) == 1:
        return words[0][:2].upper()
    return (words[0][0] + words[1][0]).upper()


def _widest_clock_sample() -> str:
    metrics = QFontMetrics(Type.font("body", tabular=True))
    samples = []
    for month in range(1, 13):
        for day in (1, 7):     # every weekday name
            date = QDate(2024, month, 20 + day)
            samples.append(_LOCALE.toString(QDateTime(date, QTime(0, 0)), Monitor.CLOCK_FORMAT))
    return max(samples, key=metrics.horizontalAdvance)


class Avatar(QWidget):
    def __init__(self, name: str, parent: QWidget | None = None):
        super().__init__(parent)
        self._initials = initials(name)
        self.setFixedSize(32, 32)
        self.setAccessibleName(name)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(Colors.P100))
        painter.drawEllipse(self.rect())
        painter.setFont(Type.font("caption-strong"))
        painter.setPen(QColor(Colors.P700))
        painter.drawText(self.rect(), int(Qt.AlignmentFlag.AlignCenter), self._initials)


class Topbar(QWidget):
    sign_out_clicked = Signal()

    def __init__(self, section: str, user_name: str, user_role: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("Topbar")
        self.setFixedHeight(Size.TOPBAR)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(Space.S6, 0, Space.S6, 1)
        layout.setSpacing(0)

        layout.addWidget(make_label(APP_NAME, "title-md"))
        layout.addSpacing(Space.S3)
        layout.addWidget(Divider(Colors.N200, vertical=True, length=20))
        layout.addSpacing(Space.S3)
        layout.addWidget(make_label(section, "body", "secondary"))
        layout.addStretch(1)

        self.clock = make_tabular_label("", "body", "secondary", sample=_widest_clock_sample())
        self.clock.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.clock)
        layout.addSpacing(Space.S6)

        layout.addWidget(Avatar(user_name or "?"))
        layout.addSpacing(Space.S2)
        identity = QVBoxLayout()
        identity.setContentsMargins(0, 0, 0, 0)
        identity.setSpacing(0)
        name_label = make_label("", "body-strong")
        role_label = make_label("", "caption", "secondary")
        for label, text, role in ((name_label, user_name, "body-strong"), (role_label, user_role, "caption")):
            metrics = QFontMetrics(Type.font(role))
            label.setText(metrics.elidedText(text or "", Qt.TextElideMode.ElideRight, 200))
            if metrics.horizontalAdvance(text or "") > 200:
                label.setToolTip(text)
            label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        identity.addStretch(1)
        identity.addWidget(name_label)
        identity.addWidget(role_label)
        identity.addStretch(1)
        layout.addLayout(identity)
        layout.addSpacing(Space.S4)

        self.sign_out = make_button(Monitor.SIGN_OUT, "secondary", "md", "log-out", tooltip=Monitor.SIGN_OUT_TIP)
        self.sign_out.clicked.connect(self.sign_out_clicked)
        layout.addWidget(self.sign_out)

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
        return QSize(1120, Size.TOPBAR)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(Colors.N0))
        painter.fillRect(QRect(0, self.height() - 1, self.width(), 1), QColor(Colors.N200))
