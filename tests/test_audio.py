"""Tests for picking the right audio track."""
import os
import tempfile
import unittest

import av
import numpy as np

from src.core.audio_processor import AudioProcessor

RATE = 16000


def write_video(path, tracks):
    """
    Write an audio-only MKV with one stream per entry in `tracks`.
    Each entry is (language, loud, is_default); a loud track holds a tone,
    a quiet one holds silence, so the decoded audio shows which was used.
    """
    seconds = 1
    with av.open(path, "w", format="matroska") as container:
        streams = []
        for language, loud, is_default in tracks:
            stream = container.add_stream("pcm_s16le", rate=RATE, layout="mono")
            if language:
                stream.metadata["language"] = language
            stream.disposition = av.stream.Disposition.default if is_default else av.stream.Disposition(0)
            samples = np.zeros(RATE * seconds, dtype=np.int16)
            if loud:
                samples = (np.sin(np.arange(samples.size) * 2 * np.pi * 440 / RATE) * 20000).astype(np.int16)
            streams.append((stream, samples))

        for stream, samples in streams:
            frame = av.AudioFrame.from_ndarray(samples.reshape(1, -1), format="s16", layout="mono")
            frame.sample_rate = RATE
            for packet in stream.encode(frame):
                container.mux(packet)
            for packet in stream.encode(None):
                container.mux(packet)


class AudioTrackTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "video.mkv")

    def tearDown(self):
        self.tmp.cleanup()

    def peak(self):
        return float(np.abs(AudioProcessor.load_audio(self.path)).max())

    def test_english_track_is_preferred_over_first(self):
        write_video(self.path, [("fra", False, True), ("eng", True, False)])
        self.assertEqual(AudioProcessor._pick_audio_track(self.path), 1)
        self.assertGreater(self.peak(), 0.3)

    def test_default_track_when_no_english(self):
        write_video(self.path, [("fra", False, False), ("deu", True, True)])
        self.assertEqual(AudioProcessor._pick_audio_track(self.path), 1)
        self.assertGreater(self.peak(), 0.3)

    def test_first_track_when_nothing_tagged(self):
        write_video(self.path, [(None, True, False), (None, False, False)])
        self.assertEqual(AudioProcessor._pick_audio_track(self.path), 0)
        self.assertGreater(self.peak(), 0.3)

    def test_single_track_uses_faster_whisper_decoder(self):
        write_video(self.path, [("eng", True, True)])
        self.assertIsNone(AudioProcessor._pick_audio_track(self.path))
        audio = AudioProcessor.load_audio(self.path)
        self.assertEqual(audio.dtype, np.float32)
        self.assertAlmostEqual(audio.size / RATE, 1.0, places=1)


if __name__ == "__main__":
    unittest.main()
