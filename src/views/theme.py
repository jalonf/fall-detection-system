"""FallSense Clinical: design tokens and the application-wide theme.

Every colour, size, radius, duration and type style of the interface is defined here once.
`style.qss` refers to the tokens through @TOKEN@ markers that `ThemeManager` fills in, and the
painted components read the same classes, so the stylesheet and the painted widgets always agree.
"""

from __future__ import annotations

import re
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
    """One role of the type scale.

    Attributes:
        px: Font size in pixels.
        weight: 400 (regular) or 600 (semibold).
        line: Line height in pixels.
        tracking: Letter spacing in pixels.
    """
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
        """Returns the line height of a role.

        Args:
            role: Type role (see `ROLES`).

        Returns:
            Line height in pixels.
        """
        return cls.ROLES[role].line

    @classmethod
    def reset_cache(cls) -> None:
        """Forgets the fonts built so far (after the application font changes)."""
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
    """Fixed heights of controls and bars, and icon sizes, in pixels."""
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
    """Animation durations (ms) and easing curves.

    Things that appear decelerate (`OUT`) and things that leave accelerate (`IN`), and leaving is
    shorter than appearing. A cross-fade, where nothing moves, follows `FADE`, which is symmetrical,
    so neither page is gone or there too early. Nothing ever blocks the user: a running transition
    is finished at once when the next one starts.
    """
    FAST = 150          # small things leave: toasts, the confirmation dialog
    BASE = 200          # small things appear; scrolling to a field
    SLOW = 280          # pages and form sections slide
    PAGE = 360          # whole screens cross-fade (sign-in and dashboard)
    PULSE = 1200        # one beat of the fall-alert pulse
    OUT = QEasingCurve.Type.OutCubic
    IN = QEasingCurve.Type.InCubic
    FADE = QEasingCurve.Type.InOutSine


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
    """Creates a label with tabular figures, for clocks, durations and metrics.

    Its font is set directly (no `type` property) so the `tnum` feature is kept; with a
    `sample` its width is fixed, so updating it never relayouts.

    Args:
        text: Initial text.
        role: Type role (see `Type.ROLES`).
        tone: Colour tone of the stylesheet, or None.
        sample: The widest text it will show; fixes the label's width.
        parent: Parent widget.

    Returns:
        The label.
    """
    label = QLabel(text, parent)
    label.setFont(Type.font(role, tabular=True))
    if tone:
        label.setProperty("tone", tone)
    label.setMinimumHeight(Type.line_height(role))
    if sample:
        label.setFixedWidth(label.fontMetrics().horizontalAdvance(sample) + 2)
    return label


C = Colors


# ---------------------------------------------------------------------- theme
class ThemeManager:
    """Applies the theme to the application: style, palette, font and stylesheet."""
    STYLESHEET = Path(__file__).with_name("style.qss")
    ASSETS = Path(__file__).with_name("assets")   # stylesheet glyphs: combo arrow, check mark, radio dot
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
        """Returns the application font: Segoe UI (Arial as fallback), 13 px."""
        font = QFont()
        font.setFamilies(["Segoe UI", "Arial"])
        font.setPixelSize(13)
        font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
        return font

    @staticmethod
    def palette() -> QPalette:
        """Returns the palette built from the colour tokens."""
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
        """Values of the @TOKEN@ markers: colours, spacing, sizes, radii and the assets folder.

        Qt resolves relative `url()`s against the working directory, not the stylesheet, so the
        glyphs are referred to through @ASSETS@, the absolute path of `views/assets/`.
        """
        tokens: dict[str, str] = {"ASSETS": cls.ASSETS.as_posix()}
        for name, value in vars(Colors).items():
            if name.isupper() and isinstance(value, str):
                tokens[name] = value
        for source in (Space, Size, Radius):
            for name, value in vars(source).items():
                if name.isupper() and isinstance(value, int):
                    tokens[name] = f"{value}px"
        return tokens

    @classmethod
    def stylesheet(cls) -> str:
        """Builds the stylesheet: the type rules and `style.qss` with its tokens filled in.

        Raises:
            KeyError: If `style.qss` uses a token that does not exist.
        """
        tokens = cls.tokens()

        def substitute(match: re.Match) -> str:
            name = match.group(1)
            if name not in tokens:
                raise KeyError(f"Unknown style token @{name}@ in {cls.STYLESHEET.name}")
            return tokens[name]

        template = cls.STYLESHEET.read_text(encoding="utf-8")
        return Type.qss() + cls._MARKER.sub(substitute, template)
