# 🎬 Video Subtitle Generator

A professional desktop application for generating accurate English subtitles from video files using **faster-whisper** with **Voice Activity Detection (VAD)**.

## ✨ Features

- **🎯 100% Accurate Timestamps**: VAD ensures subtitles sync perfectly, even during music/action scenes
- **🚀 GPU Acceleration**: Automatic CUDA detection for faster processing
- **🎨 Modern GUI**: Beautiful dark-themed interface using CustomTkinter
- **🤖 Multiple Models**: Choose from tiny, base, small, medium, or large models
- **📹 Format Support**: MP4, AVI, MOV, MKV, WMV, FLV, WebM
- **💪 Production Ready**: Clean modular architecture with proper separation of concerns

## 🔧 How It Works

1. **Select Video**: Choose any video file through the GUI
2. **Pick Model**: Select Whisper model size (base recommended)
3. **Generate**: App extracts audio, detects speech with VAD, and transcribes
4. **Done**: Subtitles saved as SRT file next to your video

### Why VAD Matters

Traditional Whisper can generate "phantom" subtitles during music, sound effects, or silence. **VAD (Voice Activity Detection)** solves this by:
- Pre-filtering audio to detect actual speech regions
- Skipping non-speech audio (music, explosions, silence)
- Ensuring timestamps match real dialogue perfectly

## 🏗️ Project Structure

```
video_subtitle_generator/
├── src/
│   ├── core/              # Business logic
│   │   ├── audio_processor.py      # Audio extraction
│   │   ├── subtitle_engine.py      # Whisper + VAD transcription
│   │   └── subtitle_formatter.py   # SRT generation
│   ├── gui/               # User interface
│   │   └── app_window.py           # CustomTkinter GUI
│   └── utils/             # Configuration
│       └── config.py               # Centralized settings
├── main.py                # Entry point
├── requirements.txt       # Dependencies
└── README.md              # This file
```

## 🚀 Installation

### Prerequisites
- Python 3.10 or 3.11
- (Optional) CUDA-compatible GPU for acceleration

### Setup

1. **Clone/Download** this repository

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **(Optional) GPU Support**:
   ```bash
   pip install torch --index-url https://download.pytorch.org/whl/cu121
   ```

4. **Run the app**:
   ```bash
   python main.py
   ```

## 💡 Usage Tips

### Model Selection
- **tiny**: Fastest, least accurate (~1GB RAM, 32MB download)
- **base**: ⭐ Recommended - Good balance (1GB RAM, 145MB download)
- **small**: Better accuracy, slower (2GB RAM, 466MB download)
- **medium/large**: Best quality, requires powerful GPU (5GB+ RAM, 1-3GB download)

### First Run
- First time using a model will download it (~140MB for base)
- Subsequent runs use cached model (instant startup)

### Performance
- **CPU**: Works fine, takes 2-3x video duration
- **GPU**: Much faster, ~0.5-1x video duration
- **Long videos**: Automatically handled, no chunking needed

## 🛠️ Technologies

| Component | Technology | Purpose |
|-----------|-----------|---------|
| AI Model | faster-whisper | Speech-to-text transcription |
| VAD | Silero VAD | Voice activity detection |
| GUI | CustomTkinter | Modern dark-themed interface |
| Media | moviepy | Video/audio processing |
| Acceleration | PyTorch + CUDA | GPU computing |

## 🎯 Technical Details

### Architecture Highlights
- **Separation of Concerns**: Core logic separated from GUI
- **Modular Design**: Each component has single responsibility
- **Centralized Config**: All settings in one place
- **Clean Imports**: Proper Python package structure

### VAD Parameters
```python
threshold=0.5                    # Speech detection sensitivity
min_speech_duration_ms=250      # Minimum speech segment
min_silence_duration_ms=2000    # Silence between segments
speech_pad_ms=400               # Padding around speech
```

## 🤝 Contributing

This is a production-ready codebase. Contributions are welcome:
1. Follow the existing architecture pattern
2. Add docstrings to new functions
3. Test with various video types

## 📄 License

MIT License - Feel free to use and modify!

## 🙏 Acknowledgments

- **OpenAI Whisper** - Amazing speech recognition model
- **faster-whisper** - Optimized implementation
- **Silero Team** - VAD model

---

**Made with ❤️ for accurate subtitle generation**
