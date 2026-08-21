from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from src.views.theme import apply_shadow

class StatCard(QFrame):
    """Component for displaying single metric statistics with a clean structural look."""
    
    def __init__(self, initial_value, label_text, attr_name, accent_color, parent=None):
        super().__init__(parent)
        self.setObjectName(f"statCard_{attr_name}")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedHeight(90)
        
        self.setStyleSheet(f"""
            QFrame#statCard_{attr_name} {{ 
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-top: 3px solid {accent_color};
                border-radius: 4px;
            }}
        """)
        apply_shadow(self, blur=6, y=2, alpha=6)

        col = QVBoxLayout(self)
        col.setContentsMargins(16, 12, 16, 12)
        col.setSpacing(2)

        lbl = QLabel(label_text)
        lbl.setStyleSheet("font-size: 10px; font-weight: 700; color: #6B7280; letter-spacing: 0.8px; background: transparent; border: none;")

        self.val_label = QLabel(str(initial_value))
        self.val_label.setStyleSheet("font-size: 24px; font-weight: 700; color: #111827; background: transparent; border: none;")

        col.addWidget(lbl)
        col.addWidget(self.val_label)
        col.addStretch()

    def set_value(self, new_value):
        self.val_label.setText(str(new_value))