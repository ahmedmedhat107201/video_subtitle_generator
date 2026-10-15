import os
import tkinter as tk
import customtkinter as ctk
from src.gui.theme import PRIMARY, PRIMARY_HOVER, MUTED, DANGER, DANGER_SOFT, CARD_DARK, TEXT, BG_DARK
from src.gui.components import RemoveButton, sync_scroll_region

SUPPORTED_TEXT = "Supported: MP4, AVI, MKV, MOV, WMV, FLV, WEBM"
HEADER_TEXT = "📁 Select Video File"
DROP_HEADER_TEXT = "📥 Drop to add videos"
DROP_PULSE_MS = 450  # border pulse speed while files are dragged over the window


class VideoCard:
    """Encapsulates the video selection card with header, file info and browse button."""

    def __init__(self, parent, browse_command=None, on_change=None):
        # Called with the queue length whenever files are added or removed
        self._on_change = on_change

        # The border matches the card until files are dragged over the window
        self.card = ctk.CTkFrame(parent, corner_radius=15, fg_color=CARD_DARK,
                                 border_width=2, border_color=CARD_DARK)
        self.card.pack(fill="x", pady=(0, 25))

        self.header_label = ctk.CTkLabel(
            self.card,
            text=HEADER_TEXT,
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w",
            text_color=TEXT,
        )
        self.header_label.pack(anchor="w", padx=20, pady=(12, 6))

        self.body = ctk.CTkFrame(self.card, corner_radius=12, fg_color=BG_DARK)
        self.body.pack(fill="both", expand=False, padx=8, pady=(0, 12))

        file_info_frame = ctk.CTkFrame(self.body, fg_color="transparent")
        file_info_frame.pack(fill="x", padx=20, pady=(15, 20))

        # Queue label
        self.file_label = ctk.CTkLabel(
            file_info_frame,
            text="No files in queue",
            font=ctk.CTkFont(size=13),
            text_color=MUTED,
            anchor="w",
            wraplength=700,
        )
        self.file_label.pack(anchor="w", pady=(0, 8))

        # Buttons: Add files and Clear queue
        buttons_frame = ctk.CTkFrame(file_info_frame, fg_color="transparent")
        buttons_frame.pack(fill="x")

        self.browse_button = ctk.CTkButton(
            buttons_frame,
            text="➕ Add Files",
            command=browse_command,
            height=40,
            font=ctk.CTkFont(size=13, weight="bold"),
            corner_radius=8,
            fg_color=PRIMARY,
            hover_color=PRIMARY_HOVER,
        )
        self.browse_button.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.clear_button = ctk.CTkButton(
            buttons_frame,
            text="🧹 Clear Queue",
            command=lambda: self.clear_queue(),
            height=40,
            font=ctk.CTkFont(size=13),
            corner_radius=8,
            fg_color=("#374151", "#111827"),
            hover_color=("#4B5563", "#1F2937"),
        )
        self.clear_button.pack(side="left", fill="x", expand=False)

        self.formats_label = ctk.CTkLabel(
            self.body,
            text=SUPPORTED_TEXT,
            font=ctk.CTkFont(size=11),
            text_color=("#9CA3AF", "#6B7280"),
        )
        self.formats_label.pack(pady=(0, 15))

        # Internal queue state
        self._queue = []

        # List area to display queued files. Use an inner canvas with a
        # vertical scrollbar so many files can be scrolled without expanding
        # the whole card. Keep an initial height so the Generate button stays
        # visible.
        # Create the list container but do not pack it yet — only show it
        # when there are files in the queue. When hidden, the UI will be
        # more compact (no empty list displayed).
        self.list_container = ctk.CTkFrame(self.body, fg_color="transparent", height=120)
        try:
            # Prevent the container from growing to fit children so it never
            # hides the Generate button when many files are added.
            self.list_container.pack_propagate(False)
        except Exception:
            pass
        
        # Create canvas + scrollbar inside the container. Use a sensible
        # solid background color (tk.Canvas doesn't accept CTk's "transparent"
        # token). Match the dark body color so the list appears seamless.
        self._list_canvas = tk.Canvas(self.list_container, highlightthickness=0, bg=BG_DARK)
        self._list_vscroll = ctk.CTkScrollbar(self.list_container, orientation="vertical", command=self._list_canvas.yview)
        self._list_canvas.configure(yscrollcommand=self._list_vscroll.set)
        self._list_vscroll.pack(side="right", fill="y")
        self._list_canvas.pack(side="left", fill="both", expand=True)

        # Inner frame where file rows will be added
        self.inner_list_frame = ctk.CTkFrame(self._list_canvas, fg_color="transparent")
        self._list_window = self._list_canvas.create_window((0, 0), window=self.inner_list_frame, anchor="nw")

        # Keep canvas scrollregion in sync and ensure inner frame width tracks
        def _on_inner_config(event):
            try:
                sync_scroll_region(self._list_canvas)
            except Exception:
                pass

        def _on_canvas_config(event):
            try:
                self._list_canvas.itemconfigure(self._list_window, width=event.width)
            except Exception:
                pass

        self.inner_list_frame.bind("<Configure>", _on_inner_config)
        self._list_canvas.bind("<Configure>", _on_canvas_config)

        # Mouse wheel scrolling for this list is handled by the global handler
        # in src.gui.components.make_scrollable_frame.

    def show_drop_hint(self):
        """Mention drag & drop under the buttons (only when it is available)."""
        self._drop_hint_text = f"or drag & drop videos here  •  {SUPPORTED_TEXT}"
        self.formats_label.configure(text=self._drop_hint_text)

    def set_drop_highlight(self, active: bool):
        """Show that files can be dropped: a gently pulsing border and a hint."""
        if active == getattr(self, "_drop_active", False):
            return
        self._drop_active = active
        if active:
            self.header_label.configure(text=DROP_HEADER_TEXT, text_color=PRIMARY_HOVER)
            self.formats_label.configure(text="Release to add them to the queue")
            self._pulse(True)
        else:
            if getattr(self, "_pulse_job", None):
                self.card.after_cancel(self._pulse_job)
                self._pulse_job = None
            self.card.configure(border_color=CARD_DARK)
            self.header_label.configure(text=HEADER_TEXT, text_color=TEXT)
            self.formats_label.configure(text=getattr(self, "_drop_hint_text", SUPPORTED_TEXT))

    def _pulse(self, bright: bool):
        """Alternate the border between two shades of the accent color."""
        self.card.configure(border_color=PRIMARY_HOVER if bright else PRIMARY)
        self._pulse_job = self.card.after(DROP_PULSE_MS, self._pulse, not bright)

    # Queue management API
    def add_files(self, file_paths):
        """Add files (iterable) to the queue and refresh display.

        Returns number of files added.
        """
        added = 0
        for p in file_paths:
            if p and p not in self._queue:
                self._queue.append(p)
                added += 1
        self._refresh_list()
        return added

    def clear_queue(self):
        """Clear the queued files and update UI."""
        # Prevent clearing if the clear button is disabled (e.g., during processing)
        try:
            if self.clear_button.cget("state") == "disabled":
                return
        except Exception:
            pass

        self._queue.clear()
        self._refresh_list()

    def get_queue(self):
        """Return a shallow copy of the queued file paths."""
        return list(self._queue)

    def _refresh_list(self):
        """Redraw the queued-files list and notify the owner of the new count."""
        self._render_list()
        if self._on_change:
            self._on_change(len(self._queue))

    def _render_list(self):
        """Refresh the visual list of queued files."""
        # Clear current inner list widgets
        for child in self.inner_list_frame.winfo_children():
            child.destroy()
        # A new list always starts at the top
        self._list_canvas.yview_moveto(0)

        if not self._queue:
            self.file_label.configure(text="No files in queue")
            # Hide the list container when there are no files to avoid
            # showing an empty scrollable area.
            try:
                if self.list_container.winfo_ismapped():
                    self.list_container.pack_forget()
            except Exception:
                pass
            return

        self.file_label.configure(text=f"{len(self._queue)} file(s) in queue")

        # Ensure the list container is visible when we have files
        try:
            if not self.list_container.winfo_ismapped():
                self.list_container.pack(fill="both", expand=False, padx=20, pady=(0, 10))
        except Exception:
            # If mapping check fails, attempt to pack anyway
            try:
                self.list_container.pack(fill="both", expand=False, padx=20, pady=(0, 10))
            except Exception:
                pass

        # Show each queued file with its basename and a remove button inside
        # the scrollable inner frame.
        for idx, path in enumerate(self._queue, start=1):
            row = ctk.CTkFrame(self.inner_list_frame, fg_color="transparent")
            row.pack(fill="x", pady=(2, 2))

            name = os.path.basename(path)
            label = ctk.CTkLabel(row, text=f"{idx}. {name}", anchor="w", text_color=("white","white"))
            label.pack(side="left", fill="x", expand=True)

            # small round remove button: a red ✕ that gets a soft red
            # circle on hover
            remove_btn = RemoveButton(row, command=lambda p=path: self._remove_item(p),
                                      bg=BG_DARK, color=DANGER, hover_bg=DANGER_SOFT)
            remove_btn.pack(side="right", padx=(6, 4))

    def _remove_item(self, path):
        try:
            self._queue.remove(path)
        except ValueError:
            pass
        self._refresh_list()
