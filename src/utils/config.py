"""
Configuration module for the subtitle generator.
Holds transcription settings and GPU library setup.
"""
import glob
import importlib.util
import os


class Config:
    """Central configuration for the application."""
    
    # Whisper model configuration
    DEFAULT_MODEL_SIZE = "base"
    
    # Audio processing settings
    AUDIO_SAMPLE_RATE = 16000  # Whisper requires 16kHz
    
    # Batched inference: transcribes several speech chunks at once.
    # Measured on a 22-min episode (GPU): 3.5x faster and slightly more
    # accurate than sequential. Set USE_BATCHED = False to go back.
    USE_BATCHED = True
    BATCH_SIZE = 8

    # GPU precision. "int8_float16" was measured too: only ~64 MB less GPU
    # memory and slightly less accurate, so float16 is kept.
    GPU_COMPUTE_TYPE = "float16"

    # Subtitle layout (how words are grouped into on-screen lines)
    MAX_CHARS_PER_LINE = 42
    MAX_LINES = 2
    MAX_CUE_DURATION = 7.0      # seconds a cue may stay on screen
    MIN_CUE_DURATION = 1.0      # short cues are extended into the following gap
    READING_SPEED_CPS = 15      # a cue stays long enough to read at this many characters/second
    END_TAIL = 0.6              # and at least this long (s) after the speech ends
    # (both only use free time: a cue never runs into the next one)
    PAUSE_BREAK = 0.8           # a pause this long (s) between words starts a new cue
    MIN_CUE_GAP = 0.05          # keep cues from touching when extended

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

    # Handles returned by os.add_dll_directory must stay alive
    _cuda_dll_handles = []
    _cuda_libraries_ready = False

    @staticmethod
    def setup_cuda_libraries():
        """
        Make the pip-installed NVIDIA libraries (cuBLAS, cuDNN) findable.
        On Windows, faster-whisper cannot locate them in site-packages on its
        own, so their bin folders are added to the DLL search path. Safe to
        call repeatedly; does nothing on other platforms or if not installed.
        """
        if Config._cuda_libraries_ready:
            return
        Config._cuda_libraries_ready = True

        if not hasattr(os, "add_dll_directory"):
            return
        spec = importlib.util.find_spec("nvidia")
        if spec is None or not spec.submodule_search_locations:
            return

        for base in spec.submodule_search_locations:
            for bin_dir in glob.glob(os.path.join(base, "*", "bin")):
                Config._cuda_dll_handles.append(os.add_dll_directory(bin_dir))
                os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")

    @staticmethod
    def get_compute_type(device):
        """Get appropriate compute type based on device."""
        return Config.GPU_COMPUTE_TYPE if device == "cuda" else "int8"
