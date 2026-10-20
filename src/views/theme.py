"""
Central design tokens, reusable visual helpers and global theme configuration.

Design language: a technical instrument panel. Cool white surfaces on a pale
blue-grey canvas, one deep instrument blue for everything interactive, hairline
borders and near-square corners. Red appears only when something is wrong, and the
video stage is the single dark element so that the image is what the eye lands on.

Single source of truth
----------------------
Every colour, radius and font stack used by `style.qss` is declared here and is
injected into the stylesheet through `@TOKEN@` placeholders (see
`ThemeManager._load_stylesheet`). Change a value once in this file and both the
Python painting code and the QSS follow.

Layers
------
    BACKGROUND      app canvas
    SURFACE         panels and cards
    SURFACE_ALT     sunken fills: inputs and inset strips
    STAGE           the video well (soft charcoal)
"""

import re
import tempfile
from pathlib import Path

from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QGraphicsDropShadowEffect,
    QListView,
)

APP_NAME = "FallSense"
APP_NAME_ACCENT = "Sense"   # end of the name drawn in the accent colour by the wordmark
APP_DESCRIPTION = "Fall risk assessment and detection"


class Colors:
    # ---- Accent: deep instrument blue (the only colour of interactive elements) ----
    PRIMARY = "#1D4FB8"
    PRIMARY_HOVER = "#173F96"
    PRIMARY_PRESSED = "#12327A"
    PRIMARY_TOP = "#2A5CC6"           # top of the subtle button gradient (bottom is PRIMARY)
    PRIMARY_EDGE = "#16398A"          # 1px outline of filled primary buttons
    PRIMARY_SOFT = "#EAF0FB"          # tinted fill
    PRIMARY_SOFT_STRONG = "#DCE7F8"   # tinted fill, stronger
    PRIMARY_BORDER = "#B9CCEE"        # tinted outline
    ACCENT = "#8FB3F2"                # light blue for use on the dark video stage
    ON_PRIMARY = "#FFFFFF"            # text / icons placed on a PRIMARY fill

    # Foreground shared by outline ("ghost") buttons: label and icon use one colour.
    ON_GHOST = "#1F2D44"

    # ---- Layers ----
    BACKGROUND = "#F1F4F9"
    SURFACE = "#FFFFFF"
    SURFACE_RAISED = "#FFFFFF"        # popups and toasts (separated by border + shadow)
    SURFACE_ALT = "#F6F8FB"           # inputs and inset strips
    FIELD_DISABLED = "#EEF1F6"
    TRACK = "#E3E8F0"                 # disabled button fill, progress track
    HOVER_TINT = "#EDF1F7"            # neutral hover on transparent controls

    # ---- Video stage (charcoal well) and dark tooltips ----
    STAGE = "#262E3B"                 # soft charcoal: dark enough for video, gentler than near-black
    STAGE_BORDER = "#3B4657"
    STAGE_TEXT = "#EEF1F6"
    STAGE_TEXT_MUTED = "#AEB8C8"
    CHROME = "#1E293B"
    CHROME_BORDER = "#334155"

    # ---- Lines ----
    BORDER = "#DCE2EC"                # structural hairline
    BORDER_INPUT = "#C5CEDC"          # idle input outline
    BORDER_STRONG = "#B4BFD0"         # controls
    BORDER_HOVER = "#8D9BB3"

    # ---- Text (all pairs >= 4.5:1 on SURFACE and BACKGROUND) ----
    TEXT_MAIN = "#0F1B2D"
    TEXT_LABEL = "#1F2D44"
    TEXT_BODY = "#3B4A63"
    TEXT_MUTED = "#4E5E78"
    TEXT_SUBTLE = "#5F6F88"
    TEXT_INVERSE = "#FFFFFF"          # text on solid danger fills

    # ---- Semantic ----
    SUCCESS = "#1F7A4D"
    SUCCESS_SOFT = "#E8F5EE"
    INFO = "#1D4FB8"
    INFO_SOFT = "#EAF0FB"
    WARNING = "#8F5400"
    WARNING_SOFT = "#FFF4E0"

    # Danger is reserved for alerts. `DANGER_SOLID*` are fills that carry white text.
    DANGER = "#C62828"
    DANGER_SOLID = "#C62828"
    DANGER_SOLID_HOVER = "#B01F1F"
    DANGER_SOLID_PRESSED = "#961818"
    DANGER_TOP = "#D23B3B"            # top of the subtle danger-button gradient
    DANGER_TEXT = "#A61E1E"           # text on DANGER_SOFT
    DANGER_PULSE = "#F04A45"          # bright phase of the alert pulse (on the dark stage)
    DANGER_DIM = "#8A2E2E"            # dim phase of the alert pulse on the dark stage
    DANGER_SOFT = "#FDF0F0"
    DANGER_BORDER = "#F0B8B8"
    FIELD_INVALID = "#FFF8F8"


class Radius:
    """One radius scale, deliberately tight. Nested shapes step down: panel > control > inner."""
    SM = 4      # chips, tags, scrollbar handles, inner tiles
    MD = 6      # inputs, buttons, stage, banners
    LG = 8      # panels, cards, toasts


class Space:
    """Spacing scale shared by every main view."""
    PAGE = 24           # outer gutter of the main body
    GUTTER = 16         # between the video column and the sidebar
    GAP = 14            # between stacked panels
    PANEL_X = 18        # inner horizontal padding of every panel
    PANEL_Y = 16        # inner vertical padding of every panel
    PANEL = (PANEL_X, PANEL_Y, PANEL_X, PANEL_Y)


class Size:
    """Fixed dimensions that must match across views."""
    CONTROL = 36        # dashboard buttons / selects
    FIELD = 42          # form inputs and primary form buttons share one height
    TOPBAR = 60
    SIDEBAR_MIN = 320   # the sidebar flexes between these two widths
    SIDEBAR_MAX = 400
    AUTH_PANEL_MIN = 480
    AUTH_PANEL_MAX = 640


class Fonts:
    UI_FAMILIES = (
        "Segoe UI Variable Text", "Segoe UI", "Inter", "SF Pro Text",
        "Helvetica Neue", "Roboto", "sans-serif",
    )
    DISPLAY_FAMILIES = (
        "Segoe UI Variable Display", "Segoe UI Semibold", "Segoe UI", "Inter",
        "SF Pro Display", "Helvetica Neue", "Roboto", "sans-serif",
    )
    # "Segoe UI Variable Display" only ships Regular and Bold, so weight 600 renders as Bold.
    # Its real semibold is a family of its own, listed first here.
    DISPLAY_SEMIBOLD_FAMILIES = ("Segoe UI Variable Display Semibold", *DISPLAY_FAMILIES[1:])
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


def apply_shadow(widget, blur: int = 24, y: int = 6, alpha: int = 40, x: int = 0):
    """
    Apply a restrained drop shadow to a widget (depth for floating cards and toasts).

    Note: graphics effects force the whole widget subtree to be re-rendered
    off-screen on every repaint, so never use it on a panel that displays live
    video or an animated child. It is meant for static cards and floating elements.
    """
    if widget is None:
        return None
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setXOffset(x)
    effect.setYOffset(y)
    effect.setColor(QColor(0, 0, 0, max(0, min(255, alpha))))
    widget.setGraphicsEffect(effect)
    return effect


def style_combo(combo: QComboBox) -> QComboBox:
    """
    Give a QComboBox a styleable popup. Without an explicit QListView the QSS rules
    for `QComboBox QAbstractItemView::item` (padding, hover) are ignored.
    """
    view = QListView(combo)
    combo.setView(view)
    return combo


def _css_families(families) -> str:
    generic = {"sans-serif", "serif", "monospace"}
    return ", ".join(f if f in generic else f'"{f}"' for f in families)


class ThemeManager:
    """
    Handles the application's visual styling, including palette configuration
    and QSS stylesheet injection.
    """
    STYLESHEET_PATH = Path(__file__).resolve().parent / "style.qss"

    _TOKEN = re.compile(r"@([A-Z0-9_]+)@")

    @classmethod
    def setup_theme(cls, app: QApplication) -> None:
        """
        Applies the base Fusion style, the light palette, the default font and the
        QSS stylesheet.
        """
        app.setStyle("Fusion")
        app.setFont(ui_font(13))

        palette = QPalette()
        role = QPalette.ColorRole
        palette.setColor(role.Window, QColor(Colors.BACKGROUND))
        palette.setColor(role.WindowText, QColor(Colors.TEXT_BODY))
        palette.setColor(role.Base, QColor(Colors.SURFACE))
        palette.setColor(role.AlternateBase, QColor(Colors.SURFACE_ALT))
        palette.setColor(role.Text, QColor(Colors.TEXT_MAIN))
        palette.setColor(role.Button, QColor(Colors.SURFACE))
        palette.setColor(role.ButtonText, QColor(Colors.TEXT_BODY))
        palette.setColor(role.BrightText, QColor(Colors.TEXT_MAIN))
        palette.setColor(role.Highlight, QColor(Colors.PRIMARY))
        palette.setColor(role.HighlightedText, QColor(Colors.ON_PRIMARY))
        palette.setColor(role.PlaceholderText, QColor(Colors.TEXT_SUBTLE))
        palette.setColor(role.ToolTipBase, QColor(Colors.CHROME))
        palette.setColor(role.ToolTipText, QColor(Colors.TEXT_INVERSE))
        palette.setColor(role.Link, QColor(Colors.PRIMARY))
        # Disabled text keeps a readable but clearly inactive tone.
        group = QPalette.ColorGroup.Disabled
        palette.setColor(group, role.Text, QColor(Colors.TEXT_SUBTLE))
        palette.setColor(group, role.ButtonText, QColor(Colors.TEXT_SUBTLE))
        palette.setColor(group, role.WindowText, QColor(Colors.TEXT_SUBTLE))
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
        tokens["FONT_DISPLAY"] = _css_families(Fonts.DISPLAY_FAMILIES)
        tokens["FONT_DISPLAY_SEMIBOLD"] = _css_families(Fonts.DISPLAY_SEMIBOLD_FAMILIES)
        tokens["FONT_MONO"] = _css_families(Fonts.MONO_FAMILIES)
        tokens.update(cls._render_glyphs())
        return tokens

    @classmethod
    def _render_glyphs(cls) -> dict[str, str]:
        """
        Render the small glyphs QSS can only reference as image files (the combo box
        chevron) from the same icon painter and colour tokens used everywhere else, so
        no static asset can drift out of sync with the palette. A 1x and an `@2x` file
        are written; Qt picks the right one for the screen automatically.
        """
        # Local import: icons.py imports this module.
        from src.views.icons import render

        glyphs = {
            "GLYPH_CHEVRON": ("chevron_down", Colors.TEXT_MUTED),
            "GLYPH_CHEVRON_HOVER": ("chevron_down", Colors.TEXT_MAIN),
        }
        tokens: dict[str, str] = {}
        try:
            folder = Path(tempfile.gettempdir()) / "fall-detection-ui-glyphs"
            folder.mkdir(parents=True, exist_ok=True)
            for token, (name, color) in glyphs.items():
                stem = f"{name}-{color.lstrip('#')}"
                render(name, color, 12, scale=1).save(str(folder / f"{stem}.png"), "PNG")
                render(name, color, 12, scale=2).save(str(folder / f"{stem}@2x.png"), "PNG")
                tokens[token] = (folder / f"{stem}.png").as_posix()
        except OSError as exc:
            print(f"[WARN] Could not render UI glyphs: {exc}")
            for token in glyphs:
                tokens[token] = ""
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
