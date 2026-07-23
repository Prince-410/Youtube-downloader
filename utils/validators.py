import re
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import parse_qs, urlparse


YOUTUBE_URL_PATTERNS = [
    r"^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+$",
]


def is_valid_url(url: str) -> bool:
    """Check if the provided string is a valid YouTube URL."""
    if not url or not isinstance(url, str):
        return False
    url = url.strip()
    return any(re.match(pattern, url, re.IGNORECASE) for pattern in YOUTUBE_URL_PATTERNS)


def is_youtube_playlist(url: str) -> bool:
    """Determine whether a YouTube URL points to a playlist or single video."""
    if not url:
        return False
    parsed = urlparse(url.strip())
    query_params = parse_qs(parsed.query)

    # Path check (e.g. /playlist?list=...)
    if "playlist" in parsed.path.lower():
        return True

    # Query param check (has 'list' parameter and doesn't explicitly target single video context only)
    if "list" in query_params:
        # Check if list parameter looks like a playlist ID (not RD/watch mix radio or channel mix)
        list_id = query_params["list"][0]
        if list_id and not list_id.startswith("RD"):
            return True
    return False


def is_duplicate_download(destination_dir: str | Path, expected_filename: str, history: List[Dict[str, Any]]) -> bool:
    """Check if a file has already been downloaded in history or exists in target folder."""
    dest_path = Path(destination_dir) / expected_filename
    if dest_path.exists():
        return True

    for entry in history:
        if entry.get("file_path") == str(dest_path):
            return True

    return False


def is_directory_writable(path: str | Path) -> bool:
    """Check if target directory exists and is writable."""
    try:
        p = Path(path)
        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)
        test_file = p / ".write_test"
        test_file.touch()
        test_file.unlink()
        return True
    except Exception:
        return False
