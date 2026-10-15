"""Design system: "Cinema".

Neutral graphite surfaces with a single teal accent, inspired by editing
suites. Every colour, font, icon and spacing value used by the GUI lives here.
"""
import re
import tkinter.font as tkfont

import customtkinter as ctk

# ----- Colours -----------------------------------------------------------
BG = "#0E0F11"              # window background (neutral graphite)
SURFACE = "#17181B"         # rows, drop zone, bars
SURFACE_HOVER = "#1E2024"
BORDER = "#26282D"          # hairlines
BORDER_STRONG = "#34373D"   # dashed drop-zone border, scrollbar

ACCENT = "#2DD4BF"          # teal: primary button, progress, highlights
ACCENT_HOVER = "#5EEAD4"
ACCENT_TINT = "#12201F"     # drag-over background, running row
ACCENT_BORDER = "#1F4A45"   # border of the running row
ACCENT_TRACK = "#1A3532"    # empty part of the progress bar
ON_ACCENT = "#042F2A"       # text on teal

TEXT = "#ECEDEF"
TEXT_MUTED = "#8E9199"
TEXT_FAINT = "#5F636B"

SUCCESS = "#6EDC8C"
WARNING = "#F2B84B"         # cancelled result
DANGER = "#FF6B6B"
DANGER_TINT = "#3A1A1D"

# ----- Spacing & shape ---------------------------------------------------
SPACE_XS = 4
SPACE_S = 8
SPACE_M = 12
SPACE_L = 16
SPACE_XL = 24
RADIUS = 6

# ----- Fonts -------------------------------------------------------------
# role: (preferred families, size, weight)
_FONT_ROLES = {
    "title":    (("Bahnschrift", "Segoe UI Semibold", "Helvetica"), 17, "bold"),
    "label":    (("Bahnschrift", "Segoe UI Semibold", "Helvetica"), 12, "bold"),
    "button":   (("Bahnschrift", "Segoe UI Semibold", "Helvetica"), 14, "bold"),
    "heading":  (("Segoe UI Variable Display", "Segoe UI", "Helvetica"), 16, "bold"),
    "body":     (("Segoe UI Variable Text", "Segoe UI", "Helvetica"), 13, "normal"),
    "small":    (("Segoe UI Variable Text", "Segoe UI", "Helvetica"), 11, "normal"),
    "mono":     (("Cascadia Mono", "Consolas", "Courier"), 12, "normal"),
    "mono_small": (("Cascadia Mono", "Consolas", "Courier"), 11, "normal"),
}
_ICON_FAMILIES = ("Segoe Fluent Icons", "Segoe MDL2 Assets")

_font_cache = {}
_family_cache = {}


def _first_available(families):
    """Pick the first installed font family (needs a Tk root to exist)."""
    key = families
    if key not in _family_cache:
        installed = set(tkfont.families())
        _family_cache[key] = next((f for f in families if f in installed), None)
    return _family_cache[key]


def font_tuple(role: str, scaling: float, size: int = None):
    """Font for plain tk widgets/canvas text (CTk scaling applied by hand)."""
    families, default_size, weight = _FONT_ROLES[role]
    family = _first_available(families) or families[-1]
    return (family, -int(round((size or default_size) * scaling)), weight)


def icon_tuple(scaling: float, size: int = 14):
    family = _first_available(_ICON_FAMILIES) or "Segoe UI"
    return (family, -int(round(size * scaling)))


def font(role: str, size: int = None) -> ctk.CTkFont:
    """Return the CTkFont for a text role, e.g. font("body") or font("label")."""
    families, default_size, weight = _FONT_ROLES[role]
    size = size or default_size
    key = (role, size)
    if key not in _font_cache:
        _font_cache[key] = ctk.CTkFont(family=_first_available(families) or families[-1],
                                       size=size, weight=weight)
    return _font_cache[key]


# ----- Icons -------------------------------------------------------------
# Segoe Fluent Icons code points, with a plain-text fallback
ICONS = {
    "upload": ("", "↑"),
    "check": ("", "✓"),
    "close": ("", "✕"),
    "error": ("", "!"),
    "video": ("", "▶"),
}


def icon(name: str):
    """Return (glyph, CTkFont) for an icon, falling back to plain text."""
    glyph, fallback = ICONS[name]
    family = _first_available(_ICON_FAMILIES)
    if family is None:
        return fallback, font("body")
    return glyph, icon_font(family)


def icon_font(family=None, size: int = 14) -> ctk.CTkFont:
    family = family or _first_available(_ICON_FAMILIES) or "Segoe UI"
    key = ("icon", family, size)
    if key not in _font_cache:
        _font_cache[key] = ctk.CTkFont(family=family, size=size)
    return _font_cache[key]


# ----- Text helpers ------------------------------------------------------
_LEADING_SYMBOLS = re.compile(r"^[^\w(]+", re.UNICODE)


def clean_status(message: str) -> str:
    """Strip the leading emoji the engine puts on status messages."""
    return _LEADING_SYMBOLS.sub("", message or "").rstrip(".").strip()
