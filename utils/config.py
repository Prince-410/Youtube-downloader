import json
import os
from pathlib import Path
from typing import Any, Dict, List


class ConfigManager:
    """Manages application settings and download history persistent storage."""

    DEFAULT_SETTINGS: Dict[str, Any] = {
        "download_location": str(Path(__file__).parent.parent / "downloads"),
        "preferred_video_quality": "Highest Available",
        "preferred_audio_quality": "320kbps",
        "filename_format": "%(title)s.%(ext)s",
        "theme_mode": "Dark",
    }

    QUALITY_OPTIONS = ["Highest Available", "1080p", "720p", "480p", "360p"]
    AUDIO_QUALITY_OPTIONS = ["320kbps", "256kbps", "192kbps", "128kbps"]

    def __init__(self, base_dir: Path | None = None) -> None:
        if base_dir is None:
            base_dir = Path(__file__).parent.parent
        self.base_dir = Path(base_dir)
        self.config_path = self.base_dir / "config.json"
        self.history_path = self.base_dir / "history.json"
        self._ensure_directories()
        self.settings = self.load_settings()

    def _ensure_directories(self) -> None:
        """Ensure necessary local folders exist."""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        downloads = Path(self.DEFAULT_SETTINGS["download_location"])
        downloads.mkdir(parents=True, exist_ok=True)

    def load_settings(self) -> Dict[str, Any]:
        """Load settings from config.json or create defaults."""
        settings = self.DEFAULT_SETTINGS.copy()
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    settings.update(loaded)
            except Exception as e:
                print(f"Error loading config.json: {e}")

        # Ensure download path exists
        dl_path = Path(settings.get("download_location", self.DEFAULT_SETTINGS["download_location"]))
        dl_path.mkdir(parents=True, exist_ok=True)
        return settings

    def save_settings(self, new_settings: Dict[str, Any] | None = None) -> None:
        """Save settings to config.json."""
        if new_settings is not None:
            self.settings.update(new_settings)

        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config.json: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting by key."""
        return self.settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a setting and save immediately."""
        self.settings[key] = value
        self.save_settings()

    # --- History Management ---

    def load_history(self) -> List[Dict[str, Any]]:
        """Load download history from history.json."""
        if not self.history_path.exists():
            return []
        try:
            with open(self.history_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading history.json: {e}")
            return []

    def add_history_entry(self, entry: Dict[str, Any]) -> None:
        """Add a new entry to download history."""
        history = self.load_history()
        # Remove existing entry with same url/file_path if present
        history = [item for item in history if item.get("file_path") != entry.get("file_path")]
        history.insert(0, entry)  # Prepend newest
        try:
            with open(self.history_path, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving history entry: {e}")

    def remove_history_entry(self, file_path: str) -> None:
        """Remove an entry from history by file path."""
        history = self.load_history()
        history = [item for item in history if item.get("file_path") != file_path]
        try:
            with open(self.history_path, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error removing history entry: {e}")

    def clear_history(self) -> None:
        """Clear all download history."""
        try:
            with open(self.history_path, "w", encoding="utf-8") as f:
                json.dump([], f, indent=4)
        except Exception as e:
            print(f"Error clearing history: {e}")
