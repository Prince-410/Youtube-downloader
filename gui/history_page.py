import os
import subprocess
import sys
from pathlib import Path
import customtkinter as ctk
from utils.config import ConfigManager
from utils.helpers import format_bytes


class HistoryPage(ctk.CTkFrame):
    """History Page displaying record of past downloads with file management options."""

    def __init__(self, parent: ctk.CTkFrame, config_manager: ConfigManager) -> None:
        super().__init__(parent, fg_color="transparent")
        self.config_manager = config_manager

        self._create_widgets()
        self.refresh_history()

    def _create_widgets(self) -> None:
        """Construct history page layout."""
        # Top toolbar frame
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=15, pady=(15, 10))

        title_label = ctk.CTkLabel(
            toolbar,
            text="Download History",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        title_label.pack(side="left")

        clear_btn = ctk.CTkButton(
            toolbar,
            text="Clear History",
            width=110,
            height=32,
            fg_color="#EF4444",
            hover_color="#DC2626",
            command=self._clear_all_history,
        )
        clear_btn.pack(side="right")

        refresh_btn = ctk.CTkButton(
            toolbar,
            text="Refresh",
            width=90,
            height=32,
            fg_color="#3B82F6",
            hover_color="#2563EB",
            command=self.refresh_history,
        )
        refresh_btn.pack(side="right", padx=(0, 10))

        # Scrollable container for history items
        self.history_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.history_scroll.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    def refresh_history(self) -> None:
        """Reload download records from configuration manager."""
        for widget in self.history_scroll.winfo_children():
            widget.destroy()

        history_items = self.config_manager.load_history()

        if not history_items:
            empty_lbl = ctk.CTkLabel(
                self.history_scroll,
                text="No download history found.",
                font=ctk.CTkFont(size=14),
                text_color="gray",
            )
            empty_lbl.pack(pady=40)
            return

        for item in history_items:
            card = ctk.CTkFrame(self.history_scroll, corner_radius=10)
            card.pack(fill="x", pady=5, ipady=8, ipadx=10)

            left_box = ctk.CTkFrame(card, fg_color="transparent")
            left_box.pack(side="left", fill="both", expand=True, padx=10)

            title_txt = item.get("title", "Unknown Title")
            ctk.CTkLabel(
                left_box,
                text=title_txt,
                font=ctk.CTkFont(size=14, weight="bold"),
                anchor="w",
            ).pack(anchor="w")

            fmt = item.get("format_type", "Video")
            quality = item.get("quality", "")
            size_str = format_bytes(item.get("file_size", 0))
            ts = item.get("timestamp", "")
            file_path = item.get("file_path", "")

            details_text = f"Format: {fmt} ({quality})  |  Size: {size_str}  |  Date: {ts}"
            ctk.CTkLabel(
                left_box,
                text=details_text,
                font=ctk.CTkFont(size=11),
                text_color="gray",
                anchor="w",
            ).pack(anchor="w", pady=(2, 0))

            path_lbl = ctk.CTkLabel(
                left_box,
                text=file_path,
                font=ctk.CTkFont(size=10),
                text_color="#64748B",
                anchor="w",
            )
            path_lbl.pack(anchor="w", pady=(2, 0))

            # Action Buttons per item
            btn_box = ctk.CTkFrame(card, fg_color="transparent")
            btn_box.pack(side="right", padx=10)

            open_btn = ctk.CTkButton(
                btn_box,
                text="Open File",
                width=80,
                height=30,
                fg_color="#10B981",
                hover_color="#059669",
                command=lambda p=file_path: self._open_file(p),
            )
            open_btn.pack(side="left", padx=(0, 5))

            folder_btn = ctk.CTkButton(
                btn_box,
                text="Open Folder",
                width=90,
                height=30,
                fg_color="#475569",
                hover_color="#334155",
                command=lambda p=file_path: self._open_folder(p),
            )
            folder_btn.pack(side="left", padx=(0, 5))

            del_btn = ctk.CTkButton(
                btn_box,
                text="X",
                width=30,
                height=30,
                fg_color="#EF4444",
                hover_color="#DC2626",
                command=lambda p=file_path: self._delete_item(p),
            )
            del_btn.pack(side="left")

    def _open_file(self, file_path: str) -> None:
        """Launch file using default operating system association."""
        path = Path(file_path)
        if not path.exists():
            print(f"File not found: {file_path}")
            return
        try:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.run(["open", str(path)])
            else:
                subprocess.run(["xdg-open", str(path)])
        except Exception as e:
            print(f"Error opening file: {e}")

    def _open_folder(self, file_path: str) -> None:
        """Open containing folder in file explorer."""
        path = Path(file_path)
        folder = path.parent if path.exists() else Path(self.config_manager.get("download_location"))
        try:
            if sys.platform == "win32":
                subprocess.run(["explorer", str(folder)])
            elif sys.platform == "darwin":
                subprocess.run(["open", str(folder)])
            else:
                subprocess.run(["xdg-open", str(folder)])
        except Exception as e:
            print(f"Error opening folder: {e}")

    def _delete_item(self, file_path: str) -> None:
        """Remove entry from history records."""
        self.config_manager.remove_history_entry(file_path)
        self.refresh_history()

    def _clear_all_history(self) -> None:
        """Clear all download history."""
        self.config_manager.clear_history()
        self.refresh_history()
