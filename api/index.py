"""
YouTube Downloader API — Vercel Serverless Function

Extracts video metadata and direct stream URLs using yt-dlp.
No files are downloaded server-side; the browser handles downloads
directly from YouTube's CDN via the returned stream URLs.
"""

import math
import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import yt_dlp
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="YouTube Downloader API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PUBLIC_DIR = Path(__file__).parent.parent / "public"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_YT_PATTERNS = [r"^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+$"]


def _is_valid_url(url: str) -> bool:
    if not url or not isinstance(url, str):
        return False
    return any(re.match(p, url.strip(), re.IGNORECASE) for p in _YT_PATTERNS)


def _is_playlist(url: str) -> bool:
    if not url:
        return False
    parsed = urlparse(url.strip())
    if "playlist" in parsed.path.lower():
        return True
    qp = parse_qs(parsed.query)
    if "list" in qp:
        list_id = qp["list"][0]
        if list_id and not list_id.startswith("RD"):
            return True
    return False


def _fmt_bytes(n: float | None) -> str:
    if n is None or n <= 0:
        return "Unknown"
    names = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(n, 1024)))
    i = min(i, len(names) - 1)
    return f"{round(n / 1024**i, 2)} {names[i]}"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/api/info")
async def get_video_info(
    url: str = Query(..., description="YouTube video or playlist URL"),
):
    """Return metadata and direct stream URLs for a YouTube video or playlist."""
    url = url.strip()

    if not _is_valid_url(url):
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "Invalid YouTube URL."},
        )

    is_pl = _is_playlist(url)

    try:
        if is_pl:
            return await _handle_playlist(url)
        return await _handle_single(url)

    except yt_dlp.utils.DownloadError as de:
        msg = str(de)
        if "Private video" in msg:
            error = "This video is private and cannot be accessed."
        elif "Video unavailable" in msg:
            error = "This video is unavailable or has been removed."
        elif "Incomplete YouTube ID" in msg or "is not a valid URL" in msg:
            error = "Invalid YouTube URL provided."
        else:
            error = f"Could not process video: {msg}"
        return JSONResponse(
            status_code=400, content={"success": False, "error": error}
        )
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Server error: {exc}"},
        )


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "YouTube Downloader API"}


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = PUBLIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return HTMLResponse("<h1>YouTube Downloader Web App</h1>")


if PUBLIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(PUBLIC_DIR), html=True), name="static")



# ---------------------------------------------------------------------------
# Internal handlers
# ---------------------------------------------------------------------------


async def _handle_playlist(url: str) -> dict:
    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": True,
        "ignoreerrors": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if not info:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Unable to retrieve playlist information.",
                },
            )

        items = []
        for idx, entry in enumerate(info.get("entries", []), 1):
            if not entry:
                continue
            v_id = entry.get("id", "")
            thumbs = entry.get("thumbnails", [])
            thumb = (
                thumbs[-1].get("url", "")
                if thumbs
                else (
                    f"https://i.ytimg.com/vi/{v_id}/hqdefault.jpg" if v_id else ""
                )
            )
            items.append(
                {
                    "index": idx,
                    "video_id": v_id,
                    "title": entry.get("title", f"Video {idx}"),
                    "duration": float(entry.get("duration") or 0),
                    "thumbnail": thumb,
                    "url": entry.get("url")
                    or f"https://www.youtube.com/watch?v={v_id}",
                }
            )

        return {
            "success": True,
            "data": {
                "title": info.get("title", "Playlist"),
                "uploader": info.get("uploader")
                or info.get("channel")
                or "Unknown Channel",
                "is_playlist": True,
                "total_count": len(items),
                "duration": sum(i["duration"] for i in items),
                "thumbnail": items[0]["thumbnail"] if items else "",
                "playlist_items": items,
                "formats": [],
                "audio_formats": [],
            },
        }


async def _handle_single(url: str) -> dict:
    opts = {"quiet": True, "no_warnings": True, "skip_download": True}

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if not info:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Unable to retrieve video information.",
                },
            )

        video_fmts: list[dict] = []
        audio_fmts: list[dict] = []
        best_audio: dict | None = None

        for f in info.get("formats", []):
            f_url = f.get("url", "")
            if not f_url:
                continue

            vcodec = f.get("vcodec") or "none"
            acodec = f.get("acodec") or "none"
            has_v = vcodec != "none"
            has_a = acodec != "none"
            height = f.get("height")
            abr = f.get("abr") or 0
            filesize = f.get("filesize") or f.get("filesize_approx") or 0

            if has_v and has_a:
                q = f"{height}p" if height else "Unknown"
                video_fmts.append(
                    {
                        "format_id": f.get("format_id", ""),
                        "ext": f.get("ext", "mp4"),
                        "quality": q,
                        "height": height or 0,
                        "filesize": filesize,
                        "filesize_str": _fmt_bytes(filesize),
                        "url": f_url,
                        "type": "video+audio",
                        "note": f.get("format_note", ""),
                    }
                )
            elif has_a and not has_v:
                q = f"{int(abr)}kbps" if abr else "Unknown"
                entry = {
                    "format_id": f.get("format_id", ""),
                    "ext": f.get("ext", "webm"),
                    "quality": q,
                    "abr": abr,
                    "filesize": filesize,
                    "filesize_str": _fmt_bytes(filesize),
                    "url": f_url,
                    "type": "audio",
                    "note": f.get("format_note", ""),
                }
                audio_fmts.append(entry)
                if best_audio is None or abr > (best_audio.get("abr") or 0):
                    best_audio = entry

        # De-duplicate by quality label, keeping the largest file per quality
        video_fmts.sort(key=lambda x: x.get("height", 0), reverse=True)
        seen_vq: set[str] = set()
        unique_video = []
        for vf in video_fmts:
            if vf["quality"] not in seen_vq:
                seen_vq.add(vf["quality"])
                unique_video.append(vf)

        audio_fmts.sort(key=lambda x: x.get("abr", 0), reverse=True)
        seen_aq: set[str] = set()
        unique_audio = []
        for af in audio_fmts:
            if af["quality"] not in seen_aq:
                seen_aq.add(af["quality"])
                unique_audio.append(af)

        # Thumbnail
        thumbs = info.get("thumbnails", [])
        thumb = thumbs[-1].get("url", "") if thumbs else ""

        return {
            "success": True,
            "data": {
                "title": info.get("title", "YouTube Video"),
                "uploader": info.get("uploader")
                or info.get("channel")
                or "Unknown Channel",
                "duration": float(info.get("duration") or 0),
                "thumbnail": thumb,
                "is_playlist": False,
                "filesize_approx": float(
                    info.get("filesize") or info.get("filesize_approx") or 0
                ),
                "formats": unique_video,
                "audio_formats": unique_audio,
                "best_audio": best_audio,
                "playlist_items": None,
            },
        }
