"""
Modern, professional GUI for subtitle generator using CustomTkinter.
Redesigned with focus on aesthetics, usability, and user experience.
"""
import os
import threading
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from tkinter import filedialog
import logging

logger = logging.getLogger(__name__)

from src.core.subtitle_engine import SubtitleEngine
from src.utils.config import Config
from src.gui.components import make_scrollable_frame
from src.gui.video_tile import make_video_tile
from src.gui.header import Header
from src.gui.video_card import VideoCard
from src.gui.action_panel import ActionPanel
from src.core.subtitle_controller import SubtitleController
# Progress dialog removed; progress UI will be shown inside the main window


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
        
        # Initialize state
        self.engine = None
        self.video_path = None
        
        # Setup FFmpeg
        Config.setup_ffmpeg()
        
        # Build modern UI
        self._build_ui()
        # Controller that performs processing in background threads
        self.controller = SubtitleController(model_size="base")
    
    def _build_ui(self):
        """Build the modern, professional user interface."""
        # Main container with gradient-like sections
        # Create a scrollable area using our helper (keeps this file focused on layout)
        main_container, canvas = make_scrollable_frame(self, canvas_bg="#0f1720")

        # Attach a clamped wheel handler here to avoid overscroll showing blank
        # bands above/below the content. Bind to the canvas directly (not
        # globally) and support X11 Button-4/5 events.
        def _clamped_wheel(event):
            try:
                if hasattr(event, "delta"):
                    step = int(-1 * (event.delta / 120))
                elif hasattr(event, "num"):
                    step = -1 if event.num == 4 else 1 if event.num == 5 else 0
                else:
                    step = 0
            except Exception:
                step = 0
            first, last = canvas.yview()
            # If at the top and scrolling up, or at bottom and scrolling down,
            # ignore to prevent blank space overscroll.
            if step < 0 and first <= 0.0:
                return "break"
            if step > 0 and last >= 1.0:
                return "break"
            canvas.yview_scroll(step, "units")
            return "break"

        canvas.bind("<MouseWheel>", _clamped_wheel)
        canvas.bind("<Button-4>", _clamped_wheel)
        canvas.bind("<Button-5>", _clamped_wheel)
        
        # ===== HEADER SECTION =====
        header = Header(main_container)
        header_frame = header.frame

        # ===== CONTENT SECTION =====
        content_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=40, pady=30)
        
        # Video selection card: make the video_card use the header color so its
        # top rounded corners belong to the header. Then place a body_frame
        # inside with a slightly smaller radius and offset so the header's
        # top corners remain visible and rounded.
        # Video selection / queue card
        video = VideoCard(content_frame, browse_command=self._add_videos)
        self.video_card = video
        # convenience references (kept for backward compatibility)
        self.file_label = getattr(video, "file_label", None)
        self.browse_button = getattr(video, "browse_button", None)
        
        # ===== ACTION SECTION =====
        self.action_panel = ActionPanel(content_frame, generate_command=self._generate_subtitles)
        self.generate_button = self.action_panel.generate_button
    
    def _select_video(self):
        """Handle video file selection with enhanced UX feedback."""
        file_path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.video_path = file_path
            filename = os.path.basename(file_path)
            
            # Update UI with selected file
            from src.gui.theme import PRIMARY

            self.file_label.configure(
                text=f"✓ {filename}",
                text_color=PRIMARY
            )
            self.generate_button.configure(state="normal")
            
            # Visual feedback
            self.browse_button.configure(text="✓ File Selected - Change")

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
            try:
                self.after(0, self.action_panel.update_progress_ui, 1.0, "✅ Complete!", f"Subtitles saved as: {filename}", True, False, self._current_index)
            except Exception:
                # fallback without index
                self.after(0, self.action_panel.update_progress_ui, 1.0, "✅ Complete!", f"Subtitles saved as: {filename}", True, False)

            def _continue():
                self._current_index += 1
                if self._current_index < len(self._queue):
                    self._start_next_in_queue()
                else:
                    self.action_panel.hide_video_tile()
                    messagebox.showinfo(
                        "All Done 🎉",
                        f"All subtitles generated successfully for {len(self._queue)} file(s)."
                    )
                    # re-enable UI
                    try:
                        self.browse_button.configure(state="normal")
                        self.generate_button.configure(state="normal")
                        self.video_card.clear_button.configure(state="normal")
                    except Exception:
                        pass

            self.after(500, _continue)
        except Exception:
            pass

    def _on_queue_file_error(self, exc: Exception):
        """Called from worker thread when a file errors; marshal to main thread and continue."""
        try:
            err = str(exc)
            # Target the current queue item row when showing an error state.
            try:
                self.after(0, self.action_panel.update_progress_ui, 0, "❌ Failed", err, False, True, self._current_index)
            except Exception:
                self.after(0, self.action_panel.update_progress_ui, 0, "❌ Failed", err, False, True)

            def _continue():
                self._current_index += 1
                if self._current_index < len(self._queue):
                    self._start_next_in_queue()
                else:
                    self.action_panel.hide_video_tile()
                    try:
                        self.browse_button.configure(state="normal")
                        self.generate_button.configure(state="normal")
                        self.video_card.clear_button.configure(state="normal")
                    except Exception:
                        pass

            self.after(1000, _continue)
        except Exception:
            pass

    # progress UI is handled by ActionPanel; modern_app_window delegates to it
