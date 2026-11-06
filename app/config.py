import os
import sys
import re
import json
import threading
from pathlib import Path

def get_resource_dir() -> Path:
    """Returns the base directory for bundled assets and resources across dev and PyInstaller."""
    if getattr(sys, 'frozen', False):
        if hasattr(sys, '_MEIPASS') and Path(sys._MEIPASS).exists():
            return Path(sys._MEIPASS)
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

def get_asset_path(filename: str = "") -> Path:
    """Returns absolute path to an asset file or the assets directory, searching all potential bundle paths."""
    candidates = []
    if getattr(sys, 'frozen', False):
        if hasattr(sys, '_MEIPASS'):
            candidates.append(Path(sys._MEIPASS) / "assets")
        candidates.append(Path(sys.executable).parent / "assets")
        candidates.append(Path(sys.executable).parent / "_internal" / "assets")
    candidates.append(Path(__file__).resolve().parent.parent / "assets")
    candidates.append(Path.cwd() / "assets")

    found_dir = candidates[-1]
    for c in candidates:
        if c.exists():
            found_dir = c
            break

    return found_dir / filename if filename else found_dir

CONFIG_DIR = Path.home() / ".lyric_ai_writer"
CONFIG_FILE = CONFIG_DIR / "config.json"

# Application Metadata & Versioning
APP_NAME = "SMG Suno Studio Pro"
APP_VERSION = "2.0"
APP_TITLE = f"{APP_NAME} v{APP_VERSION}"
DEFAULT_UPDATE_URL = "https://raw.githubusercontent.com/bousomnang57/SMG-Suno-Studio-Pro/main/version.json"

# Canonical Gemini Model Catalog (Tested & Verified Active Quota)
GEMINI_MODELS = [
    "gemini-flash-lite-latest",
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
]

DEFAULT_CONFIG = {
    "gemini_api_key": "",
    "gemini_api_keys": [],
    "gemini_model": "gemini-flash-lite-latest",
    "theme": "obsidian",
    "default_region": "Global Pop & Contemporary",
    "default_genre": "Synthwave / Retro Pop",
    "default_language": "English",
    "tts_voice": "en-US-ChristopherNeural",
    "tts_rate": "+0%",
    "auto_count_syllables": True,
    "auto_check_updates": True,
    "update_url": DEFAULT_UPDATE_URL,
    "last_lyrics": "",
    "last_title": "Untitled Song",
    "history": []
}

def is_valid_gemini_key(k: str) -> bool:
    if not k or len(k) < 25:
        return False
    # Filter placeholder/dummy/sample keys
    if any(d.lower() in k.lower() for d in ["demo", "sample", "xyz123", "examplekey", "dummy"]):
        return False
    return True

def parse_api_keys(raw) -> list[str]:
    """
    Extracts unique non-empty API keys from a string (newline, comma, semicolon, space separated) or list.
    Preserves input order while removing duplicates and invalid demo keys.
    """
    if not raw:
        return []
    if isinstance(raw, list):
        items = raw
    else:
        # Split on newlines, commas, semicolons, tabs, and spaces
        items = re.split(r'[\r\n,;\s]+', str(raw))

    keys: list[str] = []
    for item in items:
        k = str(item).strip()
        # Clean quotes, brackets, and bullet symbols
        k = k.strip("\"'[] \t•-")
        if k and k not in keys and is_valid_gemini_key(k):
            keys.append(k)
    return keys

class ConfigManager:
    """Manages application persistent settings, Gemini models, and multi-key rotation pool."""

    def __init__(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self.config = DEFAULT_CONFIG.copy()
        self._key_index = 0
        self._lock = threading.Lock()
        self.load()

    def load(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.config.update(data)
            except Exception as e:
                print(f"Warning: Failed to load config: {e}")

        # Ensure active model is valid
        current_m = self.config.get("gemini_model", "")
        legacy_deprecated = [
            "gemini-1.0-pro", "gemini-1.5-pro", "gemini-1.5-flash",
            "gemini-2.0-flash", "gemini-2.5-flash", "gemini-2.5-pro",
            "gemini-3.8-flash", "gemini-3.1-pro-preview"
        ]
        if not current_m or current_m in legacy_deprecated or current_m not in GEMINI_MODELS:
            self.config["gemini_model"] = "gemini-flash-lite-latest"
            self.save()

        # Check environment variable fallback
        env_keys = os.environ.get("GEMINI_API_KEYS", "") or os.environ.get("GEMINI_API_KEY", "")
        if env_keys and not self.get_api_keys():
            self.set_api_keys(env_keys)

        # Normalize theme
        raw_theme = self.config.get("theme", "obsidian")
        if raw_theme in ["dark", "dark_modern"]:
            self.config["theme"] = "obsidian"
            self.save()
        elif raw_theme in ["light", "modern_light"]:
            self.config["theme"] = "canvas_light"
            self.save()

        # Synchronize single and multi-key lists
        keys = self.get_api_keys()
        if keys:
            self.config["gemini_api_key"] = keys[0]
            self.config["gemini_api_keys"] = keys

    def save(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Failed to save config: {e}")

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        if key == "gemini_api_key":
            parsed = parse_api_keys(value)
            if parsed:
                # Merge into api keys pool if not already primary
                current_pool = self.get_api_keys()
                for p in parsed:
                    if p not in current_pool:
                        current_pool.append(p)
                self.config["gemini_api_keys"] = current_pool
            else:
                self.config["gemini_api_keys"] = []
        elif key == "gemini_api_keys":
            parsed = parse_api_keys(value)
            self.config["gemini_api_keys"] = parsed
            self.config["gemini_api_key"] = parsed[0] if parsed else ""
        self.save()

    def get_api_keys(self) -> list[str]:
        """Returns all configured Gemini API keys as a list of strings."""
        pool = self.config.get("gemini_api_keys")
        if isinstance(pool, list) and pool:
            cleaned = parse_api_keys(pool)
            if cleaned:
                return cleaned

        single_key = self.config.get("gemini_api_key", "")
        if single_key:
            cleaned = parse_api_keys(single_key)
            if cleaned:
                return cleaned

        return []

    def set_api_keys(self, keys: list[str] | str):
        """Saves a pool of keys, updating both gemini_api_keys and gemini_api_key."""
        parsed = parse_api_keys(keys)
        self.config["gemini_api_keys"] = parsed
        self.config["gemini_api_key"] = parsed[0] if parsed else ""
        self.save()

    def get_next_api_key(self) -> str:
        """Returns the next API key in round-robin sequence for balanced load across the pool."""
        keys = self.get_api_keys()
        if not keys:
            return ""
        with self._lock:
            key = keys[self._key_index % len(keys)]
            self._key_index = (self._key_index + 1) % len(keys)
            return key

    def get_key_count(self) -> int:
        """Returns total number of configured API keys in the rotation pool."""
        return len(self.get_api_keys())

    def get_key_badge_text(self) -> str:
        """Returns localized status badge text matching user reference."""
        count = self.get_key_count()
        if count > 0:
            return f"✓ Key ត្រឹមត្រូវ - {count} គ្រាប់"
        return "🟡 Demo Mode (Add Key for Unlimited Live Generation)"

    def add_history(self, item: dict):
        history = self.config.get("history", [])
        history.insert(0, item)
        # Keep latest 30 items
        self.config["history"] = history[:30]
        self.save()

    def get_history(self):
        return self.config.get("history", [])

# Global singleton
config_manager = ConfigManager()
