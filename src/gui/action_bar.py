"""Bottom action bar: queue summary / result on the left, the main button on the right."""
import customtkinter as ctk

from src.gui import theme

_RESULT_COLOURS = {"success": theme.SUCCESS, "warning": theme.WARNING, "danger": theme.DANGER}


class ActionBar:
    """Always-visible bar with the Generate / Cancel button."""

    def __init__(self, parent, generate_command, cancel_command):
        self._generate_command = generate_command
        self._cancel_command = cancel_command

        self.divider = ctk.CTkFrame(parent, height=1, corner_radius=0, fg_color=theme.BORDER)
        self.frame = ctk.CTkFrame(parent, fg_color=theme.SURFACE, corner_radius=0, height=76)
        self.frame.pack_propagate(False)

        text_box = ctk.CTkFrame(self.frame, fg_color="transparent")
        text_box.pack(side="left", fill="both", expand=True, padx=(theme.SPACE_XL, theme.SPACE_L))
        inner = ctk.CTkFrame(text_box, fg_color="transparent")
        inner.place(relx=0, rely=0.5, anchor="w")
        self.result = ctk.CTkLabel(inner, text="", font=theme.font("body"), text_color=theme.SUCCESS,
                                   anchor="w", height=20)
        self.summary = ctk.CTkLabel(inner, text="No videos in the queue", font=theme.font("small", 12),
                                    text_color=theme.TEXT_MUTED, anchor="w", height=18)
        self.summary.pack(anchor="w")

        self.button = ctk.CTkButton(
            self.frame, text="GENERATE", width=200, height=44, corner_radius=theme.RADIUS,
            font=theme.font("button"), border_width=1,
        )
        self.button.pack(side="right", padx=theme.SPACE_XL)
        self.set_mode("generate", enabled=False)

    def set_mode(self, mode, enabled=True):
        """mode: "generate", "cancel" or "cancelling"."""
        if mode == "generate":
            if enabled:
                self.button.configure(
                    text="GENERATE", command=self._generate_command, state="normal",
                    fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER,
                    border_color=theme.ACCENT, text_color=theme.ON_ACCENT,
                )
            else:
                self.button.configure(
                    text="GENERATE", command=self._generate_command, state="disabled",
                    fg_color=theme.SURFACE_HOVER, border_color=theme.BORDER,
                    text_color_disabled=theme.TEXT_FAINT,
                )
        elif mode == "cancel":
            self.button.configure(
                text="CANCEL", command=self._cancel_command, state="normal",
                fg_color="transparent", hover_color=theme.DANGER_TINT,
                border_color=theme.DANGER, text_color=theme.DANGER,
            )
        else:  # cancelling
            self.button.configure(
                text="CANCELLING…", state="disabled", fg_color="transparent",
                border_color=theme.BORDER, text_color_disabled=theme.TEXT_MUTED,
            )

    def set_summary(self, text):
        self.summary.configure(text=text)

    def show_result(self, kind, text):
        """Show the outcome of the last run (kind: success, warning, danger)."""
        self.result.configure(text=text, text_color=_RESULT_COLOURS[kind])
        self.result.pack(anchor="w", before=self.summary)

    def clear_result(self):
        self.result.pack_forget()
