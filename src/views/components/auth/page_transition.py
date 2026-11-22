"""Horizontal slide between the sign-in and sign-up pages.

During the transition an overlay paints snapshots of both pages, moving them 40 px and fading
them with painted opacity, then the real page is uncovered. No graphics effects are used.
"""

from __future__ import annotations

from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QParallelAnimationGroup,
    QPropertyAnimation,
    Signal,
    Slot,
)
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import QStackedWidget, QWidget

from src.views.theme import Colors, Motion

_SHIFT = 40.0


class PageTransition(QWidget):
    finished = Signal()

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.hide()
        self._from = QPixmap()
        self._to = QPixmap()
        self._from_x = 0.0
        self._to_x = 0.0
        self._group = QParallelAnimationGroup(self)
        self._out = QPropertyAnimation(self, b"from_x", self)
        self._in = QPropertyAnimation(self, b"to_x", self)
        for animation in (self._out, self._in):
            animation.setDuration(Motion.BASE)
            animation.setEasingCurve(QEasingCurve(Motion.OUT))
            self._group.addAnimation(animation)
        self._group.finished.connect(self._on_finished)

    def _get_from_x(self) -> float:
        return self._from_x

    def _set_from_x(self, value: float) -> None:
        self._from_x = value
        self.update()

    def _get_to_x(self) -> float:
        return self._to_x

    def _set_to_x(self, value: float) -> None:
        self._to_x = value
        self.update()

    from_x = Property(float, _get_from_x, _set_from_x)
    to_x = Property(float, _get_to_x, _set_to_x)

    def is_running(self) -> bool:
        return self._group.state() == QParallelAnimationGroup.State.Running

    def slide(self, stack: QStackedWidget, target: QWidget, forward: bool) -> None:
        """Makes `target` the current page of `stack`, sliding it in when the stack is visible."""
        current = stack.currentWidget()
        if current is target:
            return
        if not stack.isVisible() or current is None:
            stack.setCurrentWidget(target)
            self.finished.emit()
            return
        self._group.stop()
        self._from = current.grab()
        target.setGeometry(current.geometry())
        if target.layout() is not None:
            target.layout().activate()
        stack.setCurrentWidget(target)
        self._to = target.grab()

        direction = 1.0 if forward else -1.0
        self._out.setStartValue(0.0)
        self._out.setEndValue(-_SHIFT * direction)
        self._in.setStartValue(_SHIFT * direction)
        self._in.setEndValue(0.0)
        self._from_x, self._to_x = 0.0, _SHIFT * direction
        self.setGeometry(stack.geometry())
        self.show()
        self.raise_()
        self._group.start()

    @Slot()
    def _on_finished(self) -> None:
        self.hide()
        self._from = QPixmap()
        self._to = QPixmap()
        self.finished.emit()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(Colors.N0))
        progress = 1.0 - min(1.0, abs(self._to_x) / _SHIFT)
        if not self._from.isNull():
            painter.setOpacity(1.0 - progress)
            painter.drawPixmap(round(self._from_x), 0, self._from)
        if not self._to.isNull():
            painter.setOpacity(progress)
            painter.drawPixmap(round(self._to_x), 0, self._to)
