from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import yt_dlp


@dataclass
class PlaylistItem:
    index: int
    video_id: str
    title: str
    duration: float = 0.0
    thumbnail_url: str = ""
    url: str = ""
    selected: bool = True


@dataclass
class PlaylistInfo:
    title: str = "Playlist"
    uploader: str = "Unknown Channel"
    total_count: int = 0
    items: List[PlaylistItem] = field(default_factory=list)


class PlaylistManager:
    """Utility for extracting and handling YouTube playlist metadata."""

    @staticmethod
    def extract_playlist_info(url: str) -> PlaylistInfo:
        """Extract playlist entries without downloading media content."""
        ydl_opts = {
            "extract_flat": True,
            "skip_download": True,
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                raise ValueError("Could not extract playlist info.")

            title = info.get("title", "Playlist")
            uploader = info.get("uploader") or info.get("channel") or "Unknown Channel"
            entries = info.get("entries", [])

            items: List[PlaylistItem] = []
            idx = 1
            for entry in entries:
                if not entry:
                    continue

                v_id = entry.get("id", "")
                v_title = entry.get("title", f"Video {idx}")
                v_duration = float(entry.get("duration") or 0)
                v_url = entry.get("url") or f"https://www.youtube.com/watch?v={v_id}"

                # Thumbnails extraction
                thumbnails = entry.get("thumbnails", [])
                thumb_url = ""
                if thumbnails:
                    thumb_url = thumbnails[-1].get("url", "")
                elif v_id:
                    thumb_url = f"https://i.ytimg.com/vi/{v_id}/hqdefault.jpg"

                items.append(
                    PlaylistItem(
                        index=idx,
                        video_id=v_id,
                        title=v_title,
                        duration=v_duration,
                        thumbnail_url=thumb_url,
                        url=v_url,
                        selected=True,
                    )
                )
                idx += 1

            return PlaylistInfo(
                title=title,
                uploader=uploader,
                total_count=len(items),
                items=items,
            )
