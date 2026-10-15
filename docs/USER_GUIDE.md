# Subtitle Generator: User Guide

Subtitle Generator creates English subtitles (`.srt` files) for your videos automatically.
You add videos and press **Generate**, and a subtitle file appears next to each video.

Everything runs **on your own computer**. Your videos are never uploaded anywhere.

---

## Contents

1. [What the app does](#what-the-app-does)
2. [How it works (in plain words)](#how-it-works-in-plain-words)
3. [A quick tour of the window](#a-quick-tour-of-the-window)
4. [Making subtitles, step by step](#making-subtitles-step-by-step)
5. [Understanding the queue](#understanding-the-queue)
6. [Using your subtitles](#using-your-subtitles)
7. [Tips for the best results](#tips-for-the-best-results)
8. [Troubleshooting](#troubleshooting)
9. [Frequently asked questions](#frequently-asked-questions)

---

## What the app does

- Listens to the speech in a video and writes it down as **English subtitles**.
- Saves them as an **SRT file**, the subtitle format almost every video player understands (VLC, MPC-HC, PotPlayer, Windows Media Player, YouTube uploads and more).
- Handles **many videos in one go**: add a whole season or a whole course and let it run.
- Works with **MP4, MKV, AVI, MOV, WMV, FLV and WEBM** videos.

It's useful for:
- Watching shows or lectures with subtitles when none came with the video
- Following fast or unclear speech
- Creating subtitles to edit or translate later

---

## How it works (in plain words)

For each video, the app goes through four steps:

1. **Reads the sound.** It takes the audio track out of the video. If a video has several audio tracks (for example English and French), it picks the **English** one.
2. **Finds the speech.** A voice detector skips music, sound effects, laughter and silence, so you don't get "ghost" subtitles during the opening theme or action scenes.
3. **Writes down what is said.** A speech-recognition AI (OpenAI's Whisper, "base" size) turns the speech into text, with the exact time of every word.
4. **Builds readable subtitles.** The words are grouped into short, easy-to-read lines:
   - at most **2 lines** on screen, each at most **42 characters**
   - a subtitle stays on screen at most **7 seconds**
   - lines break at the end of sentences and at pauses
   - when people talk fast, each line is replaced as soon as the next one starts
   - when someone stops talking, the line stays a moment longer, long enough to finish reading it, and then disappears instead of hanging over silence

If your computer has an **NVIDIA graphics card**, the app uses it automatically, which is much faster. If not, or if something goes wrong with it, the app switches to the processor (CPU) on its own. It's slower, but it works the same.

---

## A quick tour of the window

```
┌────────────────────────────────────────────────────────┐
│ ▌ SUBTITLE GENERATOR                          ● GPU    │  ← top bar
├────────────────────────────────────────────────────────┤
│  ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐  │
│                ⤒  Drop videos here                     │  ← drop zone
│                   or click to browse                   │
│  └ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘  │
│  QUEUE 3                                       CLEAR   │
│  01  episode01.mkv                      ✓ DONE    ✕    │  ← queue
│  02  lecture.mp4                           64%         │
│      Transcribing · 12:30 / 22:46                      │
│      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━──────────────   │
│  03  intro.mp4                          QUEUED    ✕    │
├────────────────────────────────────────────────────────┤
│  3 videos · 1 processing · 1 queued · 1 done [CANCEL]  │  ← action bar
└────────────────────────────────────────────────────────┘
```

| Part | What it's for |
|------|---------------|
| **Top bar** | The pill on the right shows whether the app is using your graphics card (**GPU**) or your processor (**CPU**). |
| **Drop zone** | Click it to choose videos, or drag videos from File Explorer onto the window. It lights up teal while you drag. |
| **Queue** | One row per video, showing what's happening to it: waiting, working (with a progress bar), done, failed or cancelled. |
| **Action bar** | A summary of the queue, the result of the last run, and the main button (**GENERATE** or **CANCEL**). |

---

## Making subtitles, step by step

### 1. Add your videos
Do either of these:
- **Click the drop zone** and pick one or more videos (hold **Ctrl** or **Shift** to select several).
- **Drag & drop** videos from File Explorer onto the window. You can drop many at once. Files that aren't videos are ignored.

Each video appears in the queue as **QUEUED**. Adding the same video twice has no effect.

### 2. Press GENERATE
The teal **GENERATE** button starts working through every **QUEUED** video, one after another.

The first time you use the app, it downloads the speech model (about **145 MB**) before starting. After that it works offline.

### 3. Watch the progress
The video being worked on is highlighted, and shows:
- what it's doing ("Reading audio", "Transcribing", "Saving file"…)
- how far it got in the video, e.g. **12:30 / 22:46**
- a percentage and a progress line

While the app is working you can't add or remove videos; the drop zone says **Processing…**.

### 4. Get your subtitles
When a video is finished its row shows **✓ DONE** and the name of the file it saved, for example:

> Saved as `episode01_subtitles.srt`

The file is saved **in the same folder as the video**, named `<video name>_subtitles.srt`.

When the whole queue is finished, the action bar shows the result, for example
**"All done · 3 subtitle files saved next to the videos"**.

### Stopping early
Press **CANCEL** at any time:
- The video being worked on stops and is marked **CANCELLED**. No half-finished subtitle file is written.
- Videos that hadn't started yet **stay QUEUED**.
- Press **GENERATE** again later to continue with them.

---

## Understanding the queue

| Row shows | Meaning | What you can do |
|-----------|---------|-----------------|
| **QUEUED** | Waiting its turn | Remove it with **✕** |
| *percentage + progress line* | Being worked on right now | Wait, or press **CANCEL** |
| **✓ DONE** | Subtitles saved; the row says where | Remove it from the list with **✕** (the file stays on disk) |
| **! FAILED** | Something went wrong; the reason is shown in red | See [Troubleshooting](#troubleshooting) |
| **CANCELLED** | You stopped it before it finished | Remove and re-add the video to try again |

- **✕** removes a single row from the list. It **never deletes** your video or subtitle files.
- **CLEAR** empties the whole list, again without deleting any files.
- Finished rows stay in the list so you can see the results. Clear them whenever you like.

---

## Using your subtitles

**In VLC:** open the video, then **Subtitle → Add Subtitle File…** and pick the `.srt`. You can also drag the `.srt` onto the playing video.

**Automatic loading:** many players load subtitles automatically only when the subtitle file has *exactly* the same name as the video. To get that, rename
`episode01_subtitles.srt` → `episode01.srt`.

**Editing:** an SRT file is plain text. You can open it in Notepad to fix a word, or in a subtitle editor such as Subtitle Edit or Aegisub.

---

## Tips for the best results

- **Clear speech works best.** Lectures, tutorials, interviews and TV dialogue come out very well. Heavy background music, people talking over each other, or strong accents produce more mistakes.
- **English only.** The app always transcribes in English. Videos in other languages will give poor results.
- **Expect a few mistakes.** The app uses Whisper's "base" model, chosen for a good balance of speed and accuracy. Names and rare technical words are the most common errors. Skim the subtitles if they need to be perfect.
- **Use a graphics card if you can.** With an NVIDIA GPU, a 22-minute episode takes about **8 seconds**; on the CPU, about **45 seconds**.
- **Existing subtitles are replaced.** If `<video name>_subtitles.srt` already exists, generating again overwrites it. Rename the old file first if you want to keep it.

---

## Troubleshooting

| Problem | What to do |
|---------|------------|
| A video shows **FAILED** with "Invalid data found…" | The video file is damaged or isn't really a video. Check that it plays in a video player. |
| A video shows **FAILED** with a "Permission denied" message | The app couldn't write in the video's folder (for example a read-only drive). Copy the video to a normal folder such as Documents and try again. |
| The top bar says **CPU** although you have an NVIDIA card | Update your NVIDIA driver and restart the app. See also the [Installation Guide](INSTALLATION.md#the-app-says-cpu-but-i-have-an-nvidia-gpu). The app still works on CPU, just slower. |
| The first run fails before anything happens | The first run needs internet once, to download the speech model (about 145 MB). Connect and try again. |
| The drop zone says **"Click to add videos"** and dragging doesn't work | The drag & drop add-on isn't installed. Clicking still works; to enable dragging, see the [Installation Guide](INSTALLATION.md). |
| Subtitles don't show in the player | Load the `.srt` manually (see [Using your subtitles](#using-your-subtitles)), or rename it to match the video name exactly. |
| Subtitles look slightly early or late | Most players can shift subtitles (in VLC: **G** / **H** keys). Report it with the video type if it happens often. |

---

## Frequently asked questions

**Does it upload my videos or use the internet?**
No. Everything happens on your computer. The internet is only used once, to download the speech model the first time.

**Does it change or delete my videos?**
No. It only reads them, and creates a new `.srt` file next to each one.

**Which languages are supported?**
English only.

**Can I keep using my computer while it works?**
Yes. The app works in the background and the window stays responsive.

**Can I close the app while it's working?**
Yes, but the video being worked on won't get subtitles. Videos that were already **DONE** keep their subtitle files.

**Why "base" and not a bigger, more accurate model?**
It keeps the download small (about 145 MB instead of up to 3 GB) and the app fast. It's a deliberate choice.

**Where is the speech model stored?**
In `C:\Users\<you>\.cache\huggingface\hub\models--Systran--faster-whisper-base` (about 145 MB).

---

Need to install the app on another computer? See the **[Installation Guide](INSTALLATION.md)**.
