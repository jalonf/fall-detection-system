"""
Central design tokens, reusable visual helpers, and global theme configuration.
"""

from pathlib import Path
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QApplication
from PySide6.QtGui import QColor, QPalette
from PySide6.QtCore import Qt

class Colors:
    # ---- Brand / primary ----
    PRIMARY = "#2563EB"
    PRIMARY_HOVER = "#1D4ED8"
    PRIMARY_PRESSED = "#1E40AF"
    PRIMARY_SOFT = "#EFF6FF"
    PRIMARY_BORDER = "#BFDBFE"

    # ---- Neutrals (slate scale) ----
    BACKGROUND = "#F8FAFC"   # app canvas
    SURFACE = "#FFFFFF"      # cards / panels
    SURFACE_ALT = "#F1F5F9"  # muted fills
    BORDER = "#E2E8F0"
    BORDER_STRONG = "#CBD5E1"

    # ---- Text ----
    TEXT_MAIN = "#0F172A"
    TEXT_BODY = "#334155"
    TEXT_MUTED = "#64748B"
    TEXT_SUBTLE = "#94A3B8"
    TEXT_INVERSE = "#FFFFFF"

    # ---- Semantic ----
    SUCCESS = "#10B981"
    SUCCESS_SOFT = "#ECFDF5"
    DANGER = "#EF4444"
    DANGER_HOVER = "#DC2626"
    DANGER_SOFT = "#FEF2F2"
    DANGER_BORDER = "#FECACA"
    WARNING = "#F59E0B"

    # ---- Ink used for "enterprise" dark buttons ----
    INK = "#0F172A"
    INK_HOVER = "#1E293B"
    INK_PRESSED = "#334155"

class Radius:
    SM = 6
    MD = 8
    LG = 12
    PILL = 999

def apply_shadow(widget, blur: int = 20, y: int = 4, alpha: int = 20, x: int = 0):
    """
    Apply a soft, professional drop shadow to a widget.
    """
    if widget is None:
        return None
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setXOffset(x)
    effect.setYOffset(y)
    effect.setColor(QColor(15, 23, 42, max(0, min(255, alpha))))
    widget.setGraphicsEffect(effect)
    return effect

class ThemeManager:
    """
    Handles the application's visual styling, including palette configuration
    and QSS stylesheet injection.
    """
    STYLESHEET_PATH = Path(__file__).resolve().parent / "style.qss"

    @classmethod
    def setup_theme(cls, app: QApplication) -> None:
        """
        Applies the base Fusion style, custom color palette, and QSS stylesheet.
        """
        app.setStyle("Fusion")
        
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(Colors.BACKGROUND))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(Colors.TEXT_BODY))
        palette.setColor(QPalette.ColorRole.Base, QColor(Colors.SURFACE))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(Colors.SURFACE_ALT))
        palette.setColor(QPalette.ColorRole.Text, QColor(Colors.TEXT_BODY))
        palette.setColor(QPalette.ColorRole.Button, QColor(Colors.SURFACE))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(Colors.TEXT_BODY))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(Colors.PRIMARY))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(Colors.TEXT_INVERSE))
        palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(Colors.TEXT_SUBTLE))
        app.setPalette(palette)
        
        app.setStyleSheet(cls._load_stylesheet())

    @classmethod
    def _load_stylesheet(cls) -> str:
        try:
            return cls.STYLESHEET_PATH.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"[WARN] Could not load stylesheet ({cls.STYLESHEET_PATH}): {exc}")
            return ""