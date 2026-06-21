"""
Subtitle formatting module.
Handles SRT file generation from transcription segments.
"""


class SubtitleFormatter:
    """Formats transcription segments into SRT subtitle format."""
    
    @staticmethod
    def generate_srt(segments):
        """
        Convert transcription segments to SRT format.
        
        Args:
            segments: List of transcription segments with start, end, and text
            
        Returns:
            String containing formatted SRT content
        """
        srt_lines = []
        
        for index, segment in enumerate(segments, start=1):
            start_time = SubtitleFormatter._format_timestamp(segment.start)
            end_time = SubtitleFormatter._format_timestamp(segment.end)
            text = segment.text.strip()
            
            if not text:
                continue
            
            srt_lines.append(f"{index}")
            srt_lines.append(f"{start_time} --> {end_time}")
            srt_lines.append(text)
            srt_lines.append("")  # Blank line between entries
        
        return "\n".join(srt_lines)
    
    @staticmethod
    def _format_timestamp(seconds):
        """
        Convert seconds to SRT timestamp format (HH:MM:SS,mmm).
        
        Args:
            seconds: Time in seconds (float)
            
        Returns:
            Formatted timestamp string
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
