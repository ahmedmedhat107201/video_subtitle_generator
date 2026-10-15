"""
Video Subtitle Generator - Main Entry Point

A professional desktop application for generating accurate English subtitles
from video files using faster-whisper with Voice Activity Detection (VAD).

Features:
- faster-whisper ("base" model) with VAD, batched for speed
- GPU acceleration with automatic CPU fallback
- Readable SRT subtitles built from word-level timing
- One queue with live per-video progress, cancel and drag & drop
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
