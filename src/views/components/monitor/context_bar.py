"""Context bar: patient, risk, source, status and duration. The main place where the state shows.

During a fall alert it turns R50, its status pulses and an Acknowledge button appears on the right.
"""

from __future__ import annotations

from PySide6.QtCore import QRect, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFontMetrics, QPainter
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from src.views.components.common.badge import Badge
from src.views.components.common.button import make_button
from src.views.components.common.painting import Divider
from src.views.components.common.status_indicator import StatusIndicator
from src.views.strings import EM_DASH, Monitor
from src.views.theme import (
    Colors,
    Size,
    Space,
    Type,
    make_label,
    make_tabular_label,
    set_props,
)

RISK_VARIANTS = {"LOW": "success", "MEDIUM": "warning", "HIGH": "danger"}
STATUS_KIND = {"idle": "idle", "starting": "starting", "live": "live", "stopping": "stopping",
               "error": "error", "finished": "finished"}
_PATIENT_WIDTH = 240
_SOURCE_WIDTH = 200


def set_value(label: QLabel, text: str | None, width: int, mode=Qt.TextElideMode.ElideRight) -> None:
    """Shows `text` elided to `width` (with the full text as tooltip), or a muted dash."""
    if not text:
        label.setText(EM_DASH)
        label.setToolTip("")
        set_props(label, tone="tertiary")
        return
    metrics = QFontMetrics(Type.font("body-strong"))
    label.setText(metrics.elidedText(text, mode, width))
    label.setToolTip(text if metrics.horizontalAdvance(text) > width else "")
    set_props(label, tone="primary")


class ContextBar(QWidget):
    acknowledge_clicked = Signal()

    def __init__(self, patient_name: str | None, risk_level: str | None, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("ContextBar")
        self.setFixedHeight(Size.CONTEXT_BAR)
        self._alert = False
        self._state = "idle"

        layout = QHBoxLayout(self)
        layout.setContentsMargins(Space.S6, 0, Space.S6, 1)
        layout.setSpacing(0)

        self.patient = make_label("", "body-strong")
        set_value(self.patient, patient_name, _PATIENT_WIDTH)
        self._add_item(layout, Monitor.PATIENT, self.patient)

        level = (risk_level or "").strip().upper()
        if level in RISK_VARIANTS:
            self.risk: QWidget = Badge(level, RISK_VARIANTS[level])
        else:
            self.risk = make_label(EM_DASH, "body-strong", "tertiary")
        self._add_item(layout, Monitor.RISK, self.risk, divider=True)

        self.source = make_label("", "body-strong")
        set_value(self.source, None, _SOURCE_WIDTH)
        self._add_item(layout, Monitor.SOURCE, self.source, divider=True)

        reserve = (*Monitor.STATUS_TEXT.values(), Monitor.STATUS_ALERT_COUNT.format(n=99))
        self.status = StatusIndicator(reserve=reserve)
        self._add_item(layout, Monitor.STATUS, self.status, divider=True)

        self.duration = make_tabular_label(EM_DASH, "body-strong", "tertiary", sample="00:00:00")
        self._add_item(layout, Monitor.DURATION, self.duration, divider=True)
        layout.addStretch(1)

        self.acknowledge = make_button(Monitor.ACKNOWLEDGE, "danger", "sm", "check", tooltip=Monitor.ACKNOWLEDGE_TIP)
        policy = self.acknowledge.sizePolicy()
        policy.setRetainSizeWhenHidden(True)      # showing it never shifts the other items
        self.acknowledge.setSizePolicy(policy)
        self.acknowledge.hide()
        self.acknowledge.clicked.connect(self.acknowledge_clicked)
        layout.addWidget(self.acknowledge, 0, Qt.AlignmentFlag.AlignVCenter)
        self.set_state("idle")

    def _add_item(self, layout: QHBoxLayout, label: str, value: QWidget, *, divider: bool = False) -> None:
        if divider:
            layout.addSpacing(Space.S5)
            layout.addWidget(Divider(Colors.N200, vertical=True, length=16))
            layout.addSpacing(Space.S5)
        layout.addWidget(make_label(label, "caption", "secondary"))
        layout.addSpacing(Space.S2)
        layout.addWidget(value, 0, Qt.AlignmentFlag.AlignVCenter)
        value.setAccessibleName(label)

    # ------------------------------------------------------------------ API
    def set_state(self, state: str) -> None:
        self._state = state
        if not self._alert:
            self.status.set_status(STATUS_KIND[state], Monitor.STATUS_TEXT[state])

    def set_source(self, label: str | None) -> None:
        set_value(self.source, label, _SOURCE_WIDTH, Qt.TextElideMode.ElideMiddle)

    def set_duration(self, text: str | None) -> None:
        if text != self.duration.text():
            self.duration.setText(text or EM_DASH)
            set_props(self.duration, tone="primary" if text else "tertiary")

    def set_alert(self, active: bool, count: int = 1) -> None:
        """Shows the fall alert (with the number of falls since the last acknowledgement) or clears it."""
        changed = active != self._alert
        self._alert = active
        if active:
            text = Monitor.STATUS_TEXT["alert"] if count <= 1 else Monitor.STATUS_ALERT_COUNT.format(n=count)
            self.status.set_status("alert", text)
        else:
            self.status.set_status(STATUS_KIND[self._state], Monitor.STATUS_TEXT[self._state])
        self.acknowledge.setVisible(active)
        if changed:
            self.update()

    def set_pulse_phase(self, phase: float) -> None:
        self.status.set_pulse_phase(phase)

    def status_text(self) -> str:
        return self.status.text()

    # ------------------------------------------------------------------ painting
    def sizeHint(self) -> QSize:
        return QSize(1120, Size.CONTEXT_BAR)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(Colors.R50 if self._alert else Colors.N0))
        painter.fillRect(QRect(0, self.height() - 1, self.width(), 1), QColor(Colors.R200 if self._alert else Colors.N200))
