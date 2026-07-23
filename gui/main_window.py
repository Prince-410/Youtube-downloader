import customtkinter as ctk
from downloader.downloader import YoutubeDownloader
from gui.download_page import DownloadPage
from gui.history_page import HistoryPage
from gui.settings_page import SettingsPage
from utils.config import ConfigManager


class MainWindow(ctk.CTk):
    """Main Application Window for YouTube Downloader Desktop application."""

    def __init__(self, config_manager: ConfigManager, downloader: YoutubeDownloader) -> None:
        super().__init__()
        self.config_manager = config_manager
        self.downloader = downloader

        # Apply theme setting
        theme_mode = self.config_manager.get("theme_mode", "Dark")
        ctk.set_appearance_mode(theme_mode)
        ctk.set_default_color_theme("blue")

        # Window properties
        self.title("YouTube Downloader")
        self.geometry("1020x700")
        self.minsize(880, 580)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self._create_sidebar()
        self._create_content_area()
        self.select_page("download")

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_sidebar(self) -> None:
        """Create navigation sidebar."""
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        # Brand header
        logo_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="YT Downloader",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        logo_label.grid(row=0, column=0, padx=20, pady=(20, 20))

        # Navigation Buttons
        self.btn_download = ctk.CTkButton(
            self.sidebar_frame,
            text="Download",
            height=40,
            corner_radius=8,
            anchor="w",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=lambda: self.select_page("download"),
        )
        self.btn_download.grid(row=1, column=0, padx=15, pady=5, sticky="ew")

        self.btn_history = ctk.CTkButton(
            self.sidebar_frame,
            text="History",
            height=40,
            corner_radius=8,
            anchor="w",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=lambda: self.select_page("history"),
        )
        self.btn_history.grid(row=2, column=0, padx=15, pady=5, sticky="ew")

        self.btn_settings = ctk.CTkButton(
            self.sidebar_frame,
            text="Settings",
            height=40,
            corner_radius=8,
            anchor="w",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=lambda: self.select_page("settings"),
        )
        self.btn_settings.grid(row=3, column=0, padx=15, pady=5, sticky="ew")

        # Theme Option Selector at Bottom
        theme_label = ctk.CTkLabel(self.sidebar_frame, text="Appearance:", font=ctk.CTkFont(size=12))
        theme_label.grid(row=5, column=0, padx=20, pady=(10, 2), sticky="w")

        self.theme_menu = ctk.CTkOptionMenu(
            self.sidebar_frame,
            values=["Dark", "Light", "System"],
            command=self._change_appearance_mode,
        )
        self.theme_menu.grid(row=6, column=0, padx=15, pady=(0, 20), sticky="ew")
        self.theme_menu.set(self.config_manager.get("theme_mode", "Dark"))

    def _create_content_area(self) -> None:
        """Create main container frame holding dynamic page views."""
        self.content_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.content_frame.grid(row=0, column=1, sticky="nsew")

        # Instantiate page views
        self.download_page = DownloadPage(self.content_frame, self.downloader, self.config_manager)
        self.history_page = HistoryPage(self.content_frame, self.config_manager)
        self.settings_page = SettingsPage(
            self.content_frame,
            self.config_manager,
            on_theme_change=lambda t: self.theme_menu.set(t),
        )

    def select_page(self, page_name: str) -> None:
        """Switch active view page and highlight active button."""
        # Unpack all
        self.download_page.pack_forget()
        self.history_page.pack_forget()
        self.settings_page.pack_forget()

        # Reset button styles
        unselected_color = ("#3A3D40", "#2B2B2B")
        selected_color = ("#1F6AA5", "#144870")

        self.btn_download.configure(fg_color=unselected_color)
        self.btn_history.configure(fg_color=unselected_color)
        self.btn_settings.configure(fg_color=unselected_color)

        if page_name == "download":
            self.download_page.pack(fill="both", expand=True)
            self.btn_download.configure(fg_color=selected_color)
        elif page_name == "history":
            self.history_page.refresh_history()
            self.history_page.pack(fill="both", expand=True)
            self.btn_history.configure(fg_color=selected_color)
        elif page_name == "settings":
            self.settings_page.pack(fill="both", expand=True)
            self.btn_settings.configure(fg_color=selected_color)

    def _change_appearance_mode(self, new_mode: str) -> None:
        """Callback when user alters theme selector in sidebar."""
        ctk.set_appearance_mode(new_mode)
        self.config_manager.set("theme_mode", new_mode)

    def _on_close(self) -> None:
        """Gracefully handle window exit."""
        if self.downloader:
            self.downloader.cancel_download()
        self.destroy()
