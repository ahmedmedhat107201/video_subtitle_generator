"""Centralized color theme.

Design goals:
- Small, cohesive palette (primary + optional accent + neutrals)
- No green accents; use a dark cyan primary and a warm coral accent
	for highlights. Keep neutrals for backgrounds and muted text.
"""

# Primary (dark cyan) — main interactive accents (user requested)
PRIMARY = "#0E7490"
PRIMARY_HOVER = "#0891B2"

# Accent (coral) — sparing use for emphasis
ACCENT = "#FB7185"

# Backgrounds / cards (dark-only palette)
BG_DARK = "#0B1020"
CARD_DARK = "#0F1724"
CANVAS_BG = "#0f1720"

# Text colors
TEXT = "#E6EEF7"
MUTED = "#94A3B8"

# Danger (red) for destructive actions
DANGER = "#EF4444"
DANGER_HOVER = "#DC2626"
DANGER_SOFT = "#3B1A20"  # dark red tint for subtle hover backgrounds
