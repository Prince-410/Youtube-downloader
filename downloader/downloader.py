import os
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
import yt_dlp

from downloader.playlist import PlaylistInfo, PlaylistManager
from downloader.progress import CancelledException, DownloadProgress, DownloadState, ProgressHook
from utils.config import ConfigManager
from utils.helpers import sanitize_filename
from utils.validators import is_youtube_playlist


@dataclass
class VideoMetadata:
    url: str
    is_playlist: bool
    title: str
    uploader: str
    duration: float
    thumbnail_url: str
    filesize_approx: float
    playlist_info: Optional[PlaylistInfo] = None


class YoutubeDownloader:
    """Core downloading engine interfacing with yt-dlp, managing threads, pause/resume, and cancellation."""

    def __init__(self, config_manager: ConfigManager) -> None:
        self.config_manager = config_manager
        self.cancel_event = threading.Event()
        self.pause_event = threading.Event()
        self.download_thread: Optional[threading.Thread] = None
        self.current_progress = DownloadProgress()
        self.progress_callback: Optional[Callable[[DownloadProgress], None]] = None

    def fetch_info(self, url: str) -> VideoMetadata:
        """Extract metadata for a video or playlist without downloading media."""
        url = url.strip()
        is_playlist = is_youtube_playlist(url)

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "extract_flat": "in_playlist" if is_playlist else False,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    raise ValueError("Unable to retrieve information for the provided URL.")

                if is_playlist or info.get("_type") == "playlist":
                    pl_info = PlaylistManager.extract_playlist_info(url)
                    # Extract first video thumbnail if available
                    thumb_url = ""
                    if pl_info.items:
                        thumb_url = pl_info.items[0].thumbnail_url

                    return VideoMetadata(
                        url=url,
                        is_playlist=True,
                        title=pl_info.title,
                        uploader=pl_info.uploader,
                        duration=sum(item.duration for item in pl_info.items),
                        thumbnail_url=thumb_url,
                        filesize_approx=0.0,
                        playlist_info=pl_info,
                    )
                else:
                    v_title = info.get("title", "YouTube Video")
                    v_uploader = info.get("uploader") or info.get("channel") or "Unknown Channel"
                    v_duration = float(info.get("duration") or 0)

                    # Thumbnail
                    thumbnails = info.get("thumbnails", [])
                    thumb_url = ""
                    if thumbnails:
                        thumb_url = thumbnails[-1].get("url", "")

                    # Estimated filesize
                    filesize = float(info.get("filesize") or info.get("filesize_approx") or 0)

                    return VideoMetadata(
                        url=url,
                        is_playlist=False,
                        title=v_title,
                        uploader=v_uploader,
                        duration=v_duration,
                        thumbnail_url=thumb_url,
                        filesize_approx=filesize,
                        playlist_info=None,
                    )
        except yt_dlp.utils.DownloadError as de:
            err_msg = str(de)
            if "Private video" in err_msg:
                raise ValueError("This video is private and cannot be accessed.")
            elif "Video unavailable" in err_msg:
                raise ValueError("The requested video is unavailable or has been removed.")
            elif "Incomplete YouTube ID" in err_msg or "is not a valid URL" in err_msg:
                raise ValueError("Invalid YouTube URL provided.")
            else:
                raise ValueError(f"Download Error: {err_msg}")
        except Exception as e:
            raise ValueError(f"Failed to extract info: {str(e)}")

    def build_format_string(self, format_type: str, quality: str) -> Dict[str, Any]:
        """Build yt-dlp option dict based on user format and quality choices."""
        opts: Dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "nocheckcertificate": True,
            "ignoreerrors": True,
        }

        if format_type.lower() == "audio":
            audio_bitrate = quality.replace("kbps", "").strip() if "kbps" in quality else "320"
            opts.update(
                {
                    "format": "bestaudio/best",
                    "postprocessors": [
                        {
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": "mp3",
                            "preferredquality": audio_bitrate,
                        }
                    ],
                }
            )
        else:  # Video
            if quality == "Highest Available":
                opts["format"] = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best"
            elif quality == "1080p":
                opts["format"] = "bestvideo[height<=1080][ext=mp4]+bestaudio/best[height<=1080]"
            elif quality == "720p":
                opts["format"] = "bestvideo[height<=720][ext=mp4]+bestaudio/best[height<=720]"
            elif quality == "480p":
                opts["format"] = "bestvideo[height<=480][ext=mp4]+bestaudio/best[height<=480]"
            elif quality == "360p":
                opts["format"] = "bestvideo[height<=360][ext=mp4]+bestaudio/best[height<=360]"
            else:
                opts["format"] = "bestvideo+bestaudio/best"

        return opts

    def start_download(
        self,
        url: str,
        download_folder: str,
        format_type: str,
        quality: str,
        selected_items: Optional[List[str]] = None,
        on_progress: Optional[Callable[[DownloadProgress], None]] = None,
        on_complete: Optional[Callable[[bool, str], None]] = None,
    ) -> None:
        """Launch download in a separate background thread."""
        self.cancel_event.clear()
        self.pause_event.clear()
        self.progress_callback = on_progress

        def _worker():
            try:
                success, msg = self._execute_download(
                    url=url,
                    download_folder=download_folder,
                    format_type=format_type,
                    quality=quality,
                    selected_items=selected_items,
                )
                if on_complete:
                    on_complete(success, msg)
            except Exception as e:
                if on_complete:
                    on_complete(False, f"Unexpected error: {str(e)}")

        self.download_thread = threading.Thread(target=_worker, daemon=True)
        self.download_thread.start()

    def pause_download(self) -> None:
        """Pause ongoing download."""
        self.pause_event.set()

    def resume_download(self) -> None:
        """Resume paused download."""
        self.pause_event.clear()

    def cancel_download(self) -> None:
        """Cancel ongoing download."""
        self.cancel_event.set()
        self.pause_event.clear()

    def _execute_download(
        self,
        url: str,
        download_folder: str,
        format_type: str,
        quality: str,
        selected_items: Optional[List[str]] = None,
    ) -> tuple[bool, str]:
        """Internal download runner."""
        out_dir = Path(download_folder)
        out_dir.mkdir(parents=True, exist_ok=True)

        filename_format = self.config_manager.get("filename_format", "%(title)s.%(ext)s")
        output_template = str(out_dir / filename_format)

        ydl_opts = self.build_format_string(format_type, quality)
        ydl_opts["outtmpl"] = output_template

        progress_hook = ProgressHook(
            callback=self.progress_callback,
            cancel_event=self.cancel_event,
            pause_event=self.pause_event,
        )
        ydl_opts["progress_hooks"] = [progress_hook]

        try:
            # Playlist handling vs Single video
            is_pl = is_youtube_playlist(url)

            if is_pl and selected_items is not None:
                # Target specific playlist items
                total_selected = len(selected_items)
                if total_selected == 0:
                    return False, "No playlist items selected."

                for idx, video_url in enumerate(selected_items, start=1):
                    if self.cancel_event.is_set():
                        return False, "Download cancelled by user."

                    progress_hook.progress.current_item = idx
                    progress_hook.progress.total_items = total_selected
                    progress_hook.progress.status_text = f"Downloading item {idx} of {total_selected}..."

                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(video_url, download=True)
                        if info:
                            self._save_to_history(info, out_dir, format_type, quality)
            else:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    if info:
                        if "entries" in info:
                            for entry in info["entries"]:
                                if entry:
                                    self._save_to_history(entry, out_dir, format_type, quality)
                        else:
                            self._save_to_history(info, out_dir, format_type, quality)

            if self.cancel_event.is_set():
                return False, "Download cancelled."

            return True, "Download completed successfully!"

        except CancelledException:
            return False, "Download cancelled."
        except yt_dlp.utils.DownloadError as de:
            return False, f"Download failed: {str(de)}"
        except Exception as e:
            return False, f"Download error: {str(e)}"

    def _save_to_history(self, info: dict, out_dir: Path, format_type: str, quality: str) -> None:
        """Record completed download entry in persistent history."""
        try:
            title = info.get("title", "Downloaded Video")
            ext = "mp3" if format_type.lower() == "audio" else info.get("ext", "mp4")
            filename = f"{sanitize_filename(title)}.{ext}"
            file_path = str(out_dir / filename)
            size = 0.0
            if Path(file_path).exists():
                size = Path(file_path).stat().st_size
            else:
                size = float(info.get("filesize") or info.get("filesize_approx") or 0)

            history_entry = {
                "title": title,
                "url": info.get("webpage_url") or info.get("url") or "",
                "file_path": file_path,
                "file_size": size,
                "format_type": format_type,
                "quality": quality,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "thumbnail_url": info.get("thumbnail") or "",
            }
            self.config_manager.add_history_entry(history_entry)
        except Exception as e:
            print(f"Error saving to history: {e}")
