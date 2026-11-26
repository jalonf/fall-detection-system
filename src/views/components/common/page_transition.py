"""Transition between two pages of a stack: a horizontal slide, or a cross-fade.

The one transition of the interface, used between the application's screens (sign-in and dashboard),
the dashboard's tabs, sign-in and sign-up, the patients list and the new patient form, and the steps
of a multi-step form.

An overlay laid over the stack paints snapshots of the pages, moving them a few pixels and fading
them with painted opacity, then uncovers the real page. No graphics effects are used. One animated
value, `progress` (0 to 1), drives everything.

* Slide (`crossfade=False`): the fades are staggered rather than crossed: the old page is gone
  within the first part of the slide and the new one fades in after it, over `background`, so the
  two are never seen on top of each other. It decelerates (`Motion.OUT`): the new page arrives
  quickly and settles gently.
* Cross-fade (`crossfade=True`): the new page is already the real, live one underneath (a running
  video keeps playing) and only the snapshot of the old page fades out over it, on a symmetrical
  curve (`Motion.FADE`), so the old page neither vanishes at once nor lingers.
"""

from __future__ import annotations

from PySide6.QtCore import (
    Property,
    QAbstractAnimation,
    QCoreApplication,
    QEasingCurve,
    QEvent,
    QPropertyAnimation,
    Signal,
    Slot,
)
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import QStackedWidget, QWidget

from src.views.theme import Colors, Motion

_OUT_UNTIL = 0.35      # slide: the old page has faded out at this point (0..1)
_IN_FROM = 0.2         # and the new one starts to fade in here


class PageTransition(QWidget):
    """Overlay that slides or cross-fades between two pages of a QStackedWidget.

    Args:
        parent: The stack's parent: the overlay is laid over the stack, in its parent's coordinates.
        background: Slide: colour painted behind the snapshots (the surface the pages sit on).
        shift: How far, in pixels, the pages move (0: they do not move).
        duration: Length of the transition, in ms.
        crossfade: Cross-fade over the live new page instead of sliding (see the module docstring).

    Signals:
        finished: The transition ended (or was cut short) and the new page is the current one.
    """
    finished = Signal()

    def __init__(self, parent: QWidget, *, background: str = Colors.N0, shift: float = 24.0,
                 duration: int = Motion.SLOW, crossfade: bool = False):
        super().__init__(parent)
        self.hide()
        self._background = QColor(background)
        self._shift = shift
        self._crossfade = crossfade
        self._from = QPixmap()
        self._to = QPixmap()
        self._direction = 1.0
        self._progress = 0.0
        self._animation = QPropertyAnimation(self, b"progress", self)
        self._animation.setStartValue(0.0)
        self._animation.setEndValue(1.0)
        self._animation.setDuration(duration)
        self._animation.setEasingCurve(QEasingCurve(Motion.FADE if crossfade else Motion.OUT))
        self._animation.finished.connect(self._on_finished)

    def _get_progress(self) -> float:
        return self._progress

    def _set_progress(self, value: float) -> None:
        self._progress = value
        self.update()

    progress = Property(float, _get_progress, _set_progress)

    # ------------------------------------------------------------------ API
    def is_running(self) -> bool:
        """True while a transition is in progress."""
        return self._animation.state() == QAbstractAnimation.State.Running

    def slide(self, stack: QStackedWidget, target: QWidget, forward: bool = True) -> None:
        """Makes `target` the current page of `stack`, animating the change when the stack is visible.

        Args:
            stack: The stack.
            target: One of its pages.
            forward: Slide: the new page comes from the right (False: from the left).
        """
        current = stack.currentWidget()
        if current is target:
            return
        self.finish()               # a transition still running ends now
        if not stack.isVisible() or current is None:
            stack.setCurrentWidget(target)
            self.finished.emit()
            return
        self._from = current.grab()
        if self._crossfade:
            stack.setCurrentWidget(target)
        else:
            target.setGeometry(current.geometry())
            layout = target.layout()
            if layout is not None:
                layout.activate()
            stack.setCurrentWidget(target)
            # Pages that lay themselves out on resize (the step forms) post further layout requests
            # when shown: apply them, so the snapshot is the page as it will look.
            for _ in range(3):
                QCoreApplication.sendPostedEvents(None, QEvent.Type.LayoutRequest)
            self._to = target.grab()

        self._direction = 1.0 if forward else -1.0
        self._progress = 0.0
        self.setGeometry(stack.geometry())
        self.show()
        self.raise_()
        self._animation.start()

    def finish(self) -> None:
        """Ends a running transition at once (its new page is already the current one)."""
        if self.is_running():
            self._animation.stop()
            self._on_finished()

    # ------------------------------------------------------------------ internals
    @Slot()
    def _on_finished(self) -> None:
        self.hide()
        self._from = QPixmap()
        self._to = QPixmap()
        self.finished.emit()

    def paintEvent(self, event) -> None:
        """Paints the snapshots at their current offset and opacity."""
        painter = QPainter(self)
        progress = self._progress
        offset = self._shift * self._direction
        if self._crossfade:
            if not self._from.isNull():
                painter.setOpacity(1.0 - progress)
                painter.drawPixmap(round(-offset * progress), 0, self._from)
            return
        painter.fillRect(self.rect(), self._background)
        if not self._from.isNull() and progress < _OUT_UNTIL:
            painter.setOpacity(1.0 - progress / _OUT_UNTIL)
            painter.drawPixmap(round(-offset * progress), 0, self._from)
        if not self._to.isNull() and progress > _IN_FROM:
            painter.setOpacity((progress - _IN_FROM) / (1.0 - _IN_FROM))
            painter.drawPixmap(round(offset * (1.0 - progress)), 0, self._to)
