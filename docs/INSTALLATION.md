# Subtitle Generator: Installation Guide

This guide sets up Subtitle Generator on a new computer, step by step.
No programming knowledge is needed. You'll copy a few commands into a terminal.

**Time needed:** about 10–20 minutes, mostly waiting for downloads.

---

## Contents

1. [What you need](#1-what-you-need)
2. [Install Python](#2-install-python)
3. [Get the app](#3-get-the-app)
4. [Install the app's libraries](#4-install-the-apps-libraries)
5. [Start the app](#5-start-the-app)
6. [Check that the graphics card is used](#6-check-that-the-graphics-card-is-used)
7. [Updating](#7-updating)
8. [Uninstalling](#8-uninstalling)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. What you need

| | Requirement |
|---|---|
| **System** | Windows 10 or 11 (tested on Windows 11). Linux and macOS are not tested; see the notes below. |
| **Python** | Version 3.10 or newer (developed on 3.14) |
| **Disk space** | About **2.5 GB** with GPU support, or about **400 MB** for a CPU-only setup (details below) |
| **Internet** | Only during installation and the first run |
| **Graphics card** *(optional)* | An NVIDIA GPU with an up-to-date driver makes the app several times faster. Without one, the app runs on the processor. |

**Where the disk space goes**

| Part | Size |
|------|------|
| NVIDIA GPU libraries (cuBLAS, cuDNN, NVRTC) | ~2.1 GB, only needed for GPU support |
| Speech engine, audio decoder, interface (faster-whisper, CTranslate2, PyAV, ONNX Runtime, CustomTkinter…) | ~250 MB |
| Speech model ("base"), downloaded on first run | ~145 MB |

---

## 2. Install Python

Skip this step if Python 3.10+ is already installed. To check, open **Command Prompt** or **PowerShell** and run:

```bash
python --version
```

If it prints `Python 3.10` or higher, you're fine.

Otherwise:
1. Go to **https://www.python.org/downloads/** and download the latest Python for Windows.
2. Run the installer and, on the first screen, **tick "Add python.exe to PATH"**. This is important.
3. Keep the default options; they include **tcl/tk**, which the app's window needs. Click **Install Now**.
4. Close and reopen your terminal, then run `python --version` again to confirm.

> Python from the Microsoft Store also works, but the python.org installer is recommended.

---

## 3. Get the app

**Option A: download a ZIP (easiest)**
1. On the project's GitHub page, click **Code → Download ZIP**.
2. Extract it to a folder you'll keep, e.g. `C:\Apps\video_subtitle_generator`.

**Option B: with Git**
```bash
git clone <repository-url>
```

Then open a terminal **inside the app folder**, the one that contains `main.py`. In File Explorer you can open the folder, click the address bar, type `cmd` and press **Enter**.

---

## 4. Install the app's libraries

### 4.1 Create a virtual environment (recommended)
A virtual environment keeps the app's libraries in their own folder, separate from the rest of your system:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Your prompt now starts with `(.venv)`. Repeat the `activate` line every time you open a new terminal for the app.

> Prefer not to use one? Skip this step. The libraries are then installed for your whole Python installation.

### 4.2 Install

**With an NVIDIA graphics card (recommended):**
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```
This downloads about 2.3 GB, mostly NVIDIA's GPU libraries.

**Without an NVIDIA graphics card (CPU only, much smaller):**
```bash
python -m pip install --upgrade pip
pip install "faster-whisper>=1.2.1" "customtkinter>=5.2.2" "tkinterdnd2>=0.4.2"
```

> `tkinterdnd2` adds drag & drop. If it fails to install, the app still works; you can add videos by clicking.

> You do **not** need PyTorch, the CUDA Toolkit, FFmpeg or moviepy. Everything the app needs comes from the commands above.

---

## 5. Start the app

From the app folder (with `(.venv)` active if you created one):

```bash
python main.py
```

The window opens. On the **first run**, the speech model (about 145 MB) is downloaded the first time you press **GENERATE**. You need internet for that once; after that the app works offline.

Now read the **[User Guide](USER_GUIDE.md)** to learn how to use it.

### Optional: a desktop shortcut
Create a file called `Subtitle Generator.bat` in the app folder with this content:
```bat
@echo off
cd /d "%~dp0"
if exist .venv\Scripts\pythonw.exe (start "" .venv\Scripts\pythonw.exe main.py) else (start "" pythonw main.py)
```
Double-click it to start the app without a terminal window. Right-click → **Send to → Desktop (create shortcut)** to put it on your desktop.

---

## 6. Check that the graphics card is used

Look at the pill in the **top-right corner** of the window:
- **● GPU** (teal dot): the graphics card is used.
- **● CPU**: the processor is used.

The terminal also prints `Device: CUDA` (GPU) or `Device: CPU` when the first video starts.

If you have an NVIDIA card but see **CPU**, see [Troubleshooting](#the-app-says-cpu-but-i-have-an-nvidia-gpu).

---

## 7. Updating

1. Replace the app files with the new version (download the new ZIP, or run `git pull`).
2. With `(.venv)` active, run:
   ```bash
   pip install -r requirements.txt --upgrade
   ```

**Coming from an older version?** Older versions used PyTorch, moviepy and imageio-ffmpeg. They're no longer needed and can be removed to free space:
```bash
pip uninstall torch moviepy imageio-ffmpeg imageio proglog decorator python-dotenv pillow
```

---

## 8. Uninstalling

1. Delete the app folder. If you used a virtual environment, that removes all the app's libraries too.
2. Delete the downloaded speech model folder:
   `C:\Users\<you>\.cache\huggingface\hub\models--Systran--faster-whisper-base`
3. *(Optional)* Free pip's download cache: `python -m pip cache purge`

Subtitle files you created stay next to your videos until you delete them.

---

## 9. Troubleshooting

### `'python' is not recognized…`
Python isn't on your PATH. Reinstall Python and tick **"Add python.exe to PATH"**, or use `py` instead of `python` (e.g. `py main.py`).

### `ModuleNotFoundError: No module named 'src'`
The app was started from the wrong folder. Open the terminal in the folder that contains `main.py` and run `python main.py` there.

### `ModuleNotFoundError: No module named 'faster_whisper'` (or `customtkinter`)
The libraries aren't installed in the Python you're using. If you created a virtual environment, activate it (`.venv\Scripts\activate`) and run the install command from step 4 again.

### `No module named 'tkinter'` / `_tkinter`
Your Python was installed without Tcl/Tk. Run the python.org installer again, choose **Modify**, and make sure **tcl/tk and IDLE** is ticked.

### The app says CPU, but I have an NVIDIA GPU
1. Update the NVIDIA driver (GeForce Experience / NVIDIA App, or nvidia.com/drivers). The driver must support **CUDA 12**.
2. Make sure you used `pip install -r requirements.txt`, not the CPU-only command, so the NVIDIA libraries are installed.
3. Restart the app.

If the GPU fails while working, the app switches to the CPU automatically and shows **CPU** in the top bar. Your subtitles are still created.

### The first run fails while downloading the model
Check your internet connection, firewall or proxy, then try again. The model comes from Hugging Face (`huggingface.co`).

### Drag & drop doesn't work
The drop zone says **"Click to add videos"** when the drag & drop library isn't available. Install it with `pip install tkinterdnd2`, then restart the app. Clicking the drop zone always works.

### Fonts or icons look different
The design uses Windows fonts (Bahnschrift, Segoe UI Variable, Cascadia Mono, Segoe Fluent Icons). On older Windows versions or other systems, similar fonts and plain-text icons are used automatically.

---

## Notes for Linux and macOS (untested)

- Install Python 3.10+ with Tk support (e.g. `sudo apt install python3-tk` on Ubuntu).
- **macOS:** the NVIDIA libraries are skipped automatically and the app runs on the CPU.
- **Linux with an NVIDIA GPU:** the NVIDIA libraries install, but you may need to add their `lib` folders to `LD_LIBRARY_PATH` for the GPU to be used. Otherwise the app falls back to the CPU.

---

## For developers

Run the tests from the app folder:
```bash
python -m unittest discover tests
```
They run in about a second and don't need the speech model or a GPU.
