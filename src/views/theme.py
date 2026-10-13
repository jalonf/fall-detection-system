"""
Central design tokens, reusable visual helpers, and global theme configuration.

Design language: a calm "clinical care console" — a soft blue on white and blue-grey
neutrals, with red reserved for alerts.

Single source of truth
----------------------
Every colour, radius and font stack used by `style.qss` is declared here and injected
into the stylesheet through `@TOKEN@` placeholders (see `ThemeManager._load_stylesheet`).
Change a value once in this file and the Python code *and* the QSS follow.
"""

import re
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPalette, QPixmap
from PySide6.QtWidgets import QApplication, QGraphicsDropShadowEffect

APP_NAME = "Name"


class Colors:
    # ---- Brand / Primary: a calm, friendly blue (used sparingly) ----
    PRIMARY = "#3D6FBE"
    PRIMARY_HOVER = "#3361A9"
    PRIMARY_PRESSED = "#2B5290"
    PRIMARY_SOFT = "#EEF3FB"
    PRIMARY_SOFT_STRONG = "#E2EBF8"
    PRIMARY_BORDER = "#C8D8EF"
    ACCENT = "#9DB9E6"           # Light blue for use on dark surfaces

    # Foreground shared by outline ("ghost") buttons: label and icon use the same colour.
    ON_GHOST = PRIMARY_HOVER

    # ---- Dark surfaces (video stage, tooltips) ----
    CHROME = "#1E293B"
    CHROME_BORDER = "#334155"
    CHROME_TEXT_MUTED = "#94A3B8"
    STAGE = "#0F1B2D"
    STAGE_BORDER = "#243249"
    STAGE_TEXT = "#D5DEF2"
    STAGE_TEXT_MUTED = "#8A9CC0"

    # ---- Neutrals (blue-grey scale) ----
    BACKGROUND = "#F4F6FA"       # App canvas
    SURFACE = "#FFFFFF"          # Panels and cards
    SURFACE_ALT = "#F8FAFC"      # Muted fills / idle inputs
    BORDER = "#E1E6EF"           # Soft structural border
    BORDER_INPUT = "#D3DAE6"     # Idle input border
    BORDER_STRONG = "#CBD3E1"    # Controls
    BORDER_HOVER = "#AEB9CE"
    TRACK = "#E8ECF3"            # Disabled button fill, progress track
    HOVER_TINT = "#EEF1F6"       # Neutral hover on transparent controls
    FIELD_DISABLED = "#F1F4F9"

    # ---- Text ----
    TEXT_MAIN = "#1E293B"
    TEXT_LABEL = "#334155"
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
    DANGER_PRESSED = "#9F2A2A"
    DANGER_TEXT = "#922626"
    DANGER_PULSE = "#E24B4B"     # Bright phase of the alert pulse
    DANGER_DIM = "#8C3A3A"       # Dim phase of the alert pulse on dark surfaces
    DANGER_SOFT = "#FDF1F1"
    DANGER_SOFT_STRONG = "#F9DCDC"
    DANGER_BORDER = "#F3BFBF"
    FIELD_INVALID = "#FFFBFB"

    # ---- Ink ----
    INK = "#1E293B"
    INK_HOVER = "#334155"
    INK_PRESSED = "#475569"


class Radius:
    """One radius scale. Nested shapes step down: panel (LG) > stage/banner (MD) > inner (SM)."""
    SM = 6      # small chips, scrollbar handles, inner tiles
    MD = 10     # inputs, buttons, stage, banners
    LG = 14     # panels, toasts
    PILL = 999  # reference only: in QSS use half the widget height


class Space:
    """Spacing scale shared by every main view."""
    PAGE = 24           # outer gutter of the main body
    GUTTER = 20         # between the video column and the sidebar
    GAP = 16            # between stacked panels
    PANEL_X = 18        # inner horizontal padding of every panel
    PANEL_Y = 16        # inner vertical padding of every panel
    PANEL = (PANEL_X, PANEL_Y, PANEL_X, PANEL_Y)


class Size:
    """Fixed dimensions that must match across views."""
    CONTROL = 38        # dashboard buttons / selects
    FIELD = 46          # form inputs and primary form buttons share one height
    TOPBAR = 72
    SIDEBAR = 344
    LOGO_TOPBAR = 48
    LOGO_AUTH = 56


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


def with_alpha(color: str, alpha: int) -> QColor:
    """Return a token colour with the given alpha (0-255), for custom painting."""
    result = QColor(color)
    result.setAlpha(max(0, min(255, alpha)))
    return result


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


def brand_logo(size: int) -> QPixmap | None:
    """
    Load `assets/logo.png` scaled to `size` x `size` (logical px) at 2x for HiDPI.
    Returns None when the asset is missing so callers can fall back to a text mark.
    """
    path = ThemeManager.ASSETS_DIR / "logo.png"
    if not path.exists():
        return None
    pixmap = QPixmap(str(path))
    if pixmap.isNull():
        return None
    scale = 2
    scaled = pixmap.scaled(
        size * scale,
        size * scale,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    scaled.setDevicePixelRatio(scale)
    return scaled


def _css_families(families) -> str:
    generic = {"sans-serif", "serif", "monospace"}
    return ", ".join(f if f in generic else f'"{f}"' for f in families)


class ThemeManager:
    """
    Handles the application's visual styling, including palette configuration
    and QSS stylesheet injection.
    """
    STYLESHEET_PATH = Path(__file__).resolve().parent / "style.qss"
    ASSETS_DIR = Path(__file__).resolve().parent / "assets"

    _TOKEN = re.compile(r"@([A-Z0-9_]+)@")

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
    def _tokens(cls) -> dict[str, str]:
        """Every `@NAME@` placeholder the stylesheet may use."""
        tokens: dict[str, str] = {}
        for name, value in vars(Colors).items():
            if name.isupper() and isinstance(value, str):
                tokens[name] = value
        for name, value in vars(Radius).items():
            if name.isupper() and isinstance(value, int):
                tokens[f"RADIUS_{name}"] = f"{value}px"
        tokens["FONT_UI"] = _css_families(Fonts.UI_FAMILIES)
        tokens["FONT_MONO"] = _css_families(Fonts.MONO_FAMILIES)
        # QSS url() paths are resolved against the CWD, so inject an absolute path.
        tokens["ASSETS"] = cls.ASSETS_DIR.as_posix()
        return tokens

    @classmethod
    def _load_stylesheet(cls) -> str:
        try:
            css = cls.STYLESHEET_PATH.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"[WARN] Could not load stylesheet ({cls.STYLESHEET_PATH}): {exc}")
            return ""

        tokens = cls._tokens()
        unknown: set[str] = set()

        def substitute(match: re.Match) -> str:
            name = match.group(1)
            if name in tokens:
                return tokens[name]
            unknown.add(name)
            return match.group(0)

        css = cls._TOKEN.sub(substitute, css)
        if unknown:
            print(f"[WARN] Unknown stylesheet tokens: {', '.join(sorted(unknown))}")
        return css
