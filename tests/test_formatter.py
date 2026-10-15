"""Tests for subtitle cue building and SRT output."""
import unittest
from types import SimpleNamespace

from src.core.subtitle_formatter import Cue, SubtitleFormatter
from src.utils.config import Config


def word(start, end, text):
    return SimpleNamespace(start=start, end=end, word=f" {text}")


def segment(words, text=None):
    return SimpleNamespace(
        start=words[0].start if words else 0.0,
        end=words[-1].end if words else 0.0,
        text=text if text is not None else "".join(w.word for w in words),
        words=words,
    )


def steady_words(texts, start=0.0, step=0.3):
    """Words spoken back to back, each `step` seconds long."""
    return [word(start + i * step, start + (i + 1) * step, t) for i, t in enumerate(texts)]


class TimestampTests(unittest.TestCase):
    def test_rounds_to_nearest_millisecond(self):
        self.assertEqual(SubtitleFormatter._format_timestamp(2.3195), "00:00:02,320")
        self.assertEqual(SubtitleFormatter._format_timestamp(2.319), "00:00:02,319")

    def test_rounding_carries_into_next_minute(self):
        self.assertEqual(SubtitleFormatter._format_timestamp(59.9996), "00:01:00,000")

    def test_hours(self):
        self.assertEqual(SubtitleFormatter._format_timestamp(3661.5), "01:01:01,500")


class SrtOutputTests(unittest.TestCase):
    cues = [Cue(0.0, 1.5, "Hello there."), Cue(2.0, 3.25, "Second line\nwith two rows.")]

    def test_srt(self):
        self.assertEqual(
            SubtitleFormatter.to_srt(self.cues),
            "1\n00:00:00,000 --> 00:00:01,500\nHello there.\n\n"
            "2\n00:00:02,000 --> 00:00:03,250\nSecond line\nwith two rows.\n",
        )


class CueBuildingTests(unittest.TestCase):
    def assert_readable(self, cues):
        for cue in cues:
            rows = cue.text.split("\n")
            self.assertLessEqual(len(rows), Config.MAX_LINES, cue)
            for row in rows:
                self.assertLessEqual(len(row), Config.MAX_CHARS_PER_LINE, cue)
            self.assertLessEqual(cue.end - cue.start, Config.MAX_CUE_DURATION + 1e-9, cue)
        for current, following in zip(cues, cues[1:]):
            self.assertLessEqual(current.end, following.start, (current, following))

    def test_long_speech_is_split_into_readable_cues(self):
        texts = ("this is a long run of speech without any punctuation that keeps going "
                 "and going for quite a while so it must be split into several cues "
                 "that each fit on screen nicely").split()
        cues = SubtitleFormatter.build_cues([segment(steady_words(texts))])
        self.assertGreater(len(cues), 1)
        self.assert_readable(cues)
        # No words lost or reordered
        self.assertEqual(" ".join(c.text.replace("\n", " ") for c in cues), " ".join(texts))

    def test_two_rows_are_balanced(self):
        texts = "one two three four five six seven eight nine ten eleven twelve".split()
        cues = SubtitleFormatter.build_cues([segment(steady_words(texts, step=0.2))])
        self.assertEqual(len(cues), 1)
        top, bottom = cues[0].text.split("\n")
        self.assertLessEqual(abs(len(top) - len(bottom)), 6)

    def test_breaks_after_sentence_end(self):
        texts = "Okay, I think we should go to the beach now. Monica, are you coming with us?".split()
        cues = SubtitleFormatter.build_cues([segment(steady_words(texts))])
        self.assertTrue(cues[0].text.replace("\n", " ").endswith("beach now."))

    def test_breaks_on_long_pause(self):
        words = steady_words(["Hello", "there"]) + steady_words(["after", "pause"], start=5.0)
        cues = SubtitleFormatter.build_cues([segment(words)])
        self.assertEqual([c.text for c in cues], ["Hello there", "after pause"])
        # Before silence the cue lingers a little after the speech (0.6 s),
        # not until the next line starts at 5.0 s
        self.assertAlmostEqual(cues[0].end, 0.6 + Config.END_TAIL)

    def test_short_cue_gets_minimum_duration(self):
        words = [word(0.0, 0.3, "Hi.")] + steady_words(["much", "later"], start=5.0)
        cues = SubtitleFormatter.build_cues([segment(words)])
        self.assertAlmostEqual(cues[0].end - cues[0].start, Config.MIN_CUE_DURATION)

    def test_long_line_before_silence_stays_long_enough_to_read(self):
        texts = "and I don't really know what happened with that either.".split()
        words = steady_words(texts, step=0.2) + steady_words(["Later."], start=20.0)
        cue = SubtitleFormatter.build_cues([segment(words)])[0]
        reading_time = len(cue.text.replace("\n", " ")) / Config.READING_SPEED_CPS
        self.assertAlmostEqual(cue.end - cue.start, reading_time)
        self.assertGreater(cue.end, words[len(texts) - 1].end + Config.END_TAIL)

    def test_fast_dialogue_is_not_delayed(self):
        first = steady_words("I think we should go now.".split(), step=0.2)
        second = steady_words("Yes, let's go right away.".split(), start=first[-1].end + 0.1, step=0.2)
        cues = SubtitleFormatter.build_cues([segment(first), segment(second)])
        self.assertEqual(len(cues), 2)
        # The first line gives way to the second one, never overlapping it
        self.assertLessEqual(cues[0].end, cues[1].start)
        self.assertAlmostEqual(cues[1].start, second[0].start)

    def test_short_cue_merges_with_following_line(self):
        words = steady_words(["All", "right."], step=0.15) + steady_words(
            "we need to talk about the thing.".split(), start=0.35)
        cues = SubtitleFormatter.build_cues([segment(words[:2]), segment(words[2:])])
        self.assertEqual(len(cues), 1)
        self.assertTrue(cues[0].text.startswith("All right."))

    def test_stretched_word_is_capped(self):
        words = [word(0.0, 0.4, "Oh."), word(0.5, 12.0, "It's")]
        cues = SubtitleFormatter.build_cues([segment(words)])
        self.assert_readable(cues)

    def test_overlapping_word_times_do_not_overlap_cues(self):
        first = steady_words("this is the end of a sentence.".split())
        second = steady_words("and this starts slightly early".split(), start=first[-1].end - 0.2)
        cues = SubtitleFormatter.build_cues([segment(first), segment(second)])
        self.assert_readable(cues)

    def test_segment_without_words_keeps_its_own_text_and_times(self):
        seg = SimpleNamespace(start=1.0, end=4.0, text=" Plain segment text.", words=None)
        self.assertEqual(SubtitleFormatter.build_cues([seg]),
                         [Cue(1.0, 4.0 + Config.END_TAIL, "Plain segment text.")])

    def test_empty_input(self):
        self.assertEqual(SubtitleFormatter.build_cues([]), [])
        self.assertEqual(SubtitleFormatter.to_srt([]), "")


if __name__ == "__main__":
    unittest.main()
