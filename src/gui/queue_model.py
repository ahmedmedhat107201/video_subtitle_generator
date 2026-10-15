"""State of the video queue, kept separate from the widgets so it can be tested."""
from dataclasses import dataclass

QUEUED = "queued"
RUNNING = "running"
DONE = "done"
FAILED = "failed"
CANCELLED = "cancelled"


@dataclass
class QueueItem:
    path: str
    status: str = QUEUED
    progress: float = 0.0
    message: str = ""
    detail: str = ""
    error: str = ""


class QueueModel:
    """Ordered list of videos and what happened to each of them."""

    def __init__(self):
        self.items = []

    # ----- Editing -----
    def add(self, paths):
        """Append new paths (duplicates are ignored). Returns how many were added."""
        known = {item.path for item in self.items}
        added = 0
        for path in paths:
            if path and path not in known:
                self.items.append(QueueItem(path))
                known.add(path)
                added += 1
        return added

    def remove(self, path):
        """Remove a video unless it is being processed right now."""
        self.items = [i for i in self.items if i.path != path or i.status == RUNNING]

    def clear(self):
        """Remove every video that isn't being processed."""
        self.items = [i for i in self.items if i.status == RUNNING]

    # ----- Queries -----
    def pending(self):
        """Indexes of videos waiting to be processed."""
        return [n for n, item in enumerate(self.items) if item.status == QUEUED]

    def counts(self):
        """Number of videos per status."""
        result = {QUEUED: 0, RUNNING: 0, DONE: 0, FAILED: 0, CANCELLED: 0}
        for item in self.items:
            result[item.status] += 1
        return result

    def is_running(self):
        return any(item.status == RUNNING for item in self.items)

    # ----- Processing -----
    def start(self, index):
        item = self.items[index]
        item.status, item.progress, item.message, item.detail, item.error = RUNNING, 0.0, "Starting", "", ""

    def progress(self, index, value, message="", detail=""):
        item = self.items[index]
        if item.status == RUNNING:
            item.progress = max(0.0, min(1.0, value))
            item.message, item.detail = message, detail

    def finish(self, index, detail=""):
        item = self.items[index]
        item.status, item.progress, item.detail = DONE, 1.0, detail

    def fail(self, index, error):
        item = self.items[index]
        item.status, item.error = FAILED, str(error)

    def cancel_running(self):
        """The video being processed becomes cancelled; queued videos stay queued."""
        for item in self.items:
            if item.status == RUNNING:
                item.status = CANCELLED
