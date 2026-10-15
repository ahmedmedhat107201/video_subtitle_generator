"""Small GUI helper components used by the main window.

This module exposes a scrollable container factory so the main window can
remain focused on layout and behavior while the low-level canvas/scrollbar
implementation lives here.
"""
import tkinter as tk
import customtkinter as ctk
from src.gui.theme import BG_DARK


def make_scrollable_frame(parent, canvas_bg: str | None = None):
    """Create and return a tuple (scrollable_frame, canvas).

    If canvas_bg is None the theme background will be used.
    """
    if canvas_bg is None:
        canvas_bg = BG_DARK
    outer_frame = ctk.CTkFrame(parent, fg_color="transparent")
    outer_frame.pack(fill="both", expand=True, padx=0, pady=0)

    canvas = tk.Canvas(outer_frame, highlightthickness=0, bg=canvas_bg)
    v_scroll = ctk.CTkScrollbar(outer_frame, orientation="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=v_scroll.set)
    v_scroll.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    # The scrollable frame where the app contents live
    scrollable_frame = ctk.CTkFrame(canvas, fg_color="transparent")
    window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

    # Keep canvas scrollregion in sync with the size of the inner frame
    def _on_frame_config(event):
        sync_scroll_region(canvas)

    def _on_canvas_config(event):
        # make the inner frame width match the canvas width
        canvas.itemconfigure(window_id, width=event.width)

    scrollable_frame.bind("<Configure>", _on_frame_config)
    canvas.bind("<Configure>", _on_canvas_config)

    # Mouse wheel support. Bound globally so it works while the pointer is
    # over any child widget, not just bare canvas. If the pointer is inside a
    # nested scrollable canvas (e.g. the queued-files list) that one scrolls
    # instead. Scrolling is clamped so there is no overscroll past the content.
    def _on_mousewheel(event):
        step = _wheel_step(event)
        if step == 0:
            return

        target = _nested_scroll_target(event, canvas) or canvas
        first, last = target.yview()
        if step < 0 and first <= 0.0:
            return "break"
        if step > 0 and last >= 1.0:
            return "break"
        target.yview_scroll(step, "units")
        return "break"

    canvas.bind_all("<MouseWheel>", _on_mousewheel)
    canvas.bind_all("<Button-4>", _on_mousewheel)
    canvas.bind_all("<Button-5>", _on_mousewheel)

    return scrollable_frame, canvas


def sync_scroll_region(canvas):
    """Fit the canvas scroll area to its content.

    When the content becomes shorter than the view (e.g. a list is emptied),
    scroll back to the top so the scrollbar doesn't stay stuck at the bottom.
    """
    bbox = canvas.bbox("all")
    canvas.configure(scrollregion=bbox)
    if bbox is None or bbox[3] - bbox[1] <= canvas.winfo_height():
        canvas.yview_moveto(0)


def _wheel_step(event) -> int:
    """Return -1 (up), 1 (down) or 0 for a mouse wheel event on any platform."""
    # X11 sends Button-4 (up) / Button-5 (down) with delta == 0
    if getattr(event, "num", None) == 4:
        return -1
    if getattr(event, "num", None) == 5:
        return 1
    delta = getattr(event, "delta", 0) or 0
    if delta > 0:
        return -1
    if delta < 0:
        return 1
    return 0


def _nested_scroll_target(event, main_canvas):
    """Return a nested tk.Canvas under the pointer that can scroll, if any."""
    try:
        widget = event.widget.winfo_containing(event.x_root, event.y_root)
    except Exception:
        return None

    while widget is not None and widget is not main_canvas:
        if isinstance(widget, tk.Canvas):
            first, last = widget.yview()
            # Only scroll it when its content is taller than its viewport
            if first > 0.0 or last < 1.0:
                return widget
        widget = getattr(widget, "master", None)
    return None


class RemoveButton(tk.Canvas):
    """A small round ✕ button: thin red cross, soft red circle on hover.

    Drawn on a canvas because CTkButton pads rounded corners and cannot be
    made into a small circle.
    """

    def __init__(self, parent, command, size=20, bg=BG_DARK,
                 color="#EF4444", hover_bg="#3B1A20"):
        scale = ctk.ScalingTracker.get_widget_scaling(parent)
        px = int(round(size * scale))
        super().__init__(parent, width=px, height=px, bg=bg, highlightthickness=0, cursor="hand2")
        self._command = command
        self._circle = self.create_oval(1, 1, px - 1, px - 1, fill=bg, outline="")
        inset = px * 0.34
        for x0, y0, x1, y1 in ((inset, inset, px - inset, px - inset), (inset, px - inset, px - inset, inset)):
            self.create_line(x0, y0, x1, y1, fill=color, width=max(1.5, 1.6 * scale), capstyle="round")
        self._bg, self._hover_bg = bg, hover_bg
        self.bind("<Enter>", lambda e: self.itemconfigure(self._circle, fill=self._hover_bg))
        self.bind("<Leave>", lambda e: self.itemconfigure(self._circle, fill=self._bg))
        self.bind("<Button-1>", lambda e: self._command())
