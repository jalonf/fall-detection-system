"""FallSense Clinical: design tokens and the application-wide theme.

Every colour, size, radius, duration and type style of the interface is defined here once.
`style.qss` refers to the tokens through @TOKEN@ markers that `ThemeManager` fills in, and the
painted components read the same classes, so the stylesheet and the painted widgets always agree.
"""

from __future__ import annotations

import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

from PySide6.QtCore import QEasingCurve
from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import QApplication, QLabel, QWidget

APP_NAME = "FallSense"
APP_DESCRIPTION = "Fall detection and risk monitoring"


class Colors:
    """Colour tokens (section 3.2). Colour is only used to communicate state or action."""

    # Neutrals (blue grey)
    N0 = "#FFFFFF"
    N50 = "#F5F7FA"
    N100 = "#EDF0F4"
    N150 = "#E3E7ED"
    N200 = "#D3D9E2"
    N300 = "#B4BECB"
    N400 = "#8792A4"     # icons and borders only, never text (3.1:1)
    N500 = "#5F6B7E"
    N600 = "#4A5567"
    N700 = "#344052"
    N900 = "#111827"

    # Primary (clinical blue)
    P50 = "#EEF3FB"
    P100 = "#DCE6F7"
    P200 = "#B7CBEE"
    P600 = "#1E4E9E"
    P700 = "#183F82"
    P800 = "#133268"
    BRAND = "#0E2347"    # only the brand panel of the sign-in screens

    # Success
    G50 = "#E8F5EE"
    G200 = "#A8D9BE"
    G500 = "#1F9D5C"
    G600 = "#157347"
    G700 = "#0F5A37"

    # Warning
    A50 = "#FFF5E6"
    A200 = "#F4CB8A"
    A500 = "#D98A0B"
    A600 = "#B36B00"
    A700 = "#8A5200"

    # Danger
    R50 = "#FDEDED"
    R200 = "#F2B3B5"
    R300 = "#E77F83"     # dim phase of the fall-alert pulse
    R600 = "#C0262D"
    R700 = "#A11E24"

    # Stage (dark surfaces behind the video)
    S900 = "#0F151D"
    S800 = "#18212C"
    S700 = "#263241"
    S300 = "#9AA6B6"
    S100 = "#E6EAF0"

    # --- Used outside views/ (do not rename) ---
    BACKGROUND = N50
    SURFACE = N0
    SURFACE_ALT = N100
    BORDER = N200
    BORDER_STRONG = N300
    PRIMARY = P600
    PRIMARY_SOFT = P50
    PRIMARY_BORDER = P200
    DANGER = R600
    DANGER_SOFT = R50
    DANGER_BORDER = R200
    DANGER_TEXT = R700
    TEXT_MAIN = N900
    TEXT_BODY = N700
    TEXT_MUTED = N600
    TEXT_SUBTLE = N500
    TRACK = N150
    STAGE = S900


def qcolor(value: str, alpha: float = 1.0) -> QColor:
    """QColor from a #RRGGBB token, with an optional opacity (0-1)."""
    color = QColor(value)
    if alpha < 1.0:
        color.setAlphaF(alpha)
    return color


def mix(first: str, second: str, amount: float) -> QColor:
    """Linear blend between two tokens: 0 gives `first`, 1 gives `second`."""
    a, b = QColor(first), QColor(second)
    return QColor(
        round(a.red() + (b.red() - a.red()) * amount),
        round(a.green() + (b.green() - a.green()) * amount),
        round(a.blue() + (b.blue() - a.blue()) * amount),
    )


# ---------------------------------------------------------------------- typography
@dataclass(frozen=True)
class TypeSpec:
    px: int
    weight: int
    line: int
    tracking: float = 0.0


_WEIGHTS = {400: QFont.Weight.Normal, 600: QFont.Weight.DemiBold}


class Type:
    """Type scale (section 3.3). Labels take a role with `label.setProperty("type", role)`."""

    ROLES: ClassVar[dict[str, TypeSpec]] = {
        "display": TypeSpec(28, 600, 36, -0.2),
        "title-lg": TypeSpec(22, 600, 28, -0.1),
        "title-md": TypeSpec(16, 600, 22),
        "title-sm": TypeSpec(14, 600, 20),
        "lead": TypeSpec(14, 400, 22),          # brand panel paragraph only
        "body": TypeSpec(13, 400, 20),
        "body-strong": TypeSpec(13, 600, 20),
        "caption": TypeSpec(12, 400, 16),
        "caption-strong": TypeSpec(12, 600, 16),
        "overline": TypeSpec(11, 600, 16, 0.6),
        "metric": TypeSpec(16, 600, 22),
    }

    _cache: ClassVar[dict[tuple[str, bool], QFont]] = {}

    @classmethod
    def font(cls, role: str, *, tabular: bool = False) -> QFont:
        """Font of a role, based on the application font (its family and hinting)."""
        key = (role, tabular)
        font = cls._cache.get(key)
        if font is None:
            spec = cls.ROLES[role]
            font = QFont(QApplication.font())
            font.setPixelSize(spec.px)
            font.setWeight(_WEIGHTS[spec.weight])
            if spec.tracking:
                font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, spec.tracking)
            if tabular:
                font.setFeature(QFont.Tag("tnum"), 1)
            cls._cache[key] = font
        return QFont(font)

    @classmethod
    def line_height(cls, role: str) -> int:
        return cls.ROLES[role].line

    @classmethod
    def reset_cache(cls) -> None:
        cls._cache.clear()

    @classmethod
    def qss(cls) -> str:
        """`QLabel[type="<role>"]` rules, prepended to the stylesheet (the single source of truth)."""
        rules = []
        for role, spec in cls.ROLES.items():
            rules.append(
                f'QLabel[type="{role}"] {{ font-size: {spec.px}px; font-weight: {spec.weight}; '
                f"letter-spacing: {spec.tracking:g}px; }}"
            )
        return "\n".join(rules) + "\n"


def tabular(font: QFont) -> QFont:
    """Same font with tabular figures, for clocks, durations and metrics."""
    result = QFont(font)
    result.setFeature(QFont.Tag("tnum"), 1)
    return result


# ---------------------------------------------------------------------- spacing, sizes, shape, motion
class Space:
    """Spacing scale, base 4. Every margin, padding and gap comes from here."""

    S1 = 4
    S2 = 8
    S3 = 12
    S4 = 16
    S5 = 20
    S6 = 24
    S8 = 32
    S10 = 40


class Size:
    H_SM = 28           # icon buttons in headers, filter combo
    H_MD = 36           # panel buttons and combos
    H_LG = 40           # form inputs and buttons
    TOPBAR = 56
    CONTEXT_BAR = 60
    PANEL_HEADER = 48
    PANEL_FOOTER = 56
    ICON_SM = 16
    ICON_MD = 20
    ICON_LG = 32


class Radius:
    """Square containers (monitoring-console look); controls keep a barely softened corner."""

    R_SM = 2            # badges, checkboxes, tooltips, pills
    R_MD = 2            # buttons, inputs, segments, callouts
    R_LG = 0            # panels, toasts, dialogs: square
    R_INNER = R_MD - 1  # first / last segment inside a bordered control


class Motion:
    FAST = 120
    BASE = 160
    SLOW = 240
    PULSE = 1200
    OUT = QEasingCurve.Type.OutCubic
    IN = QEasingCurve.Type.InCubic
    IN_OUT = QEasingCurve.Type.InOutCubic
    SINE = QEasingCurve.Type.InOutSine


# ---------------------------------------------------------------------- widget helpers
def set_props(widget: QWidget, **props) -> None:
    """Sets dynamic properties used by the stylesheet and repolishes the widget once."""
    changed = False
    for name, value in props.items():
        if isinstance(value, bool):
            value = "true" if value else "false"
        if widget.property(name) != value:
            widget.setProperty(name, value)
            changed = True
    if changed:
        style = widget.style()
        style.unpolish(widget)
        style.polish(widget)
        widget.update()


def make_label(text: str = "", role: str = "body", tone: str | None = None, *,
               wrap: bool = False, parent: QWidget | None = None) -> QLabel:
    """QLabel with a type role (and tone) from the scale."""
    label = QLabel(text, parent)
    label.setProperty("type", role)
    if tone:
        label.setProperty("tone", tone)
    label.setWordWrap(wrap)
    if not wrap:
        label.setMinimumHeight(Type.line_height(role))
    return label


def make_tabular_label(text: str, role: str, tone: str | None = None, *, sample: str = "",
                       parent: QWidget | None = None) -> QLabel:
    """Label with tabular figures. Its font is set directly (no `type` property) so the `tnum`
    feature is kept; with a `sample` its width is fixed, so updating it never relayouts."""
    label = QLabel(text, parent)
    label.setFont(Type.font(role, tabular=True))
    if tone:
        label.setProperty("tone", tone)
    label.setMinimumHeight(Type.line_height(role))
    if sample:
        label.setFixedWidth(label.fontMetrics().horizontalAdvance(sample) + 2)
    return label


# ---------------------------------------------------------------------- contrast
def _channel(value: int) -> float:
    c = value / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _luminance(color: QColor) -> float:
    return 0.2126 * _channel(color.red()) + 0.7152 * _channel(color.green()) + 0.0722 * _channel(color.blue())


def contrast_ratio(foreground: str, background: str, alpha: float = 1.0) -> float:
    """WCAG contrast ratio; `alpha` blends the foreground over the background first."""
    fg = mix(background, foreground, alpha)
    first, second = sorted((_luminance(fg), _luminance(QColor(background))), reverse=True)
    return (first + 0.05) / (second + 0.05)


C = Colors
# Text / background pairs used by the interface: (where, text, background, text opacity).
CONTRAST_PAIRS: tuple[tuple[str, str, str, float], ...] = (
    ("main text", C.N900, C.N0, 1.0),
    ("field labels, messages", C.N700, C.N0, 1.0),
    ("secondary text", C.N600, C.N0, 1.0),
    ("tertiary text, placeholders", C.N500, C.N0, 1.0),
    ("table header", C.N600, C.N50, 1.0),
    ("tertiary text on the canvas", C.N500, C.N50, 1.0),
    ("disabled input text", C.N500, C.N100, 1.0),
    ("ghost button hover", C.N700, C.N100, 1.0),
    ("primary button", C.N0, C.P600, 1.0),
    ("links", C.P600, C.N0, 1.0),
    ("selected / info soft", C.P700, C.P50, 1.0),
    ("selected row", C.N900, C.P50, 1.0),
    ("avatar initials", C.P700, C.P100, 1.0),
    ("success badge", C.G700, C.G50, 1.0),
    ("warning badge", C.A700, C.A50, 1.0),
    ("danger badge", C.R700, C.R50, 1.0),
    ("danger text", C.R700, C.N0, 1.0),
    ("alert rows", C.N900, C.R50, 1.0),
    ("alert badge", C.N0, C.R600, 1.0),
    ("acknowledge button", C.R700, C.N0, 1.0),
    ("tooltip", C.N0, C.N900, 1.0),
    ("stage text", C.S100, C.S900, 1.0),
    ("stage secondary text", C.S300, C.S900, 1.0),
    ("text on stage containers", C.S100, C.S800, 1.0),
    ("brand headline", C.N0, C.BRAND, 1.0),
    ("brand paragraph", C.P100, C.BRAND, 1.0),
    ("brand details", C.P200, C.BRAND, 1.0),
    # The sign-in panel's gradient ends lighter than BRAND: check its text there too.
    ("brand paragraph, panel bottom", C.P100, mix(C.BRAND, C.P800, 0.45).name().upper(), 1.0),
    ("brand details, panel bottom", C.P200, mix(C.BRAND, C.P800, 0.45).name().upper(), 1.0),
)


def check_contrast(minimum: float = 4.5) -> list[str]:
    """Declared text pairs below `minimum` (WCAG AA for body text). Empty when all pass."""
    failures = []
    for where, foreground, background, alpha in CONTRAST_PAIRS:
        ratio = contrast_ratio(foreground, background, alpha)
        if ratio < minimum:
            failures.append(f"{where}: {foreground} on {background} = {ratio:.2f}:1")
    return failures


# ---------------------------------------------------------------------- theme
_GLYPH_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}" '
    'fill="none" stroke-linecap="round" stroke-linejoin="round">{body}</svg>'
)


class ThemeManager:
    STYLESHEET = Path(__file__).with_name("style.qss")
    GLYPH_DIR = Path(tempfile.gettempdir()) / "fallsense-ui"
    _MARKER = re.compile(r"@([A-Z][A-Z0-9_]*)@")

    @classmethod
    def setup_theme(cls, app: QApplication) -> None:
        """Fusion style, the full palette, the application font and the stylesheet (applied once)."""
        app.setStyle("Fusion")
        app.setPalette(cls.palette())
        app.setFont(cls.app_font())
        Type.reset_cache()
        app.setStyleSheet(cls.stylesheet())

    @staticmethod
    def app_font() -> QFont:
        font = QFont()
        font.setFamilies(["Segoe UI", "Arial"])
        font.setPixelSize(13)
        font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
        return font

    @staticmethod
    def palette() -> QPalette:
        palette = QPalette()
        role = QPalette.ColorRole
        roles = {
            role.Window: C.N50, role.WindowText: C.N900, role.Base: C.N0, role.AlternateBase: C.N50,
            role.Text: C.N900, role.PlaceholderText: C.N500, role.Button: C.N0, role.ButtonText: C.N900,
            role.Highlight: C.P600, role.HighlightedText: C.N0, role.ToolTipBase: C.N900,
            role.ToolTipText: C.N0, role.Link: C.P600, role.LinkVisited: C.P700, role.BrightText: C.N0,
            role.Light: C.N0, role.Midlight: C.N100, role.Mid: C.N300, role.Dark: C.N400, role.Shadow: C.N400,
        }
        for color_role, value in roles.items():
            palette.setColor(color_role, QColor(value))
        disabled = QPalette.ColorGroup.Disabled
        for color_role in (role.Text, role.ButtonText, role.WindowText):
            palette.setColor(disabled, color_role, QColor(C.N400))
        return palette

    @classmethod
    def tokens(cls) -> dict[str, str]:
        """Values of the @TOKEN@ markers: colours, spacing, sizes, radii and glyph URLs."""
        tokens: dict[str, str] = {}
        for name, value in vars(Colors).items():
            if name.isupper() and isinstance(value, str):
                tokens[name] = value
        for source in (Space, Size, Radius):
            for name, value in vars(source).items():
                if name.isupper() and isinstance(value, int):
                    tokens[name] = f"{value}px"
        tokens.update(cls._write_glyphs())
        return tokens

    @classmethod
    def stylesheet(cls) -> str:
        tokens = cls.tokens()

        def substitute(match: re.Match) -> str:
            name = match.group(1)
            if name not in tokens:
                raise KeyError(f"Unknown style token @{name}@ in {cls.STYLESHEET.name}")
            return tokens[name]

        template = cls.STYLESHEET.read_text(encoding="utf-8")
        return Type.qss() + cls._MARKER.sub(substitute, template)

    @classmethod
    def _write_glyphs(cls) -> dict[str, str]:
        """Writes the stylesheet glyphs (combo arrow, check mark, radio dot) as SVG files."""
        chevron = '<path d="M4.5 6.5 8 10l3.5-3.5" stroke="{c}" stroke-width="1.5"/>'
        check = '<path d="m3.5 7.2 2.3 2.3 4.7-4.8" stroke="{c}" stroke-width="1.75"/>'
        dot = '<circle cx="7" cy="7" r="3" fill="{c}"/>'
        glyphs = {
            "GLYPH_CHEVRON": (16, chevron.format(c=C.N600)),
            "GLYPH_CHEVRON_DISABLED": (16, chevron.format(c=C.N400)),
            "GLYPH_CHECK": (14, check.format(c=C.N0)),
            "GLYPH_CHECK_DISABLED": (14, check.format(c=C.N400)),
            "GLYPH_DOT": (14, dot.format(c=C.N0)),
            "GLYPH_DOT_DISABLED": (14, dot.format(c=C.N400)),
        }
        cls.GLYPH_DIR.mkdir(parents=True, exist_ok=True)
        urls = {}
        for name, (size, body) in glyphs.items():
            path = cls.GLYPH_DIR / f"{name.lower()}.svg"
            content = _GLYPH_SVG.format(size=size, body=body)
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                path.write_text(content, encoding="utf-8")
            urls[name] = f'url("{path.as_posix()}")'
        return urls
