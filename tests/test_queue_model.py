"""Tests for the queue state behind the queue list."""
import unittest

from src.gui.queue_model import CANCELLED, DONE, FAILED, QUEUED, RUNNING, QueueModel


class QueueModelTests(unittest.TestCase):
    def setUp(self):
        self.queue = QueueModel()
        self.queue.add(["a.mp4", "b.mp4", "c.mp4"])

    def test_add_ignores_duplicates_and_empty(self):
        self.assertEqual(self.queue.add(["b.mp4", "d.mp4", "", "d.mp4"]), 1)
        self.assertEqual([i.path for i in self.queue.items], ["a.mp4", "b.mp4", "c.mp4", "d.mp4"])

    def test_pending_and_counts(self):
        self.assertEqual(self.queue.pending(), [0, 1, 2])
        self.queue.start(0)
        self.queue.finish(0)
        self.queue.start(1)
        self.assertEqual(self.queue.pending(), [2])
        self.assertEqual(self.queue.counts(), {QUEUED: 1, RUNNING: 1, DONE: 1, FAILED: 0, CANCELLED: 0})
        self.assertTrue(self.queue.is_running())

    def test_progress_only_updates_running_item(self):
        self.queue.progress(0, 0.5, "Transcribing")
        self.assertEqual(self.queue.items[0].progress, 0.0)
        self.queue.start(0)
        self.queue.progress(0, 1.7, "Transcribing", "0:10 / 0:20")
        item = self.queue.items[0]
        self.assertEqual((item.progress, item.message, item.detail), (1.0, "Transcribing", "0:10 / 0:20"))

    def test_fail_keeps_error(self):
        self.queue.start(1)
        self.queue.fail(1, ValueError("bad file"))
        self.assertEqual(self.queue.items[1].status, FAILED)
        self.assertEqual(self.queue.items[1].error, "bad file")

    def test_cancel_keeps_queued_items_for_next_run(self):
        self.queue.start(0)
        self.queue.cancel_running()
        self.assertEqual([i.status for i in self.queue.items], [CANCELLED, QUEUED, QUEUED])
        self.assertEqual(self.queue.pending(), [1, 2])

    def test_remove_and_clear_never_touch_running_item(self):
        self.queue.start(1)
        self.queue.remove("b.mp4")
        self.queue.remove("a.mp4")
        self.assertEqual([i.path for i in self.queue.items], ["b.mp4", "c.mp4"])
        self.queue.clear()
        self.assertEqual([(i.path, i.status) for i in self.queue.items], [("b.mp4", RUNNING)])

    def test_restarting_a_cancelled_item_resets_it(self):
        self.queue.start(0)
        self.queue.progress(0, 0.4, "Transcribing")
        self.queue.cancel_running()
        self.queue.items[0].status = QUEUED
        self.queue.start(0)
        self.assertEqual((self.queue.items[0].progress, self.queue.items[0].error), (0.0, ""))


if __name__ == "__main__":
    unittest.main()
