"""
Main window of the subtitle generator.

Layout (top to bottom): top bar, drop zone, queue list, action bar.
Only the queue list scrolls; everything else stays in place.
"""
import logging
import os
from tkinter import filedialog

import customtkinter as ctk

logger = logging.getLogger(__name__)

# Drag & drop is optional: without tkinterdnd2 the app works as before
try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    DnDBase = TkinterDnD.DnDWrapper
except Exception:  # not installed or failed to load
    TkinterDnD = None
    DnDBase = object

from src.gui import theme
from src.gui.action_bar import ActionBar
from src.gui.drop_zone import DropZone
from src.gui.header import Header
from src.gui.queue_list import QueueList
from src.gui.queue_model import CANCELLED, DONE, FAILED, QUEUED, RUNNING, QueueModel
from src.core.subtitle_controller import SubtitleController
from src.core.subtitle_engine import SubtitleEngine, TranscriptionCancelled

VIDEO_EXTENSIONS = (".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm")


def _plural(count, word):
    return f"{count} {word}" + ("" if count == 1 else "s")


class SubtitleAppWindow(ctk.CTk, DnDBase):
    """Main application window."""

    def __init__(self):
        super().__init__()

        self.title("Subtitle Generator")
        self.geometry("900x680")
        self.minsize(760, 560)

        ctk.set_appearance_mode("dark")
        self.configure(fg_color=theme.BG)

        self.queue = QueueModel()
        # True while a queue is being processed
        self._processing = False
        self._cancelled = False

        self._build_ui()
        self._setup_drag_and_drop()
        # Controller that performs processing in background threads
        self.controller = SubtitleController(model_size="base")
        self._refresh()

    # ----- Layout -----
    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        self.header = Header(self)
        self.header.frame.grid(row=0, column=0, sticky="ew")
        self.header.divider.grid(row=1, column=0, sticky="ew")
        self.header.set_device(SubtitleEngine.detect_device())

        self.drop_zone = DropZone(self, browse_command=self._add_videos)
        self.drop_zone.grid(row=2, column=0, sticky="ew",
                            padx=theme.SPACE_XL, pady=(theme.SPACE_XL, theme.SPACE_L))

        self.queue_list = QueueList(self, on_remove=self._remove_video, on_clear=self._clear_queue)
        self.queue_list.frame.grid(row=3, column=0, sticky="nsew",
                                   padx=theme.SPACE_XL, pady=(0, theme.SPACE_L))

        self.action_bar = ActionBar(self, generate_command=self._generate_subtitles,
                                    cancel_command=self._cancel_queue)
        self.action_bar.divider.grid(row=4, column=0, sticky="ew")
        self.action_bar.frame.grid(row=5, column=0, sticky="ew")

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
            self.drop_zone.set_drag_and_drop(True)
        except Exception as exc:
            logger.warning(f"⚠️  Drag & drop unavailable ({exc})")

    # ----- Adding / removing videos -----
    def _on_drag_enter(self, event):
        if not self._processing:
            self.drop_zone.set_drag_over(True)
        return event.action

    def _on_drag_leave(self, event):
        self.drop_zone.set_drag_over(False)
        return event.action

    def _on_drop(self, event):
        """Queue the video files dropped on the window; other files are ignored."""
        self.drop_zone.set_drag_over(False)
        if self._processing:
            return event.action
        paths = self.tk.splitlist(event.data)
        videos = [p for p in paths if os.path.splitext(p)[1].lower() in VIDEO_EXTENSIONS]
        if len(videos) < len(paths):
            logger.info(f"Ignored {len(paths) - len(videos)} dropped file(s) that are not supported videos")
        self._add_paths(videos)
        return event.action

    def _add_videos(self):
        """Open the file dialog to add one or more videos."""
        if self._processing:
            return
        file_paths = filedialog.askopenfilenames(
            title="Select Video Files",
            filetypes=[
                ("Video files", " ".join(f"*{ext}" for ext in VIDEO_EXTENSIONS)),
                ("All files", "*.*")
            ]
        )
        self._add_paths(file_paths)

    def _add_paths(self, paths):
        if paths and self.queue.add(paths):
            self.action_bar.clear_result()
            self._refresh()

    def _remove_video(self, path):
        if not self._processing:
            self.queue.remove(path)
            self._refresh()

    def _clear_queue(self):
        if not self._processing:
            self.queue.clear()
            self.action_bar.clear_result()
            self._refresh()

    # ----- UI state -----
    def _refresh(self):
        """Redraw the list and update the summary and the main button."""
        self.queue_list.render(self.queue, editable=not self._processing)
        self._update_summary()
        if not self._processing:
            self.action_bar.set_mode("generate", enabled=bool(self.queue.pending()))

    def _update_summary(self):
        counts = self.queue.counts()
        total = len(self.queue.items)
        if total == 0:
            self.action_bar.set_summary("No videos in the queue")
            return
        parts = [_plural(total, "video")]
        for status, word in ((RUNNING, "processing"), (QUEUED, "queued"), (DONE, "done"),
                             (FAILED, "failed"), (CANCELLED, "cancelled")):
            if counts[status]:
                parts.append(f"{counts[status]} {word}")
        self.action_bar.set_summary("  ·  ".join(parts))

    # ----- Processing -----
    def _generate_subtitles(self):
        """Process every queued video, one after another."""
        if self._processing or not self.queue.pending():
            return
        self._processing = True
        self._cancelled = False
        self._run_done = 0
        self._run_failed = 0
        self.controller.reset_cancel()

        self.action_bar.clear_result()
        self.action_bar.set_mode("cancel")
        self.drop_zone.set_enabled(False)
        self._refresh()
        self.after(100, self._start_next_in_queue)

    def _cancel_queue(self):
        """Stop the current video as soon as possible; the rest stay queued."""
        if not self._processing or self._cancelled:
            return
        self._cancelled = True
        self.controller.cancel()
        self.action_bar.set_mode("cancelling")

    def _start_next_in_queue(self):
        pending = self.queue.pending()
        if self._cancelled or not pending:
            self._finish_queue()
            return

        index = pending[0]
        self.queue.start(index)
        self._refresh()
        self.queue_list.show_row(index)

        def progress_cb(value, message, detail="", success=False, error=False):
            self.after(0, self._on_progress, index, value, message, detail)

        try:
            self.controller.start(
                self.queue.items[index].path,
                progress_cb,
                lambda output_path: self.after(0, self._on_file_finished, index, output_path),
                lambda exc: self.after(0, self._on_file_error, index, exc),
            )
        except Exception as exc:
            logger.exception("Failed to start controller: %s", exc)
            self._on_file_error(index, exc)

    def _on_progress(self, index, value, message, detail):
        self.queue.progress(index, value, message, detail)
        self.queue_list.update_row(index, self.queue.items[index])

    def _on_file_finished(self, index, output_path):
        self.queue.finish(index, f"Saved as {os.path.basename(output_path)}")
        self._run_done += 1
        self._refresh_device_badge()
        self._refresh()
        self.after(250, self._start_next_in_queue)

    def _on_file_error(self, index, exc):
        self._refresh_device_badge()
        if isinstance(exc, TranscriptionCancelled):
            self.queue.cancel_running()
            self._refresh()
            self._finish_queue()
            return
        self.queue.fail(index, exc)
        self._run_failed += 1
        self._refresh()
        self.after(400, self._start_next_in_queue)

    def _refresh_device_badge(self):
        """Show the device the loaded model actually uses (e.g. after a CPU fallback)."""
        engine = getattr(self.controller, "engine", None)
        if engine is not None:
            self.header.set_device(engine.device)

    def _finish_queue(self):
        """Restore the UI and show the outcome of the run."""
        self._processing = False
        self.drop_zone.set_enabled(True)
        self._refresh()

        done, failed = self._run_done, self._run_failed
        left = len(self.queue.pending())
        if self._cancelled:
            self.action_bar.show_result(
                "warning", f"Cancelled  ·  {done} done, {_plural(left, 'video')} still queued")
        elif failed:
            self.action_bar.show_result("danger", f"Finished with errors  ·  {done} done, {failed} failed")
        else:
            self.action_bar.show_result(
                "success", f"All done  ·  {_plural(done, 'subtitle file')} saved next to the videos")

    def run(self):
        """Start the application."""
        self.mainloop()
