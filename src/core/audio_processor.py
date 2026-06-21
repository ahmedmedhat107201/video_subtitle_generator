"""
Audio processing module.
Handles video-to-audio extraction.
"""
import os
import warnings
from moviepy.video.io.VideoFileClip import VideoFileClip
from src.utils.config import Config


class AudioProcessor:
    """Handles audio extraction from video files."""
    
    @staticmethod
    def extract_audio(video_path, audio_path):
        """
        Extract audio from video file and save as WAV.
        
        Args:
            video_path: Path to input video file
            audio_path: Path where audio WAV file will be saved
        """
        print(f"📹 Loading video: {os.path.basename(video_path)}")
        
        # Suppress moviepy subtitle stream warning
        warnings.filterwarnings('ignore', message='.*Subtitle stream.*')
        
        video = VideoFileClip(video_path)
        
        print(f"🎵 Extracting audio...")
        video.audio.write_audiofile(
            audio_path,
            codec=Config.AUDIO_CODEC,
            fps=Config.AUDIO_SAMPLE_RATE,
            nbytes=Config.AUDIO_BYTES,
            buffersize=Config.AUDIO_BUFFER_SIZE,
            logger=None
        )
        
        video.close()
        print(f"✅ Audio extraction complete")
    
    @staticmethod
    def cleanup_temp_audio(audio_path):
        """Remove temporary audio file."""
        if os.path.exists(audio_path):
            os.remove(audio_path)
            print(f"🗑️ Cleaned up temporary audio file")
