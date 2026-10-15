"""Queue list: every video with its state, progress and result, in one place."""
import os

import customtkinter as ctk

from src.gui import theme
from src.gui.components import RemoveButton, make_scrollable_frame, refit, scroll_into_view
from src.gui.queue_model import CANCELLED, DONE, FAILED, QUEUED, RUNNING

# status -> (label text, colour, icon name or None)
_STATUS_STYLE = {
    QUEUED:    ("QUEUED", theme.TEXT_FAINT, None),
    RUNNING:   ("", theme.ACCENT, None),
    DONE:      ("DONE", theme.SUCCESS, "check"),
    FAILED:    ("FAILED", theme.DANGER, "error"),
    CANCELLED: ("CANCELLED", theme.TEXT_MUTED, None),
}


def _fit(text, label_font, max_px, scaling, middle=False):
    """Shorten `text` with an ellipsis so it fits in `max_px` pixels."""
    if max_px <= 0:
        return text
    measure = lambda t: label_font.measure(t) * scaling
    if measure(text) <= max_px:
        return text
    keep = len(text)
    while keep > 4:
        keep -= 1
        if middle:
            head = keep // 2 + keep % 2
            candidate = f"{text[:head]}…{text[len(text) - keep // 2:]}"
        else:
            candidate = f"{text[:keep]}…"
        if measure(candidate) <= max_px:
            return candidate
    return "…"


class QueueRow:
    """One video in the queue."""

    def __init__(self, parent, number, on_remove):
        self._scale = ctk.ScalingTracker.get_widget_scaling(parent)
        self._name = ""
        self._sub = ""
        self._status = None

        self.frame = ctk.CTkFrame(parent, fg_color=theme.SURFACE, corner_radius=theme.RADIUS,
                                  border_width=1, border_color=theme.BORDER)
        self.frame.grid_columnconfigure(1, weight=1)

        self.number = ctk.CTkLabel(self.frame, text=f"{number:02d}", font=theme.font("mono_small"),
                                   text_color=theme.TEXT_FAINT, width=28, anchor="w")
        self.number.grid(row=0, column=0, rowspan=2, padx=(theme.SPACE_L, 0), pady=theme.SPACE_M, sticky="w")

        self.name = ctk.CTkLabel(self.frame, text="", font=theme.font("body"), text_color=theme.TEXT,
                                 anchor="w", width=1, height=20)
        self.name.grid(row=0, column=1, sticky="ew", padx=(theme.SPACE_S, theme.SPACE_M), pady=(theme.SPACE_M, 0))

        self.sub = ctk.CTkLabel(self.frame, text="", font=theme.font("small"), text_color=theme.TEXT_FAINT,
                                anchor="w", width=1, height=16)
        self.sub.grid(row=1, column=1, sticky="ew", padx=(theme.SPACE_S, theme.SPACE_M), pady=(0, theme.SPACE_M))

        # Right side: icon + status word, or the percentage while running
        status_box = ctk.CTkFrame(self.frame, fg_color="transparent")
        status_box.grid(row=0, column=2, rowspan=2, sticky="e", padx=(0, theme.SPACE_S))
        self.icon = ctk.CTkLabel(status_box, text="", width=16, text_color=theme.TEXT_FAINT)
        self.icon.pack(side="left", padx=(0, theme.SPACE_XS))
        self.status = ctk.CTkLabel(status_box, text="", font=theme.font("label", 11),
                                   text_color=theme.TEXT_FAINT)
        self.status.pack(side="left")
        self.percent = ctk.CTkLabel(status_box, text="", font=theme.font("mono"),
                                    text_color=theme.ACCENT, width=44, anchor="e")

        self.remove = RemoveButton(self.frame, command=on_remove)
        self.remove.grid(row=0, column=3, rowspan=2, padx=(0, theme.SPACE_M))

        # Thin progress line along the bottom of the row while running
        self.bar = ctk.CTkProgressBar(self.frame, height=3, corner_radius=2, border_width=0,
                                      fg_color=theme.ACCENT_TRACK, progress_color=theme.ACCENT)
        self.bar.set(0)

        self.frame.bind("<Configure>", lambda e: self._fit_texts())

    def update(self, item, removable):
        """Show the current state of `item` (a QueueItem)."""
        self._name = os.path.basename(item.path)
        status = item.status

        if status == QUEUED:
            self._sub = os.path.dirname(item.path)
        elif status == RUNNING:
            self._sub = " · ".join(p for p in (theme.clean_status(item.message), item.detail) if p)
        elif status == DONE:
            self._sub = item.detail or "Subtitles saved"
        elif status == FAILED:
            self._sub = item.error or "Something went wrong"
        else:
            self._sub = "Stopped before it finished"

        if status != self._status:
            self._apply_status_style(status)
            self._status = status

        if status == RUNNING:
            self.bar.set(item.progress)
            self.percent.configure(text=f"{int(round(item.progress * 100))}%")

        if removable and status != RUNNING:
            self.remove.grid()
        else:
            self.remove.grid_remove()

        self._fit_texts()

    def _apply_status_style(self, status):
        word, colour, icon_name = _STATUS_STYLE[status]
        running = status == RUNNING

        bg = theme.ACCENT_TINT if running else theme.SURFACE
        self.frame.configure(fg_color=bg, border_color=theme.ACCENT_BORDER if running else theme.BORDER)
        self.remove.set_background(bg)

        self.number.configure(text_color=theme.ACCENT if running else theme.TEXT_FAINT)
        self.name.configure(text_color=theme.TEXT_MUTED if status == CANCELLED else theme.TEXT)
        self.sub.configure(text_color={FAILED: theme.DANGER, RUNNING: theme.TEXT_MUTED}.get(status, theme.TEXT_FAINT))

        self.status.configure(text=word, text_color=colour)
        if running:
            self.status.pack_forget()
            self.percent.pack(side="left")
            self.bar.grid(row=2, column=0, columnspan=4, sticky="ew",
                          padx=theme.SPACE_L, pady=(0, theme.SPACE_S))
        else:
            self.percent.pack_forget()
            self.status.pack(side="left")
            self.bar.grid_remove()

        if icon_name:
            glyph, glyph_font = theme.icon(icon_name)
            self.icon.configure(text=glyph, font=glyph_font, text_color=colour)
            self.icon.pack(side="left", padx=(0, theme.SPACE_XS), before=self.status)
        else:
            self.icon.pack_forget()

    def _fit_texts(self):
        """Shorten the name / detail so they never push the status off the row."""
        width = self.name.winfo_width()
        if width <= 1:
            return
        self.name.configure(text=_fit(self._name, theme.font("body"), width - 4, self._scale, middle=True))
        self.sub.configure(text=_fit(self._sub, theme.font("small"), width - 4, self._scale))


class QueueList:
    """Header ("QUEUE n" + Clear) and the scrollable list of rows."""

    def __init__(self, parent, on_remove, on_clear):
        self._on_remove = on_remove
        self.frame = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        self.frame.grid_rowconfigure(1, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self.frame, fg_color="transparent", height=32)
        header.grid(row=0, column=0, sticky="ew", pady=(0, theme.SPACE_S))
        ctk.CTkLabel(header, text="QUEUE", font=theme.font("label"), text_color=theme.TEXT_MUTED).pack(side="left")
        self.count = ctk.CTkLabel(header, text="0", font=theme.font("mono_small"), text_color=theme.TEXT_FAINT)
        self.count.pack(side="left", padx=(theme.SPACE_S, 0))
        self.clear_button = ctk.CTkButton(
            header, text="CLEAR", command=on_clear, width=64, height=26,
            font=theme.font("label", 11), corner_radius=theme.RADIUS,
            fg_color="transparent", hover_color=theme.SURFACE_HOVER,
            text_color=theme.TEXT_MUTED, text_color_disabled=theme.TEXT_FAINT,
        )
        self.clear_button.pack(side="right")

        outer, self.body, self.canvas = make_scrollable_frame(self.frame, bg=theme.BG)
        outer.grid(row=1, column=0, sticky="nsew")

        self.empty = ctk.CTkLabel(self.body, text="No videos yet. Add some above to get started.",
                                  font=theme.font("small", 12), text_color=theme.TEXT_FAINT)
        self.rows = []
        self._paths = []

    def render(self, model, editable=True):
        """Bring the rows in line with the model."""
        paths = [item.path for item in model.items]
        if paths != self._paths:
            for row in self.rows:
                row.frame.destroy()
            self.rows = []
            for number, item in enumerate(model.items, start=1):
                row = QueueRow(self.body, number, on_remove=lambda p=item.path: self._on_remove(p))
                row.frame.pack(fill="x", pady=(0, theme.SPACE_S), padx=(0, theme.SPACE_XS))
                self.rows.append(row)
            self._paths = paths

        if self.rows:
            self.empty.pack_forget()
        else:
            self.empty.pack(pady=theme.SPACE_XL)

        for row, item in zip(self.rows, model.items):
            row.update(item, removable=editable)

        # Rows change height with their state (progress line), so refit every time
        refit(self.canvas)
        self.count.configure(text=str(len(model.items)))
        has_removable = any(item.status != RUNNING for item in model.items)
        self.clear_button.configure(state="normal" if editable and has_removable else "disabled")

    def update_row(self, index, item, editable=False):
        """Refresh a single row (cheap; used for progress updates)."""
        if 0 <= index < len(self.rows):
            self.rows[index].update(item, removable=editable)

    def show_row(self, index):
        """Scroll so the row at `index` is visible."""
        if 0 <= index < len(self.rows):
            scroll_into_view(self.canvas, self.rows[index].frame)
