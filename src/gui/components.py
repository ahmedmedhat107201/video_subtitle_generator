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
        canvas.configure(scrollregion=canvas.bbox("all"))

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
