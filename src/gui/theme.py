"""Centralized color theme.

Design goals:
- Small, cohesive palette (primary + optional accent + neutrals)
- No green accents; use a rich violet primary and a warm coral accent
	for highlights. Keep neutrals for backgrounds and muted text.
"""

# Primary (dark cyan) — main interactive accents (user requested)
PRIMARY = "#0E7490"

# Accent (coral) — sparing use for emphasis
ACCENT = "#FB7185"

# Backgrounds / cards (dark-only palette)
BG_DARK = "#0B1020"
CARD_DARK = "#0F1724"

# Text colors
TEXT = "#E6EEF7"
MUTED = "#94A3B8"

# Danger (red) for destructive actions
DANGER = "#EF4444"
