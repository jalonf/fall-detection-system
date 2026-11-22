"""Fall alert banner: a red card on top of the stage that stays until the operator acknowledges it."""

from __future__ import annotations

import re

from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QParallelAnimationGroup,
    QPropertyAnimation,
    QRectF,
    Qt,
    QTime,
    Signal,
    Slot,
)
from PySide6.QtGui import (
    QAccessible,
    QAccessibleEvent,
    QColor,
    QFontMetrics,
    QPainter,
    QPixmap,
)
from PySide6.QtWidgets import QWidget

from src.views import icons
from src.views.components.common.button import Button
from src.views.components.common.painting import shadow_pixmap
from src.views.strings import Monitor
from src.views.theme import Colors, Motion, Radius, Type, qcolor

HEIGHT = 56
MARGIN = 12
_BLUR, _DY, _ALPHA = 16, 4, 0.18
_PERCENT = re.compile(r"\((\d+)%\)")


class FallAlertBanner(QWidget):
    acknowledged = Signal()

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.hide()
        self._count = 0
        self._detail = ""
        self._opacity = 1.0
        self._offset = 0.0
        self._snapshot: QPixmap | None = None

        self.button = Button(Monitor.ACKNOWLEDGE, "on-danger", "sm", parent=self)
        self.button.setToolTip(Monitor.ACKNOWLEDGE_TIP)
        self.button.clicked.connect(self.acknowledged)

        self._group = QParallelAnimationGroup(self)
        self._fade = QPropertyAnimation(self, b"opacity", self)
        self._slide = QPropertyAnimation(self, b"offset_y", self)
        for animation, start in ((self._fade, 0.0), (self._slide, -8.0)):
            animation.setDuration(Motion.SLOW)
            animation.setEasingCurve(QEasingCurve(Motion.IN_OUT))
            animation.setStartValue(start)
            animation.setEndValue(1.0 if animation is self._fade else 0.0)
            self._group.addAnimation(animation)
        self._group.finished.connect(self._on_appeared)

    # ------------------------------------------------------------------ properties
    def _get_opacity(self) -> float:
        return self._opacity

    def _set_opacity(self, value: float) -> None:
        self._opacity = value
        self.update()

    def _get_offset(self) -> float:
        return self._offset

    def _set_offset(self, value: float) -> None:
        self._offset = value
        self.update()

    opacity = Property(float, _get_opacity, _set_opacity)
    offset_y = Property(float, _get_offset, _set_offset)

    # ------------------------------------------------------------------ API
    @property
    def count(self) -> int:
        return self._count

    def detail(self) -> str:
        return self._detail

    def show_fall(self, message: str, at: QTime) -> None:
        """Shows the alert, or updates it (percentage, time and repeat count) if already shown."""
        match = _PERCENT.search(message)
        if match:
            self._detail = Monitor.FALL_DETAIL.format(percent=match.group(1), time=at.toString("HH:mm:ss"))
        else:
            self._detail = message
        self._count += 1
        self.setAccessibleName(f"{Monitor.FALL_TITLE}. {self._detail}")
        if not self.isVisible():
            self._appear()
        else:
            self.update()
        QAccessible.updateAccessibility(QAccessibleEvent(self, QAccessible.Event.Alert))

    def dismiss(self) -> None:
        self._group.stop()
        self.hide()
        self._count = 0
        self._snapshot = None

    def place(self, stage_width: int) -> None:
        """Positions the banner 12 px from the top and sides of a stage `stage_width` wide."""
        self.setGeometry(MARGIN - _BLUR, MARGIN - (_BLUR - _DY), stage_width - 2 * MARGIN + 2 * _BLUR,
                         HEIGHT + 2 * _BLUR)

    def _card(self) -> QRectF:
        return QRectF(_BLUR, _BLUR - _DY, self.width() - 2 * _BLUR, HEIGHT)

    def _appear(self) -> None:
        self.button.adjustSize()
        self._place_button()
        self._snapshot = self.button.grab()
        self.button.hide()
        self._opacity, self._offset = 0.0, -8.0
        self.show()
        self.raise_()
        self._group.start()

    @Slot()
    def _on_appeared(self) -> None:
        self._snapshot = None
        self.button.show()
        self.update()

    # ------------------------------------------------------------------ layout and painting
    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._place_button()

    def _place_button(self) -> None:
        card = self._card()
        self.button.move(round(card.right() - 12 - self.button.width()),
                         round(card.center().y() - self.button.height() / 2))

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setOpacity(self._opacity)
        painter.translate(0, self._offset)
        card = self._card()
        dpr = round(self.devicePixelRatioF(), 2)
        painter.drawPixmap(round(card.left()) - _BLUR, round(card.top()) - _BLUR,
                           shadow_pixmap(round(card.width()), HEIGHT, Radius.R_MD, _BLUR, _DY, _ALPHA, dpr))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(Colors.R600))
        painter.drawRoundedRect(card, Radius.R_MD, Radius.R_MD)

        x = card.left() + 16
        painter.drawPixmap(round(x), round(card.center().y() - 10), icons.icon_pixmap("alert-triangle", Colors.N0, 20, dpr))
        x += 20 + 12
        top = card.top() + (HEIGHT - 36) / 2
        button_left = card.right() - 12 - self.button.width()
        hint_font = Type.font("caption")
        hint_width = QFontMetrics(hint_font).horizontalAdvance(Monitor.ACKNOWLEDGE_HINT)
        text_right = button_left - 8 - hint_width - 16

        painter.setFont(Type.font("title-sm"))
        painter.setPen(QColor(Colors.N0))
        title_width = painter.fontMetrics().horizontalAdvance(Monitor.FALL_TITLE)
        painter.drawText(QRectF(x, top, title_width + 1, 20), int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                         Monitor.FALL_TITLE)
        if self._count > 1:
            badge_text = f"×{self._count}"
            painter.setFont(Type.font("overline"))
            badge = QRectF(x + title_width + 8, top, painter.fontMetrics().horizontalAdvance(badge_text) + 16, 20)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(Colors.R700))
            painter.drawRoundedRect(badge, Radius.R_SM, Radius.R_SM)
            painter.setPen(QColor(Colors.N0))
            painter.drawText(badge, int(Qt.AlignmentFlag.AlignCenter), badge_text)

        painter.setFont(hint_font)
        painter.setPen(qcolor(Colors.N0, 0.85))
        detail = painter.fontMetrics().elidedText(self._detail, Qt.TextElideMode.ElideRight, max(0, int(text_right - x)))
        painter.drawText(QRectF(x, top + 20, max(0.0, text_right - x), 16),
                         int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), detail)
        painter.drawText(QRectF(button_left - 8 - hint_width, card.top(), hint_width, HEIGHT),
                         int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter), Monitor.ACKNOWLEDGE_HINT)

        if self._snapshot is not None:
            painter.drawPixmap(self.button.pos(), self._snapshot)
