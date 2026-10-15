"""
Subtitle formatting module.
Groups transcribed words into readable on-screen cues and writes SRT.
"""
from collections import namedtuple

from src.utils.config import Config


# One subtitle on screen. `text` may contain a "\n" between its two rows.
Cue = namedtuple("Cue", ["start", "end", "text"])

SENTENCE_END = (".", "?", "!", "…")
CLAUSE_END = (",", ";", ":")


class SubtitleFormatter:
    """Builds subtitle cues from transcription segments and formats them."""

    # ----- Cue building -------------------------------------------------
    @staticmethod
    def build_cues(segments):
        """
        Turn transcription segments into readable cues.

        Uses word timestamps when available: lines are at most
        Config.MAX_CHARS_PER_LINE characters, Config.MAX_LINES rows and
        Config.MAX_CUE_DURATION seconds, break at sentence ends and pauses,
        and end when the speech ends. Segments without word data become one
        cue each, using the segment's own text and times.

        Args:
            segments: Transcription segments (start, end, text, words)

        Returns:
            List of Cue(start, end, text)
        """
        cues = []
        words = []  # (start, end, text) of the cue being built

        def flush():
            if words:
                cues.extend(SubtitleFormatter._cues_from_words(words))
                words.clear()

        for segment in segments:
            seg_words = getattr(segment, "words", None)
            if not seg_words:
                # No word timing: keep the whole segment as one cue
                flush()
                text = segment.text.strip()
                if text:
                    cues.append(Cue(segment.start, segment.end, SubtitleFormatter._wrap(text)))
                continue
            for word in seg_words:
                if word.word.strip():
                    words.append((word.start, word.end, word.word.strip()))
        flush()

        return SubtitleFormatter._fix_timing(SubtitleFormatter._merge_short(cues))

    @staticmethod
    def _merge_short(cues):
        """Merge a too-short cue into the next one when it follows right after and still fits."""
        merged = []
        i = 0
        while i < len(cues):
            cue = cues[i]
            if i + 1 < len(cues) and cue.end - cue.start < Config.MIN_CUE_DURATION:
                nxt = cues[i + 1]
                text = f"{cue.text} {nxt.text}".replace("\n", " ")
                fits = (
                    nxt.start - cue.end <= Config.PAUSE_BREAK
                    and nxt.end - cue.start <= Config.MAX_CUE_DURATION
                    and len(SubtitleFormatter._wrap_lines(text)) <= Config.MAX_LINES
                )
                if fits:
                    merged.append(Cue(cue.start, nxt.end, SubtitleFormatter._wrap(text)))
                    i += 2
                    continue
            merged.append(cue)
            i += 1
        return merged

    @staticmethod
    def _cues_from_words(words):
        """Group a run of (start, end, text) words into cues."""
        cues = []
        current = []

        for word in words:
            if current and SubtitleFormatter._must_break(current, word):
                # Prefer to cut after punctuation in the second half of the cue
                cut = SubtitleFormatter._best_cut(current)
                cues.append(SubtitleFormatter._make_cue(current[:cut]))
                current = current[cut:]
            current.append(word)

            # A sentence end closes a cue once it holds a reasonable amount of text
            if word[2].endswith(SENTENCE_END) and len(SubtitleFormatter._join(current)) >= Config.MAX_CHARS_PER_LINE // 2:
                cues.append(SubtitleFormatter._make_cue(current))
                current = []

        if current:
            cues.append(SubtitleFormatter._make_cue(current))
        return cues

    @staticmethod
    def _must_break(current, word):
        """True if `word` cannot join the cue being built."""
        if word[0] - current[-1][1] > Config.PAUSE_BREAK:
            return True
        if word[1] - current[0][0] > Config.MAX_CUE_DURATION:
            return True
        candidate = SubtitleFormatter._join(current + [word])
        return len(SubtitleFormatter._wrap_lines(candidate)) > Config.MAX_LINES

    @staticmethod
    def _best_cut(current):
        """Index to split `current` at: after the last punctuation past the halfway point, else at the end."""
        total = len(SubtitleFormatter._join(current))
        for i in range(len(current) - 1, 0, -1):
            text = current[i - 1][2]
            if text.endswith(SENTENCE_END + CLAUSE_END) and len(SubtitleFormatter._join(current[:i])) >= total / 2:
                return i
        return len(current)

    @staticmethod
    def _make_cue(words):
        return Cue(words[0][0], words[-1][1], SubtitleFormatter._wrap(SubtitleFormatter._join(words)))

    @staticmethod
    def _join(words):
        return " ".join(w[2] for w in words)

    @staticmethod
    def _fix_timing(cues):
        """
        Decide how long each cue stays on screen.

        A cue stays long enough to be read (Config.READING_SPEED_CPS) and a
        little after the speech ends (Config.END_TAIL), but only using free
        time: it never runs into the next cue, so fast dialogue is unchanged.
        """
        fixed = []
        for i, cue in enumerate(cues):
            start = cue.start
            reading_time = len(cue.text.replace("\n", " ")) / Config.READING_SPEED_CPS
            end = max(cue.end + Config.END_TAIL,
                      start + reading_time,
                      start + Config.MIN_CUE_DURATION)

            if i + 1 < len(cues):
                next_start = cues[i + 1].start
                limit = next_start - Config.MIN_CUE_GAP
                if end > limit:
                    # Extend only up to the gap before the next cue, and cut
                    # any real overlap at the next cue's start
                    end = max(limit, min(cue.end, next_start))

            # Whisper sometimes stretches one word across a pause; never keep
            # a cue on screen longer than the maximum
            end = min(end, start + Config.MAX_CUE_DURATION)
            fixed.append(Cue(start, max(end, start), cue.text))
        return fixed

    # ----- Line wrapping ------------------------------------------------
    @staticmethod
    def _wrap_lines(text):
        """Greedy word wrap at Config.MAX_CHARS_PER_LINE."""
        lines = []
        for word in text.split():
            if lines and len(lines[-1]) + 1 + len(word) <= Config.MAX_CHARS_PER_LINE:
                lines[-1] += " " + word
            else:
                lines.append(word)
        return lines

    @staticmethod
    def _wrap(text):
        """Wrap text into rows; two rows are balanced so neither looks cramped."""
        lines = SubtitleFormatter._wrap_lines(text)
        if len(lines) != 2:
            return "\n".join(lines)

        words = text.split()
        best = None
        for i in range(1, len(words)):
            top, bottom = " ".join(words[:i]), " ".join(words[i:])
            if len(top) <= Config.MAX_CHARS_PER_LINE and len(bottom) <= Config.MAX_CHARS_PER_LINE:
                score = abs(len(top) - len(bottom))
                if best is None or score < best[0]:
                    best = (score, top, bottom)
        return f"{best[1]}\n{best[2]}" if best else "\n".join(lines)

    # ----- SRT output ---------------------------------------------------
    @staticmethod
    def to_srt(cues):
        """Format cues as SRT text."""
        blocks = []
        for index, cue in enumerate(cues, start=1):
            start = SubtitleFormatter._format_timestamp(cue.start)
            end = SubtitleFormatter._format_timestamp(cue.end)
            blocks.append(f"{index}\n{start} --> {end}\n{cue.text}\n")
        return "\n".join(blocks)

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
