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

# Drag & drop is optional: without tkinterdnd2 the app works as before
try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    DnDBase = TkinterDnD.DnDWrapper
except Exception:  # not installed or failed to load
    TkinterDnD = None
    DnDBase = object

from src.gui.components import make_scrollable_frame, sync_scroll_region
from src.gui.header import Header
from src.gui.video_card import VideoCard
from src.gui.action_panel import ActionPanel
from src.gui.theme import CANVAS_BG
from src.core.subtitle_controller import SubtitleController
from src.core.subtitle_engine import SubtitleEngine, TranscriptionCancelled

VIDEO_EXTENSIONS = (".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm")


class SubtitleAppWindow(ctk.CTk, DnDBase):
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

        # True while a queue is being processed
        self._processing = False

        # Build modern UI
        self._build_ui()
        self._setup_drag_and_drop()
        # Controller that performs processing in background threads
        self.controller = SubtitleController(model_size="base")

    def _build_ui(self):
        """Build the modern, professional user interface."""
        # Scrollable main container (mouse wheel handling lives in the helper)
        main_container, self._page_canvas = make_scrollable_frame(self, canvas_bg=CANVAS_BG)

        # ===== HEADER SECTION =====
        self.header = Header(main_container)
        self.header.set_device(SubtitleEngine.detect_device())

        # ===== CONTENT SECTION =====
        content_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=40, pady=30)

        # Video selection / queue card
        video = VideoCard(content_frame, browse_command=self._add_videos, on_change=self._on_queue_changed)
        self.video_card = video
        self.browse_button = video.browse_button

        # ===== ACTION SECTION =====
        self.action_panel = ActionPanel(
            content_frame,
            generate_command=self._generate_subtitles,
            cancel_command=self._cancel_queue,
        )
        self.generate_button = self.action_panel.generate_button

    def _setup_drag_and_drop(self):
        """Let users drop video files onto the window (if tkinterdnd2 works here)."""
        if TkinterDnD is None:
            logger.warning("⚠️  Drag & drop unavailable (tkinterdnd2 not installed)")
            return
        try:
            self.TkdndVersion = TkinterDnD._require(self)
            self.drop_target_register(DND_FILES)
            self.dnd_bind("<<Drop>>", self._on_drop)
            self.dnd_bind("<<DropEnter>>", self._on_drag_enter)
            self.dnd_bind("<<DropLeave>>", self._on_drag_leave)
            self.video_card.show_drop_hint()
        except Exception as exc:
            logger.warning(f"⚠️  Drag & drop unavailable ({exc})")

    def _on_drag_enter(self, event):
        """Files are being dragged over the window: highlight the file card."""
        if not self._processing:
            self.video_card.set_drop_highlight(True)
        return event.action

    def _on_drag_leave(self, event):
        self.video_card.set_drop_highlight(False)
        return event.action

    def _on_drop(self, event):
        """Queue the video files dropped on the window; other files are ignored."""
        self.video_card.set_drop_highlight(False)
        if self._processing:
            return event.action
        paths = self.tk.splitlist(event.data)
        videos = [p for p in paths if os.path.splitext(p)[1].lower() in VIDEO_EXTENSIONS]
        if len(videos) < len(paths):
            logger.info(f"Ignored {len(paths) - len(videos)} dropped file(s) that are not supported videos")
        if videos:
            self.video_card.add_files(videos)
        return event.action

    def _add_videos(self):
        """Open dialog to add one or more video files to the queue."""
        file_paths = filedialog.askopenfilenames(
            title="Select Video Files",
            filetypes=[
                ("Video files", " ".join(f"*{ext}" for ext in VIDEO_EXTENSIONS)),
                ("All files", "*.*")
            ]
        )

        if not file_paths:
            return

        # Generate is enabled through _on_queue_changed
        self.video_card.add_files(file_paths)

    def _on_queue_changed(self, count):
        """Enable Generate only when files are queued and nothing is running."""
        if count == 0:
            # The file list was hidden: shrink the page and scroll back up
            self.after_idle(self._fit_page)
        button = getattr(self, "generate_button", None)
        if button is None or self._processing:
            return
        button.configure(state="normal" if count > 0 else "disabled")

    def _generate_subtitles(self):
        """Start subtitle generation for the queued files (sequential)."""
        queue = self.video_card.get_queue() if hasattr(self, "video_card") else []
        if not queue:
            messagebox.showwarning(
                "No Video Selected",
                "Please add one or more video files to the queue first"
            )
            return

        # Disable interaction; the Generate button becomes Cancel
        self._processing = True
        self._cancelled = False
        self.controller.reset_cancel()
        self.action_panel.set_processing(True)
        try:
            self.browse_button.configure(state="disabled")
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

    def _fit_page(self):
        """Shrink the page to its content after a list is hidden, and scroll to the top.

        Hiding content does not resize the scrollable page by itself, which
        left the scrollbar stuck at the bottom.
        """
        self.update_idletasks()
        sync_scroll_region(self._page_canvas)
        self._page_canvas.yview_moveto(0)

    def _cancel_queue(self):
        """Stop the current file as soon as possible and skip the rest."""
        if not self._processing or self._cancelled:
            return
        self._cancelled = True
        self.controller.cancel()
        self.generate_button.configure(text="⏹ Cancelling…", state="disabled")

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
                self._refresh_device_badge()
                self._advance_queue()

            self.after(500, _record_success)
        except Exception:
            logger.exception("Failed to handle finished file")

    def _on_queue_file_error(self, exc: Exception):
        """Called from worker thread when a file errors; marshal to main thread and continue."""
        try:
            if isinstance(exc, TranscriptionCancelled):
                self.after(0, self.action_panel.update_progress_ui, 0, "⏹ Cancelled", "", False, True, self._current_index)
                self.after(0, self._finish_queue, self._current_index + 1)
                return

            err = str(exc)
            # Target the current queue item row when showing an error state.
            self.after(0, self.action_panel.update_progress_ui, 0, "❌ Failed", err, False, True, self._current_index)

            def _record_failure():
                self._failed.append(os.path.basename(self._queue[self._current_index]))
                self._refresh_device_badge()
                self._advance_queue()

            self.after(1000, _record_failure)
        except Exception:
            logger.exception("Failed to handle file error")

    def _refresh_device_badge(self):
        """Show the device the loaded model actually uses (e.g. after a CPU fallback)."""
        engine = getattr(self.controller, "engine", None)
        if engine is not None:
            self.header.set_device(engine.device)

    def _advance_queue(self):
        """Move to the next queued file, or finish and show a summary."""
        self._current_index += 1
        if self._current_index < len(self._queue) and not self._cancelled:
            self._start_next_in_queue()
            return
        self._finish_queue(self._current_index)

    def _finish_queue(self, first_unstarted=None):
        """Restore the UI and show a summary of the queue.

        first_unstarted: index of the first file that never started (used to
        label the remaining rows after a cancel).
        """
        if self._cancelled and first_unstarted is not None:
            # Label the files that were never started
            self.action_panel.mark_rows(first_unstarted, "⏭ Not processed")
            self.update_idletasks()

        self.action_panel.hide_video_tile()
        self._fit_page()

        # re-enable UI; Generate follows the (now empty) queue
        self._processing = False
        self.action_panel.set_processing(False)
        try:
            self.browse_button.configure(state="normal")
            self.video_card.clear_button.configure(state="normal")
        except Exception:
            pass
        self._on_queue_changed(len(self.video_card.get_queue()))

        not_processed = len(self._queue) - self._succeeded - len(self._failed)
        failed_list = "\n".join(f"• {name}" for name in self._failed)

        if self._cancelled:
            title = "Cancelled ⏹"
            message = f"Cancelled – {self._succeeded} done, {not_processed} not processed."
            if self._failed:
                message += f"\n\n{len(self._failed)} failed:\n{failed_list}"
        elif self._failed:
            title = "Finished with errors"
            message = f"{self._succeeded} succeeded, {len(self._failed)} failed:\n{failed_list}"
        else:
            title = "All Done 🎉"
            message = f"Subtitles generated for {self._succeeded} file(s)."

        if self._cancelled or self._failed:
            messagebox.showwarning(title, message)
        else:
            messagebox.showinfo(title, message)
