"""
Suno Music Downloader & Metadata Engine:
Resolves Suno song links, CDN endpoints, and Next.js page state into high-quality
MP3 audio, MP4 video visualizer, HD album artwork, and song lyrics.
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Optional, Tuple, Callable

from PyQt6.QtCore import QThread, pyqtSignal

# Standard desktop User-Agent to avoid generic automated scraper 403 blocks
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"

# Primary & alternate Suno CDN domains
SUNO_CDN_SERVERS = [
    "https://cdn1.suno.ai",
    "https://cdn2.suno.ai",
]


class SunoLinkParser:
    """Extracts track UUID, CDN media endpoints, and metadata from arbitrary Suno links."""

    UUID_REGEX = re.compile(r"([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})")

    @classmethod
    def extract_uuid(cls, text: str) -> Optional[str]:
        if not text:
            return None
        m = cls.UUID_REGEX.search(text.strip())
        return m.group(1).lower() if m else None

    @classmethod
    def resolve_short_url(cls, url: str) -> str:
        """Resolve short redirect links like https://suno.com/s/... to their canonical URL."""
        if not url:
            return ""
        clean_url = url.strip()
        if not (clean_url.startswith("http://") or clean_url.startswith("https://")):
            clean_url = "https://" + clean_url

        try:
            req = urllib.request.Request(clean_url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=6) as resp:
                return resp.geturl()
        except Exception:
            return clean_url

    @classmethod
    def parse_input(cls, input_text: str) -> Dict:
        """
        Normalize input into structured media candidate URLs.
        Supports:
          - https://suno.com/song/<UUID>
          - https://suno.com/s/<short-id>
          - https://cdn1.suno.ai/<UUID>.mp3 (or .mp4)
          - Raw UUID string
          - Direct MP3/WAV/MP4 URLs
        """
        raw = input_text.strip()
        uuid = cls.extract_uuid(raw)

        # If it's a short URL without UUID, try resolving redirects
        if not uuid and ("suno.com/s/" in raw or "app.suno.ai/s/" in raw):
            resolved = cls.resolve_short_url(raw)
            uuid = cls.extract_uuid(resolved)

        if uuid:
            return {
                "is_suno": True,
                "uuid": uuid,
                "audio_url": f"https://cdn1.suno.ai/{uuid}.mp3",
                "audio_url_alt": f"https://cdn2.suno.ai/{uuid}.mp3",
                "video_url": f"https://cdn1.suno.ai/{uuid}.mp4",
                "image_url": f"https://cdn1.suno.ai/image_{uuid}.png",
                "image_large_url": f"https://cdn1.suno.ai/image_large_{uuid}.png",
                "page_url": f"https://suno.com/song/{uuid}",
            }

        # Direct media URL fallback (e.g. from Udio or generic audio link)
        if raw.startswith("http://") or raw.startswith("https://"):
            lower = raw.lower()
            is_media = any(lower.endswith(ext) or (ext + "?") in lower for ext in [".mp3", ".wav", ".m4a", ".ogg", ".mp4"])
            return {
                "is_suno": False,
                "uuid": None,
                "audio_url": raw if not lower.endswith(".mp4") else "",
                "audio_url_alt": raw,
                "video_url": raw if lower.endswith(".mp4") else "",
                "image_url": "",
                "image_large_url": "",
                "page_url": raw,
            }

        return {}

    @classmethod
    def fetch_metadata(cls, input_text: str) -> Dict:
        """
        Fetch title, style prompt, lyrics, and verified media URLs from Suno's page state.
        Falls back to direct CDN endpoints if page scraping is blocked.
        """
        info = cls.parse_input(input_text)
        if not info:
            return {
                "title": "Unknown Song",
                "artist": "Suno AI",
                "style": "",
                "lyrics": "",
                "audio_url": "",
                "video_url": "",
                "image_url": "",
                "duration": 0,
            }

        meta = {
            "title": f"Suno Song {info['uuid'][:8]}" if info.get("uuid") else "Suno Track",
            "artist": "Suno AI",
            "style": "",
            "lyrics": "",
            "audio_url": info.get("audio_url", ""),
            "video_url": info.get("video_url", ""),
            "image_url": info.get("image_url", ""),
            "duration": 0,
            "uuid": info.get("uuid", ""),
            "page_url": info.get("page_url", ""),
        }

        # If it's a Suno track, attempt to fetch rich metadata from https://suno.com/song/<UUID>
        page_url = info.get("page_url")
        if page_url and info.get("is_suno"):
            try:
                req = urllib.request.Request(page_url, headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(req, timeout=6) as resp:
                    html = resp.read().decode("utf-8", errors="ignore")

                # 1. Parse __NEXT_DATA__ JSON state (most complete source)
                next_m = re.search(r'<script\s+id="__NEXT_DATA__"\s+type="application/json">([^<]+)</script>', html)
                if next_m:
                    try:
                        data = json.loads(next_m.group(1))

                        def _search_clip(node):
                            if isinstance(node, dict):
                                if "audio_url" in node or ("title" in node and "id" in node):
                                    return node
                                for v in node.values():
                                    res = _search_clip(v)
                                    if res:
                                        return res
                            elif isinstance(node, list):
                                for item in node:
                                    res = _search_clip(item)
                                    if res:
                                        return res
                            return None

                        clip = _search_clip(data)
                        if clip:
                            if clip.get("title"):
                                meta["title"] = clip["title"].strip()
                            if clip.get("audio_url"):
                                meta["audio_url"] = clip["audio_url"]
                            if clip.get("video_url"):
                                meta["video_url"] = clip["video_url"]
                            if clip.get("image_url"):
                                meta["image_url"] = clip["image_url"]
                            if clip.get("image_large_url"):
                                meta["image_url"] = clip["image_large_url"]
                            if clip.get("display_name"):
                                meta["artist"] = clip["display_name"].strip()
                            clip_meta = clip.get("metadata", {})
                            if isinstance(clip_meta, dict):
                                if clip_meta.get("tags"):
                                    meta["style"] = clip_meta["tags"].strip()
                                if clip_meta.get("prompt"):
                                    meta["lyrics"] = clip_meta["prompt"].strip()
                                if clip_meta.get("duration"):
                                    meta["duration"] = int(clip_meta["duration"])
                    except Exception:
                        pass

                # 2. OpenGraph Fallbacks if title/lyrics are still missing
                if meta["title"].startswith("Suno Song"):
                    og_title = re.search(r'<meta\s+(?:property|name)="og:title"\s+content="([^"]+)"', html, re.I)
                    if og_title:
                        raw_t = og_title.group(1).replace("| Suno", "").replace("- Suno", "").strip()
                        if raw_t:
                            meta["title"] = raw_t

                if not meta["lyrics"]:
                    og_desc = re.search(r'<meta\s+(?:property|name)="og:description"\s+content="([^"]+)"', html, re.I)
                    if og_desc:
                        desc_txt = og_desc.group(1).strip()
                        if "[" in desc_txt or "\n" in desc_txt or len(desc_txt) > 20:
                            meta["lyrics"] = desc_txt

                if not meta["image_url"]:
                    og_img = re.search(r'<meta\s+(?:property|name)="og:image"\s+content="([^"]+)"', html, re.I)
                    if og_img:
                        meta["image_url"] = og_img.group(1).strip()

            except Exception:
                # If page fetch fails (e.g. offline or blocked), CDN links remain reliable
                pass

        return meta


class SunoDownloadWorker(QThread):
    """
    Background threaded downloader with chunk streaming, percentage progress,
    speed measurement, and automatic multi-CDN failover.
    """

    progress = pyqtSignal(int, int, int, float)  # (percent, downloaded_bytes, total_bytes, speed_kbps)
    status_message = pyqtSignal(str)
    finished = pyqtSignal(bool, str, dict, str)  # (success, file_path, metadata, error_message)

    def __init__(
        self,
        input_url_or_uuid: str,
        media_format: str = "mp3",  # "mp3", "mp4", "png", "pack"
        custom_destination_dir: Optional[str] = None,
        custom_filename: Optional[str] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.input_url = input_url_or_uuid
        self.media_format = media_format.lower()
        self.custom_dest_dir = custom_destination_dir
        self.custom_filename = custom_filename
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    @staticmethod
    def default_download_dir() -> Path:
        d = Path.home() / ".lyric_ai_writer" / "suno_downloads"
        d.mkdir(parents=True, exist_ok=True)
        return d

    @staticmethod
    def sanitize_filename(name: str) -> str:
        # Preserve Khmer Unicode (\u1780-\u17FF), English, digits, hyphens, and spaces
        safe = re.sub(r'[\\/*?:"<>|]', "", name).strip()
        safe = re.sub(r"\s+", " ", safe)
        return safe or "Suno_Song"

    def run(self):
        try:
            self.status_message.emit("🔍 Resolving Suno song link & metadata...")
            metadata = SunoLinkParser.fetch_metadata(self.input_url)
            if self._is_cancelled:
                self.finished.emit(False, "", metadata, "Download cancelled")
                return

            dest_dir = Path(self.custom_dest_dir) if self.custom_dest_dir else self.default_download_dir()
            dest_dir.mkdir(parents=True, exist_ok=True)

            title_clean = self.sanitize_filename(metadata.get("title", "Suno_Song"))
            uuid = metadata.get("uuid", "")
            uuid_short = f"_{uuid[:8]}" if uuid else ""

            # Determine download URLs to try in priority order
            urls_to_try = []
            ext = ".mp3"

            if self.media_format == "mp4":
                ext = ".mp4"
                if metadata.get("video_url"):
                    urls_to_try.append(metadata["video_url"])
                if uuid:
                    urls_to_try.append(f"https://cdn1.suno.ai/{uuid}.mp4")
                    urls_to_try.append(f"https://cdn2.suno.ai/{uuid}.mp4")
            elif self.media_format == "png":
                ext = ".png"
                if metadata.get("image_url"):
                    urls_to_try.append(metadata["image_url"])
                if uuid:
                    urls_to_try.append(f"https://cdn1.suno.ai/image_large_{uuid}.png")
                    urls_to_try.append(f"https://cdn1.suno.ai/image_{uuid}.png")
            else:
                # Default MP3 audio
                ext = ".mp3"
                if metadata.get("audio_url"):
                    urls_to_try.append(metadata["audio_url"])
                if uuid:
                    urls_to_try.append(f"https://cdn1.suno.ai/{uuid}.mp3")
                    urls_to_try.append(f"https://cdn2.suno.ai/{uuid}.mp3")

            if not urls_to_try:
                self.finished.emit(False, "", metadata, "Could not determine a valid download URL for this link.")
                return

            dest_filename = self.custom_filename or f"{title_clean}{uuid_short}{ext}"
            target_path = dest_dir / dest_filename

            # Avoid overwriting existing files by appending counter
            counter = 2
            stem = target_path.stem
            while target_path.exists():
                target_path = dest_dir / f"{stem}_{counter}{ext}"
                counter += 1

            # Attempt download across candidate URLs
            success = False
            last_err = ""

            for idx, dl_url in enumerate(urls_to_try):
                if self._is_cancelled:
                    break
                try:
                    self.status_message.emit(f"⬇️ Downloading from CDN server ({idx + 1}/{len(urls_to_try)})...")
                    success = self._stream_download(dl_url, target_path)
                    if success:
                        break
                except Exception as e:
                    last_err = str(e)
                    continue

            if self._is_cancelled:
                if target_path.exists():
                    try:
                        target_path.unlink()
                    except Exception:
                        pass
                self.finished.emit(False, "", metadata, "Download cancelled by user.")
                return

            if not success or not target_path.exists() or target_path.stat().st_size == 0:
                err_msg = last_err or "Failed to download media file from Suno CDN."
                self.finished.emit(False, "", metadata, err_msg)
                return

            # If Full Pack is requested, also save lyrics and cover artwork alongside MP3
            if self.media_format == "pack":
                self._save_companion_pack(target_path, metadata)

            self.status_message.emit(f"✅ Download complete: {target_path.name}")
            self.finished.emit(True, str(target_path), metadata, "")

        except Exception as e:
            self.finished.emit(False, "", {}, f"Unexpected error: {e}")

    def _stream_download(self, url: str, output_path: Path) -> bool:
        """Download file in 64KB chunks, calculating real-time speed and progress."""
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=12) as response:
            total_size = int(response.headers.get("Content-Length", 0))
            downloaded = 0
            chunk_size = 64 * 1024  # 64 KB

            start_time = time.time()
            last_speed_time = start_time
            last_speed_bytes = 0
            current_speed = 0.0

            with open(output_path, "wb") as f:
                while True:
                    if self._is_cancelled:
                        return False
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)

                    now = time.time()
                    dt = now - last_speed_time
                    if dt >= 0.35:
                        current_speed = ((downloaded - last_speed_bytes) / 1024.0) / dt
                        last_speed_time = now
                        last_speed_bytes = downloaded

                    percent = int((downloaded / total_size) * 100) if total_size > 0 else 50
                    self.progress.emit(percent, downloaded, total_size, current_speed)

        return output_path.exists() and output_path.stat().st_size > 0

    def _save_companion_pack(self, audio_path: Path, metadata: Dict):
        """Save companion lyrics .txt and cover art .png in the same directory."""
        try:
            # 1. Save Lyrics .txt
            lyrics = metadata.get("lyrics", "").strip()
            title = metadata.get("title", audio_path.stem)
            style = metadata.get("style", "")
            uuid = metadata.get("uuid", "")

            txt_content = (
                f"Title: {title}\n"
                f"Suno ID: {uuid}\n"
                f"Style Prompt: {style}\n"
                f"Audio File: {audio_path.name}\n"
                f"{'=' * 50}\n\n"
                f"{lyrics if lyrics else '(No lyrics metadata embedded)'}\n"
            )
            txt_path = audio_path.with_suffix(".txt")
            txt_path.write_text(txt_content, encoding="utf-8")

            # 2. Download companion artwork .png
            img_url = metadata.get("image_url")
            if img_url:
                img_path = audio_path.with_suffix(".png")
                req = urllib.request.Request(img_url, headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(req, timeout=8) as r:
                    img_path.write_bytes(r.read())
        except Exception:
            pass
