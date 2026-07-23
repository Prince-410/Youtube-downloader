import io
import math
import re
from pathlib import Path
from typing import Optional, Tuple
import requests
from PIL import Image


def format_bytes(size_bytes: Optional[float]) -> str:
    """Format byte count into human-readable string (KB, MB, GB)."""
    if size_bytes is None or size_bytes <= 0:
        return "0 B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    if i >= len(size_name):
        i = len(size_name) - 1
    return f"{s} {size_name[i]}"


def format_seconds(seconds: Optional[float]) -> str:
    """Format duration in seconds to HH:MM:SS or MM:SS format."""
    if seconds is None or seconds < 0:
        return "00:00"
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def format_speed(bytes_per_sec: Optional[float]) -> str:
    """Format transfer speed into human-readable string per second."""
    if bytes_per_sec is None or bytes_per_sec <= 0:
        return "0 KB/s"
    return f"{format_bytes(bytes_per_sec)}/s"


def sanitize_filename(filename: str) -> str:
    """Remove illegal characters from string to make it safe for OS filesystem."""
    return re.sub(r'[\\/*?:"<>|]', "", filename).strip()


def fetch_thumbnail_image(url: str, size: Tuple[int, int] = (200, 112)) -> Optional[Image.Image]:
    """Fetch thumbnail image from URL and return a PIL Image object."""
    if not url:
        return None
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        response = requests.get(url, headers=headers, timeout=8)
        if response.status_code == 200:
            img = Image.open(io.BytesIO(response.content))
            img.thumbnail(size, Image.Resampling.LANCZOS)
            return img
    except Exception as e:
        print(f"Error fetching thumbnail image from {url}: {e}")
    return None
