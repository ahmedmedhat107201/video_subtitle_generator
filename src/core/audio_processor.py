"""
Audio processing module.
Reads the audio track straight from a video file.
"""
import os
from faster_whisper import decode_audio
from src.utils.config import Config


class AudioProcessor:
    """Handles reading audio from video files."""

    @staticmethod
    def load_audio(video_path):
        """
        Decode the video's audio track into memory (no temporary files).

        Args:
            video_path: Path to input video file

        Returns:
            16 kHz mono float32 numpy array, ready for Whisper
        """
        print(f"📹 Loading video: {os.path.basename(video_path)}")
        audio = decode_audio(video_path, sampling_rate=Config.AUDIO_SAMPLE_RATE)
        print(f"✅ Audio loaded")
        return audio
