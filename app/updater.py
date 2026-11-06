"""
Live Auto-Updater Engine for SMG Suno Studio Pro.
Handles background update checking, version parsing, chunked installer downloading,
and seamless detached restart & install on Windows.
"""

import os
import sys
import re
import json
import time
import tempfile
import urllib.request
import urllib.error
import subprocess
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QApplication

from app.config import APP_VERSION, APP_NAME, DEFAULT_UPDATE_URL

def parse_version(ver_str: str) -> tuple[int, ...]:
    """
    Parses a version string (e.g. 'v2.1.0', '2.0', '2.0.4b') into a tuple of integers for comparison.
    """
    if not ver_str:
        return (0,)
    clean = ver_str.strip().lstrip("vV")
    numbers = re.findall(r'\d+', clean)
    if not numbers:
        return (0,)
    return tuple(int(n) for n in numbers)

def is_newer_version(remote_ver: str, current_ver: str = APP_VERSION) -> bool:
    """
    Returns True if remote_ver is strictly newer than current_ver.
    Pads tuples with zeros to handle different lengths (e.g. 2.1 vs 2.1.0).
    """
    r_parts = list(parse_version(remote_ver))
    c_parts = list(parse_version(current_ver))
    
    max_len = max(len(r_parts), len(c_parts))
    r_parts.extend([0] * (max_len - len(r_parts)))
    c_parts.extend([0] * (max_len - len(c_parts)))
    
    return tuple(r_parts) > tuple(c_parts)


def resolve_github_asset_url(download_url: str) -> str:
    """
    If download_url points to a GitHub Release, queries GitHub Releases API
    to dynamically retrieve the exact live installer .exe asset, avoiding 404 filename mismatches.
    """
    if "github.com" not in download_url or "releases" not in download_url:
        return download_url

    match = re.search(r'github\.com/([^/]+)/([^/]+)/releases', download_url)
    if not match:
        return download_url

    owner, repo = match.group(1), match.group(2)
    tag_match = re.search(r'/releases/download/([^/]+)/', download_url)
    if tag_match:
        tag = tag_match.group(1)
        api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/tags/{tag}"
    else:
        api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"

    try:
        req = urllib.request.Request(
            api_url,
            headers={
                "User-Agent": f"SMG-Suno-Studio-Pro/{APP_VERSION} (Windows; x64)",
                "Accept": "application/vnd.github.v3+json"
            }
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            assets = data.get("assets", [])
            for asset in assets:
                name = asset.get("name", "")
                if name.endswith(".exe"):
                    return asset.get("browser_download_url", download_url)
    except Exception:
        pass

    return download_url


class UpdateCheckWorker(QThread):
    """
    Background worker that queries the version manifest JSON from remote URL without blocking the GUI.
    """
    update_available = pyqtSignal(dict)  # Emits update manifest dictionary
    up_to_date = pyqtSignal(str)        # Emits current/latest version string
    check_failed = pyqtSignal(str)      # Emits error description

    def __init__(self, update_url: str = "", current_version: str = APP_VERSION, timeout: int = 8, parent=None):
        super().__init__(parent)
        self.update_url = update_url.strip() or DEFAULT_UPDATE_URL
        self.current_version = current_version
        self.timeout = timeout

    def run(self):
        try:
            check_url = self.update_url
            sep = "&" if "?" in check_url else "?"
            check_url = f"{check_url}{sep}_t={int(time.time())}"

            req = urllib.request.Request(
                check_url,
                headers={
                    "User-Agent": f"SMG-Suno-Studio-Pro/{self.current_version} (Windows; x64)",
                    "Cache-Control": "no-cache",
                    "Pragma": "no-cache"
                }
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                if response.status != 200:
                    self.check_failed.emit(f"HTTP Error {response.status}: Failed to reach update server")
                    return
                raw_data = response.read().decode("utf-8")
                manifest = json.loads(raw_data)
                
            remote_ver = manifest.get("version", "").strip()
            if not remote_ver:
                self.check_failed.emit("Invalid manifest: Missing version field")
                return

            if is_newer_version(remote_ver, self.current_version):
                self.update_available.emit(manifest)
            else:
                self.up_to_date.emit(remote_ver)

        except urllib.error.URLError as e:
            self.check_failed.emit(f"Network error: {e.reason}")
        except json.JSONDecodeError as e:
            self.check_failed.emit("Failed to parse update manifest JSON")
        except Exception as e:
            self.check_failed.emit(f"Update check failed: {str(e)}")


class UpdateDownloadWorker(QThread):
    """
    Background worker that downloads the installer file in chunks,
    emitting real-time progress, download percentage, and network speed.
    """
    progress = pyqtSignal(int, int, int, str)  # bytes_read, total_bytes, percent, speed_str
    finished = pyqtSignal(str)                 # local installer file path
    failed = pyqtSignal(str)                   # error message

    def __init__(self, download_url: str, target_filename: str = "", parent=None):
        super().__init__(parent)
        self.download_url = download_url
        self.target_filename = target_filename or "SMG_Suno_Studio_Pro_Update.exe"
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            temp_dir = Path(tempfile.gettempdir())
            dest_file = temp_dir / self.target_filename

            download_url = self.download_url
            try:
                resolved = resolve_github_asset_url(download_url)
                if resolved:
                    download_url = resolved
            except Exception:
                pass

            req = urllib.request.Request(
                download_url,
                headers={"User-Agent": f"SMG-Suno-Studio-Pro/{APP_VERSION} (Windows; x64)"}
            )

            start_time = time.time()
            bytes_read = 0

            with urllib.request.urlopen(req, timeout=20) as response:
                total_bytes = int(response.headers.get("Content-Length", 0))
                chunk_size = 64 * 1024  # 64 KB chunks

                with open(dest_file, "wb") as f:
                    while True:
                        if self._is_cancelled:
                            self.failed.emit("Download cancelled by user")
                            return

                        chunk = response.read(chunk_size)
                        if not chunk:
                            break

                        f.write(chunk)
                        bytes_read += len(chunk)

                        # Calculate metrics
                        elapsed = max(0.001, time.time() - start_time)
                        speed_bps = bytes_read / elapsed
                        if speed_bps >= 1024 * 1024:
                            speed_str = f"{speed_bps / (1024 * 1024):.1f} MB/s"
                        else:
                            speed_str = f"{speed_bps / 1024:.0f} KB/s"

                        percent = int((bytes_read / total_bytes) * 100) if total_bytes > 0 else 0
                        self.progress.emit(bytes_read, total_bytes, percent, speed_str)

            if not dest_file.exists() or dest_file.stat().st_size == 0:
                self.failed.emit("Downloaded installer file is empty or missing")
                return

            self.finished.emit(str(dest_file))

        except urllib.error.URLError as e:
            self.failed.emit(f"Download network error: {e.reason}")
        except Exception as e:
            self.failed.emit(f"Download error: {str(e)}")


def restart_and_install(installer_path: str, run_silent: bool = False):
    """
    Launches the downloaded installer as an independent detached process and
    immediately closes the current application to release all Windows binary file locks.
    """
    p = Path(installer_path)
    if not p.exists():
        raise FileNotFoundError(f"Installer not found at: {installer_path}")

    cmd = [str(p.resolve())]
    if run_silent:
        # Inno Setup silent install flags
        cmd.extend(["/SILENT", "/CLOSEAPPLICATIONS", "/RESTARTAPPLICATIONS"])

    creationflags = 0
    if sys.platform == "win32":
        creationflags = getattr(subprocess, 'DETACHED_PROCESS', 0) | getattr(subprocess, 'CREATE_NEW_PROCESS_GROUP', 0)

    # Launch detached installer
    subprocess.Popen(
        cmd,
        creationflags=creationflags,
        close_fds=True,
        shell=False
    )

    # Gracefully exit the running Qt application
    app_inst = QApplication.instance()
    if app_inst:
        app_inst.quit()
    else:
        sys.exit(0)


def open_download_url(url: str):
    """Opens the download URL in the user's default web browser."""
    if url:
        QDesktopServices.openUrl(QUrl(url))

