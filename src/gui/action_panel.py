import logging

import customtkinter as ctk
from src.gui.video_tile import make_video_tile
from src.gui.theme import PRIMARY, MUTED, DANGER, ACCENT


logger = logging.getLogger(__name__)


class ActionPanel:
    """Encapsulates the action area with Generate button and the video tile."""

    def __init__(self, parent, generate_command=None):
        self.frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.frame.pack(fill="x")

        self.generate_button = ctk.CTkButton(
            self.frame,
            text="🎬 Generate Subtitles",
            command=generate_command,
            height=60,
            font=ctk.CTkFont(size=18, weight="bold"),
            corner_radius=15,
            fg_color=PRIMARY,
            hover_color=PRIMARY,
            state="disabled",
        )
        self.generate_button.pack(fill="x", pady=(0, 15))

        # create video tile under this panel
        self.video_tile, widgets = make_video_tile(self.frame)
        self.video_widgets = widgets

        # track if a queue is being processed
        self._processing_queue = False

    # --- Progress UI control helpers ---
    def show_video_tile(self, video_title: str = None):
        """Show the embedded video tile and set title if provided.

        This method is kept for backward compatibility (single title display).
        For queue-based rendering use `show_video_queue`.
        """
        if video_title:
            try:
                self.video_widgets["title_label"].configure(text=f"🎞️  {video_title}")
            except Exception as exc:
                logger.exception("Failed to set video title: %s", exc)
        try:
            self.video_tile.pack(fill="x", pady=(6, 12))
        except Exception as exc:
            logger.exception("Failed to show video tile: %s", exc)

    def show_video_queue(self, file_paths):
        """Render a list of files inside the video tile with per-file progress bars."""
        try:
            # clear any existing items
            container = self.video_widgets.get("queue_container")
            if container is None:
                return
            for child in container.winfo_children():
                child.destroy()

            self.video_widgets["queue_items"] = []
            for idx, path in enumerate(file_paths, start=1):
                row = ctk.CTkFrame(container, fg_color="transparent")
                row.pack(fill="x", pady=(4, 4))

                # Left column: file name and a small status label under it
                left_col = ctk.CTkFrame(row, fg_color="transparent")
                left_col.pack(side="left", fill="both", expand=True)

                name = path.split("/")[-1].split("\\")[-1]
                label = ctk.CTkLabel(left_col, text=f"{idx}. {name}", anchor="w")
                label.pack(fill="x")

                status_lbl = ctk.CTkLabel(left_col, text="Queued", anchor="w", font=ctk.CTkFont(size=11), text_color=MUTED)
                status_lbl.pack(fill="x", pady=(2,0))

                # Right column: progress bar and percent
                right_col = ctk.CTkFrame(row, fg_color="transparent")
                right_col.pack(side="right", fill="y")

                bar = ctk.CTkProgressBar(right_col, height=12, corner_radius=6, progress_color=PRIMARY)
                bar.set(0)
                bar.pack(side="top", fill="x", expand=False, padx=(6,0))

                percent = ctk.CTkLabel(right_col, text="0%", width=40, text_color=PRIMARY)
                percent.pack(side="top", padx=(6,0), pady=(4,0))

                self.video_widgets["queue_items"].append({
                    "path": path,
                    "label": label,
                    "status": status_lbl,
                    "bar": bar,
                    "percent": percent,
                })

            # show tile
            self.video_tile.pack(fill="x", pady=(6, 12))
            self._processing_queue = True
        except Exception as exc:
            logger.exception("Failed to render video queue: %s", exc)

    def hide_video_tile(self):
        """Hide the embedded video tile."""
        try:
            self.video_tile.pack_forget()
        except Exception as exc:
            logger.exception("Failed to hide video tile: %s", exc)

    def update_progress_ui(self, value: float, message: str, detail: str = "", success: bool = False, error: bool = False, current_index: int = None):
        """Update the widgets inside the embedded video tile.

        value: float in 0..1
        """
        try:
            # If a queue is being processed and we have queue items, update specific item
            queue_items = self.video_widgets.get("queue_items")
            if queue_items and current_index is not None and 0 <= current_index < len(queue_items):
                item = queue_items[current_index]
                bar = item["bar"]
                bar.set(value)
                percent = max(0, min(100, int(round(value * 100))))
                item["percent"].configure(text=f"{percent}%")

                # Update per-item status label as well as the global status line
                try:
                    item["status"].configure(text=message)
                except Exception:
                    pass

                # Per-item status label already updated above. We no longer
                # maintain a global status/detail in the tile to avoid
                # duplicating messages; the per-item label is authoritative.

                # Color state
                if success:
                    # success uses accent (coral) for visibility
                    item["percent"].configure(text_color=ACCENT)
                elif error:
                    item["percent"].configure(text_color=DANGER)
                else:
                    # default per-item percent color should match PRIMARY
                    item["percent"].configure(text_color=PRIMARY)
                return

            # Fallback single-item update (backwards compatible). If a
            # fallback progress widget exists (older versions) update it,
            # otherwise only update status/detail text so the action button
            # area remains compact.
            if "progress_bar" in self.video_widgets:
                try:
                    bar = self.video_widgets["progress_bar"]
                    bar.set(value)
                except Exception:
                    pass
            if "progress_percent" in self.video_widgets:
                try:
                    percent = max(0, min(100, int(round(value * 100))))
                    self.video_widgets["progress_percent"].configure(text=f"{percent}%")
                except Exception:
                    pass

            # No global status/detail — update fallback percent color only
            if success:
                if "progress_percent" in self.video_widgets:
                    try:
                        self.video_widgets["progress_percent"].configure(text_color=ACCENT)
                    except Exception:
                        pass
            elif error:
                if "progress_percent" in self.video_widgets:
                    try:
                        self.video_widgets["progress_percent"].configure(text_color=DANGER)
                    except Exception:
                        pass
            else:
                if "progress_percent" in self.video_widgets:
                    try:
                        self.video_widgets["progress_percent"].configure(text_color=PRIMARY)
                    except Exception:
                        pass
        except Exception as exc:
            logger.exception("Failed to update progress UI: %s", exc)
