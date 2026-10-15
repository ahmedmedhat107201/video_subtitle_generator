# 🎬 Video Subtitle Generator

A professional desktop application for generating accurate English subtitles from video files using **faster-whisper** with **Voice Activity Detection (VAD)**.

## ✨ Features

- **🎯 100% Accurate Timestamps**: VAD ensures subtitles sync perfectly, even during music/action scenes
- **🚀 GPU Acceleration**: Automatic NVIDIA GPU detection, with automatic fallback to CPU if the GPU can't be used
- **🎨 Modern GUI**: Beautiful dark-themed interface using CustomTkinter
- **📂 Batch Queue**: Add several videos and process them one after another, each with its own progress bar
- **📹 Format Support**: MP4, AVI, MOV, MKV, WMV, FLV, WebM
- **💪 Production Ready**: Clean modular architecture with proper separation of concerns

## 🔧 How It Works

1. **Add Videos**: Add one or more video files to the queue
2. **Generate**: App extracts audio, detects speech with VAD, and transcribes each file in turn
3. **Done**: Subtitles saved as `<video name>_subtitles.srt` next to each video, with a summary of how many succeeded or failed

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
│   │   ├── subtitle_controller.py  # Runs jobs in a background thread
│   │   ├── subtitle_engine.py      # Whisper + VAD transcription
│   │   └── subtitle_formatter.py   # SRT generation
│   ├── gui/               # User interface
│   │   ├── app_window.py           # Main window and queue processing
│   │   ├── header.py               # Title and badges
│   │   ├── video_card.py           # File queue (add / remove / clear)
│   │   ├── action_panel.py         # Generate button and per-file progress
│   │   ├── video_tile.py           # Progress tile widgets
│   │   ├── components.py           # Scrollable container + mouse wheel
│   │   └── theme.py                # Color palette
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
   This includes NVIDIA's cuBLAS and cuDNN libraries for GPU support. An NVIDIA
   driver is all you need on top (no CUDA Toolkit, no PyTorch). The header shows
   whether the app is running in GPU or CPU mode.

3. **Run the app**:
   ```bash
   python main.py
   ```

## 💡 Usage Tips

### Model
- The app uses the Whisper **base** model (~1GB RAM), a good balance of speed and accuracy
- It is fixed on purpose, so no other models are ever downloaded

### First Run
- The first run downloads the base model once (~145MB)
- Later runs use the cached model. It is loaded into memory once per app session and reused for every file

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
| Acceleration | CTranslate2 + CUDA (cuBLAS/cuDNN) | GPU computing, CPU fallback |

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
