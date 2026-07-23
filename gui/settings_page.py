import tkinter as tk
from pathlib import Path
import customtkinter as ctk
from utils.config import ConfigManager
from utils.validators import is_directory_writable


class SettingsPage(ctk.CTkFrame):
    """Settings Page for configuring default options and user preferences."""

    def __init__(self, parent: ctk.CTkFrame, config_manager: ConfigManager, on_theme_change=None) -> None:
        super().__init__(parent, fg_color="transparent")
        self.config_manager = config_manager
        self.on_theme_change = on_theme_change

        self._create_widgets()
        self._load_settings()

    def _create_widgets(self) -> None:
        """Build settings UI layout."""
        container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=15, pady=15)

        # Title
        title_label = ctk.CTkLabel(
            container,
            text="Settings & Preferences",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        title_label.pack(anchor="w", pady=(0, 15))

        # --- General Settings Card ---
        gen_card = ctk.CTkFrame(container, corner_radius=10)
        gen_card.pack(fill="x", pady=(0, 15), ipady=10, ipadx=10)

        ctk.CTkLabel(
            gen_card,
            text="General Settings",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="w", padx=15, pady=(10, 15))

        # Download Path Setting
        path_frame = ctk.CTkFrame(gen_card, fg_color="transparent")
        path_frame.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(path_frame, text="Default Download Location:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 5))

        path_inner = ctk.CTkFrame(path_frame, fg_color="transparent")
        path_inner.pack(fill="x")

        self.path_entry = ctk.CTkEntry(path_inner, height=35)
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        browse_btn = ctk.CTkButton(
            path_inner,
            text="Browse...",
            width=90,
            height=35,
            command=self._browse_folder,
        )
        browse_btn.pack(side="left")

        # Theme Mode Setting
        theme_frame = ctk.CTkFrame(gen_card, fg_color="transparent")
        theme_frame.pack(fill="x", padx=15, pady=(15, 5))

        ctk.CTkLabel(theme_frame, text="App Theme Mode:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(0, 15))

        self.theme_var = ctk.StringVar(value="Dark")
        self.theme_menu = ctk.CTkOptionMenu(
            theme_frame,
            values=["Dark", "Light", "System"],
            variable=self.theme_var,
            width=150,
        )
        self.theme_menu.pack(side="left")

        # --- Quality & Naming Preferences Card ---
        pref_card = ctk.CTkFrame(container, corner_radius=10)
        pref_card.pack(fill="x", pady=(0, 15), ipady=10, ipadx=10)

        ctk.CTkLabel(
            pref_card,
            text="Quality & Naming Defaults",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="w", padx=15, pady=(10, 15))

        grid_frame = ctk.CTkFrame(pref_card, fg_color="transparent")
        grid_frame.pack(fill="x", padx=15)

        # Video Quality Preference
        ctk.CTkLabel(grid_frame, text="Default Video Quality:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w", pady=10)
        self.video_q_var = ctk.StringVar(value="Highest Available")
        self.video_q_menu = ctk.CTkOptionMenu(
            grid_frame,
            values=ConfigManager.QUALITY_OPTIONS,
            variable=self.video_q_var,
            width=180,
        )
        self.video_q_menu.grid(row=0, column=1, sticky="w", padx=(15, 0), pady=10)

        # Audio Quality Preference
        ctk.CTkLabel(grid_frame, text="Default Audio Quality:", font=ctk.CTkFont(weight="bold")).grid(row=1, column=0, sticky="w", pady=10)
        self.audio_q_var = ctk.StringVar(value="320kbps")
        self.audio_q_menu = ctk.CTkOptionMenu(
            grid_frame,
            values=ConfigManager.AUDIO_QUALITY_OPTIONS,
            variable=self.audio_q_var,
            width=180,
        )
        self.audio_q_menu.grid(row=1, column=1, sticky="w", padx=(15, 0), pady=10)

        # Filename Format Template
        ctk.CTkLabel(grid_frame, text="Filename Format Template:", font=ctk.CTkFont(weight="bold")).grid(row=2, column=0, sticky="w", pady=10)
        self.filename_entry = ctk.CTkEntry(grid_frame, width=280, height=35)
        self.filename_entry.grid(row=2, column=1, sticky="w", padx=(15, 0), pady=10)

        ctk.CTkLabel(
            pref_card,
            text="Supported placeholders: %(title)s, %(id)s, %(ext)s, %(uploader)s",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).pack(anchor="w", padx=15, pady=(0, 10))

        # --- Action Buttons & Status ---
        action_card = ctk.CTkFrame(container, fg_color="transparent")
        action_card.pack(fill="x", pady=10)

        save_btn = ctk.CTkButton(
            action_card,
            text="Save Settings",
            height=40,
            width=140,
            fg_color="#10B981",
            hover_color="#059669",
            font=ctk.CTkFont(weight="bold"),
            command=self._save_settings,
        )
        save_btn.pack(side="left", padx=(0, 10))

        reset_btn = ctk.CTkButton(
            action_card,
            text="Reset Defaults",
            height=40,
            width=120,
            fg_color="#475569",
            hover_color="#334155",
            command=self._reset_defaults,
        )
        reset_btn.pack(side="left")

        self.status_lbl = ctk.CTkLabel(
            action_card,
            text="",
            font=ctk.CTkFont(size=12),
        )
        self.status_lbl.pack(side="left", padx=15)

    def _load_settings(self) -> None:
        """Load values from config manager into UI."""
        self.path_entry.delete(0, tk.END)
        self.path_entry.insert(0, self.config_manager.get("download_location", ""))

        self.theme_var.set(self.config_manager.get("theme_mode", "Dark"))
        self.video_q_var.set(self.config_manager.get("preferred_video_quality", "Highest Available"))
        self.audio_q_var.set(self.config_manager.get("preferred_audio_quality", "320kbps"))

        self.filename_entry.delete(0, tk.END)
        self.filename_entry.insert(0, self.config_manager.get("filename_format", "%(title)s.%(ext)s"))

    def _browse_folder(self) -> None:
        selected = ctk.filedialog.askdirectory(initialdir=self.path_entry.get())
        if selected:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, selected)

    def _save_settings(self) -> None:
        """Validate and save updated settings."""
        loc = self.path_entry.get().strip()
        if not is_directory_writable(loc):
            self.status_lbl.configure(text="Error: Selected download location is not writable.", text_color="#EF4444")
            return

        fmt = self.filename_entry.get().strip()
        if not fmt:
            fmt = "%(title)s.%(ext)s"

        theme = self.theme_var.get()

        new_settings = {
            "download_location": loc,
            "theme_mode": theme,
            "preferred_video_quality": self.video_q_var.get(),
            "preferred_audio_quality": self.audio_q_var.get(),
            "filename_format": fmt,
        }

        self.config_manager.save_settings(new_settings)
        ctk.set_appearance_mode(theme)

        if self.on_theme_change:
            self.on_theme_change(theme)

        self.status_lbl.configure(text="Settings saved successfully!", text_color="#10B981")

    def _reset_defaults(self) -> None:
        """Reset settings to original factory defaults."""
        defaults = self.config_manager.DEFAULT_SETTINGS.copy()
        self.config_manager.save_settings(defaults)
        self._load_settings()
        ctk.set_appearance_mode(defaults["theme_mode"])
        self.status_lbl.configure(text="Reset to default settings.", text_color="#F59E0B")
