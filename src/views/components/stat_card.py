from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from src.views.theme import apply_shadow

class StatCard(QFrame):
    def __init__(self, initial_value, label_text, attr_name, accent_color, parent=None):
        super().__init__(parent)
        self.setObjectName(f"statCard_{attr_name}")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True) # <-- Clave para habilitar QSS
        self.setFixedHeight(95)
        
        self.setStyleSheet(f"""
            QFrame#statCard_{attr_name} {{ 
                background-color: rgba(255, 255, 255, 0.75); /* Translúcido */
                border: 1px solid rgba(255, 255, 255, 0.9);
                border-top: 3px solid {accent_color};
                border-radius: 12px;
            }}
        """)
        apply_shadow(self, blur=10, y=2, alpha=6)

        col = QVBoxLayout(self)
        col.setContentsMargins(18, 14, 18, 14)
        col.setSpacing(2)

        lbl = QLabel(label_text)
        lbl.setStyleSheet("font-size: 10px; font-weight: 700; color: #64748B; letter-spacing: 0.8px; background: transparent; border: none;")

        self.val_label = QLabel(str(initial_value))
        self.val_label.setStyleSheet("font-size: 28px; font-weight: 700; color: #0F172A; background: transparent; border: none;")

        col.addWidget(lbl)
        col.addWidget(self.val_label)
        col.addStretch()

    def set_value(self, new_value):
        self.val_label.setText(str(new_value))