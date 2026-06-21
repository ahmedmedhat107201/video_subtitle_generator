"""
Configuration module for the subtitle generator.
Handles FFmpeg setup and system-level configuration.
"""
import os
from imageio_ffmpeg import get_ffmpeg_exe


class Config:
    """Central configuration for the application."""
    
    # Whisper model configuration
    DEFAULT_MODEL_SIZE = "base"
    MODEL_SIZES = ["tiny", "base", "small", "medium", "large-v2", "large-v3"]
    
    # Audio processing settings
    AUDIO_SAMPLE_RATE = 16000  # Whisper requires 16kHz
    AUDIO_CODEC = 'pcm_s16le'
    AUDIO_BYTES = 2
    AUDIO_BUFFER_SIZE = 2000
    
    # Transcription quality settings
    BEAM_SIZE = 5
    BEST_OF = 5
    TEMPERATURE = 0.0
    
    # VAD (Voice Activity Detection) parameters
    VAD_THRESHOLD = 0.5
    VAD_MIN_SPEECH_DURATION_MS = 250
    VAD_MAX_SPEECH_DURATION_S = float('inf')
    VAD_MIN_SILENCE_DURATION_MS = 2000
    VAD_SPEECH_PAD_MS = 400
    
    # Quality thresholds
    COMPRESSION_RATIO_THRESHOLD = 2.4
    LOG_PROB_THRESHOLD = -1.0
    NO_SPEECH_THRESHOLD = 0.6
    
    @staticmethod
    def setup_ffmpeg():
        """
        Configure FFmpeg environment variables.
        Must be called before importing moviepy or whisper.
        """
        ffmpeg_exe = get_ffmpeg_exe()
        ffmpeg_dir = os.path.dirname(ffmpeg_exe)
        
        os.environ["IMAGEIO_FFMPEG_EXE"] = ffmpeg_exe
        os.environ["FFMPEG_BINARY"] = ffmpeg_exe
        os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
    
    @staticmethod
    def get_compute_type(device):
        """Get appropriate compute type based on device."""
        return "float16" if device == "cuda" else "int8"
