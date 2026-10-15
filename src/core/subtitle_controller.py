"""Controller that runs subtitle generation in a background thread.

This encapsulates model loading, calling `SubtitleEngine.generate_subtitles`,
and reporting progress via provided callbacks. The callbacks will be invoked
from the worker thread, so callers (UI) should marshal to the main thread
if needed (for example using `tk.after`).
"""
import threading
import time
from typing import Callable, Optional

from src.core.subtitle_engine import SubtitleEngine


class SubtitleController:
    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self.engine: Optional[SubtitleEngine] = None
        # Shared by every file of a queue; set by cancel()
        self._cancel_event = threading.Event()

    def cancel(self):
        """Ask the running (and any following) file to stop as soon as possible."""
        self._cancel_event.set()

    def reset_cancel(self):
        """Clear a previous cancel request; call when a new queue starts."""
        self._cancel_event.clear()

    def start(self, video_path: str,
              progress_callback: Callable[[float, str, str, bool, bool], None],
              finished_callback: Callable[[str], None],
              error_callback: Callable[[Exception], None]):
        """Start processing `video_path` in a background thread.

        progress_callback(value, message, detail, success, error)
        finished_callback(output_path)
        error_callback(exception)  # TranscriptionCancelled when cancelled
        """
        thread = threading.Thread(
            target=self._run,
            args=(video_path, progress_callback, finished_callback, error_callback),
            daemon=True,
        )
        thread.start()

    def _run(self, video_path, progress_callback, finished_callback, error_callback):
        try:
            # Load the model only once and reuse it for every queued file.
            # Files are processed sequentially, so sharing the engine is safe.
            if self.engine is None:
                try:
                    progress_callback(0.01, "🔧 Loading AI model...", f"Preparing Whisper {self.model_size} model...", False, False)
                except Exception:
                    pass

                # small delay to allow UI to render first
                time.sleep(0.1)

                # Initialize engine (heavy operation)
                self.engine = SubtitleEngine(model_size=self.model_size)
                try:
                    progress_callback(0.05, "✅ AI model loaded", "Model ready for transcription", False, False)
                except Exception:
                    pass

            # Run generation with the provided progress callback
            output_path = self.engine.generate_subtitles(
                video_path,
                progress_callback=progress_callback,
                cancel_event=self._cancel_event,
            )

            # finished
            try:
                finished_callback(output_path)
            except Exception:
                pass

        except Exception as e:
            try:
                error_callback(e)
            except Exception:
                pass
