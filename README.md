# 🎬 Video Subtitle Generator

A professional desktop application for generating accurate English subtitles from video files using **faster-whisper** with **Voice Activity Detection (VAD)**.

## ✨ Features

- **🎯 100% Accurate Timestamps**: VAD ensures subtitles sync perfectly, even during music/action scenes
- **🚀 GPU Acceleration**: Automatic NVIDIA GPU detection, with automatic fallback to CPU if the GPU can't be used
- **🎨 Cinema-style GUI**: Graphite interface with a teal accent, built with CustomTkinter
- **⚡ Batched Transcription**: Transcribes several speech chunks at once (about 3.5x faster on GPU)
- **📖 Readable Subtitles**: Word-level timing; lines of at most 42 characters, 2 rows and 7 seconds, ending when the speech ends
- **📂 One Queue**: Click or drag & drop videos onto the drop zone; each video shows its progress and result (done / failed / cancelled) in the same list. Cancelled runs keep the remaining videos queued so you can continue later
- **🎧 Smart Audio Track**: Videos with several audio tracks use the English one
- **📹 Format Support**: MP4, AVI, MOV, MKV, WMV, FLV, WebM
- **💪 Production Ready**: Clean modular architecture with proper separation of concerns

## 🔧 How It Works

1. **Add Videos**: Click the drop zone or drag & drop videos onto the window (it lights up teal while you drag)
2. **Generate**: The app reads the audio straight from the video (no temporary files), detects speech with VAD, and transcribes each queued video in turn. Click **Cancel** at any time to stop
3. **Done**: Subtitles are saved as `<video name>_subtitles.srt` next to each video. The list shows where each file was saved (or why it failed), and the bottom bar shows a summary

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
│   │   ├── audio_processor.py      # Audio loading
│   │   ├── subtitle_controller.py  # Runs jobs in a background thread
│   │   ├── subtitle_engine.py      # Whisper + VAD transcription
│   │   └── subtitle_formatter.py   # Readable cues + SRT output
│   ├── gui/               # User interface
│   │   ├── app_window.py           # Main window layout and queue processing
│   │   ├── header.py               # Top bar: app name + GPU/CPU pill
│   │   ├── drop_zone.py            # Dashed drop / click-to-browse area
│   │   ├── queue_list.py           # The queue: one row per video with progress + result
│   │   ├── queue_model.py          # Queue state (no widgets, unit-tested)
│   │   ├── action_bar.py           # Summary, result line and Generate / Cancel
│   │   ├── components.py           # Scroll area, mouse wheel, round remove button
│   │   └── theme.py                # Design system: colours, fonts, icons, spacing
│   └── utils/             # Configuration
│       └── config.py               # Centralized settings
├── tests/                 # Unit tests (python -m unittest discover tests)
├── main.py                # Entry point
├── requirements.txt       # Dependencies
└── README.md              # This file
```

## 🎨 Design

The interface uses a "Cinema" design system defined in `src/gui/theme.py`:

| Role | Value |
|------|-------|
| Background / surfaces | `#0E0F11` / `#17181B` (neutral graphite) |
| Accent | `#2DD4BF` teal (progress, primary button, drag-over) |
| Text | `#ECEDEF`, muted `#8E9199` |
| Success / warning / danger | `#6EDC8C` / `#F2B84B` / `#FF6B6B` |
| Fonts | Bahnschrift (titles, labels, buttons), Segoe UI Variable (text), Cascadia Mono (numbers) |
| Icons | Segoe Fluent Icons, with plain-text fallbacks |

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
- **GPU**: A 22-minute episode takes about 8 seconds on an RTX 3050 Laptop GPU
- **CPU**: Slower, but works everywhere
- **Long videos**: Automatically handled, no chunking needed

### Subtitle Layout
Line length, rows, on-screen time and pause handling are set in `src/utils/config.py`
(`MAX_CHARS_PER_LINE`, `MAX_LINES`, `MAX_CUE_DURATION`, `MIN_CUE_DURATION`, `PAUSE_BREAK`).

## 🛠️ Technologies

| Component | Technology | Purpose |
|-----------|-----------|---------|
| AI Model | faster-whisper | Speech-to-text transcription |
| VAD | Silero VAD | Voice activity detection |
| GUI | CustomTkinter + tkinterdnd2 | Modern dark-themed interface, drag & drop |
| Media | PyAV (FFmpeg, via faster-whisper) | Reading audio from video files |
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

## 🧪 Tests

```bash
python -m unittest discover tests
```

The tests cover subtitle layout, SRT output, audio track selection, cancelling and the GPU→CPU fallback. They don't load the real model, so they run in under a second.

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
