"""Drop zone: the big dashed area that adds videos (click or drag & drop)."""
import tkinter as tk

import customtkinter as ctk

from src.gui import theme

FORMATS_TEXT = "MP4 · MKV · AVI · MOV · WMV · FLV · WEBM"
HEIGHT = 132

# state -> (border colour, border dashed?, fill, title colour)
_STYLES = {
    "idle":     (theme.BORDER_STRONG, True, theme.SURFACE, theme.TEXT),
    "hover":    (theme.ACCENT, True, theme.SURFACE_HOVER, theme.TEXT),
    "drag":     (theme.ACCENT, False, theme.ACCENT_TINT, theme.ACCENT),
    "disabled": (theme.BORDER, True, theme.BG, theme.TEXT_FAINT),
}


class DropZone(tk.Canvas):
    """A dashed, rounded area: click to browse, or drop files on the window.

    Drawn on a canvas because CTk frames cannot have dashed borders.
    """

    def __init__(self, parent, browse_command):
        self._scale = ctk.ScalingTracker.get_widget_scaling(parent)
        super().__init__(parent, height=int(HEIGHT * self._scale), bg=theme.BG,
                         highlightthickness=0, bd=0, cursor="hand2")
        self._browse = browse_command
        self._state = "idle"
        self._dnd_available = False
        self._hovering = False

        self.bind("<Configure>", lambda e: self._draw())
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)

    # ----- Public API -----
    def set_drag_and_drop(self, available: bool):
        """Mention dropping only when drag & drop actually works."""
        self._dnd_available = available
        self._draw()

    def set_drag_over(self, active: bool):
        """Highlight while files are dragged over the window."""
        if self._state == "disabled":
            return
        self._set_state("drag" if active else ("hover" if self._hovering else "idle"))

    def set_enabled(self, enabled: bool):
        self.configure(cursor="hand2" if enabled else "arrow")
        self._set_state(("hover" if self._hovering else "idle") if enabled else "disabled")

    # ----- Events -----
    def _on_enter(self, _event):
        self._hovering = True
        if self._state == "idle":
            self._set_state("hover")

    def _on_leave(self, _event):
        self._hovering = False
        if self._state == "hover":
            self._set_state("idle")

    def _on_click(self, _event):
        if self._state != "disabled" and self._browse:
            self._browse()

    # ----- Drawing -----
    def _set_state(self, state):
        if state != self._state:
            self._state = state
            self._draw()

    def _texts(self):
        if self._state == "drag":
            return "Release to add videos", "They will be added to the queue"
        if self._state == "disabled":
            return "Processing…", "You can add more videos when it's finished"
        if self._dnd_available:
            return "Drop videos here", "or click to browse"
        return "Click to add videos", "Choose one or more video files"

    def _draw(self):
        self.delete("all")
        width, height = self.winfo_width(), self.winfo_height()
        if width < 10 or height < 10:
            return
        s = self._scale
        border, dashed, fill, title_color = _STYLES[self._state]
        pad = 1 + (1 if not dashed else 0)
        self._rounded_rect(pad, pad, width - pad, height - pad, theme.RADIUS * 1.5 * s,
                           fill=fill, outline=border, width=2 if not dashed else 1,
                           dash=(6, 4) if dashed else None)

        cx, cy = width / 2, height / 2
        icon_color = theme.ACCENT if self._state in ("hover", "drag") else (
            theme.TEXT_FAINT if self._state == "disabled" else theme.TEXT_MUTED)
        glyph, _font = theme.icon("upload")
        title, subtitle = self._texts()

        self.create_text(cx, cy - 34 * s, text=glyph, fill=icon_color, font=theme.icon_tuple(s, 22))
        self.create_text(cx, cy + 2 * s, text=title, fill=title_color, font=theme.font_tuple("heading", s, 15))
        self.create_text(cx, cy + 24 * s, text=subtitle,
                         fill=theme.TEXT_FAINT if self._state == "disabled" else theme.TEXT_MUTED,
                         font=theme.font_tuple("small", s, 12))
        if self._state != "drag":
            self.create_text(cx, cy + 48 * s, text=FORMATS_TEXT, fill=theme.TEXT_FAINT,
                             font=theme.font_tuple("mono_small", s, 10))

    def _rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        """Draw a rounded rectangle as a smoothed polygon."""
        dash = kwargs.pop("dash", None)
        points = [
            x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
            x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
            x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
        ]
        if dash:
            kwargs["dash"] = dash
        return self.create_polygon(points, smooth=True, **kwargs)
