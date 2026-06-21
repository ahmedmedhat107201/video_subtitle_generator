import os
import tkinter as tk
import customtkinter as ctk
from src.gui.theme import PRIMARY, MUTED, DANGER, CARD_DARK, TEXT, BG_DARK


class VideoCard:
    """Encapsulates the video selection card with header, file info and browse button."""

    def __init__(self, parent, browse_command=None):
        self.card = ctk.CTkFrame(parent, corner_radius=15, fg_color=CARD_DARK)
        self.card.pack(fill="x", pady=(0, 25))

        self.header_label = ctk.CTkLabel(
            self.card,
            text="📁 Select Video File",
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
            hover_color=PRIMARY,
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

        formats_label = ctk.CTkLabel(
            self.body,
            text="Supported: MP4, AVI, MKV, MOV, WMV, FLV, WEBM",
            font=ctk.CTkFont(size=11),
            text_color=("#9CA3AF", "#6B7280"),
        )
        formats_label.pack(pady=(0, 15))

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
        canvas_bg = "#0f1720"
        self._list_canvas = tk.Canvas(self.list_container, highlightthickness=0, bg=canvas_bg)
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
                self._list_canvas.configure(scrollregion=self._list_canvas.bbox("all"))
            except Exception:
                pass

        def _on_canvas_config(event):
            try:
                self._list_canvas.itemconfigure(self._list_window, width=event.width)
            except Exception:
                pass

        self.inner_list_frame.bind("<Configure>", _on_inner_config)
        self._list_canvas.bind("<Configure>", _on_canvas_config)

        # Mouse wheel support for the inner canvas
        def _on_mousewheel(event):
            try:
                if hasattr(event, "delta"):
                    step = int(-1 * (event.delta / 120))
                elif hasattr(event, "num"):
                    step = -1 if event.num == 4 else 1 if event.num == 5 else 0
                else:
                    step = 0
            except Exception:
                step = 0
            self._list_canvas.yview_scroll(step, "units")

        self._list_canvas.bind("<MouseWheel>", _on_mousewheel)
        self._list_canvas.bind("<Button-4>", _on_mousewheel)
        self._list_canvas.bind("<Button-5>", _on_mousewheel)

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
        """Refresh the visual list of queued files."""
        # Clear current inner list widgets
        for child in self.inner_list_frame.winfo_children():
            child.destroy()

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

            # small remove button
            remove_btn = ctk.CTkButton(row, text="✖", width=28, height=24, corner_radius=8,
                                      fg_color=DANGER, hover_color=DANGER,
                                      command=lambda p=path: self._remove_item(p))
            remove_btn.pack(side="right")

    def _remove_item(self, path):
        try:
            self._queue.remove(path)
        except ValueError:
            pass
        self._refresh_list()
