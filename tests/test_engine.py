"""Tests for the engine's cancel, GPU fallback and output handling (no real model)."""
import os
import tempfile
import threading
import unittest
from types import SimpleNamespace
from unittest import mock

import numpy as np

from src.core.subtitle_engine import SubtitleEngine, TranscriptionCancelled
from src.utils.config import Config


def fake_segments(count=3):
    segments = []
    for i in range(count):
        words = [SimpleNamespace(start=i * 3.0, end=i * 3.0 + 1.0, word=f" Line{i}.")]
        segments.append(SimpleNamespace(start=i * 3.0, end=i * 3.0 + 1.0, text=f" Line{i}.", words=words))
    return segments


class FakeModel:
    """Stands in for WhisperModel; records options and can fail or trigger a cancel."""

    def __init__(self, fail=False, on_segment=None):
        self.fail = fail
        self.on_segment = on_segment
        self.options = None

    def transcribe(self, audio, **options):
        if self.fail:
            raise RuntimeError("Library cublas64_12.dll is not found or cannot be loaded")
        self.options = options
        info = SimpleNamespace(duration=9.0, language="en", language_probability=1.0)

        def generate():
            for segment in fake_segments():
                if self.on_segment:
                    self.on_segment()
                yield segment

        return generate(), info


def make_engine(model, device="cpu"):
    """Build an engine without loading anything."""
    engine = SubtitleEngine.__new__(SubtitleEngine)
    engine.model_size = "base"
    engine.device = device
    engine.compute_type = Config.get_compute_type(device)
    engine.model = model
    engine.pipeline = None
    return engine


@mock.patch.object(Config, "USE_BATCHED", False)
@mock.patch("src.core.subtitle_engine.AudioProcessor.load_audio", return_value=np.zeros(16000, dtype=np.float32))
class EngineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.video = os.path.join(self.tmp.name, "clip.mp4")

    def tearDown(self):
        self.tmp.cleanup()

    def test_writes_srt_next_to_video(self, _load):
        path = make_engine(FakeModel()).generate_subtitles(self.video)
        self.assertEqual(os.path.basename(path), "clip_subtitles.srt")
        self.assertEqual(os.listdir(self.tmp.name), ["clip_subtitles.srt"])
        with open(path, encoding="utf-8") as f:
            self.assertTrue(f.read().startswith("1\n00:00:00,000 --> "))

    def test_uses_word_timestamps(self, _load):
        model = FakeModel()
        make_engine(model).generate_subtitles(self.video)
        self.assertTrue(model.options["word_timestamps"])

    def test_cancel_stops_and_writes_nothing(self, _load):
        cancel = threading.Event()
        engine = make_engine(FakeModel(on_segment=cancel.set))
        with self.assertRaises(TranscriptionCancelled):
            engine.generate_subtitles(self.video, cancel_event=cancel)
        self.assertEqual(os.listdir(self.tmp.name), [])

    def test_cancel_does_not_trigger_cpu_fallback(self, _load):
        cancel = threading.Event()
        engine = make_engine(FakeModel(on_segment=cancel.set), device="cuda")
        with mock.patch.object(engine, "_create_model") as create:
            with self.assertRaises(TranscriptionCancelled):
                engine.generate_subtitles(self.video, cancel_event=cancel)
            create.assert_not_called()
        self.assertEqual(engine.device, "cuda")

    def test_gpu_failure_falls_back_to_cpu(self, _load):
        engine = make_engine(FakeModel(fail=True), device="cuda")
        progress = []
        with mock.patch.object(engine, "_create_model", return_value=FakeModel()):
            path = engine.generate_subtitles(self.video, progress_callback=lambda v, m, d="": progress.append(m))
        self.assertEqual(engine.device, "cpu")
        self.assertTrue(os.path.exists(path))
        self.assertIn("⚠️ GPU unavailable, switching to CPU...", progress)

    def test_progress_moves_with_segments(self, _load):
        values = []
        make_engine(FakeModel()).generate_subtitles(self.video, progress_callback=lambda v, m, d="": values.append(v))
        transcribing = [v for v in values if 0.35 < v < 0.85]
        self.assertEqual(len(transcribing), 3)
        self.assertEqual(transcribing, sorted(transcribing))
        self.assertEqual(values[-1], 1.0)


if __name__ == "__main__":
    unittest.main()
