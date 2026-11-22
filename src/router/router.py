import logging

from PySide6.QtCore import QEasingCurve, QPropertyAnimation
from PySide6.QtWidgets import QGraphicsOpacityEffect, QLabel, QStackedWidget, QWidget

logger = logging.getLogger(__name__)


class ViewRouter:
    """
    Manages navigation between application views,
    applying smooth transition animations.
    """
    def __init__(self, parent_window):
        self.parent_window = parent_window
        self.stacked_widget = QStackedWidget()
        self.parent_window.setCentralWidget(self.stacked_widget)

        # The running cross-fade, if any: (overlay, animation, callback to run when it ends).
        self._transition: tuple[QLabel, QPropertyAnimation, object] | None = None
        logger.info("ViewRouter initialized successfully.")

    def add_view(self, view: QWidget):
        """Adds a view to the manager without showing it immediately."""
        view_name = view.__class__.__name__
        logger.debug("Adding view to stack: %s", view_name)
        self.stacked_widget.addWidget(view)

    def remove_view(self, view: QWidget):
        """Removes a view from the manager."""
        view_name = view.__class__.__name__
        logger.debug("Removing view from stack: %s", view_name)
        self.stacked_widget.removeWidget(view)

    def navigate_to(self, next_widget: QWidget, on_finish_callback=None):
        """
        Performs an animated transition to the new view using
        a cross-fade effect.
        """
        # A transition still running (e.g. signing out while the dashboard is fading in) ends now,
        # so its overlay is removed and its callback runs instead of being lost under the new one.
        self._finish_transition()

        current_widget = self.stacked_widget.currentWidget()
        next_name = next_widget.__class__.__name__
        current_name = current_widget.__class__.__name__ if current_widget else "None"

        logger.info("Navigation requested from [%s] to [%s]", current_name, next_name)

        # If it is the first view or the same view, switch without animation
        if current_widget is None or current_widget is next_widget:
            logger.debug("Performing direct view switch without animation.")
            self.stacked_widget.setCurrentWidget(next_widget)
            if on_finish_callback:
                on_finish_callback()
            return

        # Capture the current state for a smooth transition
        overlay = QLabel(self.parent_window)
        overlay.setPixmap(current_widget.grab())
        overlay.resize(self.parent_window.size())
        overlay.move(0, 0)
        overlay.show()
        overlay.raise_()

        # Change the actual view underneath the overlay
        self.stacked_widget.setCurrentWidget(next_widget)

        # Animate the disappearance of the overlay. The effect and the animation are children of
        # the overlay, so they live exactly as long as it does.
        effect = QGraphicsOpacityEffect(overlay)
        overlay.setGraphicsEffect(effect)
        animation = QPropertyAnimation(effect, b"opacity", overlay)
        animation.setDuration(400)
        animation.setStartValue(1.0)
        animation.setEndValue(0.0)
        animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

        self._transition = (overlay, animation, on_finish_callback)
        animation.finished.connect(self._finish_transition)
        animation.start()

    def _finish_transition(self):
        """Removes the overlay of the running transition and runs its callback (no-op when idle)."""
        if self._transition is None:
            return
        overlay, animation, on_finish_callback = self._transition
        self._transition = None
        animation.stop()
        overlay.hide()
        overlay.deleteLater()

        logger.debug("Transition finished for view: %s", self.stacked_widget.currentWidget().__class__.__name__)
        if on_finish_callback:
            on_finish_callback()
