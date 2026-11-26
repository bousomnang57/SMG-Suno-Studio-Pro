"""
Comprehensive Automated Verification Suite for Mode 7 (8th Studio Tab):
DistroKid & TuneCore Single Song & Full Album Auto-Upload Studio (v2 Clean Pro Edition).
"""
import os
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np
from PIL import Image

os.environ["QT_QPA_PLATFORM"] = "offscreen"

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import QApplication

from app.distro_packager import (
    DistroAutoFillBuilder,
    DistroPreflightValidator,
    DistroStagePackager,
    clean_lyrics_for_stores,
    detect_hook_start_timestamp,
    format_store_compliant_title,
    generate_store_cover_3000,
    generate_synced_lrc,
    generate_vertical_canvas_1080x1920,
    has_store_title_warning,
    normalize_image_to_store_3000,
    validate_cover_art,
)
from app.ui.main_window import MainWindow


def _make_test_wav(path_str: str, duration_sec: float = 1.2, sr: int = 44100) -> str:
    t = np.linspace(0, duration_sec, int(sr * duration_sec), endpoint=False)
    left = 0.35 * np.sin(2 * np.pi * 440 * t)
    right = 0.35 * np.sin(2 * np.pi * 554.37 * t)
    stereo = np.column_stack([left, right])
    i16 = np.clip(stereo * 32767.0, -32768, 32767).astype(np.int16)
    with wave.open(path_str, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(i16.tobytes())
    return path_str


def _make_chorus_peak_wav(path_str: str, duration_sec: float = 36.0, sr: int = 22050) -> str:
    """Create a 36s stereo WAV with a clear loud chorus lift between 12s and 27s."""
    n = int(sr * duration_sec)
    t = np.linspace(0, duration_sec, n, endpoint=False)
    env = np.full(n, 0.08, dtype=np.float32)
    env[int(12 * sr):int(27 * sr)] = 0.75  # Loud chorus drop at 00:12!
    sig = env * np.sin(2 * np.pi * 440 * t)
    stereo = np.column_stack([sig, sig])
    i16 = np.clip(stereo * 32767.0, -32768, 32767).astype(np.int16)
    with wave.open(path_str, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(i16.tobytes())
    return path_str


def run_all_tests():
    app = QApplication.instance() or QApplication(sys.argv)

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        tmp = Path(td)

        print("[1/6] Testing Store Title Case Shield, Hook Detector, Lyric Cleaner & 3000px / 9:16 Art...")
        assert has_store_title_warning("01 - SKYLINE FEVER_Mastered_Pro") is not None
        fixed_t = format_store_compliant_title("01 - SKYLINE IN THE NIGHT_Mastered_Pro", featured_artist="Luna")
        assert fixed_t == "Skyline in the Night (feat. Luna)", f"Got: {fixed_t}"
        assert has_store_title_warning(fixed_t) is None

        peak_wav = _make_chorus_peak_wav(str(tmp / "chorus_test.wav"))
        hook_mmss = detect_hook_start_timestamp(peak_wav)
        assert hook_mmss in ("00:11", "00:12", "00:13"), f"Expected ~00:12 chorus hook, got {hook_mmss}"

        raw_suno_lyrics = """[Intro: 120 BPM, Synthpop]
[Am] [F] [C] [G]

[Verse 1: Intimate Female Vocal]
[Am] Streetlights flicker on the [F] wet windshield glass,
[C] Every mile marker lets the [G] old doubts pass!

[Chorus]
(Instrumental Break)
[F] Underneath the [C] midnight neon lights...
"""
        cleaned = clean_lyrics_for_stores(raw_suno_lyrics)
        assert "[" not in cleaned and "]" not in cleaned
        assert "Instrumental Break" not in cleaned
        lrc = generate_synced_lrc(cleaned, duration_sec=150.0, title="Neon", artist="SMG")
        assert "[00:" in lrc

        cov_path = tmp / "store_cover.jpg"
        generate_store_cover_3000("Skyline Dreams", "Alex Rivers", "cyberpunk_neon", cov_path)
        assert validate_cover_art(cov_path)["ok"] is True

        canvas_path = tmp / "canvas_9_16.jpg"
        generate_vertical_canvas_1080x1920("Skyline Dreams", "Alex Rivers", "cyberpunk_neon", canvas_path)
        with Image.open(canvas_path) as cim:
            assert cim.size == (1080, 1920)

        raw_rect = tmp / "rect.png"
        Image.new("RGBA", (800, 600), (40, 80, 160, 255)).save(raw_rect)
        fitted_cov = tmp / "fitted_3000.jpg"
        assert normalize_image_to_store_3000(raw_rect, fitted_cov) == (3000, 3000)
        print("  ✓ Title Case Shield, RMS Chorus Hook Finder, Clean Lyrics, 3000px Cover & 9:16 Canvas verified")

        print("[2/6] Testing Single Song & Multi-Track Album Packager + Royalty Splits CSV...")
        wav1 = _make_test_wav(str(tmp / "song1.wav"))
        wav2 = _make_test_wav(str(tmp / "song2.wav"))
        wav3 = _make_test_wav(str(tmp / "song3.wav"))

        album_proj = {
            "platform": "TuneCore",
            "release_mode": "album",
            "artist_name": "Alex Rivers",
            "release_title": "Neon Odyssey",
            "songwriter_first": "Alexander",
            "songwriter_last": "Rivers",
            "primary_genre": "Electronic",
            "language": "English",
            "release_date": "2026-12-12",
            "record_label": "Rivers Audio",
            "cover_path": str(cov_path),
            "splits": [
                {"name": "Alexander Rivers", "role": "Artist", "email": "alex@example.com", "share_pct": 70.0},
                {"name": "Maya Lin", "role": "Producer", "email": "maya@example.com", "share_pct": 30.0},
            ],
            "tracks": [
                {"title": "Midnight Drive", "audio_path": wav1, "hook_start": "00:38", "lyrics": cleaned},
                {"title": "Starlight Pulse", "audio_path": wav2, "hook_start": "00:44", "lyrics": cleaned},
                {"title": "Ocean Horizon", "audio_path": wav3, "hook_start": "00:50", "lyrics": cleaned},
            ],
        }
        qc_album = DistroPreflightValidator.validate_release(album_proj)
        assert qc_album["passed"] is True and qc_album["score"] == 100
        album_pack = DistroStagePackager.build_staged_release(album_proj, output_root=tmp / "staged_album")
        assert len(album_pack["tracks"]) == 3
        assert Path(album_pack["csv_path"]).exists()
        assert Path(album_pack["splits_csv_path"]).exists()
        assert Path(album_pack["canvas_path"]).exists()
        assert Path(album_pack["social_path"]).exists()
        print("  ✓ Album 100/100 QC, numbered 24-bit WAVs, Splits CSV, 9:16 Canvas & Social Launch Copy verified")

        print("[3/6] Testing DistroKid & TuneCore Auto-Fill JS (Hook Start Times + Splits + Safety Guard)...")
        js_tc = DistroAutoFillBuilder.build_autofill_js("TuneCore", album_proj)
        assert "00:38" in js_tc and "maya@example.com" in js_tc and "auth_page" in js_tc
        print("  ✓ Auto-Fill JS verified with Hook Start Time, Collaborator Splits & Auth Safety Guard")

        print("[4/6] Testing Clean 4-Tab DistroUploadView, Artist Presets, Splits & Drag-and-Drop...")
        win = MainWindow()
        win.resize(1400, 860)
        win.show()
        win._set_studio_mode(7)

        dv = win.distro_view
        assert dv.dock_tabs.count() == 4
        assert dv.dock_tabs.usesScrollButtons() is False

        # Test Artist Profile Save & Reload
        dv.txt_artist_name.setText("Nova Pulse")
        dv.txt_sw_first.setText("Liam")
        dv.txt_sw_last.setText("Carter")
        dv.save_current_artist_profile()
        assert "Nova Pulse" in dv.artist_profiles

        # Test Even Collaborator Splits
        dv._add_collaborator_split()
        dv._balance_even_splits()
        assert abs(sum(float(s["share_pct"]) for s in dv.splits) - 100.0) < 0.01

        # Test Drag-and-Drop File Routing (2 WAVs + 1 Cover Image -> Album Mode!)
        dv.handle_dropped_files([wav1, wav2, str(raw_rect)])
        assert dv.release_mode == "album"
        assert len(dv.tracks) == 2
        assert validate_cover_art(dv.cover_path)["ok"] is True

        # Test Title Fixer Button
        dv.txt_release_title.setText("01 - SUMMER NIGHTS_Mastered_Pro")
        dv.auto_fix_all_store_titles()
        assert dv.txt_release_title.text() == "Summer Nights"
        print("  ✓ Clean 4-Tab UI, Saved Artist Profiles, 100% Splits, Title Shield & Drag-Drop verified")

        print("[5/6] Testing All 5 Studio Themes & Bridges...")
        for th in ["obsidian", "cyber_blue", "emerald", "sunset_amber", "canvas_light"]:
            win.set_theme(th)
            assert dv.theme_key == th
        print("  ✓ All 5 Studio Themes applied cleanly")

        print("[6/6] Releasing multimedia handles...")
        dv.hook_player.stop()
        dv.hook_player.setSource(QUrl())
        win.master_view.player.stop()
        win.master_view.player.setSource(QUrl())
        win.close()
        app.processEvents()

    print("\n🎉 ALL DISTROKID & TUNECORE V2 CLEAN PRO TESTS PASSED 100%!")
    sys.stdout.flush()
    os._exit(0)


if __name__ == "__main__":
    run_all_tests()
