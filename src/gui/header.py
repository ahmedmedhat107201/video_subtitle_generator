import customtkinter as ctk
from src.gui.theme import PRIMARY, BG_DARK, TEXT


class Header:
    """Encapsulates the top header (title + badges)."""

    def __init__(self, parent):
        # Use the app's primary palette for a clean header
        self.frame = ctk.CTkFrame(parent, fg_color=BG_DARK, corner_radius=0, height=140)
        self.frame.pack(fill="x", padx=0, pady=0)
        self.frame.pack_propagate(False)

        self.title_label = ctk.CTkLabel(
            self.frame,
            text="🎬 AI Subtitle Generator",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=TEXT,
        )
        self.title_label.pack(pady=(25, 5))

        badges_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        badges_frame.pack(pady=(5, 10))

        badges = [
            ("⚡", "Fast Processing"),
            ("🎯", "Accurate Timestamps"),
            ("🚀", "GPU Accelerated"),
        ]

        for emoji, text in badges:
            badge = ctk.CTkLabel(
                badges_frame,
                text=f"{emoji} {text}",
                font=ctk.CTkFont(size=11),
                text_color=TEXT,
            )
            badge.pack(side="left", padx=15)
