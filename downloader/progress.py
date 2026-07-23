import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional, Any


class DownloadState(str, Enum):
    IDLE = "idle"
    FETCHING = "fetching"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


@dataclass
class DownloadProgress:
    status: DownloadState = DownloadState.IDLE
    filename: str = ""
    percentage: float = 0.0
    downloaded_bytes: float = 0.0
    total_bytes: float = 0.0
    speed: float = 0.0
    eta: float = 0.0
    current_item: int = 1
    total_items: int = 1
    status_text: str = ""
    error_message: str = ""


class CancelledException(Exception):
    """Exception raised when user requests download cancellation."""
    pass


class ProgressHook:
    """yt-dlp progress hook adapter handling pause, cancel, and UI updates."""

    def __init__(
        self,
        callback: Optional[Callable[[DownloadProgress], None]] = None,
        cancel_event: Optional[Any] = None,
        pause_event: Optional[Any] = None,
    ) -> None:
        self.callback = callback
        self.cancel_event = cancel_event
        self.pause_event = pause_event
        self.progress = DownloadProgress()

    def __call__(self, d: dict) -> None:
        # Check cancellation
        if self.cancel_event and self.cancel_event.is_set():
            self.progress.status = DownloadState.CANCELLED
            self.progress.status_text = "Download cancelled"
            if self.callback:
                self.callback(self.progress)
            raise CancelledException("User cancelled the download.")

        # Handle Pause logic
        if self.pause_event and self.pause_event.is_set():
            self.progress.status = DownloadState.PAUSED
            self.progress.status_text = "Download paused"
            if self.callback:
                self.callback(self.progress)

            while self.pause_event.is_set():
                if self.cancel_event and self.cancel_event.is_set():
                    self.progress.status = DownloadState.CANCELLED
                    self.progress.status_text = "Download cancelled"
                    if self.callback:
                        self.callback(self.progress)
                    raise CancelledException("User cancelled the download.")
                time.sleep(0.2)

            # Resumed
            self.progress.status = DownloadState.DOWNLOADING
            self.progress.status_text = "Downloading..."

        status_str = d.get("status", "")
        if status_str == "downloading":
            downloaded = float(d.get("downloaded_bytes", 0))
            total = float(d.get("total_bytes") or d.get("total_bytes_estimate") or 0)
            speed = float(d.get("speed") or 0)
            eta = float(d.get("eta") or 0)
            filename = d.get("filename", "")

            percentage = 0.0
            if total > 0:
                percentage = min(100.0, (downloaded / total) * 100.0)
            elif "_percent_str" in d:
                try:
                    clean_pct = d["_percent_str"].replace("%", "").strip()
                    percentage = float(clean_pct)
                except ValueError:
                    percentage = 0.0

            self.progress.status = DownloadState.DOWNLOADING
            self.progress.filename = filename
            self.progress.downloaded_bytes = downloaded
            self.progress.total_bytes = total
            self.progress.percentage = percentage
            self.progress.speed = speed
            self.progress.eta = eta
            self.progress.status_text = f"Downloading... {percentage:.1f}%"

            if self.callback:
                self.callback(self.progress)

        elif status_str == "finished":
            self.progress.percentage = 100.0
            self.progress.status = DownloadState.COMPLETED
            self.progress.status_text = "Processing finished..."
            if self.callback:
                self.callback(self.progress)
