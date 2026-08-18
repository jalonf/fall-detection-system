from PySide6.QtCore import Qt, QTime
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QListWidget, QListWidgetItem
)
from src.views.theme import apply_shadow, Colors

class EventLog(QFrame):
    """Component for displaying system events and alerts."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("panel")
        apply_shadow(self, blur=15, y=4, alpha=6)
        self._empty_hint_active = False
        self._build_ui()

    def _build_ui(self):
        log_wrapper = QVBoxLayout(self)
        log_wrapper.setContentsMargins(20, 20, 20, 20)
        log_wrapper.setSpacing(12)

        log_header = QHBoxLayout()
        log_title = QLabel("EVENT LOG")
        log_title.setObjectName("sectionTitle")
        log_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748B; letter-spacing: 1px;")
        log_header.addWidget(log_title)
        log_header.addStretch()

        clear_btn = QPushButton("Clear log")
        clear_btn.setObjectName("subtle")
        clear_btn.setFixedHeight(24)
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.setStyleSheet("color: #3B82F6; font-size: 12px; font-weight: 600; border: none; background: transparent;")
        clear_btn.clicked.connect(self.clear_events)
        log_header.addWidget(clear_btn)
        log_wrapper.addLayout(log_header)

        self.event_list = QListWidget()
        self.event_list.setObjectName("eventLog")
        self.event_list.setMinimumHeight(200)
        self.event_list.setSpacing(0)
        self.event_list.setWordWrap(True) 
        self.event_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.event_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.event_list.setStyleSheet("""
            QListWidget {
                background-color: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 6px;
                padding: 4px;
                outline: none;
            }
            QListWidget::item {
                border-bottom: 1px solid #F1F5F9;
                padding: 10px 8px;
            }
            QListWidget::item:last {
                border-bottom: none;
            }
            QListWidget::item:selected {
                background-color: transparent;
            }
        """)
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