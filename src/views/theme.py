"""
Central design tokens, reusable visual helpers, and global theme configuration.
"""

from pathlib import Path
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QApplication
from PySide6.QtGui import QColor, QPalette
from PySide6.QtCore import Qt

class Colors:
    # ---- Brand / Primary ----
    PRIMARY = "#1E3A8A"        # Deep Corporate Blue
    PRIMARY_HOVER = "#1E40AF"
    PRIMARY_PRESSED = "#1E3A8A"
    PRIMARY_SOFT = "#EFF6FF"
    PRIMARY_BORDER = "#BFDBFE"

    # ---- Neutrals (Professional Light & Clean scale) ----
    BACKGROUND = "#F9FAFB"     # Clean off-white canvas
    SURFACE = "#FFFFFF"        # Cards and panels
    SURFACE_ALT = "#F3F4F6"    # Muted fills
    BORDER = "#E5E7EB"         # Soft structural border
    BORDER_STRONG = "#D1D5DB"  # Stronger border

    # ---- Text ----
    TEXT_MAIN = "#111827"
    TEXT_BODY = "#374151"
    TEXT_MUTED = "#6B7280"
    TEXT_SUBTLE = "#9CA3AF"
    TEXT_INVERSE = "#FFFFFF"

    # ---- Semantic ----
    SUCCESS = "#059669"
    SUCCESS_SOFT = "#ECFDF5"
    DANGER = "#DC2626"
    DANGER_HOVER = "#B91C1C"
    DANGER_SOFT = "#FEF2F2"
    DANGER_BORDER = "#FECACA"
    WARNING = "#D97706"

    # ---- Ink ----
    INK = "#111827"
    INK_HOVER = "#1F2937"
    INK_PRESSED = "#374151"

class Radius:
    SM = 4
    MD = 4
    LG = 6
    PILL = 999

def apply_shadow(widget, blur: int = 10, y: int = 2, alpha: int = 10, x: int = 0):
    """
    Apply a subtle, professional drop shadow to a widget.
    """
    if widget is None:
        return None
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setXOffset(x)
    effect.setYOffset(y)
    effect.setColor(QColor(17, 24, 39, max(0, min(255, alpha))))
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