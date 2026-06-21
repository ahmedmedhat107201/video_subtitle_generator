"""
Subtitle generation engine using faster-whisper with VAD.
This is the core transcription logic.
"""
import os
import torch
from faster_whisper import WhisperModel

from src.utils.config import Config
from src.core.audio_processor import AudioProcessor
from src.core.subtitle_formatter import SubtitleFormatter


class SubtitleEngine:
    """
    Main subtitle generation engine.
    Uses faster-whisper with Voice Activity Detection for accurate timestamps.
    """
    
    def __init__(self, model_size=None):
        """
        Initialize the subtitle engine.
        
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large-v2, large-v3)
                       Defaults to Config.DEFAULT_MODEL_SIZE
        """
        self.model_size = model_size or Config.DEFAULT_MODEL_SIZE
        self.device = self._detect_device()
        self.compute_type = Config.get_compute_type(self.device)
        self.model = self._load_model()
    
    def _detect_device(self):
        """Detect and configure compute device (CUDA or CPU)."""
        if torch.cuda.is_available():
            device = "cuda"
            gpu_name = torch.cuda.get_device_name(0)
            print(f"🖥️  Device: CUDA")
            print(f"🚀 GPU: {gpu_name}")
        else:
            device = "cpu"
            print(f"🖥️  Device: CPU")
        
        return device
    
    def _load_model(self):
        """Load the Whisper model with VAD support."""
        print(f"📥 Loading faster-whisper '{self.model_size}' model...")
        
        model = WhisperModel(
            self.model_size,
            device=self.device,
            compute_type=self.compute_type
        )
        
        print(f"✅ Model loaded successfully")
        return model
    
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
        
        # Create temporary audio file path
        temp_audio_path = self._get_temp_audio_path(video_path)
        
        try:
            # Extract audio
            if progress_callback:
                progress_callback(0.1, "🎵 Extracting audio...", "Separating audio track from video file")
            AudioProcessor.extract_audio(video_path, temp_audio_path)
            
            # Transcribe with VAD
            if progress_callback:
                progress_callback(0.3, "🎤 Transcribing speech...", "AI is analyzing audio and detecting speech segments")
            segments = self._transcribe_with_vad(temp_audio_path, progress_callback)
            
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
            
        finally:
            # Always cleanup temp file
            AudioProcessor.cleanup_temp_audio(temp_audio_path)
    
    def _transcribe_with_vad(self, audio_path, progress_callback=None):
        """
        Transcribe audio using faster-whisper with VAD.
        
        Args:
            audio_path: Path to audio file
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of transcription segments
        """
        print(f"🤖 Transcribing with VAD...")
        
        if progress_callback:
            progress_callback(0.35, "🤖 Running AI transcription...", "Processing audio with Whisper AI model")
        
        segments, info = self.model.transcribe(
            audio_path,
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
    def _get_temp_audio_path(video_path):
        """Generate temporary audio file path."""
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        return f"{base_name}_temp.wav"
    
    @staticmethod
    def _save_subtitles(output_path, content):
        """Save SRT content to file."""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
