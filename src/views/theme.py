"""
Central design tokens + reusable visual helpers.

Everything here is intentionally small and dependency-free so it can be
imported from any view. The palette follows an enterprise "slate + blue"
system with a strict, limited set of accents for a clean, medical-grade feel.
"""

from PySide6.QtWidgets import QGraphicsDropShadowEffect
from PySide6.QtGui import QColor
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

    Previously this was a no-op ("crisp borders only"). Re-enabling a *very*
    subtle shadow adds real depth and hierarchy that flat borders can't convey,
    which is a big part of a polished, modern desktop UI. Kept low-alpha so it
    never looks heavy or "web-like".
    """
    if widget is None:
        return None
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setXOffset(x)
    effect.setYOffset(y)
    effect.setColor(QColor(15, 23, 42, max(0, min(255, alpha))))  # slate-900 tint
    widget.setGraphicsEffect(effect)
    return effect