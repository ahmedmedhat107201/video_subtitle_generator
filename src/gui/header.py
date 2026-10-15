"""Top bar: app name on the left, the compute device on the right."""
import customtkinter as ctk

from src.gui import theme

APP_NAME = "SUBTITLE GENERATOR"


class Header:
    """Compact top bar with an accent marker, the app name and a device pill."""

    def __init__(self, parent):
        self.frame = ctk.CTkFrame(parent, fg_color=theme.BG, corner_radius=0, height=60)
        self.frame.grid_propagate(False)
        self.frame.pack_propagate(False)

        brand = ctk.CTkFrame(self.frame, fg_color="transparent")
        brand.pack(side="left", padx=(theme.SPACE_XL, 0))

        # Accent marker bar, like a clip on an editing timeline
        ctk.CTkFrame(brand, width=4, height=22, corner_radius=2, fg_color=theme.ACCENT).pack(
            side="left", padx=(0, theme.SPACE_M))
        ctk.CTkLabel(brand, text=APP_NAME, font=theme.font("title"), text_color=theme.TEXT).pack(side="left")

        # Device pill: "● GPU" (accent) or "● CPU" (muted)
        self.device_pill = ctk.CTkFrame(
            self.frame, fg_color=theme.SURFACE, corner_radius=12,
            border_width=1, border_color=theme.BORDER, height=26,
        )
        self.device_pill.pack(side="right", padx=theme.SPACE_XL)
        self._device_dot = ctk.CTkLabel(self.device_pill, text="●", font=theme.font("small", 10),
                                        text_color=theme.TEXT_FAINT, width=10)
        self._device_dot.pack(side="left", padx=(theme.SPACE_M, theme.SPACE_XS))
        self._device_text = ctk.CTkLabel(self.device_pill, text="DETECTING", font=theme.font("label", 11),
                                         text_color=theme.TEXT_MUTED)
        self._device_text.pack(side="left", padx=(0, theme.SPACE_M))

        # Hairline under the bar
        self.divider = ctk.CTkFrame(parent, height=1, corner_radius=0, fg_color=theme.BORDER)

    def set_device(self, device: str):
        """Show whether transcription runs on the GPU ("cuda") or the CPU."""
        if device == "cuda":
            self._device_dot.configure(text_color=theme.ACCENT)
            self._device_text.configure(text="GPU", text_color=theme.TEXT)
        else:
            self._device_dot.configure(text_color=theme.TEXT_FAINT)
            self._device_text.configure(text="CPU", text_color=theme.TEXT_MUTED)
