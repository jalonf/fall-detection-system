from PySide6.QtCore import Qt, QTime
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QListWidget, QListWidgetItem
)
from src.views.theme import apply_shadow, Colors

class EventLog(QFrame):
    """Component for displaying system events and alerts with a formal layout."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("panel")
        apply_shadow(self, blur=8, y=2, alpha=6)
        self._empty_hint_active = False
        self._build_ui()

    def _build_ui(self):
        log_wrapper = QVBoxLayout(self)
        log_wrapper.setContentsMargins(16, 16, 16, 16)
        log_wrapper.setSpacing(10)

        log_header = QHBoxLayout()
        log_title = QLabel("EVENT LOG")
        log_title.setObjectName("sectionTitle")
        log_header.addWidget(log_title)
        log_header.addStretch()

        clear_btn = QPushButton("Clear log")
        clear_btn.setObjectName("subtle")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self.clear_events)
        log_header.addWidget(clear_btn)
        log_wrapper.addLayout(log_header)

        self.event_list = QListWidget()
        self.event_list.setObjectName("eventLog")
        self.event_list.setMinimumHeight(180)
        self.event_list.setWordWrap(True)
        log_wrapper.addWidget(self.event_list, 1)
        self._refresh_empty_log_hint()

    def add_event(self, event_type: str, message: str):
        if self._empty_hint_active:
            self.event_list.clear()
            self._empty_hint_active = False

        timestamp = QTime.currentTime().toString("HH:mm:ss")
        item = QListWidgetItem(f"[{timestamp}]  {event_type}  —  {message}")
        if event_type == "ALERT":
            item.setForeground(QColor(Colors.DANGER))
        elif event_type == "INFO":
            item.setForeground(QColor(Colors.PRIMARY))
        else:
            item.setForeground(QColor(Colors.TEXT_MUTED))
        self.event_list.insertItem(0, item)

    def clear_events(self):
        self.event_list.clear()
        self._refresh_empty_log_hint()

    def _refresh_empty_log_hint(self):
        self.event_list.clear()
        hint = QListWidgetItem("No events recorded in this session.")
        hint.setForeground(QColor(Colors.TEXT_SUBTLE))
        hint.setFlags(Qt.ItemFlag.NoItemFlags)
        self.event_list.addItem(hint)
        self._empty_hint_active = True