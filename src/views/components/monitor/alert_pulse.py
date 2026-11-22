"""The single clock of the fall-alert pulse, so the stage border and the status triangle stay in step."""

from __future__ import annotations

import math

from PySide6.QtCore import QObject, QVariantAnimation, Signal, Slot

from src.views.theme import Motion


class AlertPulse(QObject):
    """Emits a phase from 0 (R600) to 1 (R300) and back every 1200 ms, sine-eased, while active."""

    phase_changed = Signal(float)

    def __init__(self, parent: QObject):
        super().__init__(parent)
        self._animation = QVariantAnimation(self)
        self._animation.setStartValue(0.0)
        self._animation.setEndValue(1.0)
        self._animation.setDuration(Motion.PULSE)
        self._animation.setLoopCount(-1)
        self._animation.valueChanged.connect(self._on_value)

    def start(self) -> None:
        if self._animation.state() != QVariantAnimation.State.Running:
            self._animation.start()

    def stop(self) -> None:
        self._animation.stop()
        self.phase_changed.emit(0.0)

    def is_active(self) -> bool:
        return self._animation.state() == QVariantAnimation.State.Running

    @Slot("QVariant")
    def _on_value(self, value) -> None:
        self.phase_changed.emit(0.5 - 0.5 * math.cos(2 * math.pi * float(value)))
