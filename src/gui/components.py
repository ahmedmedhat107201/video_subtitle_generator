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
    """Create and return a tuple (scrollable_frame, canvas).

    The returned `scrollable_frame` is a CTkFrame that should be used as the
    main container for building the rest of the app. The function wires
    resizing and scrolling behaviour.
    """
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

    # Mouse wheel support: bind to the canvas directly for Windows/macOS and
    # also support X11 Button-4/5. Callers may still attach a clamping handler
    # if they want to prevent overscroll.
    def _on_mousewheel(event):
        try:
            if hasattr(event, "delta"):
                step = int(-1 * (event.delta / 120))
            elif hasattr(event, "num"):
                # X11: Button-4 (up) / Button-5 (down)
                step = -1 if event.num == 4 else 1 if event.num == 5 else 0
            else:
                step = 0
        except Exception:
            step = 0
        canvas.yview_scroll(step, "units")

    # Bind directly to the canvas (not bind_all) to avoid global handlers.
    canvas.bind("<MouseWheel>", _on_mousewheel)
    canvas.bind("<Button-4>", _on_mousewheel)
    canvas.bind("<Button-5>", _on_mousewheel)

    return scrollable_frame, canvas
