import threading
import tkinter as tk
from pathlib import Path
from typing import List, Optional, Any
import customtkinter as ctk
from PIL import Image

from downloader.downloader import VideoMetadata, YoutubeDownloader
from downloader.playlist import PlaylistItem
from downloader.progress import DownloadProgress, DownloadState
from utils.config import ConfigManager
from utils.helpers import fetch_thumbnail_image, format_bytes, format_seconds, format_speed
from utils.validators import is_directory_writable, is_duplicate_download, is_valid_url, is_youtube_playlist


class DownloadPage(ctk.CTkFrame):
    """Main Download Page handling URL input, metadata preview, quality settings, playlist choices, and download progress."""

    def __init__(self, parent: ctk.CTkFrame, downloader: YoutubeDownloader, config_manager: ConfigManager) -> None:
        super().__init__(parent, fg_color="transparent")
        self.downloader = downloader
        self.config_manager = config_manager
        self.current_metadata: Optional[VideoMetadata] = None
        self.playlist_checkboxes: List[tuple[PlaylistItem, ctk.CTkCheckBox]] = []

        self._create_widgets()
        self._load_defaults()

    def _create_widgets(self) -> None:
        """Construct page UI components."""
        # Scrollable container for whole page
        self.scroll_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_container.pack(fill="both", expand=True, padx=15, pady=15)

        # Header Title
        title_label = ctk.CTkLabel(
            self.scroll_container,
            text="YouTube Downloader",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        title_label.pack(anchor="w", pady=(0, 15))

        # --- 1. URL Input Card ---
        url_card = ctk.CTkFrame(self.scroll_container, corner_radius=10)
        url_card.pack(fill="x", pady=(0, 15), ipady=10, ipadx=10)

        url_title = ctk.CTkLabel(
            url_card,
            text="Paste Video or Playlist URL",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        url_title.pack(anchor="w", padx=15, pady=(5, 5))

        url_input_frame = ctk.CTkFrame(url_card, fg_color="transparent")
        url_input_frame.pack(fill="x", padx=15, pady=5)

        self.url_entry = ctk.CTkEntry(
            url_input_frame,
            placeholder_text="https://www.youtube.com/watch?v=... or playlist URL",
            height=40,
            font=ctk.CTkFont(size=13),
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        paste_btn = ctk.CTkButton(
            url_input_frame,
            text="Paste",
            width=70,
            height=40,
            fg_color="#3B82F6",
            hover_color="#2563EB",
            command=self._paste_clipboard,
        )
        paste_btn.pack(side="left", padx=(0, 10))

        self.fetch_btn = ctk.CTkButton(
            url_input_frame,
            text="Fetch Info",
            width=100,
            height=40,
            fg_color="#10B981",
            hover_color="#059669",
            font=ctk.CTkFont(weight="bold"),
            command=self._fetch_metadata_threaded,
        )
        self.fetch_btn.pack(side="left")

        self.status_banner = ctk.CTkLabel(
            url_card,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="#F59E0B",
        )
        self.status_banner.pack(anchor="w", padx=15, pady=(5, 0))

        # --- 2. Video Preview Card ---
        self.preview_card = ctk.CTkFrame(self.scroll_container, corner_radius=10)
        # Will be packed once metadata is loaded

        # Sub-components inside preview card
        preview_inner = ctk.CTkFrame(self.preview_card, fg_color="transparent")
        preview_inner.pack(fill="x", padx=15, pady=15)

        self.thumb_label = ctk.CTkLabel(
            preview_inner,
            text="[ Thumbnail ]",
            width=200,
            height=112,
            fg_color="#1E293B",
            corner_radius=8,
        )
        self.thumb_label.pack(side="left", padx=(0, 15))

        info_box = ctk.CTkFrame(preview_inner, fg_color="transparent")
        info_box.pack(side="left", fill="both", expand=True)

        self.preview_badge = ctk.CTkLabel(
            info_box,
            text="SINGLE VIDEO",
            fg_color="#3B82F6",
            text_color="white",
            corner_radius=6,
            font=ctk.CTkFont(size=10, weight="bold"),
            width=100,
            height=22,
        )
        self.preview_badge.pack(anchor="w", pady=(0, 5))

        self.preview_title = ctk.CTkLabel(
            info_box,
            text="Video Title Placeholder",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w",
            wraplength=450,
            justify="left",
        )
        self.preview_title.pack(anchor="w", pady=(0, 5))

        self.preview_uploader = ctk.CTkLabel(
            info_box,
            text="Channel Name",
            font=ctk.CTkFont(size=12),
            text_color="gray",
            anchor="w",
        )
        self.preview_uploader.pack(anchor="w", pady=(0, 5))

        self.preview_details = ctk.CTkLabel(
            info_box,
            text="Duration: --:-- | Approx. Size: -- MB",
            font=ctk.CTkFont(size=12),
            anchor="w",
        )
        self.preview_details.pack(anchor="w")

        # --- 3. Playlist Video Selection Section (hidden unless playlist) ---
        self.playlist_frame = ctk.CTkFrame(self.scroll_container, corner_radius=10)
        # Will be packed conditionally

        pl_header = ctk.CTkFrame(self.playlist_frame, fg_color="transparent")
        pl_header.pack(fill="x", padx=15, pady=(10, 5))

        ctk.CTkLabel(
            pl_header,
            text="Playlist Items Selection",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(side="left")

        select_all_btn = ctk.CTkButton(
            pl_header,
            text="Select All",
            width=80,
            height=28,
            fg_color="#475569",
            command=self._select_all_playlist,
        )
        select_all_btn.pack(side="right", padx=(5, 0))

        deselect_all_btn = ctk.CTkButton(
            pl_header,
            text="Deselect All",
            width=80,
            height=28,
            fg_color="#475569",
            command=self._deselect_all_playlist,
        )
        deselect_all_btn.pack(side="right")

        self.playlist_scroll = ctk.CTkScrollableFrame(self.playlist_frame, height=180, fg_color="#1E293B")
        self.playlist_scroll.pack(fill="x", padx=15, pady=(5, 15))

        # --- 4. Options & Destination Card ---
        self.options_card = ctk.CTkFrame(self.scroll_container, corner_radius=10)
        self.options_card.pack(fill="x", pady=(0, 15), ipady=10, ipadx=10)

        ctk.CTkLabel(
            self.options_card,
            text="Download Options",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", padx=15, pady=(10, 10))

        opts_grid = ctk.CTkFrame(self.options_card, fg_color="transparent")
        opts_grid.pack(fill="x", padx=15)

        # Format choice (Video / Audio)
        ctk.CTkLabel(opts_grid, text="Format:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w", pady=5)
        self.format_var = ctk.StringVar(value="Video")
        self.format_menu = ctk.CTkOptionMenu(
            opts_grid,
            values=["Video", "Audio (MP3)"],
            variable=self.format_var,
            command=self._on_format_changed,
            width=150,
        )
        self.format_menu.grid(row=0, column=1, sticky="w", padx=(10, 30), pady=5)

        # Quality choice
        ctk.CTkLabel(opts_grid, text="Quality:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=2, sticky="w", pady=5)
        self.quality_var = ctk.StringVar(value="Highest Available")
        self.quality_menu = ctk.CTkOptionMenu(
            opts_grid,
            values=ConfigManager.QUALITY_OPTIONS,
            variable=self.quality_var,
            width=170,
        )
        self.quality_menu.grid(row=0, column=3, sticky="w", padx=(10, 0), pady=5)

        # Download Folder Picker
        folder_frame = ctk.CTkFrame(self.options_card, fg_color="transparent")
        folder_frame.pack(fill="x", padx=15, pady=(10, 5))

        ctk.CTkLabel(folder_frame, text="Download Folder:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(0, 10))

        self.folder_entry = ctk.CTkEntry(folder_frame, height=35)
        self.folder_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        browse_btn = ctk.CTkButton(
            folder_frame,
            text="Browse...",
            width=90,
            height=35,
            command=self._browse_folder,
        )
        browse_btn.pack(side="left")

        # --- 5. Download Progress & Control Card ---
        self.progress_card = ctk.CTkFrame(self.scroll_container, corner_radius=10)
        self.progress_card.pack(fill="x", pady=(0, 15), ipady=10, ipadx=10)

        ctk.CTkLabel(
            self.progress_card,
            text="Download Progress",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", padx=15, pady=(10, 5))

        self.progress_bar = ctk.CTkProgressBar(self.progress_card, height=14)
        self.progress_bar.set(0.0)
        self.progress_bar.pack(fill="x", padx=15, pady=10)

        # Progress stats labels
        stats_frame = ctk.CTkFrame(self.progress_card, fg_color="transparent")
        stats_frame.pack(fill="x", padx=15)

        self.lbl_percentage = ctk.CTkLabel(stats_frame, text="0.0%", font=ctk.CTkFont(weight="bold", size=14))
        self.lbl_percentage.pack(side="left")

        self.lbl_size = ctk.CTkLabel(stats_frame, text="0.0 MB / 0.0 MB", text_color="gray")
        self.lbl_size.pack(side="left", padx=20)

        self.lbl_speed = ctk.CTkLabel(stats_frame, text="0 KB/s", text_color="gray")
        self.lbl_speed.pack(side="left", padx=20)

        self.lbl_eta = ctk.CTkLabel(stats_frame, text="ETA: --:--", text_color="gray")
        self.lbl_eta.pack(side="right")

        self.lbl_status_text = ctk.CTkLabel(self.progress_card, text="Ready", font=ctk.CTkFont(size=12), text_color="#10B981")
        self.lbl_status_text.pack(anchor="w", padx=15, pady=(5, 10))

        # Control Buttons
        ctrl_frame = ctk.CTkFrame(self.progress_card, fg_color="transparent")
        ctrl_frame.pack(fill="x", padx=15, pady=5)

        self.start_btn = ctk.CTkButton(
            ctrl_frame,
            text="Start Download",
            height=40,
            fg_color="#10B981",
            hover_color="#059669",
            font=ctk.CTkFont(weight="bold", size=14),
            command=self._start_download,
        )
        self.start_btn.pack(side="left", padx=(0, 10))

        self.pause_btn = ctk.CTkButton(
            ctrl_frame,
            text="Pause",
            height=40,
            width=100,
            fg_color="#F59E0B",
            hover_color="#D97706",
            font=ctk.CTkFont(weight="bold", size=14),
            command=self._toggle_pause,
            state="disabled",
        )
        self.pause_btn.pack(side="left", padx=(0, 10))

        self.cancel_btn = ctk.CTkButton(
            ctrl_frame,
            text="Cancel",
            height=40,
            width=100,
            fg_color="#EF4444",
            hover_color="#DC2626",
            font=ctk.CTkFont(weight="bold", size=14),
            command=self._cancel_download,
            state="disabled",
        )
        self.cancel_btn.pack(side="left")

    def _load_defaults(self) -> None:
        """Load default settings into controls."""
        default_loc = self.config_manager.get("download_location", "")
        self.folder_entry.insert(0, default_loc)

        pref_video_q = self.config_manager.get("preferred_video_quality", "Highest Available")
        self.quality_var.set(pref_video_q)

    def _paste_clipboard(self) -> None:
        """Paste contents of clipboard into URL field."""
        try:
            text = self.clipboard_get()
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, text.strip())
        except Exception:
            pass

    def _browse_folder(self) -> None:
        """Open folder selection dialog."""
        selected = ctk.filedialog.askdirectory(initialdir=self.folder_entry.get())
        if selected:
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, selected)

    def _on_format_changed(self, choice: str) -> None:
        """Update quality menu options depending on Video vs Audio format choice."""
        if choice == "Audio (MP3)":
            self.quality_menu.configure(values=ConfigManager.AUDIO_QUALITY_OPTIONS)
            self.quality_var.set(self.config_manager.get("preferred_audio_quality", "320kbps"))
        else:
            self.quality_menu.configure(values=ConfigManager.QUALITY_OPTIONS)
            self.quality_var.set(self.config_manager.get("preferred_video_quality", "Highest Available"))

    # --- Metadata Extraction ---

    def _fetch_metadata_threaded(self) -> None:
        """Run metadata extraction in background thread."""
        url = self.url_entry.get().strip()
        if not is_valid_url(url):
            self.status_banner.configure(text="Invalid YouTube URL. Please check and try again.", text_color="#EF4444")
            return

        self.fetch_btn.configure(state="disabled", text="Fetching...")
        self.status_banner.configure(text="Extracting video metadata...", text_color="#F59E0B")

        def _task():
            try:
                meta = self.downloader.fetch_info(url)
                # Fetch thumbnail image
                img = None
                if meta.thumbnail_url:
                    img = fetch_thumbnail_image(meta.thumbnail_url)
                self.after(0, lambda: self._on_metadata_loaded(meta, img))
            except Exception as e:
                self.after(0, lambda: self._on_metadata_error(str(e)))

        threading.Thread(target=_task, daemon=True).start()

    def _on_metadata_loaded(self, meta: VideoMetadata, thumb_img: Optional[Image.Image]) -> None:
        """Update UI with extracted metadata."""
        self.fetch_btn.configure(state="normal", text="Fetch Info")
        self.status_banner.configure(text="Metadata fetched successfully!", text_color="#10B981")
        self.current_metadata = meta

        # Display preview card
        self.preview_card.pack(fill="x", pady=(0, 15), ipady=10, ipadx=10)

        # Set thumbnail
        if thumb_img:
            ctk_img = ctk.CTkImage(light_image=thumb_img, dark_image=thumb_img, size=(200, 112))
            self.thumb_label.configure(image=ctk_img, text="")
        else:
            self.thumb_label.configure(image=None, text="[ No Image ]")

        # Set text details
        self.preview_title.configure(text=meta.title)
        self.preview_uploader.configure(text=f"Channel: {meta.uploader}")

        if meta.is_playlist:
            self.preview_badge.configure(text=f"PLAYLIST ({meta.playlist_info.total_count} videos)", fg_color="#8B5CF6")
            self.preview_details.configure(text=f"Total Playlist Duration: {format_seconds(meta.duration)}")
            self._build_playlist_selection(meta.playlist_info)
        else:
            self.preview_badge.configure(text="SINGLE VIDEO", fg_color="#3B82F6")
            size_str = format_bytes(meta.filesize_approx) if meta.filesize_approx > 0 else "Unknown"
            self.preview_details.configure(text=f"Duration: {format_seconds(meta.duration)} | Size: ~{size_str}")
            self.playlist_frame.pack_forget()

    def _on_metadata_error(self, err_msg: str) -> None:
        """Handle metadata fetch error."""
        self.fetch_btn.configure(state="normal", text="Fetch Info")
        self.status_banner.configure(text=f"Error: {err_msg}", text_color="#EF4444")
        self.preview_card.pack_forget()
        self.playlist_frame.pack_forget()

    # --- Playlist Selection ---

    def _build_playlist_selection(self, pl_info: Optional[Any]) -> None:
        """Populate scrollable list of playlist videos with checkboxes."""
        if not pl_info:
            return

        # Clear existing checkboxes
        for widget in self.playlist_scroll.winfo_children():
            widget.destroy()

        self.playlist_checkboxes.clear()

        for item in pl_info.items:
            item_frame = ctk.CTkFrame(self.playlist_scroll, fg_color="transparent")
            item_frame.pack(fill="x", pady=2)

            chk_var = ctk.BooleanVar(value=item.selected)
            chk = ctk.CTkCheckBox(
                item_frame,
                text=f"{item.index}. {item.title} ({format_seconds(item.duration)})",
                variable=chk_var,
                font=ctk.CTkFont(size=12),
            )
            chk.pack(side="left", anchor="w")
            self.playlist_checkboxes.append((item, chk))

        self.playlist_frame.pack(fill="x", pady=(0, 15))

    def _select_all_playlist(self) -> None:
        for item, chk in self.playlist_checkboxes:
            chk.select()

    def _deselect_all_playlist(self) -> None:
        for item, chk in self.playlist_checkboxes:
            chk.deselect()

    # --- Download Execution ---

    def _start_download(self) -> None:
        """Validate input and initiate download."""
        url = self.url_entry.get().strip()
        if not url:
            self.lbl_status_text.configure(text="Please enter a YouTube URL.", text_color="#EF4444")
            return

        folder = self.folder_entry.get().strip()
        if not is_directory_writable(folder):
            self.lbl_status_text.configure(text="Invalid or unwritable download folder.", text_color="#EF4444")
            return

        selected_urls = None
        if self.current_metadata and self.current_metadata.is_playlist:
            selected_items = [item.url for item, chk in self.playlist_checkboxes if chk.get()]
            if not selected_items:
                self.lbl_status_text.configure(text="Please select at least one video from playlist.", text_color="#EF4444")
                return
            selected_urls = selected_items

        # Duplicate check preview for single video
        if self.current_metadata and not self.current_metadata.is_playlist:
            ext = "mp3" if self.format_var.get() == "Audio (MP3)" else "mp4"
            expected_fn = f"{self.current_metadata.title}.{ext}"
            history = self.config_manager.load_history()
            if is_duplicate_download(folder, expected_fn, history):
                self.lbl_status_text.configure(
                    text="Warning: File already exists in folder or history. Overwriting...",
                    text_color="#F59E0B",
                )

        # UI state updates for downloading
        self.start_btn.configure(state="disabled")
        self.pause_btn.configure(state="normal", text="Pause")
        self.cancel_btn.configure(state="normal")
        self.lbl_status_text.configure(text="Initializing download...", text_color="#10B981")
        self.progress_bar.set(0.0)

        # Start download
        self.downloader.start_download(
            url=url,
            download_folder=folder,
            format_type="audio" if self.format_var.get() == "Audio (MP3)" else "video",
            quality=self.quality_var.get(),
            selected_items=selected_urls,
            on_progress=self._on_download_progress,
            on_complete=self._on_download_complete,
        )

    def _on_download_progress(self, progress: DownloadProgress) -> None:
        """Callback for progress bar and metrics updates."""
        def _update():
            frac = min(1.0, max(0.0, progress.percentage / 100.0))
            self.progress_bar.set(frac)

            self.lbl_percentage.configure(text=f"{progress.percentage:.1f}%")
            self.lbl_size.configure(text=f"{format_bytes(progress.downloaded_bytes)} / {format_bytes(progress.total_bytes)}")
            self.lbl_speed.configure(text=format_speed(progress.speed))
            self.lbl_eta.configure(text=f"ETA: {format_seconds(progress.eta)}")
            self.lbl_status_text.configure(text=progress.status_text)

        self.after(0, _update)

    def _on_download_complete(self, success: bool, message: str) -> None:
        """Callback when download finishes, is cancelled, or errors out."""
        def _finish():
            self.start_btn.configure(state="normal")
            self.pause_btn.configure(state="disabled", text="Pause")
            self.cancel_btn.configure(state="disabled")

            if success:
                self.progress_bar.set(1.0)
                self.lbl_percentage.configure(text="100.0%")
                self.lbl_status_text.configure(text=message, text_color="#10B981")
            else:
                self.lbl_status_text.configure(text=message, text_color="#EF4444")

        self.after(0, _finish)

    def _toggle_pause(self) -> None:
        """Pause or resume download."""
        if self.pause_btn.cget("text") == "Pause":
            self.downloader.pause_download()
            self.pause_btn.configure(text="Resume")
            self.lbl_status_text.configure(text="Download Paused", text_color="#F59E0B")
        else:
            self.downloader.resume_download()
            self.pause_btn.configure(text="Pause")
            self.lbl_status_text.configure(text="Resuming Download...", text_color="#10B981")

    def _cancel_download(self) -> None:
        """Cancel download."""
        self.downloader.cancel_download()
        self.start_btn.configure(state="normal")
        self.pause_btn.configure(state="disabled", text="Pause")
        self.cancel_btn.configure(state="disabled")
        self.lbl_status_text.configure(text="Cancelling download...", text_color="#EF4444")
