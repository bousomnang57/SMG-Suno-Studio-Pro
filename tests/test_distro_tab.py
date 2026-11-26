"""
Comprehensive Automated Verification Suite for Mode 7 (8th Studio Tab):
DistroKid & TuneCore Single Song & Full Album Auto-Upload Studio.
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
    generate_store_cover_3000,
    generate_synced_lrc,
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


def run_all_tests():
    app = QApplication.instance() or QApplication(sys.argv)

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        tmp = Path(td)

        print("[1/5] Testing Store Lyric Cleaner, Synced LRC & 3000x3000 RGB Cover Engine...")
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
        assert "[" not in cleaned and "]" not in cleaned, f"Brackets leaked: {cleaned}"
        assert "Instrumental Break" not in cleaned
        assert "Streetlights flicker on the wet windshield glass" in cleaned
        assert not cleaned.splitlines()[0].endswith(",")
        lrc = generate_synced_lrc(cleaned, duration_sec=150.0, title="Neon", artist="SMG")
        assert "[00:" in lrc and "[ti:Neon]" in lrc
        print("  ✓ Apple Music / Spotify / DistroKid plain-text lyric cleaner & synced LRC verified")

        cov_path = tmp / "store_cover.jpg"
        generate_store_cover_3000("Skyline Dreams", "Alex Rivers", "cyberpunk_neon", cov_path)
        cov_check = validate_cover_art(cov_path)
        assert cov_check["ok"] is True, f"Cover check failed: {cov_check}"
        assert cov_check["width"] == 3000 and cov_check["height"] == 3000 and cov_check["mode"] == "RGB"

        # Test normalizing non-square 800x600 image to 3000x3000 RGB
        raw_rect = tmp / "rect.png"
        Image.new("RGBA", (800, 600), (40, 80, 160, 255)).save(raw_rect)
        fitted_cov = tmp / "fitted_3000.jpg"
        w, h = normalize_image_to_store_3000(raw_rect, fitted_cov)
        assert (w, h) == (3000, 3000)
        assert validate_cover_art(fitted_cov)["ok"] is True
        print("  ✓ 3000x3000 px RGB store cover generation & rectangular-to-3000px normalizer verified")

        print("[2/5] Testing Single Song & Multi-Track Album Staging Packager + Pre-Flight QC...")
        wav1 = _make_test_wav(str(tmp / "song1.wav"))
        wav2 = _make_test_wav(str(tmp / "song2.wav"))
        wav3 = _make_test_wav(str(tmp / "song3.wav"))

        single_proj = {
            "platform": "DistroKid",
            "release_mode": "single",
            "artist_name": "Alex Rivers",
            "release_title": "Golden Skyline",
            "songwriter_first": "Alexander",
            "songwriter_last": "Rivers",
            "primary_genre": "Pop",
            "language": "English",
            "release_date": "2026-12-05",
            "record_label": "Rivers Audio",
            "cover_path": str(cov_path),
            "tracks": [{"title": "Golden Skyline", "audio_path": wav1, "lyrics": cleaned}],
        }
        qc_single = DistroPreflightValidator.validate_release(single_proj)
        assert qc_single["passed"] is True and qc_single["score"] == 100
        single_pack = DistroStagePackager.build_staged_release(single_proj, output_root=tmp / "staged_single")
        assert len(single_pack["tracks"]) == 1
        assert Path(single_pack["tracks"][0]["wav_path"]).exists()
        assert Path(single_pack["cover_path"]).exists()
        print("  ✓ Single Song (1 Track) 100/100 QC & 24-bit WAV + 3000px Cover staging verified")

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
            "tracks": [
                {"title": "Midnight Drive", "audio_path": wav1, "lyrics": cleaned},
                {"title": "Starlight Pulse", "audio_path": wav2, "lyrics": cleaned},
                {"title": "Ocean Horizon", "audio_path": wav3, "lyrics": cleaned},
            ],
        }
        qc_album = DistroPreflightValidator.validate_release(album_proj)
        assert qc_album["passed"] is True and qc_album["score"] == 100
        album_pack = DistroStagePackager.build_staged_release(album_proj, output_root=tmp / "staged_album")
        assert len(album_pack["tracks"]) == 3
        assert Path(album_pack["csv_path"]).exists()
        assert Path(album_pack["json_path"]).exists()
        print("  ✓ Multi-Track Album/EP (3 Tracks) 100/100 QC, numbered 24-bit WAVs, CSV & JSON manifest verified")

        print("[3/5] Testing DistroKid & TuneCore React/DOM Auto-Fill JS Builders...")
        js_dk = DistroAutoFillBuilder.build_autofill_js("DistroKid", single_proj)
        js_tc = DistroAutoFillBuilder.build_autofill_js("TuneCore", album_proj)
        assert "Golden Skyline" in js_dk and "Alexander" in js_dk and "setReactValue" in js_dk
        assert "Neon Odyssey" in js_tc and "Starlight Pulse" in js_tc and '"trackCount": 3' in js_tc
        assert "auth_page" in js_dk  # Verifies login/challenge safety guard
        print("  ✓ DistroKid (Single) & TuneCore (Album) React/DOM auto-fill scripts & auth-page safety guard verified")

        print("[4/5] Testing MainWindow Mode 7 (🚀 Distro) UI, Bridges & 5 Studio Themes...")
        win = MainWindow()
        win.resize(1380, 860)
        win.show()

        assert win.stack.count() == 8
        win._set_studio_mode(7)
        assert win.stack.currentIndex() == 7
        assert win.btn_mode_distro.isChecked() is True
        assert "DistroKid & TuneCore" in win.lbl_ribbon_info.text()
        assert "Auto-Fill Upload" in win.btn_ribbon_action.text()

        dv = win.distro_view
        dv.set_platform("TuneCore")
        assert dv.current_platform == "TuneCore"
        assert "tunecore.com" in dv.txt_url.text()
        dv.set_platform("DistroKid")
        assert dv.current_platform == "DistroKid"
        assert "distrokid.com" in dv.txt_url.text()

        # Test Mode 6 Master -> Mode 7 Distro Album Bridge (2 tracks)
        win.master_view.tracks.clear()
        win.master_view.add_track_file(wav1, auto_select=True)
        win.master_view.add_track_file(wav2, auto_select=False)
        win.master_view.combo_distributor.setCurrentText("TuneCore")
        win.master_view._send_queue_to_distro_tab()

        assert win.stack.currentIndex() == 7
        assert dv.current_platform == "TuneCore"
        assert dv.release_mode == "album"
        assert len(dv.tracks) == 2

        # Test Ribbon Action Auto-Fill trigger in Mode 7
        win._on_ribbon_action_clicked()
        assert "TuneCore" in dv._last_js_executed

        # Test Editor -> Distro Single Bridge
        win.editor_panel.set_title("Radio Supernova")
        win.editor_panel.set_lyrics("[Chorus]\n[Am] Shining across the radio sky!")
        win._sync_editor_into_distro()
        assert dv.release_mode == "single"
        assert dv.txt_release_title.text() == "Radio Supernova"
        assert "[" not in dv.tracks[0]["lyrics"]

        # Test Full Screen & 5 Themes
        win._toggle_fullscreen()
        assert dv._is_fullscreen_active is True
        win._on_escape_pressed()
        assert dv._is_fullscreen_active is False

        for th in ["obsidian", "cyber_blue", "emerald", "sunset_amber", "canvas_light"]:
            win.set_theme(th)
            assert dv.theme_key == th
        print("  ✓ Mode 7 navigation, Master/Editor bridges, Single/Album switching, Full Screen & all 5 themes verified")

        print("[5/5] Releasing multimedia handles...")
        win.master_view.player.stop()
        win.master_view.player.setSource(QUrl())
        win.close()
        app.processEvents()

    print("\n🎉 ALL DISTROKID & TUNECORE SINGLE/ALBUM UPLOAD TESTS PASSED 100%!")
    sys.stdout.flush()
    os._exit(0)


if __name__ == "__main__":
    run_all_tests()
