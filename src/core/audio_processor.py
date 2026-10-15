"""
Audio processing module.
Reads the audio track straight from a video file.
"""
import gc
import logging
import os

import av
import numpy as np
from faster_whisper import decode_audio

from src.utils.config import Config

logger = logging.getLogger(__name__)

ENGLISH_TAGS = ("eng", "en")


class AudioProcessor:
    """Handles reading audio from video files."""

    @staticmethod
    def load_audio(video_path):
        """
        Decode the video's audio track into memory (no temporary files).

        Videos with several audio tracks use the English one when tagged,
        else the track marked default, else the first track.

        Args:
            video_path: Path to input video file

        Returns:
            16 kHz mono float32 numpy array, ready for Whisper
        """
        logger.info(f"📹 Loading video: {os.path.basename(video_path)}")

        track = AudioProcessor._pick_audio_track(video_path)
        if track is None:
            # Single audio track: faster-whisper's own decoder
            audio = decode_audio(video_path, sampling_rate=Config.AUDIO_SAMPLE_RATE)
        else:
            audio = AudioProcessor._decode_track(video_path, track)

        logger.info(f"✅ Audio loaded")
        return audio

    @staticmethod
    def _pick_audio_track(video_path):
        """
        Return the index (among audio tracks) to decode, or None when the
        file has at most one audio track.
        """
        with av.open(video_path, metadata_errors="ignore") as container:
            tracks = list(container.streams.audio)
            if len(tracks) <= 1:
                return None

            languages = [(t.metadata.get("language") or "").lower() for t in tracks]
            for position, language in enumerate(languages):
                if language in ENGLISH_TAGS:
                    choice, reason = position, "English"
                    break
            else:
                defaults = [p for p, t in enumerate(tracks) if t.disposition & av.stream.Disposition.default]
                choice, reason = (defaults[0], "default") if defaults else (0, "first")

            logger.info(f"🎧 {len(tracks)} audio tracks found; using track {choice + 1} "
                        f"({reason}, language: {languages[choice] or 'unknown'})")
            return choice

    @staticmethod
    def _decode_track(video_path, track):
        """Decode one audio track to 16 kHz mono float32, like faster-whisper's decode_audio."""
        resampler = av.audio.resampler.AudioResampler(
            format="s16", layout="mono", rate=Config.AUDIO_SAMPLE_RATE
        )
        chunks = []
        with av.open(video_path, metadata_errors="ignore") as container:
            for frame in AudioProcessor._valid_frames(container.decode(audio=track)):
                for resampled in resampler.resample(frame):
                    chunks.append(resampled.to_ndarray().reshape(-1))
            for resampled in resampler.resample(None):  # flush
                chunks.append(resampled.to_ndarray().reshape(-1))

        # Same cleanup faster-whisper does: resampler objects are not freed otherwise
        del resampler
        gc.collect()

        if not chunks:
            return np.zeros(0, dtype=np.float32)
        return np.concatenate(chunks).astype(np.float32) / 32768.0

    @staticmethod
    def _valid_frames(frames):
        """Skip frames that fail to decode instead of aborting (as faster-whisper does)."""
        while True:
            try:
                yield next(frames)
            except StopIteration:
                return
            except av.error.InvalidDataError:
                continue
