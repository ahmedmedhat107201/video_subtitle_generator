"""
Subtitle generation engine using faster-whisper with VAD.
This is the core transcription logic.
"""
import os
import ctranslate2
from faster_whisper import WhisperModel, download_model
from huggingface_hub.utils import LocalEntryNotFoundError

from src.utils.config import Config
from src.core.audio_processor import AudioProcessor
from src.core.subtitle_formatter import SubtitleFormatter


class SubtitleEngine:
    """
    Main subtitle generation engine.
    Uses faster-whisper with Voice Activity Detection for accurate timestamps.
    Runs on the GPU when available and falls back to the CPU if it fails.
    """

    def __init__(self, model_size=None):
        """
        Initialize the subtitle engine.

        Args:
            model_size: Whisper model size. Defaults to Config.DEFAULT_MODEL_SIZE ("base")
        """
        Config.setup_cuda_libraries()
        self.model_size = model_size or Config.DEFAULT_MODEL_SIZE
        self._model_dir = self._model_path()
        self.device = self._detect_device()
        self.compute_type = Config.get_compute_type(self.device)
        self.model = self._load_model()

    @staticmethod
    def detect_device():
        """Return "cuda" if faster-whisper can see an NVIDIA GPU, else "cpu"."""
        try:
            return "cuda" if ctranslate2.get_cuda_device_count() > 0 else "cpu"
        except Exception:
            return "cpu"

    def _detect_device(self):
        """Detect and configure compute device (CUDA or CPU)."""
        device = self.detect_device()
        print(f"🖥️  Device: {device.upper()}")
        return device

    def _model_path(self):
        """Return the local model folder, downloading only if it isn't cached yet."""
        try:
            # Cached copy: no network request at all
            return download_model(self.model_size, local_files_only=True)
        except LocalEntryNotFoundError:
            print(f"📥 Downloading faster-whisper '{self.model_size}' model (first run only)...")
            return download_model(self.model_size)

    def _create_model(self):
        """Create the Whisper model on the current device."""
        print(f"📥 Loading faster-whisper '{self.model_size}' model ({self.device}, {self.compute_type})...")

        model = WhisperModel(
            self._model_dir,
            device=self.device,
            compute_type=self.compute_type
        )

        print(f"✅ Model loaded successfully")
        return model

    def _load_model(self):
        """Load the Whisper model, falling back to the CPU if the GPU fails."""
        try:
            return self._create_model()
        except Exception as exc:
            if self.device != "cuda":
                raise
            print(f"⚠️  GPU model load failed ({exc}); falling back to CPU")
            self._use_cpu()
            return self._create_model()

    def _use_cpu(self):
        """Switch the engine's settings to CPU mode."""
        self.device = "cpu"
        self.compute_type = Config.get_compute_type("cpu")
    
    def generate_subtitles(self, video_path, output_path=None, progress_callback=None):
        """
        Generate subtitle file from video.
        
        Args:
            video_path: Path to input video file
            output_path: Path for output SRT file (optional)
            progress_callback: Callback function for progress updates (optional)
            
        Returns:
            Path to generated subtitle file
        """
        # Determine output path
        if output_path is None:
            base_name = os.path.splitext(os.path.basename(video_path))[0]
            output_dir = os.path.dirname(video_path)
            output_path = os.path.join(output_dir, f"{base_name}_subtitles.srt")
        
        # Read audio straight from the video. This happens outside the GPU
        # fallback, so a broken video is reported as a normal error instead
        # of triggering a switch to the CPU.
        if progress_callback:
            progress_callback(0.1, "🎵 Reading audio...", "Decoding the audio track from the video")
        audio = AudioProcessor.load_audio(video_path)
        
        # Transcribe with VAD
        if progress_callback:
            progress_callback(0.3, "🎤 Transcribing speech...", "AI is analyzing audio and detecting speech segments")
        segments = self._transcribe_with_vad(audio, progress_callback)
        
        # Generate SRT
        if progress_callback:
            progress_callback(0.85, "📝 Formatting subtitles...", "Creating SRT file with timestamps")
        srt_content = SubtitleFormatter.generate_srt(segments)
        
        # Save file
        if progress_callback:
            progress_callback(0.95, "💾 Saving file...", "Writing subtitles to disk")
        self._save_subtitles(output_path, srt_content)
        
        if progress_callback:
            progress_callback(1.0, "✅ Complete!", f"Successfully generated {len(segments)} subtitle segments")
        
        print(f"✅ Subtitles saved: {os.path.basename(output_path)}")
        return output_path
    
    def _transcribe_with_vad(self, audio, progress_callback=None):
        """
        Transcribe audio using faster-whisper with VAD.
        
        Args:
            audio: Decoded 16 kHz mono audio (from AudioProcessor.load_audio)
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of transcription segments
        """
        print(f"🤖 Transcribing with VAD...")

        try:
            return self._run_transcription(audio, progress_callback)
        except Exception as exc:
            if self.device != "cuda":
                raise
            print(f"⚠️  GPU transcription failed ({exc}); switching to CPU")
            if progress_callback:
                progress_callback(0.35, "⚠️ GPU unavailable, switching to CPU...", str(exc))
            self._use_cpu()
            self.model = self._create_model()
            return self._run_transcription(audio, progress_callback)

    def _run_transcription(self, audio, progress_callback=None):
        """Run the Whisper model on decoded audio and return the segment list."""
        if progress_callback:
            progress_callback(0.35, "🤖 Running AI transcription...", "Processing audio with Whisper AI model")

        segments, info = self.model.transcribe(
            audio,
            language="en",
            task="transcribe",
            beam_size=Config.BEAM_SIZE,
            best_of=Config.BEST_OF,
            temperature=Config.TEMPERATURE,
            vad_filter=True,
            vad_parameters=dict(
                threshold=Config.VAD_THRESHOLD,
                min_speech_duration_ms=Config.VAD_MIN_SPEECH_DURATION_MS,
                max_speech_duration_s=Config.VAD_MAX_SPEECH_DURATION_S,
                min_silence_duration_ms=Config.VAD_MIN_SILENCE_DURATION_MS,
                speech_pad_ms=Config.VAD_SPEECH_PAD_MS
            ),
            condition_on_previous_text=False,
            compression_ratio_threshold=Config.COMPRESSION_RATIO_THRESHOLD,
            log_prob_threshold=Config.LOG_PROB_THRESHOLD,
            no_speech_threshold=Config.NO_SPEECH_THRESHOLD
        )
        
        if progress_callback:
            progress_callback(0.6, "📊 Processing results...", "Collecting and validating transcription segments")
        
        # Convert generator to list
        segment_list = list(segments)
        
        print(f"📊 Language: {info.language} ({info.language_probability:.2f})")
        print(f"⏱️  Duration: {info.duration:.1f}s")
        print(f"✅ Found {len(segment_list)} speech segments")
        
        if progress_callback:
            progress_callback(0.8, "✅ Transcription complete", f"Found {len(segment_list)} speech segments in {info.duration:.1f}s video")
        
        return segment_list
    
    @staticmethod
    def _save_subtitles(output_path, content):
        """Save SRT content to file."""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
