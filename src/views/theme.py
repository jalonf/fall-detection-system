"""
Central design tokens, reusable visual helpers, and global theme configuration.

Design language: a calm "clinical care console" — a soft blue on white and blue-grey
neutrals, with red reserved for alerts.
"""

from pathlib import Path

from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import QApplication, QGraphicsDropShadowEffect


class Colors:
    # ---- Brand / Primary: a calm, friendly blue (used sparingly) ----
    PRIMARY = "#3D6FBE"
    PRIMARY_HOVER = "#3361A9"
    PRIMARY_PRESSED = "#2B5290"
    PRIMARY_SOFT = "#EEF3FB"
    PRIMARY_SOFT_STRONG = "#E2EBF8"
    PRIMARY_BORDER = "#C8D8EF"
    ACCENT = "#9DB9E6"           # Light blue for use on dark surfaces

    # ---- Dark surfaces (video stage, tooltips) ----
    CHROME = "#1E293B"
    CHROME_BORDER = "#334155"
    CHROME_TEXT_MUTED = "#94A3B8"
    STAGE = "#0F1B2D"
    STAGE_BORDER = "#243249"

    # ---- Neutrals (blue-grey scale) ----
    BACKGROUND = "#F4F6FA"       # App canvas
    SURFACE = "#FFFFFF"          # Panels and cards
    SURFACE_ALT = "#F8FAFC"      # Muted fills / idle inputs
    BORDER = "#E1E6EF"           # Soft structural border
    BORDER_STRONG = "#CBD3E1"    # Controls
    BORDER_HOVER = "#AEB9CE"

    # ---- Text ----
    TEXT_MAIN = "#1E293B"
    TEXT_BODY = "#475569"
    TEXT_MUTED = "#64748B"
    TEXT_SUBTLE = "#94A3B8"
    TEXT_INVERSE = "#FFFFFF"

    # ---- Semantic (kept restrained; red is reserved for alerts) ----
    SUCCESS = "#2E8A68"
    SUCCESS_SOFT = "#EAF6F1"
    SUCCESS_BORDER = "#BFE3D3"
    INFO = "#3D6FBE"
    INFO_SOFT = "#EEF3FB"
    WARNING = "#B7791F"
    WARNING_SOFT = "#FEF7E8"
    WARNING_BORDER = "#F0D9A6"
    DANGER = "#D43D3D"
    DANGER_HOVER = "#B93030"
    DANGER_SOFT = "#FDF1F1"
    DANGER_BORDER = "#F3BFBF"

    # ---- Ink ----
    INK = "#1E293B"
    INK_HOVER = "#334155"
    INK_PRESSED = "#475569"


class Radius:
    SM = 6      # small chips, scrollbar handles
    MD = 10     # inputs, buttons
    LG = 14     # panels
    PILL = 999


class Fonts:
    UI_FAMILIES = ("Segoe UI", "Inter", "SF Pro Text", "Helvetica Neue", "Roboto", "sans-serif")
    MONO_FAMILIES = ("Cascadia Mono", "SF Mono", "Consolas", "Menlo", "monospace")


def ui_font(pixel_size: int = 13, bold: bool = False) -> QFont:
    font = QFont()
    font.setFamilies(list(Fonts.UI_FAMILIES))
    font.setPixelSize(pixel_size)
    if bold:
        font.setWeight(QFont.Weight.DemiBold)
    return font


def mono_font(pixel_size: int = 12, bold: bool = False) -> QFont:
    font = QFont()
    font.setFamilies(list(Fonts.MONO_FAMILIES))
    font.setStyleHint(QFont.StyleHint.Monospace)
    font.setPixelSize(pixel_size)
    if bold:
        font.setWeight(QFont.Weight.DemiBold)
    return font


def set_prop(widget, name: str, value) -> None:
    """
    Set a dynamic property used by QSS attribute selectors (e.g. [state="alert"])
    and re-polish the widget so the new style is applied immediately.
    """
    if widget is None or widget.property(name) == value:
        return
    widget.setProperty(name, value)
    style = widget.style()
    style.unpolish(widget)
    style.polish(widget)
    widget.update()


def apply_shadow(widget, blur: int = 10, y: int = 2, alpha: int = 10, x: int = 0):
    """
    Apply a subtle drop shadow to a widget.

    Note: graphics effects force the whole widget subtree to be re-rendered
    off-screen on every repaint, so avoid using it on panels that display
    live video. It is meant for small floating elements (e.g. toasts).
    """
    if widget is None:
        return None
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setXOffset(x)
    effect.setYOffset(y)
    effect.setColor(QColor(30, 41, 59, max(0, min(255, alpha))))
    widget.setGraphicsEffect(effect)
    return effect


class ThemeManager:
    """
    Handles the application's visual styling, including palette configuration
    and QSS stylesheet injection.
    """
    STYLESHEET_PATH = Path(__file__).resolve().parent / "style.qss"
    ASSETS_DIR = Path(__file__).resolve().parent / "assets"

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
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(Colors.CHROME))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(Colors.TEXT_INVERSE))
        app.setPalette(palette)

        app.setStyleSheet(cls._load_stylesheet())

    @classmethod
    def _load_stylesheet(cls) -> str:
        try:
            css = cls.STYLESHEET_PATH.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"[WARN] Could not load stylesheet ({cls.STYLESHEET_PATH}): {exc}")
            return ""
        # QSS url() paths are resolved against the CWD, so inject an absolute path.
        return css.replace("@ASSETS@", cls.ASSETS_DIR.as_posix())
