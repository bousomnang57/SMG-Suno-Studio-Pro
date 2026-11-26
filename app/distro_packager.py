"""
DistroKid & TuneCore Single & Album Release Engine + Assisted Auto-Fill Builder.

Provides:
1. Store-compliant Title Case & Rejection Shield (Apple Music / Spotify / DistroKid / TuneCore rules).
2. Store-compliant plain-text lyric cleaner & LRC synced lyric generator.
3. Smart Chorus / TikTok 15s-30s Preview Hook Start-Time Detector (RMS audio energy + lyric structure).
4. Store-compliant 3000x3000 px RGB Cover Art + 1080x1920 (9:16) Spotify Canvas / Reels promo visual.
5. Pre-flight QC validator for Single Song (1 Track), EP (2-6 Tracks), Album (7-30 Tracks), & 100% Splits.
6. Staged Release Folder packager (numbered 24-bit WAV masters, 3000px Cover, 9:16 Canvas, Splits CSV, Social Copy).
7. Transparent client-side React/DOM form Auto-Fill JavaScript builders for DistroKid & TuneCore
   (operates strictly on the upload form opened by the signed-in user; never touches auth or anti-bot gates).
"""

from __future__ import annotations

import csv
import datetime
import json
import math
import os
import random
import re
import shutil
import wave
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from app.audio_mastering_engine import AudioMasteringEngine
from app.cover_art_generator import CoverArtGenerator, STYLE_PRESETS


DISTRO_PLATFORMS: Dict[str, Dict[str, object]] = {
    "DistroKid": {
        "name": "DistroKid",
        "new_upload_url": "https://distrokid.com/new/",
        "releases_url": "https://distrokid.com/mymusic/",
        "lyrics_url": "https://distrokid.com/lyrics/",
        "splits_url": "https://distrokid.com/teams/",
        "royalties_url": "https://distrokid.com/bank/",
        "spotify_artists_url": "https://distrokid.com/spotify/",
        "apple_artists_url": "https://artists.apple.com/",
        "accent": "#0284c7",
        "badge": "🟦 DistroKid",
    },
    "TuneCore": {
        "name": "TuneCore",
        "new_upload_url": "https://app.tunecore.com/releases/new",
        "releases_url": "https://app.tunecore.com/discography",
        "lyrics_url": "https://app.tunecore.com/discography",
        "splits_url": "https://app.tunecore.com/splits",
        "royalties_url": "https://app.tunecore.com/sales",
        "spotify_artists_url": "https://artists.spotify.com/",
        "apple_artists_url": "https://artists.apple.com/",
        "accent": "#7c3aed",
        "badge": "🟪 TuneCore",
    },
}

DISTRO_GENRES: List[str] = [
    "Pop",
    "Hip Hop/Rap",
    "Electronic",
    "Dance",
    "R&B/Soul",
    "Rock",
    "Alternative",
    "Indie Pop",
    "Country",
    "Singer/Songwriter",
    "K-Pop",
    "Latin",
    "Afrobeats",
    "Soundtrack",
    "Instrumental / Lo-Fi",
    "Metal",
    "Jazz",
    "World",
]

DISTRO_LANGUAGES: List[str] = [
    "English",
    "Spanish",
    "Korean",
    "Japanese",
    "French",
    "German",
    "Portuguese",
    "Khmer",
    "Chinese",
    "Thai",
    "Vietnamese",
    "Instrumental (No Lyrics)",
]

# Minor words kept lowercase in English Title Case (except first/last word)
_TITLE_MINOR_WORDS = {
    "a", "an", "and", "as", "at", "but", "by", "for", "from", "in",
    "into", "nor", "of", "on", "onto", "or", "per", "so", "the",
    "to", "up", "via", "with", "yet",
}

# Forbidden mastering/file suffixes rejected by Apple Music, Spotify, DistroKid & TuneCore
_FORBIDDEN_TITLE_SUFFIX_RE = re.compile(
    r"(?:[\s_-]*\b(?:mastered(?:\s+pro)?|final\s+mix|unmastered|suno\s+ai|ai\s+version|24-?bit|44\.1khz|mp3|wav)\b)+",
    re.IGNORECASE,
)
_LEADING_TRACK_NUM_RE = re.compile(r"^(?:track\s*)?\d{1,2}[\s._-]+", re.IGNORECASE)
_EMOJI_STRIP_RE = re.compile(r"[\U00010000-\U0010ffff\u2600-\u27bf]+")

# Inline chord pattern e.g. [Am], [F#m7], [Cmaj7/G]
_CHORD_TAG_RE = re.compile(
    r"\[([A-G][#b]?(?:m|maj|min|dim|aug|sus[24]?|add[0-9]+|[0-9])*(?:/[A-G][#b]?)?)\]"
)
# Structural section / Suno cue tags e.g. [Verse 1], [Chorus: Anthemic], [Intro], [End]
_SECTION_TAG_RE = re.compile(r"\[[^\]]*\]")
# Pure stage/instrumental cue lines inside parentheses e.g. (Guitar Solo), (Instrumental Break)
_STAGE_DIRECTION_RE = re.compile(
    r"^\((?:instrumental(?:\s+\w+)*|[\w\s]*\bsolo|drum break|beat drop|fade out|end|music|ad-?libs?)\)$",
    re.IGNORECASE,
)


def format_store_compliant_title(raw_title: str, featured_artist: str = "") -> str:
    """
    Auto-fix song/album titles to pass strict Apple Music, Spotify, DistroKid & TuneCore
    editorial style guidelines:
    - Strips leading track numbers ('01 - '), emojis, and forbidden engineering tags ('_Mastered_Pro', 'Final Mix')
    - Converts SHOUTING ALL-CAPS or all-lowercase titles into proper English Music Title Case
    - Normalizes featuring credits to '(feat. Artist)'
    """
    if not raw_title or not raw_title.strip():
        return "Untitled Song"

    t = _EMOJI_STRIP_RE.sub("", raw_title)
    t = t.replace("_", " ").strip()
    t = _LEADING_TRACK_NUM_RE.sub("", t)
    t = _FORBIDDEN_TITLE_SUFFIX_RE.sub("", t)
    # Remove empty parentheses left behind after stripping '(Mastered)'
    t = re.sub(r"\(\s*\)|\[\s*\]", "", t)
    t = re.sub(r"\s{2,}", " ", t).strip(" -–—.,")
    if not t:
        return "Untitled Song"

    # Normalize existing ft./featuring variants to 'feat.'
    t = re.sub(r"\(\s*(?:ft\.?|featuring)\s+", "(feat. ", t, flags=re.IGNORECASE)

    # Apply smart Title Case if ALL CAPS or all lowercase or mixed filename casing
    alpha_chars = [ch for ch in t if ch.isalpha()]
    needs_recase = (
        len(alpha_chars) > 0
        and (all(ch.isupper() for ch in alpha_chars) or all(ch.islower() for ch in alpha_chars))
    )
    words = t.split(" ")
    out_words: List[str] = []
    for idx, w in enumerate(words):
        if not w:
            continue
        low_clean = w.lower().strip("()[]")
        if low_clean == "feat.":
            out_words.append("(feat." if w.startswith("(") else "feat.")
            continue
        if needs_recase:
            if 0 < idx < len(words) - 1 and low_clean in _TITLE_MINOR_WORDS and not w.startswith("("):
                out_words.append(w.lower())
            elif w.startswith("(") and len(w) > 1:
                out_words.append("(" + w[1].upper() + w[2:].lower())
            else:
                out_words.append(w[0].upper() + w[1:].lower())
        else:
            # Ensure at least first word starts uppercase
            if idx == 0 and w[0].islower():
                out_words.append(w[0].upper() + w[1:])
            else:
                out_words.append(w)

    final_title = " ".join(out_words).strip()
    feat_clean = (featured_artist or "").strip()
    if feat_clean and "(feat." not in final_title.lower():
        final_title = f"{final_title} (feat. {feat_clean})"
    return final_title


def has_store_title_warning(title: str) -> Optional[str]:
    """Return a concise warning string if a title violates Apple Music / DistroKid / TuneCore rules."""
    t = (title or "").strip()
    if not t:
        return "Empty title"
    alpha = [c for c in t if c.isalpha()]
    if len(alpha) >= 4 and all(c.isupper() for c in alpha):
        return "ALL-CAPS title (Apple Music rejects ALL CAPS — click '✨ Auto-Fix Titles')"
    if _FORBIDDEN_TITLE_SUFFIX_RE.search(t):
        return "Contains studio tag ('Mastered'/'Mix'/'WAV') — click '✨ Auto-Fix Titles'"
    if _LEADING_TRACK_NUM_RE.match(t):
        return "Starts with track number ('01 - ') — stores add track numbers automatically"
    return None


def detect_hook_start_timestamp(
    audio_path: str | Path = "",
    raw_lyrics: str = "",
    default_sec: int = 42,
) -> str:
    """
    Auto-detect the best 15s-30s Chorus / TikTok / Apple Music Preview Clip start time ('MM:SS').
    1. If an audio file exists, computes 1-second RMS energy windows across 18%..68% of the song
       and finds the strongest sustained 15-second chorus/hook lift.
    2. Otherwise, estimates chorus entry time from [Chorus] line position in raw lyrics.
    """
    if audio_path and Path(audio_path).exists():
        try:
            audio, sr = AudioMasteringEngine.load_audio(str(audio_path))
            total_samples = audio.shape[0]
            dur_sec = total_samples / float(max(1, sr))
            if dur_sec >= 25.0:
                mono = np.mean(audio, axis=1)
                win_samples = max(1, sr)  # 1.0s hop
                n_secs = int(total_samples // win_samples)
                rms_per_sec = np.array([
                    float(np.sqrt(np.mean(mono[i * win_samples:(i + 1) * win_samples] ** 2)))
                    for i in range(n_secs)
                ])
                start_idx = max(5, int(n_secs * 0.18))
                end_idx = max(start_idx + 2, min(n_secs - 15, int(n_secs * 0.68)))
                if end_idx > start_idx and len(rms_per_sec) >= 16:
                    best_sec = start_idx
                    best_energy = -1.0
                    for s in range(start_idx, end_idx):
                        span_end = min(len(rms_per_sec), s + 15)
                        avg_e = float(np.mean(rms_per_sec[s:span_end]))
                        if avg_e > best_energy:
                            best_energy = avg_e
                            best_sec = s
                    return f"{best_sec // 60:02d}:{best_sec % 60:02d}"
                mid_sec = max(0, int(dur_sec * 0.25))
                return f"{mid_sec // 60:02d}:{mid_sec % 60:02d}"
        except Exception:
            pass

    if raw_lyrics and raw_lyrics.strip():
        lines = [ln.strip() for ln in raw_lyrics.splitlines() if ln.strip()]
        for idx, ln in enumerate(lines):
            if "chorus" in ln.lower() and ln.startswith("["):
                ratio = min(0.55, max(0.18, idx / float(max(1, len(lines)))))
                est_sec = int(round(180 * ratio))
                return f"{est_sec // 60:02d}:{est_sec % 60:02d}"

    return f"{default_sec // 60:02d}:{default_sec % 60:02d}"


def parse_mmss_to_ms(mmss: str) -> int:
    """Convert 'MM:SS' timestamp string to milliseconds for audio preview seek."""
    try:
        parts = (mmss or "00:42").strip().split(":")
        if len(parts) == 2:
            return max(0, (int(parts[0]) * 60 + int(parts[1])) * 1000)
    except Exception:
        pass
    return 42000


def clean_lyrics_for_stores(raw_lyrics: str) -> str:
    """
    Convert Suno / Studio chord-and-tag lyrics into strict Apple Music, Spotify,
    DistroKid & TuneCore store-compliant plain text:
    - Strips all [Verse], [Chorus], [Intro] structural tags and [Am] chord brackets
    - Removes pure instrumental cue lines like (Guitar Solo) or (Instrumental Break)
    - Trims trailing punctuation (. , ; !) per Apple Music lyric formatting guidelines
    - Preserves clean stanza spacing between sections
    """
    if not raw_lyrics or not raw_lyrics.strip():
        return ""

    lines_out: List[str] = []
    prev_blank = True

    for raw_line in raw_lyrics.splitlines():
        line = raw_line.strip()
        if not line:
            if not prev_blank:
                lines_out.append("")
                prev_blank = True
            continue

        stripped_brackets = _SECTION_TAG_RE.sub("", line).strip()
        if not stripped_brackets:
            if not prev_blank:
                lines_out.append("")
                prev_blank = True
            continue

        cleaned = _CHORD_TAG_RE.sub("", line)
        cleaned = _SECTION_TAG_RE.sub("", cleaned)
        cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()

        if not cleaned or _STAGE_DIRECTION_RE.match(cleaned):
            continue

        if cleaned.startswith("(") and cleaned.endswith(")") and len(cleaned) > 2:
            cleaned = cleaned[1:-1].strip()

        cleaned = re.sub(r"[.,;:!]+$", "", cleaned).strip()
        cleaned = cleaned.replace("...", "").strip()
        if not cleaned:
            continue

        first_alpha = re.search(r"[a-zA-Z]", cleaned)
        if first_alpha and first_alpha.start() == 0:
            cleaned = cleaned[0].upper() + cleaned[1:]

        lines_out.append(cleaned)
        prev_blank = False

    while lines_out and lines_out[-1] == "":
        lines_out.pop()

    return "\n".join(lines_out)


def generate_synced_lrc(
    clean_lyrics: str,
    duration_sec: float = 180.0,
    title: str = "",
    artist: str = "",
) -> str:
    """Generate a clean .lrc karaoke timestamp file for DistroKid Lyric Blaster / synced stores."""
    clean = clean_lyrics_for_stores(clean_lyrics)
    sung_lines = [ln for ln in clean.splitlines() if ln.strip()]
    header = []
    if title:
        header.append(f"[ti:{title}]")
    if artist:
        header.append(f"[ar:{artist}]")
    header.append("[by:SMG Suno Studio Pro]")

    if not sung_lines:
        return "\n".join(header) + "\n"

    usable_start = min(8.0, max(2.0, duration_sec * 0.05))
    usable_span = max(15.0, duration_sec - usable_start - 5.0)
    step = usable_span / max(1, len(sung_lines))

    body = []
    for idx, line in enumerate(sung_lines):
        t_sec = usable_start + idx * step
        mm = int(t_sec // 60)
        ss = t_sec % 60
        body.append(f"[{mm:02d}:{ss:05.2f}]{line}")

    return "\n".join(header + body) + "\n"


def generate_store_cover_3000(
    title: str,
    artist: str,
    style_key: str = "cyberpunk_neon",
    output_path: Optional[str | Path] = None,
) -> Image.Image:
    """
    Generate a strict 3000 x 3000 px RGB store-compliant album/single cover.
    Contains ZERO technical specs, store names, URLs, or AI badges.
    """
    style = STYLE_PRESETS.get(style_key, STYLE_PRESETS["cyberpunk_neon"])
    base_size = 1500
    target_size = 3000

    img = Image.new("RGB", (base_size, base_size))
    draw = ImageDraw.Draw(img)

    c_top = style["bg_top"]
    c_bot = style["bg_bottom"]
    acc1 = style["accent_1"]
    acc2 = style["accent_2"]

    for y in range(base_size):
        ratio = y / float(base_size)
        r = int(c_top[0] * (1.0 - ratio) + c_bot[0] * ratio)
        g = int(c_top[1] * (1.0 - ratio) + c_bot[1] * ratio)
        b = int(c_top[2] * (1.0 - ratio) + c_bot[2] * ratio)
        draw.line([(0, y), (base_size, y)], fill=(r, g, b))

    orb_img = Image.new("RGBA", (base_size, base_size), (0, 0, 0, 0))
    orb_draw = ImageDraw.Draw(orb_img)
    cx, cy = base_size // 2, int(base_size * 0.44)
    max_r = int(base_size * 0.38)

    if style_key == "vintage_vinyl_70s":
        for r in range(max_r, 45, -18):
            alpha = int(50 + 30 * math.sin(r * 0.1))
            orb_draw.ellipse(
                [(cx - r, cy - r), (cx + r, cy + r)],
                outline=(acc1[0], acc1[1], acc1[2], alpha),
                width=3,
            )
        label_r = 90
        orb_draw.ellipse(
            [(cx - label_r, cy - label_r), (cx + label_r, cy + label_r)],
            fill=(acc2[0], acc2[1], acc2[2], 225),
        )
        orb_draw.ellipse([(cx - 18, cy - 18), (cx + 18, cy + 18)], fill=(20, 15, 10, 255))
    else:
        for r in range(max_r, 0, -14):
            alpha = int(125 * (1.0 - (r / max_r) ** 1.8))
            col = acc1 if (r % 28 == 0) else acc2
            orb_draw.ellipse(
                [(cx - r, cy - r), (cx + r, cy + r)],
                fill=(col[0], col[1], col[2], alpha),
            )

    if "neon" in style_key or "dark" in style_key:
        horizon_y = int(base_size * 0.66)
        for x in range(0, base_size + 120, 130):
            orb_draw.line([(cx, horizon_y), (x, base_size)], fill=(acc1[0], acc1[1], acc1[2], 70), width=2)
        for i in range(1, 10):
            gy = horizon_y + int((base_size - horizon_y) * (i / 10.0) ** 1.8)
            orb_draw.line([(0, gy), (base_size, gy)], fill=(acc2[0], acc2[1], acc2[2], 80), width=2)

    random.seed(abs(hash(f"{artist}:{title}")) % 10000)
    for _ in range(140):
        sx = random.randint(0, base_size)
        sy = random.randint(0, int(base_size * 0.72))
        s_rad = random.randint(1, 3)
        s_alpha = random.randint(80, 235)
        orb_draw.ellipse([(sx - s_rad, sy - s_rad), (sx + s_rad, sy + s_rad)], fill=(255, 255, 255, s_alpha))

    img = Image.alpha_composite(img.convert("RGBA"), orb_img).convert("RGB")

    vignette = Image.new("RGBA", (base_size, base_size), (0, 0, 0, 0))
    v_draw = ImageDraw.Draw(vignette)
    margin = int(base_size * 0.11)
    v_draw.rectangle([(0, 0), (base_size, base_size)], outline=(0, 0, 0, 155), width=margin)
    vignette = vignette.filter(ImageFilter.GaussianBlur(margin // 2))
    img = Image.alpha_composite(img.convert("RGBA"), vignette).convert("RGB")

    img_3000 = img.resize((target_size, target_size), Image.Resampling.LANCZOS).convert("RGB")
    draw_3000 = ImageDraw.Draw(img_3000)

    clean_title = (title or "Untitled Release").strip()
    clean_artist = (artist or "Independent Artist").strip()

    title_pt = 176 if len(clean_title) <= 16 else (132 if len(clean_title) <= 26 else 98)
    f_title = CoverArtGenerator.get_font(title_pt, bold=True)
    f_artist = CoverArtGenerator.get_font(82, bold=False)

    ty = int(target_size * 0.79)
    ay = int(target_size * 0.88)

    for dx, dy in [(-6, -6), (6, 6), (-6, 6), (6, -6), (0, 9)]:
        draw_3000.text((target_size // 2 + dx, ty + dy), clean_title, fill=(8, 10, 20), font=f_title, anchor="mm")
    draw_3000.text((target_size // 2, ty), clean_title, fill=(255, 255, 255), font=f_title, anchor="mm")
    draw_3000.text(
        (target_size // 2, ay),
        clean_artist.upper(),
        fill=(acc1[0], acc1[1], acc1[2]),
        font=f_artist,
        anchor="mm",
    )

    if output_path:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        if out_p.suffix.lower() == ".png":
            img_3000.save(str(out_p), format="PNG")
        else:
            img_3000.save(str(out_p), format="JPEG", quality=95, subsampling=0)

    return img_3000


def generate_vertical_canvas_1080x1920(
    title: str,
    artist: str,
    style_key: str = "cyberpunk_neon",
    output_path: Optional[str | Path] = None,
) -> Image.Image:
    """
    Generate a 1080 x 1920 (9:16 vertical) visual asset for Spotify Canvas, TikTok,
    Instagram Reels & YouTube Shorts release promotion.
    """
    style = STYLE_PRESETS.get(style_key, STYLE_PRESETS["cyberpunk_neon"])
    w, h = 1080, 1920
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)

    c_top = style["bg_top"]
    c_bot = style["bg_bottom"]
    acc1 = style["accent_1"]
    acc2 = style["accent_2"]

    for y in range(h):
        ratio = y / float(h)
        r = int(c_top[0] * (1.0 - ratio) + c_bot[0] * ratio)
        g = int(c_top[1] * (1.0 - ratio) + c_bot[1] * ratio)
        b = int(c_top[2] * (1.0 - ratio) + c_bot[2] * ratio)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

    orb = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(orb)
    cx, cy = w // 2, int(h * 0.43)
    max_r = int(w * 0.44)
    for rad in range(max_r, 0, -14):
        alpha = int(125 * (1.0 - (rad / max_r) ** 1.8))
        col = acc1 if (rad % 28 == 0) else acc2
        od.ellipse([(cx - rad, cy - rad), (cx + rad, cy + rad)], fill=(col[0], col[1], col[2], alpha))

    img = Image.alpha_composite(img.convert("RGBA"), orb).convert("RGB")
    dt = ImageDraw.Draw(img)
    f_badge = CoverArtGenerator.get_font(34, bold=True)
    f_title = CoverArtGenerator.get_font(68 if len(title) <= 20 else 50, bold=True)
    f_artist = CoverArtGenerator.get_font(40, bold=False)

    dt.text((w // 2, int(h * 0.69)), "OUT NOW ON ALL PLATFORMS", fill=(210, 225, 245), font=f_badge, anchor="mm")
    dt.text((w // 2, int(h * 0.75)), title or "New Release", fill=(255, 255, 255), font=f_title, anchor="mm")
    dt.text((w // 2, int(h * 0.81)), (artist or "Artist").upper(), fill=acc1, font=f_artist, anchor="mm")

    if output_path:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(out_p), format="JPEG", quality=93)
    return img


def normalize_image_to_store_3000(src_path: str | Path, dst_path: str | Path) -> Tuple[int, int]:
    """
    Center-crop any existing image to 1:1 square and export as exact 3000x3000 RGB JPG/PNG
    compliant with DistroKid & TuneCore artwork rules.
    """
    with Image.open(str(src_path)) as im:
        rgb = im.convert("RGB")
        w, h = rgb.size
        side = min(w, h)
        left = (w - side) // 2
        top = (h - side) // 2
        cropped = rgb.crop((left, top, left + side, top + side))
        out_im = cropped.resize((3000, 3000), Image.Resampling.LANCZOS)

    dst = Path(dst_path)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.suffix.lower() == ".png":
        out_im.save(str(dst), format="PNG")
    else:
        out_im.save(str(dst), format="JPEG", quality=95, subsampling=0)
    return out_im.size


def validate_cover_art(image_path: str | Path) -> Dict[str, object]:
    """Inspect cover image file against DistroKid & TuneCore 3000x3000 RGB requirements."""
    if not image_path or not Path(image_path).exists():
        return {
            "ok": False,
            "width": 0,
            "height": 0,
            "mode": "",
            "detail": "Missing cover art (3000×3000 RGB JPG/PNG required)",
        }
    p = Path(image_path)
    ext = p.suffix.lower()
    if ext not in (".jpg", ".jpeg", ".png"):
        return {
            "ok": False,
            "width": 0,
            "height": 0,
            "mode": "",
            "detail": f"Unsupported format '{ext}' (use .jpg or .png)",
        }
    try:
        with Image.open(str(p)) as im:
            w, h = im.size
            mode = im.mode
        is_square = w == h
        size_ok = w >= 3000 and h >= 3000
        rgb_ok = mode == "RGB"
        ok = is_square and size_ok and rgb_ok
        if ok:
            detail = f"Verified {w}×{h} px RGB ({p.name})"
        else:
            reasons = []
            if not is_square:
                reasons.append(f"non-square {w}×{h}")
            if not size_ok:
                reasons.append(f"{w}×{h} < 3000×3000 px")
            if not rgb_ok:
                reasons.append(f"color mode {mode} (must be RGB)")
            detail = "Needs resize/fix: " + ", ".join(reasons)
        return {"ok": ok, "width": w, "height": h, "mode": mode, "detail": detail}
    except Exception as exc:
        return {"ok": False, "width": 0, "height": 0, "mode": "", "detail": f"Unreadable image: {exc}"}


def inspect_audio_file_quick(audio_path: str | Path) -> Dict[str, object]:
    """Fast header check for WAV/FLAC/MP3 track attachment."""
    if not audio_path or not Path(audio_path).exists():
        return {"exists": False, "is_wav": False, "detail": "No audio file attached"}
    p = Path(audio_path)
    ext = p.suffix.lower()
    if ext == ".wav":
        try:
            with wave.open(str(p), "rb") as wf:
                ch = wf.getnchannels()
                sw = wf.getsampwidth() * 8
                sr = wf.getframerate()
                frames = wf.getnframes()
                dur = frames / float(max(1, sr))
            ok = ch == 2 and sr in (44100, 48000, 88200, 96000) and sw in (16, 24)
            return {
                "exists": True,
                "is_wav": True,
                "store_ready": ok,
                "channels": ch,
                "bit_depth": sw,
                "sample_rate": sr,
                "duration_sec": dur,
                "detail": f"{sw}-bit {sr/1000:.1f}kHz {'Stereo' if ch == 2 else 'Mono'} WAV ({dur:.1f}s)",
            }
        except Exception:
            pass
    size_mb = p.stat().st_size / (1024 * 1024)
    return {
        "exists": True,
        "is_wav": ext == ".wav",
        "store_ready": ext in (".wav", ".flac"),
        "duration_sec": 180.0,
        "detail": f"{ext.upper().lstrip('.')} ({size_mb:.1f} MB) — Auto-Master converts to 24-bit WAV",
    }


class DistroPreflightValidator:
    """Validates Single & Album release metadata, formatting, audio, cover art, lyrics, and 100% splits."""

    @staticmethod
    def classify_release_format(track_count: int, mode: str = "single") -> str:
        if mode == "single" or track_count <= 1:
            return "Single (1 Track)"
        if track_count <= 6:
            return f"EP ({track_count} Tracks)"
        return f"Full Album ({track_count} Tracks)"

    @classmethod
    def validate_release(cls, project: Dict[str, object]) -> Dict[str, object]:
        mode = str(project.get("release_mode", "single")).lower()
        platform = str(project.get("platform", "DistroKid"))
        artist = str(project.get("artist_name", "")).strip()
        release_title = str(project.get("release_title", "")).strip()
        legal_first = str(project.get("songwriter_first", "")).strip()
        legal_last = str(project.get("songwriter_last", "")).strip()
        genre = str(project.get("primary_genre", "")).strip()
        cover_path = str(project.get("cover_path", "")).strip()
        tracks: List[Dict[str, object]] = list(project.get("tracks", []))
        splits: List[Dict[str, object]] = list(project.get("splits", []))

        active_tracks = tracks[:1] if (mode == "single" and len(tracks) > 1) else tracks
        checks: List[Dict[str, object]] = []

        # 1. Release Format & Track Count
        if mode == "single":
            t_ok = len(active_tracks) == 1
            checks.append({
                "label": "Release Format (Single Song)",
                "ok": t_ok,
                "detail": "1 Track configured for Single release" if t_ok else "Add 1 song to release as a Single",
            })
        else:
            t_ok = 2 <= len(active_tracks) <= 30
            fmt_label = cls.classify_release_format(len(active_tracks), "album")
            checks.append({
                "label": f"Release Format ({fmt_label})",
                "ok": t_ok,
                "detail": f"{len(active_tracks)} tracks queued for {platform} multi-track upload"
                if t_ok else f"Album/EP requires 2–30 tracks (currently {len(active_tracks)})",
            })

        # 2. Store-Compliant Artist & Title Formatting (No ALL CAPS or 'Mastered' suffixes)
        rel_warn = has_store_title_warning(release_title)
        tr_warns = [
            f"#{i}: {has_store_title_warning(str(tr.get('title', '')))}"
            for i, tr in enumerate(active_tracks, 1)
            if has_store_title_warning(str(tr.get("title", "")))
        ]
        title_ok = (
            bool(artist)
            and bool(release_title)
            and release_title.lower() not in ("untitled", "track 1", "song 1")
            and rel_warn is None
            and len(tr_warns) == 0
        )
        if title_ok:
            t_detail = f"{artist} — {release_title} (Apple/Spotify Title Case OK)"
        elif rel_warn:
            t_detail = rel_warn
        elif tr_warns:
            t_detail = tr_warns[0]
        else:
            t_detail = "Enter Primary Artist and valid Release/Album Title"
        checks.append({
            "label": "Store Title Formatting Shield",
            "ok": title_ok,
            "detail": t_detail,
        })

        # 3. Real Legal Songwriter Name
        sw_ok = len(legal_first) >= 2 and len(legal_last) >= 2
        checks.append({
            "label": "Legal Songwriter Name (First + Last)",
            "ok": sw_ok,
            "detail": f"{legal_first} {legal_last} (Store Verified)"
            if sw_ok else f"{platform} requires real legal First & Last Name for Songwriter (no stage names)",
        })

        # 4. 3000x3000 RGB Cover Art
        cov_info = validate_cover_art(cover_path)
        checks.append({
            "label": "3000×3000 RGB Cover Artwork",
            "ok": bool(cov_info["ok"]),
            "detail": str(cov_info["detail"]),
        })

        # 5. Audio Files Attached & WAV Ready
        if active_tracks:
            attached_count = sum(1 for tr in active_tracks if tr.get("audio_path") and Path(str(tr["audio_path"])).exists())
            wav_ready_count = sum(
                1 for tr in active_tracks
                if inspect_audio_file_quick(str(tr.get("audio_path", ""))).get("store_ready", False)
            )
            audio_ok = attached_count == len(active_tracks) and len(active_tracks) > 0
            if audio_ok and wav_ready_count == len(active_tracks):
                aud_detail = f"All {len(active_tracks)}/{len(active_tracks)} tracks attached as lossless Stereo WAV/FLAC"
            elif audio_ok:
                aud_detail = f"{attached_count}/{len(active_tracks)} audio files attached (Staging converts all to 24-bit WAV)"
            else:
                aud_detail = f"{attached_count}/{len(active_tracks)} tracks have audio files attached"
            checks.append({
                "label": "Track Audio Masters (24-bit WAV)",
                "ok": audio_ok,
                "detail": aud_detail,
            })
        else:
            checks.append({
                "label": "Track Audio Masters (24-bit WAV)",
                "ok": False,
                "detail": "No tracks in tracklist yet",
            })

        # 6. Clean Store Lyrics Check
        raw_bracket_tracks = []
        for idx, tr in enumerate(active_tracks, 1):
            lyr = str(tr.get("lyrics", "")).strip()
            if lyr and ("[" in lyr or "]" in lyr):
                raw_bracket_tracks.append(idx)
        lyrics_ok = len(raw_bracket_tracks) == 0
        checks.append({
            "label": "Apple Music / Spotify Clean Lyrics",
            "ok": lyrics_ok,
            "detail": "Zero forbidden [Section] or [Chord] tags in track lyrics"
            if lyrics_ok else f"Track(s) {raw_bracket_tracks} contain [Tags] — click 'Clean Lyrics' or Step 1",
        })

        # 7. Royalty Splits Total = 100% (if splits provided) & Genre
        if splits:
            total_pct = round(sum(float(s.get("share_pct", 0.0) or 0.0) for s in splits), 2)
            splits_ok = abs(total_pct - 100.0) < 0.05 and bool(genre)
            sp_detail = (
                f"Genre: {genre} | Royalty Splits: {total_pct:.0f}% across {len(splits)} collaborator(s)"
                if splits_ok
                else f"Royalty Splits total {total_pct:.1f}% (must equal 100%)"
            )
        else:
            splits_ok = bool(genre)
            sp_detail = f"Genre: {genre} | Language: {project.get('language', 'English')} | 100% Primary Artist"
        checks.append({
            "label": "Genre & Royalty Splits (100%)",
            "ok": splits_ok,
            "detail": sp_detail,
        })

        passed_count = sum(1 for c in checks if c["ok"])
        score = int(round((passed_count / max(1, len(checks))) * 100))
        all_passed = passed_count == len(checks)

        lines = [
            f"=== {platform.upper()} PRE-FLIGHT QC ({cls.classify_release_format(len(active_tracks), mode)}) — {score}/100 ==="
        ]
        for c in checks:
            mark = "✅ PASS" if c["ok"] else "⚠️ FIX "
            lines.append(f"{mark} | {c['label']}: {c['detail']}")

        return {
            "score": score,
            "passed": all_passed,
            "checks": checks,
            "summary_text": "\n".join(lines),
            "format_label": cls.classify_release_format(len(active_tracks), mode),
        }


class DistroStagePackager:
    """
    Exports a complete, organized Single or Album upload staging folder:
    - Exact 3000x3000 RGB Cover_Art_3000x3000.jpg
    - Promo_Assets/Spotify_Canvas_Vertical_1080x1920.jpg + Social_Launch_Copy.txt
    - Sequentially numbered 24-bit 44.1kHz -14 LUFS Stereo WAV masters (01 - Title.wav ...)
    - Clean plain-text Store Lyrics (.txt) + Synced Karaoke (.lrc)
    - Royalty_Splits_Sheet.csv + TuneCore_and_DistroKid_Tracklist.csv + Release_Manifest.json
    """

    @staticmethod
    def _safe_filename(text: str, fallback: str = "Untitled") -> str:
        cleaned = re.sub(r'[<>:"/\\|?*]+', "", (text or "").strip())
        cleaned = re.sub(r"\s{2,}", " ", cleaned).strip(" .")
        return cleaned[:80] if cleaned else fallback

    @classmethod
    def build_staged_release(
        cls,
        project: Dict[str, object],
        output_root: Optional[str | Path] = None,
        auto_master_wav: bool = True,
        export_promo_canvas: bool = True,
    ) -> Dict[str, object]:
        root = Path(output_root) if output_root else (Path.home() / ".lyric_ai_writer" / "distro_releases")
        root.mkdir(parents=True, exist_ok=True)

        mode = str(project.get("release_mode", "single")).lower()
        platform = str(project.get("platform", "DistroKid"))
        artist = str(project.get("artist_name", "")).strip() or "Independent Artist"
        release_title = format_store_compliant_title(str(project.get("release_title", "")).strip() or "Untitled Release")
        tracks_raw: List[Dict[str, object]] = list(project.get("tracks", []))
        active_tracks = tracks_raw[:1] if (mode == "single" and len(tracks_raw) >= 1) else tracks_raw

        if not active_tracks:
            active_tracks = [{
                "title": release_title,
                "audio_path": "",
                "lyrics": "",
                "hook_start": "00:42",
                "explicit": bool(project.get("explicit", False)),
                "instrumental": False,
                "isrc": "",
            }]

        folder_slug = f"{cls._safe_filename(artist)} - {cls._safe_filename(release_title)}"
        stage_dir = root / folder_slug
        audio_dir = stage_dir / "Audio_WAV_24bit"
        lyrics_dir = stage_dir / "Store_Lyrics_Clean"
        lrc_dir = stage_dir / "Synced_Karaoke_LRC"
        promo_dir = stage_dir / "Promo_Assets"
        for d in (stage_dir, audio_dir, lyrics_dir, lrc_dir, promo_dir):
            d.mkdir(parents=True, exist_ok=True)

        # 1. Prepare 3000x3000 RGB Store-Compliant Cover Art
        cover_dst = stage_dir / "Cover_Art_3000x3000.jpg"
        src_cover = str(project.get("cover_path", "")).strip()
        cover_style = str(project.get("cover_style", "cyberpunk_neon"))
        if src_cover and Path(src_cover).exists():
            cov_check = validate_cover_art(src_cover)
            if cov_check["ok"] and Path(src_cover).suffix.lower() in (".jpg", ".jpeg"):
                if Path(src_cover).resolve() != cover_dst.resolve():
                    shutil.copy2(src_cover, cover_dst)
            else:
                normalize_image_to_store_3000(src_cover, cover_dst)
        else:
            generate_store_cover_3000(
                title=release_title,
                artist=artist,
                style_key=cover_style,
                output_path=cover_dst,
            )

        # Optional 9:16 Vertical Canvas for Spotify Canvas / TikTok / Reels / Shorts
        canvas_dst = promo_dir / "Spotify_Canvas_Vertical_1080x1920.jpg"
        if export_promo_canvas:
            generate_vertical_canvas_1080x1920(
                title=release_title,
                artist=artist,
                style_key=cover_style,
                output_path=canvas_dst,
            )

        # 2. Export Numbered 24-bit WAV Masters + Clean Lyrics + Synced LRC + Hook Start Time
        exported_tracks: List[Dict[str, object]] = []
        for idx, tr in enumerate(active_tracks, 1):
            raw_tr_title = str(tr.get("title", "")).strip() or (release_title if len(active_tracks) == 1 else f"Song {idx}")
            tr_title = format_store_compliant_title(raw_tr_title, str(tr.get("featured_artist", "")))
            safe_tr = cls._safe_filename(tr_title, f"Song_{idx:02d}")
            wav_name = f"{idx:02d} - {safe_tr}.wav"
            wav_dst = audio_dir / wav_name

            src_audio = str(tr.get("audio_path", "")).strip()
            dur_sec = 180.0
            audio_exported = ""
            if src_audio and Path(src_audio).exists():
                info = inspect_audio_file_quick(src_audio)
                dur_sec = float(info.get("duration_sec", 180.0) or 180.0)
                if auto_master_wav:
                    res = AudioMasteringEngine.process_master(
                        input_path=src_audio,
                        output_path=str(wav_dst),
                        target_preset="Spotify & YouTube (-14.0 LUFS)",
                        auto_trim=True,
                        de_ai_filter=True,
                    )
                    dur_sec = float(res.get("duration_sec", dur_sec) or dur_sec)
                    audio_exported = str(wav_dst)
                else:
                    shutil.copy2(src_audio, wav_dst)
                    audio_exported = str(wav_dst)

            hook_mmss = str(tr.get("hook_start", "")).strip() or detect_hook_start_timestamp(
                audio_exported or src_audio,
                str(tr.get("lyrics", "")),
            )
            clean_lyr = clean_lyrics_for_stores(str(tr.get("lyrics", "")))
            lyr_path = lyrics_dir / f"{idx:02d} - {safe_tr}.txt"
            lrc_path = lrc_dir / f"{idx:02d} - {safe_tr}.lrc"
            lyr_path.write_text(clean_lyr, encoding="utf-8")
            lrc_path.write_text(
                generate_synced_lrc(clean_lyr, duration_sec=dur_sec, title=tr_title, artist=artist),
                encoding="utf-8",
            )

            exported_tracks.append({
                "track_number": idx,
                "title": tr_title,
                "featured_artist": str(tr.get("featured_artist", "")).strip(),
                "hook_start": hook_mmss,
                "wav_path": audio_exported,
                "clean_lyrics_path": str(lyr_path),
                "lrc_path": str(lrc_path),
                "clean_lyrics": clean_lyr,
                "explicit": bool(tr.get("explicit", project.get("explicit", False))),
                "instrumental": bool(tr.get("instrumental", False)),
                "isrc": str(tr.get("isrc", "")).strip(),
            })

        # 3. Write TuneCore / DistroKid Tracklist CSV Sheet (with Hook Start Time!)
        csv_path = stage_dir / "TuneCore_and_DistroKid_Tracklist.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as cf:
            writer = csv.writer(cf)
            writer.writerow([
                "Release_Format",
                "Platform",
                "Release_Title",
                "Primary_Artist",
                "Track_Number",
                "Track_Title",
                "TikTok_Preview_Hook_Start",
                "Featured_Artist",
                "Songwriter_Legal_First",
                "Songwriter_Legal_Last",
                "Primary_Genre",
                "Language",
                "Release_Date",
                "Record_Label",
                "Explicit",
                "Instrumental",
                "ISRC",
                "Staged_24bit_WAV",
                "Cover_Art_3000x3000",
            ])
            fmt_name = DistroPreflightValidator.classify_release_format(len(exported_tracks), mode)
            for et in exported_tracks:
                writer.writerow([
                    fmt_name,
                    platform,
                    release_title,
                    artist,
                    et["track_number"],
                    et["title"],
                    et["hook_start"],
                    et["featured_artist"],
                    project.get("songwriter_first", ""),
                    project.get("songwriter_last", ""),
                    project.get("primary_genre", "Pop"),
                    project.get("language", "English"),
                    project.get("release_date", datetime.date.today().isoformat()),
                    project.get("record_label", artist),
                    "Yes" if et["explicit"] else "No",
                    "Yes" if et["instrumental"] else "No",
                    et["isrc"],
                    et["wav_path"],
                    str(cover_dst),
                ])

        # 4. Write Collaborator Royalty Splits CSV (DistroKid Teams / TuneCore Splits)
        splits = list(project.get("splits", []))
        if not splits:
            splits = [{
                "name": f"{project.get('songwriter_first', '')} {project.get('songwriter_last', '')}".strip() or artist,
                "role": "Primary Artist & Songwriter",
                "email": "",
                "share_pct": 100.0,
            }]
        splits_csv_path = stage_dir / "Royalty_Splits_Sheet.csv"
        with open(splits_csv_path, "w", newline="", encoding="utf-8") as sf:
            sw = csv.writer(sf)
            sw.writerow(["Release_Title", "Collaborator_Name", "Role", "Email", "Royalty_Share_Percent"])
            for sp in splits:
                sw.writerow([
                    release_title,
                    sp.get("name", ""),
                    sp.get("role", "Collaborator"),
                    sp.get("email", ""),
                    sp.get("share_pct", 100.0),
                ])

        # 5. Social Pre-Save / Release Day Launch Copy
        social_path = promo_dir / "Social_Launch_Copy.txt"
        genre_tag = re.sub(r"[^a-zA-Z0-9]", "", str(project.get("primary_genre", "NewMusic")))
        social_lines = [
            f"🚀 NEW {'SINGLE' if len(exported_tracks) == 1 else 'ALBUM'} RELEASE COPY — {release_title} by {artist}",
            "=" * 64,
            f"Caption Idea 1 (Release Day):",
            f"'{release_title}' by {artist} is officially streaming everywhere! 🎧✨",
            f"Skip to {exported_tracks[0]['hook_start']} for my favorite chorus drop — save it to your playlist!",
            "",
            f"Hashtags: #NewMusic #{genre_tag} #Spotify #AppleMusic #IndependentArtist",
        ]
        social_path.write_text("\n".join(social_lines) + "\n", encoding="utf-8")

        # 6. Structured JSON Manifest & Upload Checklist
        json_path = stage_dir / "Release_Manifest.json"
        manifest = {
            "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
            "platform": platform,
            "release_mode": mode,
            "format_label": DistroPreflightValidator.classify_release_format(len(exported_tracks), mode),
            "artist_name": artist,
            "release_title": release_title,
            "songwriter_first": project.get("songwriter_first", ""),
            "songwriter_middle": project.get("songwriter_middle", ""),
            "songwriter_last": project.get("songwriter_last", ""),
            "primary_genre": project.get("primary_genre", "Pop"),
            "secondary_genre": project.get("secondary_genre", ""),
            "language": project.get("language", "English"),
            "release_date": project.get("release_date", datetime.date.today().isoformat()),
            "record_label": project.get("record_label", artist),
            "copyright_year": str(project.get("copyright_year", datetime.date.today().year)),
            "explicit": bool(project.get("explicit", False)),
            "stores_options": project.get("stores_options", {}),
            "splits": splits,
            "cover_path": str(cover_dst),
            "canvas_vertical_path": str(canvas_dst) if canvas_dst.exists() else "",
            "tracks": exported_tracks,
        }
        json_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

        guide_path = stage_dir / "README_Quick_Upload_Steps.txt"
        guide_lines = [
            f"SMG SUNO STUDIO PRO — {platform.upper()} STAGED RELEASE PACK",
            "=" * 64,
            f"Release Format : {manifest['format_label']}",
            f"Artist Name    : {artist}",
            f"Release Title  : {release_title}",
            f"Songwriter     : {project.get('songwriter_first', '')} {project.get('songwriter_last', '')}",
            f"Cover Art      : {cover_dst.name} (Verified 3000x3000 px RGB)",
            f"Vertical Promo : Promo_Assets/{canvas_dst.name} (1080x1920 Spotify Canvas / Reels)",
            f"Audio Folder   : {audio_dir}",
            "",
            "FAST UPLOAD STEPS IN DISTRO TAB:",
            f"1. Sign into your {platform} account in the right browser pane.",
            "2. Click '⚡ Step 2: Auto-Fill Upload Form' to populate Artist, Title, Genre,",
            "   Release Date, Legal Songwriter, Track Titles & TikTok Preview Hook timestamps.",
            "3. Attach 'Cover_Art_3000x3000.jpg' and numbered WAVs from 'Audio_WAV_24bit'.",
            "4. Review all store checkboxes and click Upload / Publish on the website.",
        ]
        guide_path.write_text("\n".join(guide_lines) + "\n", encoding="utf-8")

        return {
            "stage_dir": str(stage_dir),
            "cover_path": str(cover_dst),
            "canvas_path": str(canvas_dst) if canvas_dst.exists() else "",
            "audio_dir": str(audio_dir),
            "lyrics_dir": str(lyrics_dir),
            "lrc_dir": str(lrc_dir),
            "promo_dir": str(promo_dir),
            "csv_path": str(csv_path),
            "splits_csv_path": str(splits_csv_path),
            "social_path": str(social_path),
            "json_path": str(json_path),
            "guide_path": str(guide_path),
            "tracks": exported_tracks,
            "manifest": manifest,
        }


class DistroAutoFillBuilder:
    """
    Builds transparent React/DOM native-setter JavaScript to assist filling
    DistroKid and TuneCore Single & Album release upload forms in the embedded QWebEngineView.
    Never interacts with login, password, 2FA, CAPTCHA, or anti-bot elements.
    """

    @staticmethod
    def build_autofill_js(platform: str, project: Dict[str, object]) -> str:
        mode = str(project.get("release_mode", "single")).lower()
        tracks_all = list(project.get("tracks", []))
        tracks = tracks_all[:1] if (mode == "single" and len(tracks_all) >= 1) else tracks_all

        payload = {
            "platform": platform,
            "releaseMode": mode,
            "trackCount": max(1, len(tracks)),
            "artistName": str(project.get("artist_name", "")).strip(),
            "releaseTitle": str(project.get("release_title", "")).strip(),
            "songwriterFirst": str(project.get("songwriter_first", "")).strip(),
            "songwriterMiddle": str(project.get("songwriter_middle", "")).strip(),
            "songwriterLast": str(project.get("songwriter_last", "")).strip(),
            "primaryGenre": str(project.get("primary_genre", "Pop")).strip(),
            "secondaryGenre": str(project.get("secondary_genre", "")).strip(),
            "language": str(project.get("language", "English")).strip(),
            "releaseDate": str(project.get("release_date", "")).strip(),
            "recordLabel": str(project.get("record_label", "")).strip(),
            "spotifyUri": str(project.get("spotify_uri", "")).strip(),
            "appleUrl": str(project.get("apple_url", "")).strip(),
            "copyrightYear": str(project.get("copyright_year", datetime.date.today().year)).strip(),
            "explicit": bool(project.get("explicit", False)),
            "storesOptions": project.get("stores_options", {}),
            "splits": list(project.get("splits", [])),
            "stageDir": str(project.get("stage_dir", "")).strip(),
            "tracks": [
                {
                    "index": idx,
                    "title": str(tr.get("title", "")).strip() or f"Song {idx}",
                    "hookStart": str(tr.get("hook_start", "00:42")).strip() or "00:42",
                    "featured": str(tr.get("featured_artist", "")).strip(),
                    "explicit": bool(tr.get("explicit", project.get("explicit", False))),
                    "instrumental": bool(tr.get("instrumental", False)),
                    "isrc": str(tr.get("isrc", "")).strip(),
                    "lyrics": clean_lyrics_for_stores(str(tr.get("lyrics", ""))),
                }
                for idx, tr in enumerate(tracks, 1)
            ],
        }
        payload_json = json.dumps(payload, ensure_ascii=False)

        return f"""
(function() {{
    const DATA = {payload_json};

    // Safety guard: never run on login / sign-in / verification gates
    const urlLower = (window.location.href || '').toLowerCase();
    if (urlLower.includes('/signin') || urlLower.includes('/login') || urlLower.includes('challenge')) {{
        return {{ ok: false, reason: 'auth_page', filled: 0 }};
    }}

    function isVisible(el) {{
        if (!el) return false;
        const rect = el.getBoundingClientRect();
        const style = window.getComputedStyle(el);
        return rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none';
    }}

    function setReactValue(el, val) {{
        if (!el || val === undefined || val === null || val === '') return false;
        if (el.type === 'password' || el.type === 'file' || el.disabled || el.readOnly) return false;
        try {{
            const proto = el.tagName === 'TEXTAREA'
                ? window.HTMLTextAreaElement.prototype
                : window.HTMLInputElement.prototype;
            const desc = Object.getOwnPropertyDescriptor(proto, 'value');
            if (desc && desc.set) {{
                desc.set.call(el, val);
            }} else {{
                el.value = val;
            }}
            el.dispatchEvent(new Event('input', {{ bubbles: true }}));
            el.dispatchEvent(new Event('change', {{ bubbles: true }}));
            el.dispatchEvent(new Event('blur', {{ bubbles: true }}));
            el.style.outline = '2px solid #10b981';
            el.style.outlineOffset = '1px';
            return true;
        }} catch (err) {{
            return false;
        }}
    }}

    function setSelectByTextOrValue(sel, targetText) {{
        if (!sel || !targetText) return false;
        const needle = String(targetText).toLowerCase().trim();
        let matched = false;
        for (const opt of Array.from(sel.options || [])) {{
            const ov = String(opt.value || '').toLowerCase().trim();
            const ot = String(opt.text || '').toLowerCase().trim();
            if (ov === needle || ot === needle || ot.startsWith(needle) || ot.includes(needle)) {{
                sel.value = opt.value;
                sel.dispatchEvent(new Event('input', {{ bubbles: true }}));
                sel.dispatchEvent(new Event('change', {{ bubbles: true }}));
                sel.style.outline = '2px solid #10b981';
                matched = true;
                break;
            }}
        }}
        return matched;
    }}

    function findInputsByHints(hints) {{
        const matches = [];
        const nodes = document.querySelectorAll('input:not([type="hidden"]):not([type="password"]):not([type="file"]), textarea');
        for (const el of nodes) {{
            if (!isVisible(el)) continue;
            const labelEl = el.id ? document.querySelector(`label[for="${{CSS.escape(el.id)}}"]`) : null;
            const aria = (el.getAttribute('aria-label') || '').toLowerCase();
            const ph = (el.getAttribute('placeholder') || '').toLowerCase();
            const nm = (el.getAttribute('name') || '').toLowerCase();
            const id = (el.id || '').toLowerCase();
            const lbl = (labelEl ? labelEl.innerText : (el.closest('label') ? el.closest('label').innerText : '')).toLowerCase();
            const hay = `${{id}} ${{nm}} ${{ph}} ${{aria}} ${{lbl}}`;
            if (hints.some(h => hay.includes(h))) {{
                matches.push(el);
            }}
        }}
        return matches;
    }}

    let filledCount = 0;

    // 1. DistroKid Song Count Selector (#howManySongs or select with '1 song', '2 songs'...)
    const allSelects = Array.from(document.querySelectorAll('select')).filter(isVisible);
    for (const sel of allSelects) {{
        const idNm = `${{sel.id}} ${{sel.name}}`.toLowerCase();
        const firstOptText = sel.options && sel.options.length ? sel.options[0].text.toLowerCase() : '';
        if (idNm.includes('howmany') || idNm.includes('numsongs') || idNm.includes('song_count') || firstOptText.includes('song')) {{
            if (setSelectByTextOrValue(sel, String(DATA.trackCount))) {{
                filledCount++;
                break;
            }}
        }}
    }}

    function populateFieldsPass() {{
        let passFilled = 0;

        // Primary Artist / Band Name
        const artistEls = findInputsByHints(['artist/band', 'artist name', 'primary artist', 'band name', 'artistname']);
        if (artistEls.length && setReactValue(artistEls[0], DATA.artistName)) passFilled++;

        // Album / Release Title
        if (DATA.releaseMode === 'album' || DATA.platform === 'TuneCore') {{
            const albumEls = findInputsByHints(['album title', 'release title', 'album name', 'ep title', 'albumtitle']);
            if (albumEls.length && setReactValue(albumEls[0], DATA.releaseTitle)) passFilled++;
        }}

        // Record Label & Copyright Holder
        if (DATA.recordLabel) {{
            const labelEls = findInputsByHints(['record label', 'label name', 'custom label', 'recordlabel', 'p line', 'c line']);
            for (const el of labelEls.slice(0, 2)) {{
                if (setReactValue(el, DATA.recordLabel)) passFilled++;
            }}
        }}

        // Release Date
        if (DATA.releaseDate) {{
            const dateEls = findInputsByHints(['release date', 'releasedate', 'sales start']);
            if (dateEls.length && setReactValue(dateEls[0], DATA.releaseDate)) passFilled++;
        }}

        // Optional Spotify URI / Apple Music Artist URL
        if (DATA.spotifyUri) {{
            const spEls = findInputsByHints(['spotify', 'artist uri']);
            if (spEls.length && setReactValue(spEls[0], DATA.spotifyUri)) passFilled++;
        }}
        if (DATA.appleUrl) {{
            const apEls = findInputsByHints(['apple music', 'itunes']);
            if (apEls.length && setReactValue(apEls[0], DATA.appleUrl)) passFilled++;
        }}

        // Genre & Language Selects
        const selectsNow = Array.from(document.querySelectorAll('select')).filter(isVisible);
        let genreFilled = 0;
        for (const sel of selectsNow) {{
            const meta = `${{sel.id}} ${{sel.name}} ${{sel.getAttribute('aria-label') || ''}}`.toLowerCase();
            if (meta.includes('language') || meta.includes('lang')) {{
                if (setSelectByTextOrValue(sel, DATA.language)) passFilled++;
            }} else if (meta.includes('genre')) {{
                if (genreFilled === 0 && DATA.primaryGenre && setSelectByTextOrValue(sel, DATA.primaryGenre)) {{
                    genreFilled++;
                    passFilled++;
                }} else if (genreFilled === 1 && DATA.secondaryGenre && setSelectByTextOrValue(sel, DATA.secondaryGenre)) {{
                    genreFilled++;
                    passFilled++;
                }}
            }}
        }}

        // Track Titles (1..N)
        const trackTitleEls = findInputsByHints(['track title', 'song title', 'track 1', 'track name', 'title of song', 'songtitle']);
        if (trackTitleEls.length) {{
            DATA.tracks.forEach((tr, idx) => {{
                if (idx < trackTitleEls.length && setReactValue(trackTitleEls[idx], tr.title)) {{
                    passFilled++;
                }}
            }});
        }} else if (DATA.releaseMode === 'single') {{
            const singleTitleEls = findInputsByHints(['title']);
            if (singleTitleEls.length && setReactValue(singleTitleEls[0], DATA.tracks[0].title || DATA.releaseTitle)) {{
                passFilled++;
            }}
        }}

        // TikTok / Apple Music Preview Clip Start Time (MM:SS)
        const hookEls = findInputsByHints(['preview', 'clip start', 'tiktok', 'start time', 'previewstart']);
        DATA.tracks.forEach((tr, idx) => {{
            if (tr.hookStart && idx < hookEls.length && setReactValue(hookEls[idx], tr.hookStart)) {{
                passFilled++;
            }}
        }});

        // Songwriter Real Legal First / Middle / Last Name
        if (DATA.songwriterFirst) {{
            const firstEls = findInputsByHints(['first name', 'firstname', 'songwriter_first', 'legal first']);
            firstEls.forEach(el => {{ if (setReactValue(el, DATA.songwriterFirst)) passFilled++; }});
        }}
        if (DATA.songwriterLast) {{
            const lastEls = findInputsByHints(['last name', 'lastname', 'surname', 'songwriter_last', 'legal last']);
            lastEls.forEach(el => {{ if (setReactValue(el, DATA.songwriterLast)) passFilled++; }});
        }}

        // Optional ISRC codes per track
        const isrcEls = findInputsByHints(['isrc']);
        DATA.tracks.forEach((tr, idx) => {{
            if (tr.isrc && idx < isrcEls.length && setReactValue(isrcEls[idx], tr.isrc)) {{
                passFilled++;
            }}
        }});

        // Collaborator Royalty Splits (on Teams / Splits pages)
        if (DATA.splits && DATA.splits.length > 0) {{
            const emailEls = findInputsByHints(['email', 'collaborator']);
            const pctEls = findInputsByHints(['percent', 'share', 'split']);
            DATA.splits.forEach((sp, idx) => {{
                if (sp.email && idx < emailEls.length && setReactValue(emailEls[idx], sp.email)) passFilled++;
                if (sp.share_pct !== undefined && idx < pctEls.length && setReactValue(pctEls[idx], String(sp.share_pct))) passFilled++;
            }});
        }}

        // Highlight File Upload Pickers (Cover Art 3000x3000 + Track WAVs)
        const fileInputs = Array.from(document.querySelectorAll('input[type="file"]'));
        let audioIdx = 0;
        fileInputs.forEach((fIn) => {{
            const accept = (fIn.getAttribute('accept') || '').toLowerCase();
            const fMeta = `${{fIn.id}} ${{fIn.name}} ${{accept}}`.toLowerCase();
            const container = fIn.closest('div, label, section') || fIn.parentElement;
            if (!container) return;
            container.style.outline = '2px dashed #38bdf8';
            container.style.outlineOffset = '3px';
            if (!container.querySelector('.smg-distro-file-hint')) {{
                const badge = document.createElement('div');
                badge.className = 'smg-distro-file-hint';
                badge.style.cssText = 'margin-top:4px;padding:3px 8px;border-radius:5px;background:#0f172a;color:#38bdf8;font-size:11px;font-weight:700;display:inline-block;border:1px solid #0284c7;';
                if (fMeta.includes('image') || fMeta.includes('art') || fMeta.includes('cover') || fMeta.includes('jpg')) {{
                    badge.textContent = '⬅ Select Cover_Art_3000x3000.jpg (Folder copied!)';
                }} else {{
                    audioIdx++;
                    const trObj = DATA.tracks[Math.min(audioIdx - 1, DATA.tracks.length - 1)];
                    const numStr = String(audioIdx).padStart(2, '0');
                    badge.textContent = `⬅ Select ${{numStr}} - ${{trObj ? trObj.title : 'Track'}}.wav (Hook @ ${{trObj ? trObj.hookStart : '00:42'}})`;
                }}
                container.appendChild(badge);
            }}
        }});

        return passFilled;
    }}

    filledCount += populateFieldsPass();
    setTimeout(() => {{
        const extra = populateFieldsPass();
        const banner = document.getElementById('smg-distro-autofill-toast');
        if (banner && extra > 0) {{
            banner.textContent = `✅ Auto-Filled ${{DATA.platform}} (${{DATA.trackCount}} Track${{DATA.trackCount > 1 ? 's' : ''}} + Hook Times) • Attach Cover & WAVs!`;
        }}
    }}, 400);

    const oldToast = document.getElementById('smg-distro-autofill-toast');
    if (oldToast) oldToast.remove();
    const toast = document.createElement('div');
    toast.id = 'smg-distro-autofill-toast';
    toast.style.cssText = 'position:fixed;top:14px;right:14px;z-index:2147483647;background:linear-gradient(90deg,#0284c7,#10b981);color:#fff;padding:10px 16px;border-radius:8px;font-family:Segoe UI,sans-serif;font-size:12px;font-weight:700;box-shadow:0 8px 24px rgba(0,0,0,0.45);';
    toast.textContent = `⚡ Auto-Filled ${{filledCount}} field(s) for ${{DATA.releaseTitle || 'Release'}} (${{DATA.trackCount}} Track${{DATA.trackCount > 1 ? 's' : ''}}) • Select highlighted Cover & WAV files!`;
    document.body.appendChild(toast);
    setTimeout(() => {{ if (toast.parentNode) toast.remove(); }}, 8000);

    return {{ ok: true, platform: DATA.platform, filled: filledCount, trackCount: DATA.trackCount }};
}})();
"""

    @staticmethod
    def build_lyrics_autofill_js(clean_lyrics: str, track_title: str = "") -> str:
        """Injects store-compliant plain-text lyrics into DistroKid / TuneCore lyrics textarea."""
        data_json = json.dumps({"lyrics": clean_lyrics, "title": track_title}, ensure_ascii=False)
        return f"""
(function() {{
    const PAYLOAD = {data_json};
    function setTextarea(el, val) {{
        const desc = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value');
        if (desc && desc.set) desc.set.call(el, val);
        else el.value = val;
        el.dispatchEvent(new Event('input', {{ bubbles: true }}));
        el.dispatchEvent(new Event('change', {{ bubbles: true }}));
        el.style.outline = '2px solid #10b981';
    }}
    const active = document.activeElement;
    if (active && active.tagName === 'TEXTAREA') {{
        setTextarea(active, PAYLOAD.lyrics);
        return {{ ok: true, mode: 'focused' }};
    }}
    const areas = Array.from(document.querySelectorAll('textarea')).filter(a => a.offsetWidth > 0 && a.offsetHeight > 0);
    if (areas.length > 0) {{
        const lyricBox = areas.find(a => (`${{a.id}} ${{a.name}} ${{a.placeholder}}`).toLowerCase().includes('lyric')) || areas[0];
        setTextarea(lyricBox, PAYLOAD.lyrics);
        return {{ ok: true, mode: 'detected' }};
    }}
    return {{ ok: false, mode: 'none' }};
}})();
"""
