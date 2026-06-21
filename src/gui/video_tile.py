"""Provides a factory to create the in-window video progress tile.

This module only builds widgets and returns them so the main window can keep
references as instance attributes.
"""
import customtkinter as ctk


def make_video_tile(parent):
    """Create the video tile widgets and return a dict of widgets.

    Returns: (video_tile, widgets_dict)
    widgets_dict contains: title_label, progress_status, progress_bar,
    progress_percent, progress_detail
    """
    from src.gui.theme import CARD_DARK, BG_DARK

    video_tile = ctk.CTkFrame(
        parent,
        corner_radius=12,
        fg_color=CARD_DARK,
        border_width=1,
    border_color=BG_DARK
    )

    from src.gui.theme import TEXT

    title_label = ctk.CTkLabel(
        video_tile,
        text="",
        font=ctk.CTkFont(size=14, weight="bold"),
        anchor="w",
        text_color=TEXT,
    )
    title_label.pack(fill="x", padx=12, pady=(10, 6))

    # Container where each queued file will be represented as a row
    queue_container = ctk.CTkFrame(video_tile, fg_color="transparent")
    queue_container.pack(fill="both", padx=12, pady=(0, 6))

    # Note: Removed the large fallback progress bar to keep the action area
    # compact. Per-item progress is represented inside the queue rows.

    # hide by default
    video_tile.pack_forget()

    widgets = {
        "title_label": title_label,
        "queue_container": queue_container,
        # populated by ActionPanel when showing a queue
        "queue_items": [],
        # Note: no global status/detail or fallback progress widgets; per-item
        # status is shown inside queue rows.
    }

    return video_tile, widgets
