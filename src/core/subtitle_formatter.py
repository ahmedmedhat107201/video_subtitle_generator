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
        index = 0

        for segment in segments:
            text = segment.text.strip()

            # Skip empty segments without consuming a number
            if not text:
                continue

            index += 1
            start_time = SubtitleFormatter._format_timestamp(segment.start)
            end_time = SubtitleFormatter._format_timestamp(segment.end)

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
        # Round to the nearest millisecond, then split with integer math so
        # values like 59.9996 become 00:01:00,000 instead of 00:00:59,999
        total_ms = int(round(seconds * 1000))
        hours, total_ms = divmod(total_ms, 3_600_000)
        minutes, total_ms = divmod(total_ms, 60_000)
        secs, millis = divmod(total_ms, 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
