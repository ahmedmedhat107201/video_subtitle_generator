"""
Video Subtitle Generator - Main Entry Point

A professional desktop application for generating accurate English subtitles
from video files using faster-whisper with Voice Activity Detection (VAD).

Features:
- Modern, professional UI with enhanced UX
- Faster-whisper with VAD for 100% accurate timestamps
- GPU acceleration with automatic CPU fallback
- Batch queue with per-file progress
- No phantom subtitles during music/action scenes

Usage:
    python main.py
"""
import logging

logging.basicConfig(level=logging.INFO, format="%(message)s")

from src.gui.app_window import SubtitleAppWindow

if __name__ == "__main__":
    app = SubtitleAppWindow()
    app.run()
