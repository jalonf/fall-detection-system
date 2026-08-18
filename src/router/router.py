from PySide6.QtCore import QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import QStackedWidget, QLabel, QGraphicsOpacityEffect, QWidget

class ViewRouter:
    """
    Manages navigation between application views,
    applying smooth transition animations.
    """
    def __init__(self, parent_window):
        self.parent_window = parent_window
        self.stacked_widget = QStackedWidget()
        self.parent_window.setCentralWidget(self.stacked_widget)
        
        # References to prevent the garbage collector from deleting the animations
        self.effect_out = None
        self.anim_out = None
        self.overlay = None

    def add_view(self, view: QWidget):
        """Adds a view to the manager without showing it immediately."""
        self.stacked_widget.addWidget(view)

    def remove_view(self, view: QWidget):
        """Removes a view from the manager."""
        self.stacked_widget.removeWidget(view)

    def navigate_to(self, next_widget: QWidget, on_finish_callback=None):
        """
        Performs an animated transition to the new view using
        a cross-fade effect.
        """
        current_widget = self.stacked_widget.currentWidget()
        
        # If it is the first view or the same view, switch without animation
        if current_widget is None or current_widget == next_widget:
            self.stacked_widget.setCurrentWidget(next_widget)
            if on_finish_callback:
                on_finish_callback()
            return

        # Capture the current state for a smooth transition
        pixmap = current_widget.grab()
        
        self.overlay = QLabel(self.parent_window)
        self.overlay.setPixmap(pixmap)
        self.overlay.resize(self.parent_window.size())
        self.overlay.move(0, 0)
        self.overlay.show()
        self.overlay.raise_()

        # Change the actual view underneath the overlay
        self.stacked_widget.setCurrentWidget(next_widget)

        # Animate the disappearance of the overlay
        self.effect_out = QGraphicsOpacityEffect(self.overlay)
        self.overlay.setGraphicsEffect(self.effect_out)

        self.anim_out = QPropertyAnimation(self.effect_out, b"opacity")
        self.anim_out.setDuration(400)
        self.anim_out.setStartValue(1.0)
        self.anim_out.setEndValue(0.0)
        self.anim_out.setEasingCurve(QEasingCurve.Type.InOutQuad)

        def on_transition_finished():
            assert self.overlay is not None
            self.overlay.hide()
            self.overlay.deleteLater()
            self.overlay = None
            
            if on_finish_callback:
                on_finish_callback()

        self.anim_out.finished.connect(on_transition_finished)
        self.anim_out.start()