"""
Modern, professional GUI for subtitle generator using CustomTkinter.
Redesigned with focus on aesthetics, usability, and user experience.
"""
import os
from tkinter import messagebox
import customtkinter as ctk
from tkinter import filedialog
import logging

logger = logging.getLogger(__name__)

from src.utils.config import Config
from src.gui.components import make_scrollable_frame
from src.gui.header import Header
from src.gui.video_card import VideoCard
from src.gui.action_panel import ActionPanel
from src.gui.theme import CANVAS_BG
from src.core.subtitle_controller import SubtitleController


class SubtitleAppWindow(ctk.CTk):
    """Modern, professional GUI for subtitle generation with enhanced UX."""

    def __init__(self):
        super().__init__()

        # Configure window
        self.title("AI Subtitle Generator")
        self.geometry("900x650")
        self.minsize(800, 600)

        # Set modern appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Setup FFmpeg
        Config.setup_ffmpeg()

        # Build modern UI
        self._build_ui()
        # Controller that performs processing in background threads
        self.controller = SubtitleController(model_size="base")

    def _build_ui(self):
        """Build the modern, professional user interface."""
        # Scrollable main container (mouse wheel handling lives in the helper)
        main_container, _canvas = make_scrollable_frame(self, canvas_bg=CANVAS_BG)

        # ===== HEADER SECTION =====
        Header(main_container)

        # ===== CONTENT SECTION =====
        content_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=40, pady=30)

        # Video selection / queue card
        video = VideoCard(content_frame, browse_command=self._add_videos)
        self.video_card = video
        self.browse_button = video.browse_button

        # ===== ACTION SECTION =====
        self.action_panel = ActionPanel(content_frame, generate_command=self._generate_subtitles)
        self.generate_button = self.action_panel.generate_button

    def _add_videos(self):
        """Open dialog to add one or more video files to the queue."""
        file_paths = filedialog.askopenfilenames(
            title="Select Video Files",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm"),
                ("All files", "*.*")
            ]
        )

        if not file_paths:
            return

        added = self.video_card.add_files(file_paths)
        if added:
            # enable generate when there is at least one file
            try:
                self.generate_button.configure(state="normal")
            except Exception:
                pass

    def _generate_subtitles(self):
        """Start subtitle generation for the queued files (sequential)."""
        queue = self.video_card.get_queue() if hasattr(self, "video_card") else []
        if not queue:
            messagebox.showwarning(
                "No Video Selected",
                "Please add one or more video files to the queue first"
            )
            return

        # Disable interaction
        try:
            self.browse_button.configure(state="disabled")
        except Exception:
            pass
        try:
            self.generate_button.configure(state="disabled")
        except Exception:
            pass

        # Ensure main window stays visible and focused
        self.state('normal')
        self.lift()
        self.update_idletasks()

        # Begin sequential processing of the queue
        self._queue = queue
        self._current_index = 0
        self._succeeded = 0
        self._failed = []
        # Render the queue in the action panel (shows list with 0% for others)
        try:
            self.action_panel.show_video_queue(self._queue)
        except Exception:
            pass

        # Clear and hide the selected-files list from the VideoCard since the
        # generating tile now contains the queue. This keeps the UI focused
        # on generation and prevents duplicate lists.
        try:
            self.video_card.clear_queue()
        except Exception:
            pass

        # Disable the clear button while processing
        try:
            self.video_card.clear_button.configure(state="disabled")
        except Exception:
            pass

        # Start processing first file after short delay so the UI updates
        self.after(100, lambda: self._start_next_in_queue())

    def run(self):
        """Start the application."""
        self.mainloop()

    # --- Queue processing helpers ---
    def _progress_callback(self, value, message, detail="", success=False, error=False, current_index: int = None):
        """Thread-safe progress callback marshalled to the main thread.

        Accepts an optional current_index so queue-based updates target the
        correct per-item progress bar.
        """
        try:
            # forward the current_index to the ActionPanel so it updates the
            # correct queue item (if any).
            self.after(0, self.action_panel.update_progress_ui, value, message, detail, success, error, current_index)
        except Exception:
            pass

    def _start_next_in_queue(self):
        """Start the controller for the next file in the queue (sequential)."""
        if not hasattr(self, "_queue") or self._current_index >= len(self._queue):
            return

        path = self._queue[self._current_index]
        title = os.path.basename(path)
        # Ensure the queue is visible and set current item to 0%
        try:
            # Update status and make sure queue is visible
            self.action_panel.update_progress_ui(0.0, f"🚀 Starting {title}", "Preparing to load AI model", current_index=self._current_index)
        except Exception:
            pass

        # begin controller work for this file. Capture the current index so
        # progress callbacks update the proper queue item even if
        # self._current_index changes later.
        try:
            idx = self._current_index

            def progress_cb(value, message, detail="", success=False, error=False):
                # delegate to the central callback with captured index
                return self._progress_callback(value, message, detail, success, error, current_index=idx)

            self.controller.start(
                path,
                progress_cb,
                self._on_queue_file_finished,
                self._on_queue_file_error,
            )
        except Exception as exc:
            logger.exception("Failed to start controller for %s: %s", path, exc)

    def _on_queue_file_finished(self, output_path):
        """Called from worker thread when a file finishes; marshal to main thread."""
        try:
            filename = os.path.basename(output_path)
            # Mark the just-finished item as complete (set its progress to 100%)
            # and target the current_index so the correct row updates.
            self.after(0, self.action_panel.update_progress_ui, 1.0, "✅ Complete!", f"Subtitles saved as: {filename}", True, False, self._current_index)

            def _record_success():
                self._succeeded += 1
                self._advance_queue()

            self.after(500, _record_success)
        except Exception:
            logger.exception("Failed to handle finished file")

    def _on_queue_file_error(self, exc: Exception):
        """Called from worker thread when a file errors; marshal to main thread and continue."""
        try:
            err = str(exc)
            # Target the current queue item row when showing an error state.
            self.after(0, self.action_panel.update_progress_ui, 0, "❌ Failed", err, False, True, self._current_index)

            def _record_failure():
                self._failed.append(os.path.basename(self._queue[self._current_index]))
                self._advance_queue()

            self.after(1000, _record_failure)
        except Exception:
            logger.exception("Failed to handle file error")

    def _advance_queue(self):
        """Move to the next queued file, or finish and show a summary."""
        self._current_index += 1
        if self._current_index < len(self._queue):
            self._start_next_in_queue()
            return

        self.action_panel.hide_video_tile()

        # re-enable UI
        try:
            self.browse_button.configure(state="normal")
            self.generate_button.configure(state="normal")
            self.video_card.clear_button.configure(state="normal")
        except Exception:
            pass

        if self._failed:
            failed_list = "\n".join(f"• {name}" for name in self._failed)
            messagebox.showwarning(
                "Finished with errors",
                f"{self._succeeded} succeeded, {len(self._failed)} failed:\n{failed_list}"
            )
        else:
            messagebox.showinfo(
                "All Done 🎉",
                f"Subtitles generated for {self._succeeded} file(s)."
            )
