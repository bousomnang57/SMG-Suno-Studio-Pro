"""
Unified Studio Song Project Manager (.smgsong).
Provides full-fidelity save/load for songwriting projects across all 5 studio modes:
Title, Lyrics, Multi-Take History, Suno/Udio Style Prompt, Negative Prompt,
BPM, Musical Key, Genre, Mood, Language, and Chord Progression.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


PROJECT_FILE_EXT = ".smgsong"
PROJECT_FORMAT_VERSION = "2.0"


@dataclass
class SongProject:
    """Complete serializable state of a professional songwriting project."""
    title: str = "Untitled Song"
    lyrics: str = ""
    style_prompt: str = ""
    negative_prompt: str = ""
    bpm: int = 120
    key: str = "C"
    genre: str = "Pop & Synthpop"
    mood: str = "Euphoric"
    language: str = "English"
    chord_progression: str = ""
    takes: Dict[str, str] = field(default_factory=dict)
    current_take: str = "Take 1 (Main)"
    format_version: str = PROJECT_FORMAT_VERSION
    updated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["smg_studio_project"] = True
        payload["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        return payload


class ProjectManager:
    """Save and load native .smgsong studio projects plus legacy .json/.txt/.lrc/.cho files."""

    @staticmethod
    def parse_bpm(bpm_value: Any, default: int = 120) -> int:
        """Extract an integer BPM from strings like '120 BPM', '88-96 BPM', or ints."""
        if bpm_value is None:
            return default
        if isinstance(bpm_value, (int, float)):
            val = int(round(bpm_value))
            return max(40, min(220, val))
        match = re.search(r"\d{2,3}", str(bpm_value))
        if match:
            try:
                val = int(match.group(0))
                return max(40, min(220, val))
            except ValueError:
                pass
        return default

    @staticmethod
    def save_project(filepath: str, project: SongProject) -> Path:
        """Write a SongProject atomically as UTF-8 JSON (.smgsong)."""
        target = Path(filepath)
        if not target.suffix:
            target = target.with_suffix(PROJECT_FILE_EXT)
        target.parent.mkdir(parents=True, exist_ok=True)

        data = project.to_dict()
        tmp_path = target.with_suffix(target.suffix + ".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        tmp_path.replace(target)
        return target

    @staticmethod
    def load_project(filepath: str) -> SongProject:
        """
        Load a .smgsong studio project, legacy Exporter .json, or plain text (.txt/.lrc/.cho).
        Always returns a populated SongProject.
        """
        p = Path(filepath)
        raw_text = p.read_text(encoding="utf-8-sig")

        # Try structured JSON (.smgsong or .json)
        if p.suffix.lower() in (PROJECT_FILE_EXT, ".json") or raw_text.lstrip().startswith("{"):
            try:
                obj = json.loads(raw_text)
                if isinstance(obj, dict):
                    return ProjectManager._from_json_dict(obj, fallback_title=p.stem)
            except json.JSONDecodeError:
                pass

        # Fallback: Plain text / LRC / ChordPro file
        title = p.stem
        title_match = re.search(r"^\[Title:\s*(.+?)\]\s*$", raw_text, flags=re.IGNORECASE | re.MULTILINE)
        if title_match:
            title = title_match.group(1).strip() or title
        else:
            # ChordPro {title: ...} or LRC [ti:...]
            meta_match = re.search(r"^(?:\{title:\s*(.+?)\}|\[ti:(.+?)\])\s*$", raw_text, flags=re.IGNORECASE | re.MULTILINE)
            if meta_match:
                extracted = (meta_match.group(1) or meta_match.group(2) or "").strip()
                if extracted:
                    title = extracted

        return SongProject(
            title=title,
            lyrics=raw_text,
            takes={"Take 1 (Main)": raw_text},
            current_take="Take 1 (Main)",
        )

    @staticmethod
    def _from_json_dict(obj: Dict[str, Any], fallback_title: str = "Untitled Song") -> SongProject:
        """Parse either a native .smgsong dict or a legacy Exporter.export_json dict."""
        meta = obj.get("metadata") if isinstance(obj.get("metadata"), dict) else {}

        title = str(obj.get("title") or meta.get("title") or fallback_title).strip() or fallback_title
        lyrics = str(obj.get("lyrics") or "")

        # Handle legacy JSON format where lyrics may be stored in structured sections
        if not lyrics and isinstance(obj.get("sections"), list):
            parts = []
            for sec in obj["sections"]:
                if isinstance(sec, dict):
                    hdr = sec.get("header", "")
                    lines = sec.get("lines", [])
                    if hdr:
                        parts.append(f"[{hdr}]")
                    if isinstance(lines, list):
                        parts.extend(str(ln) for ln in lines)
                    parts.append("")
            lyrics = "\n".join(parts).strip()

        style_prompt = str(obj.get("style_prompt") or meta.get("style_prompt") or "").strip()
        negative_prompt = str(obj.get("negative_prompt") or meta.get("negative_prompt") or "").strip()
        bpm = ProjectManager.parse_bpm(obj.get("bpm") or meta.get("bpm"), default=120)
        key = str(obj.get("key") or meta.get("key") or "C").strip() or "C"
        genre = str(obj.get("genre") or meta.get("genre") or "Pop & Synthpop").strip()
        mood = str(obj.get("mood") or meta.get("mood") or "Euphoric").strip()
        language = str(obj.get("language") or meta.get("language") or "English").strip()
        chord_progression = str(obj.get("chord_progression") or meta.get("chord_progression") or "").strip()

        raw_takes = obj.get("takes")
        takes: Dict[str, str] = {}
        if isinstance(raw_takes, dict):
            for k, v in raw_takes.items():
                if str(k).strip():
                    takes[str(k)] = str(v) if v is not None else ""

        current_take = str(obj.get("current_take") or "").strip()
        if not takes:
            takes = {"Take 1 (Main)": lyrics}
            current_take = "Take 1 (Main)"
        elif current_take not in takes:
            current_take = next(iter(takes.keys()))

        # Ensure active lyrics match current_take if lyrics was empty
        if not lyrics and current_take in takes:
            lyrics = takes[current_take]

        return SongProject(
            title=title,
            lyrics=lyrics,
            style_prompt=style_prompt,
            negative_prompt=negative_prompt,
            bpm=bpm,
            key=key,
            genre=genre,
            mood=mood,
            language=language,
            chord_progression=chord_progression,
            takes=takes,
            current_take=current_take,
            format_version=str(obj.get("format_version") or PROJECT_FORMAT_VERSION),
            updated_at=str(obj.get("updated_at") or ""),
        )
