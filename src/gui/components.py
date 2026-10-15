"""Small reusable GUI building blocks: scrollable area, mouse wheel, icon button."""
import tkinter as tk
import customtkinter as ctk

from src.gui import theme


def make_scrollable_frame(parent, bg=theme.BG):
    """Create a vertically scrollable area inside `parent`.

    Returns (outer_frame, scrollable_frame, canvas). Pack/grid `outer_frame`
    yourself and put content in `scrollable_frame`. The scrollbar only
    appears when the content is taller than the area.
    """
    outer_frame = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)

    canvas = tk.Canvas(outer_frame, highlightthickness=0, bd=0, bg=bg)
    v_scroll = ctk.CTkScrollbar(
        outer_frame, orientation="vertical", command=canvas.yview, width=10,
        fg_color="transparent", button_color=theme.BORDER_STRONG,
        button_hover_color=theme.TEXT_FAINT,
    )
    canvas.pack(side="left", fill="both", expand=True)

    def _set_scroll(first, last):
        # Auto-hide the scrollbar when everything fits
        v_scroll.set(first, last)
        needed = float(first) > 0.0 or float(last) < 1.0
        if needed and not v_scroll.winfo_ismapped():
            v_scroll.pack(side="right", fill="y", before=canvas)
        elif not needed and v_scroll.winfo_ismapped():
            v_scroll.pack_forget()

    canvas.configure(yscrollcommand=_set_scroll)

    scrollable_frame = ctk.CTkFrame(canvas, fg_color="transparent", corner_radius=0)
    window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas._content, canvas._window_id = scrollable_frame, window_id

    scrollable_frame.bind("<Configure>", lambda e: sync_scroll_region(canvas))
    canvas.bind("<Configure>", lambda e: canvas.itemconfigure(window_id, width=e.width))

    # Mouse wheel, bound globally so it works over any child widget; it only
    # scrolls when the pointer is inside this area. Clamped: no overscroll.
    def _on_mousewheel(event):
        step = _wheel_step(event)
        if step == 0 or not _pointer_inside(event, canvas):
            return
        first, last = canvas.yview()
        if (step < 0 and first <= 0.0) or (step > 0 and last >= 1.0):
            return "break"
        canvas.yview_scroll(step, "units")
        return "break"

    canvas.bind_all("<MouseWheel>", _on_mousewheel)
    canvas.bind_all("<Button-4>", _on_mousewheel)
    canvas.bind_all("<Button-5>", _on_mousewheel)

    return outer_frame, scrollable_frame, canvas


def sync_scroll_region(canvas):
    """Fit the canvas scroll area to its content.

    When the content becomes shorter than the view (e.g. a list is emptied),
    scroll back to the top so the scrollbar doesn't stay stuck at the bottom.
    """
    bbox = canvas.bbox("all")
    canvas.configure(scrollregion=bbox)
    if bbox is None or bbox[3] - bbox[1] <= canvas.winfo_height():
        canvas.yview_moveto(0)


def refit(canvas):
    """Resize the scrollable content to what it needs now, then fix the scroll area.

    A frame inside a canvas does not shrink by itself when children are
    removed, which left the list scrolled down after it was emptied.
    """
    canvas.update_idletasks()
    canvas.itemconfigure(canvas._window_id, height=canvas._content.winfo_reqheight())
    canvas.update_idletasks()
    sync_scroll_region(canvas)


def scroll_into_view(canvas, widget):
    """Scroll `canvas` just enough to show `widget` (a descendant of it)."""
    canvas.update_idletasks()
    bbox = canvas.bbox("all")
    if not bbox:
        return
    total = bbox[3] - bbox[1]
    view = canvas.winfo_height()
    if total <= view:
        return
    top = widget.winfo_rooty() - canvas.winfo_rooty() + canvas.canvasy(0)
    bottom = top + widget.winfo_height()
    first = canvas.canvasy(0)
    if top < first:
        canvas.yview_moveto(top / total)
    elif bottom > first + view:
        canvas.yview_moveto((bottom - view) / total)


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


def _pointer_inside(event, canvas):
    """True if the mouse pointer is over `canvas` or one of its children."""
    try:
        widget = event.widget.winfo_containing(event.x_root, event.y_root)
    except Exception:
        return False
    while widget is not None:
        if widget is canvas:
            return True
        widget = getattr(widget, "master", None)
    return False


class RemoveButton(tk.Canvas):
    """A small round ✕ button: faint cross that turns red on a soft red circle.

    Drawn on a canvas because CTkButton pads rounded corners and cannot be
    made into a small circle.
    """

    def __init__(self, parent, command, size=22, bg=theme.SURFACE):
        scale = ctk.ScalingTracker.get_widget_scaling(parent)
        px = int(round(size * scale))
        super().__init__(parent, width=px, height=px, bg=bg, highlightthickness=0, bd=0, cursor="hand2")
        self._command = command
        self._bg = bg
        self._circle = self.create_oval(1, 1, px - 1, px - 1, fill=bg, outline="")
        inset = px * 0.35
        self._lines = [
            self.create_line(x0, y0, x1, y1, fill=theme.TEXT_FAINT,
                             width=max(1.5, 1.5 * scale), capstyle="round")
            for x0, y0, x1, y1 in ((inset, inset, px - inset, px - inset),
                                   (inset, px - inset, px - inset, inset))
        ]
        self.bind("<Enter>", lambda e: self._paint(theme.DANGER_TINT, theme.DANGER))
        self.bind("<Leave>", lambda e: self._paint(self._bg, theme.TEXT_FAINT))
        self.bind("<Button-1>", lambda e: self._command())

    def set_background(self, bg):
        """Match the row background (e.g. when the row changes state)."""
        self._bg = bg
        self.configure(bg=bg)
        self._paint(bg, theme.TEXT_FAINT)

    def _paint(self, circle, cross):
        self.itemconfigure(self._circle, fill=circle)
        for line in self._lines:
            self.itemconfigure(line, fill=cross)
