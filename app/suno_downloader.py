"""
Suno Music Downloader & Local Conversion Engine:
Inspired by UseSuno (usesuno.com/tools/downloader).
Downloads any public Suno Song, Hook, or Playlist as MP3, Lossless Studio WAV,
Original raw audio stream, MP4 Video Visualizer, HD Cover Artwork, or Full Production ZIP.
All decryption, audio decoding, and format conversion completes 100% locally in-app.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request
import urllib.error
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Callable

from PyQt6.QtCore import QThread, pyqtSignal

# Standard desktop User-Agent to avoid generic scraper blocks
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"

# Primary & alternate Suno CDN domains
SUNO_CDN_SERVERS = [
    "https://cdn1.suno.ai",
    "https://cdn2.suno.ai",
]


class SunoAudioConverter:
    """Handles local audio conversion (MP3 -> Lossless PCM WAV) and Production ZIP packaging."""

    _cached_ffmpeg: Optional[str] = None

    @classmethod
    def get_ffmpeg_path(cls) -> Optional[str]:
        if cls._cached_ffmpeg and os.path.exists(cls._cached_ffmpeg):
            return cls._cached_ffmpeg

        # 1. Try PyInstaller frozen bundle directory
        if getattr(sys, "frozen", False):
            try:
                from app.config import get_resource_dir
                for base in [Path(getattr(sys, "_MEIPASS", "")), get_resource_dir()]:
                    if not base or not base.exists():
                        continue
                    for cand in [
                        base / "imageio_ffmpeg" / "binaries" / "ffmpeg.exe",
                        base / "imageio_ffmpeg" / "binaries" / "ffmpeg-win-x86_64-v7.1.exe",
                        base / "ffmpeg.exe",
                    ]:
                        if cand.exists():
                            cls._cached_ffmpeg = str(cand)
                            return str(cand)
            except Exception:
                pass

        # 2. Try bundled imageio-ffmpeg
        try:
            import imageio_ffmpeg
            exe = imageio_ffmpeg.get_ffmpeg_exe()
            if exe and os.path.exists(exe):
                cls._cached_ffmpeg = exe
                return exe
        except Exception:
            pass

        # 3. Try system PATH
        sys_ffmpeg = shutil.which("ffmpeg")
        if sys_ffmpeg:
            cls._cached_ffmpeg = sys_ffmpeg
            return sys_ffmpeg

        return None

    @classmethod
    def convert_to_wav(
        cls,
        source_audio_path: str,
        target_wav_path: str,
        sample_rate: int = 44100,
        bit_depth: int = 16,
    ) -> bool:
        """
        Convert source MP3/M4A/audio into lossless PCM WAV locally.
        Uses bundled FFmpeg with fallback to soundfile.
        """
        src = Path(source_audio_path)
        dst = Path(target_wav_path)
        if not src.exists() or src.stat().st_size == 0:
            return False

        ffmpeg = cls.get_ffmpeg_path()
        if ffmpeg:
            try:
                codec = "pcm_s16le" if bit_depth == 16 else "pcm_s24le"
                cmd = [
                    ffmpeg, "-y",
                    "-i", str(src),
                    "-acodec", codec,
                    "-ar", str(sample_rate),
                    "-ac", "2",
                    str(dst)
                ]
                res = subprocess.run(cmd, capture_output=True, timeout=30)
                if res.returncode == 0 and dst.exists() and dst.stat().st_size > 0:
                    return True
            except Exception:
                pass

        # Fallback using soundfile if available
        try:
            import soundfile as sf
            data, sr = sf.read(str(src))
            subtype = "PCM_16" if bit_depth == 16 else "PCM_24"
            sf.write(str(dst), data, sr, subtype=subtype)
            return dst.exists() and dst.stat().st_size > 0
        except Exception:
            pass

        return False

    @classmethod
    def create_production_zip(
        cls,
        output_zip_path: str,
        assets: Dict[str, str],  # {"mp3": path, "wav": path, "mp4": path, "png": path, "txt": path, "lrc": path, "json": path}
        metadata: Dict,
    ) -> str:
        """Create a complete studio production bundle (.zip) with all generated assets."""
        zip_p = Path(output_zip_path)
        zip_p.parent.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_p, "w", zipfile.ZIP_DEFLATED) as zf:
            for kind, f_path in assets.items():
                if f_path and os.path.exists(f_path):
                    p = Path(f_path)
                    zf.write(p, arcname=p.name)

            # Ensure metadata JSON is included
            meta_json = json.dumps(metadata, indent=2, ensure_ascii=False)
            zf.writestr("Track_Metadata.json", meta_json)

        return str(zip_p)


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
    def extract_all_uuids(cls, text: str, max_limit: Optional[int] = None) -> List[str]:
        """Extract multiple unique Suno UUIDs for bulk downloading (unlimited when max_limit is None)."""
        if not text:
            return []
        matches = cls.UUID_REGEX.findall(text)
        seen = set()
        result = []
        for uid in matches:
            u_clean = uid.lower()
            if u_clean not in seen:
                seen.add(u_clean)
                result.append(u_clean)
                if max_limit is not None and max_limit > 0 and len(result) >= max_limit:
                    break
        return result

    @classmethod
    def detect_track_type(cls, text: str) -> str:
        """Detect whether input is a Suno Song, Hook, Playlist, or Direct CDN link."""
        raw = text.lower()
        if "/hook/" in raw or "hook" in raw:
            return "Hook"
        if "/playlist/" in raw:
            return "Playlist"
        if "cdn1.suno.ai" in raw or "cdn2.suno.ai" in raw:
            return "Direct CDN"
        return "Song"

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
          - https://suno.com/hook/<UUID>
          - https://suno.com/playlist/<UUID>
          - https://suno.com/s/<short-id>
          - https://cdn1.suno.ai/<UUID>.mp3 (or .mp4)
          - Raw UUID string
          - Direct MP3/WAV/MP4 URLs
        """
        raw = input_text.strip()
        track_type = cls.detect_track_type(raw)
        uuid = cls.extract_uuid(raw)

        # If it's a short URL without UUID, try resolving redirects
        if not uuid and ("suno.com/s/" in raw or "app.suno.ai/s/" in raw):
            resolved = cls.resolve_short_url(raw)
            uuid = cls.extract_uuid(resolved)
            track_type = cls.detect_track_type(resolved)

        if uuid:
            return {
                "is_suno": True,
                "track_type": track_type,
                "uuid": uuid,
                "audio_url": f"https://cdn1.suno.ai/{uuid}.mp3",
                "audio_url_alt": f"https://cdn2.suno.ai/{uuid}.mp3",
                "video_url": f"https://cdn1.suno.ai/{uuid}.mp4",
                "image_url": f"https://cdn1.suno.ai/image_{uuid}.png",
                "image_large_url": f"https://cdn1.suno.ai/image_large_{uuid}.png",
                "page_url": f"https://suno.com/{'hook' if track_type == 'Hook' else 'song'}/{uuid}",
            }

        # Direct media URL fallback (e.g. from Udio or generic audio link)
        if raw.startswith("http://") or raw.startswith("https://"):
            lower = raw.lower()
            return {
                "is_suno": False,
                "track_type": "Direct Media",
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
        Fetch title, style prompt, lyrics, duration, and verified media URLs from Suno's page state.
        Falls back to direct CDN endpoints if page scraping is blocked.
        """
        info = cls.parse_input(input_text)
        if not info:
            return {
                "title": "Unknown Song",
                "artist": "Suno AI",
                "track_type": "Song",
                "style": "",
                "lyrics": "",
                "audio_url": "",
                "video_url": "",
                "image_url": "",
                "duration": 0,
                "duration_str": "0:00",
                "model_version": "v4",
            }

        meta = {
            "title": f"Suno {info.get('track_type', 'Song')} {info['uuid'][:8]}" if info.get("uuid") else "Suno Track",
            "artist": "Suno AI",
            "track_type": info.get("track_type", "Song"),
            "style": "",
            "lyrics": "",
            "audio_url": info.get("audio_url", ""),
            "video_url": info.get("video_url", ""),
            "image_url": info.get("image_url", ""),
            "duration": 0,
            "duration_str": "0:00",
            "model_version": "v4",
            "uuid": info.get("uuid", ""),
            "page_url": info.get("page_url", ""),
        }

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
                            if clip.get("major_model_version"):
                                meta["model_version"] = clip["major_model_version"]

                            clip_meta = clip.get("metadata", {})
                            if isinstance(clip_meta, dict):
                                if clip_meta.get("tags"):
                                    meta["style"] = clip_meta["tags"].strip()
                                if clip_meta.get("prompt"):
                                    meta["lyrics"] = clip_meta["prompt"].strip()
                                if clip_meta.get("duration"):
                                    dur = float(clip_meta["duration"])
                                    meta["duration"] = int(dur)
                                    mins = int(dur // 60)
                                    secs = int(dur % 60)
                                    meta["duration_str"] = f"{mins}:{secs:02d}"
                    except Exception:
                        pass

                # 2. OpenGraph Fallbacks if title/lyrics are still missing
                if meta["title"].startswith("Suno "):
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
                pass

        return meta

    @classmethod
    def fetch_playlist_tracks(cls, playlist_url: str) -> List[Dict]:
        """Fetch all track clips from a Suno playlist or album URL."""
        uuid = cls.extract_uuid(playlist_url)
        clean_url = playlist_url if playlist_url.startswith("http") else f"https://suno.com/playlist/{uuid}"
        tracks = []
        try:
            req = urllib.request.Request(clean_url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=8) as resp:
                html = resp.read().decode("utf-8", errors="ignore")

            # Extract from __NEXT_DATA__
            next_m = re.search(r'<script\s+id="__NEXT_DATA__"\s+type="application/json">([^<]+)</script>', html)
            if next_m:
                d = json.loads(next_m.group(1))

                def _find_playlist_clips(node):
                    if isinstance(node, dict):
                        if "playlist_clips" in node and isinstance(node["playlist_clips"], list):
                            return node["playlist_clips"]
                        for v in node.values():
                            res = _find_playlist_clips(v)
                            if res:
                                return res
                    elif isinstance(node, list):
                        for item in node:
                            res = _find_playlist_clips(item)
                            if res:
                                return res
                    return None

                clips = _find_playlist_clips(d)
                if clips:
                    for clip_wrap in clips:
                        c = clip_wrap.get("clip") if isinstance(clip_wrap, dict) and "clip" in clip_wrap else clip_wrap
                        if isinstance(c, dict) and c.get("id"):
                            c_id = c["id"]
                            c_meta = c.get("metadata", {})
                            dur = float(c_meta.get("duration", 0))
                            tracks.append({
                                "uuid": c_id,
                                "title": c.get("title") or f"Track {len(tracks) + 1}",
                                "artist": c.get("display_name") or "Suno AI",
                                "style": c_meta.get("tags", ""),
                                "lyrics": c_meta.get("prompt", ""),
                                "audio_url": c.get("audio_url") or f"https://cdn1.suno.ai/{c_id}.mp3",
                                "video_url": c.get("video_url") or f"https://cdn1.suno.ai/{c_id}.mp4",
                                "image_url": c.get("image_url") or f"https://cdn1.suno.ai/image_{c_id}.png",
                                "duration_str": f"{int(dur // 60)}:{int(dur % 60):02d}",
                            })
        except Exception:
            pass

        # Fallback: regex search for all UUIDs in the page
        if not tracks:
            all_uids = cls.extract_all_uuids(playlist_url)
            for uid in all_uids:
                tracks.append(cls.fetch_metadata(uid))

        return tracks


class SunoDownloadWorker(QThread):
    """
    Background threaded downloader with chunk streaming, percentage progress,
    speed measurement, automatic multi-CDN failover, and local WAV/ZIP conversions.
    """

    progress = pyqtSignal(int, int, int, float)  # (percent, downloaded_bytes, total_bytes, speed_kbps)
    status_message = pyqtSignal(str)
    finished = pyqtSignal(bool, str, dict, str)  # (success, file_path, metadata, error_message)

    def __init__(
        self,
        input_url_or_uuid: str,
        media_format: str = "mp3",  # "mp3", "wav", "original", "mp4", "png", "lyrics", "pack", "zip"
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
        safe = re.sub(r'[\\/*?:"<>|]', "", name).strip()
        safe = re.sub(r"\s+", " ", safe)
        return safe or "Suno_Song"

    def run(self):
        try:
            self.status_message.emit("🔍 Resolving Suno link & metadata...")
            metadata = SunoLinkParser.fetch_metadata(self.input_url)
            if self._is_cancelled:
                self.finished.emit(False, "", metadata, "Download cancelled")
                return

            dest_dir = Path(self.custom_dest_dir) if self.custom_dest_dir else self.default_download_dir()
            dest_dir.mkdir(parents=True, exist_ok=True)

            title_clean = self.sanitize_filename(metadata.get("title", "Suno_Song"))
            uuid = metadata.get("uuid", "")
            uuid_short = f"_{uuid[:8]}" if uuid else ""

            # Handle Lyrics only export
            if self.media_format == "lyrics":
                txt_path = dest_dir / f"{title_clean}{uuid_short}.txt"
                lyrics = metadata.get("lyrics", "").strip() or "(No lyrics metadata found)"
                txt_content = (
                    f"Title: {metadata.get('title')}\n"
                    f"Artist: {metadata.get('artist')}\n"
                    f"Style Tags: {metadata.get('style')}\n"
                    f"Suno ID: {uuid}\n"
                    f"{'=' * 50}\n\n"
                    f"{lyrics}\n"
                )
                txt_path.write_text(txt_content, encoding="utf-8")
                self.finished.emit(True, str(txt_path), metadata, "")
                return

            # Determine primary media URLs to download
            urls_to_try = []
            target_ext = ".mp3"

            if self.media_format == "mp4":
                target_ext = ".mp4"
                if metadata.get("video_url"):
                    urls_to_try.append(metadata["video_url"])
                if uuid:
                    urls_to_try.append(f"https://cdn1.suno.ai/{uuid}.mp4")
                    urls_to_try.append(f"https://cdn2.suno.ai/{uuid}.mp4")
            elif self.media_format == "png":
                target_ext = ".png"
                if metadata.get("image_url"):
                    urls_to_try.append(metadata["image_url"])
                if uuid:
                    urls_to_try.append(f"https://cdn1.suno.ai/image_large_{uuid}.png")
                    urls_to_try.append(f"https://cdn1.suno.ai/image_{uuid}.png")
            else:
                # Audio (MP3, WAV, Original, Pack)
                target_ext = ".mp3"
                if metadata.get("audio_url"):
                    urls_to_try.append(metadata["audio_url"])
                if uuid:
                    urls_to_try.append(f"https://cdn1.suno.ai/{uuid}.mp3")
                    urls_to_try.append(f"https://cdn2.suno.ai/{uuid}.mp3")

            if not urls_to_try:
                self.finished.emit(False, "", metadata, "Could not determine a valid download endpoint for this link.")
                return

            dest_filename = self.custom_filename or f"{title_clean}{uuid_short}{target_ext}"
            target_path = dest_dir / dest_filename

            counter = 2
            stem = target_path.stem
            while target_path.exists():
                target_path = dest_dir / f"{stem}_{counter}{target_ext}"
                counter += 1

            # Download stream
            success = False
            last_err = ""
            for idx, dl_url in enumerate(urls_to_try):
                if self._is_cancelled:
                    break
                try:
                    self.status_message.emit(f"⬇️ Streaming from Suno CDN ({idx + 1}/{len(urls_to_try)})...")
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
                self.finished.emit(False, "", metadata, last_err or "Failed to stream audio file from Suno CDN.")
                return

            final_output_path = str(target_path)

            # Local Conversion: Lossless Studio WAV
            if self.media_format == "wav":
                self.status_message.emit("🎚️ Converting to Lossless Studio WAV (PCM 44.1kHz)...")
                wav_path = target_path.with_suffix(".wav")
                conv_ok = SunoAudioConverter.convert_to_wav(str(target_path), str(wav_path))
                if conv_ok and wav_path.exists():
                    final_output_path = str(wav_path)
                    # Optionally remove intermediate mp3
                    try:
                        target_path.unlink()
                    except Exception:
                        pass
                else:
                    self.status_message.emit("⚠️ WAV conversion unavailable; saved as high-quality MP3.")

            # Local Production Bundle: ZIP
            elif self.media_format in ("pack", "zip"):
                self.status_message.emit("📦 Compiling Full Production Bundle (ZIP)...")
                wav_path = target_path.with_suffix(".wav")
                SunoAudioConverter.convert_to_wav(str(target_path), str(wav_path))

                # Download companion artwork & lyrics
                txt_path = target_path.with_suffix(".txt")
                txt_content = (
                    f"Title: {metadata.get('title')}\n"
                    f"Artist: {metadata.get('artist')}\n"
                    f"Style: {metadata.get('style')}\n"
                    f"Suno ID: {uuid}\n"
                    f"{'=' * 50}\n\n"
                    f"{metadata.get('lyrics', '')}\n"
                )
                txt_path.write_text(txt_content, encoding="utf-8")

                png_path = target_path.with_suffix(".png")
                if metadata.get("image_url"):
                    try:
                        req = urllib.request.Request(metadata["image_url"], headers={"User-Agent": USER_AGENT})
                        with urllib.request.urlopen(req, timeout=8) as r:
                            png_path.write_bytes(r.read())
                    except Exception:
                        pass

                zip_out = target_path.with_suffix(".zip")
                assets = {
                    "mp3": str(target_path) if target_path.exists() else "",
                    "wav": str(wav_path) if wav_path.exists() else "",
                    "txt": str(txt_path) if txt_path.exists() else "",
                    "png": str(png_path) if png_path.exists() else "",
                }
                zip_res = SunoAudioConverter.create_production_zip(str(zip_out), assets, metadata)
                final_output_path = zip_res

            self.status_message.emit(f"✅ Ready: {Path(final_output_path).name}")
            self.finished.emit(True, final_output_path, metadata, "")

        except Exception as e:
            self.finished.emit(False, "", {}, f"Unexpected error: {e}")

    def _stream_download(self, url: str, output_path: Path) -> bool:
        """Download file in 64KB chunks, calculating real-time speed and progress."""
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=12) as response:
            total_size = int(response.headers.get("Content-Length", 0))
            downloaded = 0
            chunk_size = 64 * 1024

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


class SunoBulkDownloadWorker(QThread):
    """Processes a batch queue of Suno links (up to 20 tracks or playlist)."""

    track_started = pyqtSignal(int, int, str)  # (current_idx, total_count, url)
    track_progress = pyqtSignal(int, int, int, float)  # (track_idx, total_tracks, percent, speed_kbps)
    track_finished = pyqtSignal(int, bool, str, dict, str)  # (track_idx, success, path, metadata, err)
    batch_finished = pyqtSignal(int, int, list)  # (success_count, fail_count, saved_paths)

    def __init__(
        self,
        urls: List[str],
        media_format: str = "mp3",
        destination_dir: Optional[str] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.urls = list(urls)  # Unlimited track queue (no monthly download caps)
        self.media_format = media_format
        self.dest_dir = destination_dir or str(SunoDownloadWorker.default_download_dir())
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        success_count = 0
        fail_count = 0
        saved_paths = []
        total = len(self.urls)

        for i, url in enumerate(self.urls):
            if self._is_cancelled:
                break
            self.track_started.emit(i + 1, total, url)

            worker = SunoDownloadWorker(
                input_url_or_uuid=url,
                media_format=self.media_format,
                custom_destination_dir=self.dest_dir,
            )

            res_ok = False
            res_path = ""
            res_meta = {}
            res_err = ""

            def _on_prog(pct, cur, tot, spd):
                self.track_progress.emit(i + 1, total, pct, spd)

            def _on_done(ok, p, m, e):
                nonlocal res_ok, res_path, res_meta, res_err
                res_ok = ok
                res_path = p
                res_meta = m
                res_err = e

            worker.progress.connect(_on_prog)
            worker.finished.connect(_on_done)
            worker.start()
            worker.wait()

            if res_ok and res_path:
                success_count += 1
                saved_paths.append(res_path)
            else:
                fail_count += 1

            self.track_finished.emit(i + 1, res_ok, res_path, res_meta, res_err)

        self.batch_finished.emit(success_count, fail_count, saved_paths)
