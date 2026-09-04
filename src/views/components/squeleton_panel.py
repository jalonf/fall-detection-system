from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import QFrame, QLabel, QSizePolicy, QVBoxLayout

from src.views.theme import apply_shadow


class SkeletonPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("panel")
        apply_shadow(self, blur=8, y=2, alpha=5)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("TELEMETRY (LANDMARKS)")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)
        
        self.view = QLabel()
        self.view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.view.setMinimumHeight(150)
        self.view.setStyleSheet("background-color: #0F172A; border-radius: 4px;")
        layout.addWidget(self.view)
        
        data_layout = QVBoxLayout()
        data_layout.setContentsMargins(15, 8, 15, 4)
        data_layout.setSpacing(6)
        
        font = QFont("Consolas", 9)
        
        self.lbl_inf = self._create_data_label("Inference: -- ms", font)
        self.lbl_cent = self._create_data_label("Centroid (Y): --", font)
        self.lbl_conf = self._create_data_label("Confidence: --%", font)
        
        data_layout.addWidget(self.lbl_inf)
        data_layout.addWidget(self.lbl_cent)
        data_layout.addWidget(self.lbl_conf)
        
        layout.addLayout(data_layout)
        
    def _create_data_label(self, text, font):
        lbl = QLabel(text)
        lbl.setFont(font)
        lbl.setStyleSheet("color: #475569;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        return lbl
        
    def update_frame(self, qimage):
        pixmap = QPixmap.fromImage(qimage)
        self.view.setPixmap(pixmap.scaled(
            self.view.size(), 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        ))
        
    def update_telemetry(self, data: dict):
        if not data:
            self.lbl_inf.setText("Inference: -- ms")
            self.lbl_cent.setText("Centroid (Y): --")
            self.lbl_conf.setText("Confidence: --%")
            return
            
        inf = data.get('inference_ms', 0.0)
        cent = data.get('centroid_y')
        conf = data.get('confidence', 0.0)
        
        self.lbl_inf.setText(f"Inference: {inf:.1f} ms")
        self.lbl_cent.setText(f"Centroid (Y): {cent:.3f}" if cent is not None else "Centroid (Y): --")
        self.lbl_conf.setText(f"Confidence: {int(conf*100)}%")
        
    def clear_video(self):
        self.view.clear()
        self.update_telemetry({})