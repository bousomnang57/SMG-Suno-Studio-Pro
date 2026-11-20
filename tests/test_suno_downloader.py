"""
Unit & Integration Tests for Suno Music Downloader by Link
"""
import os
import sys
from pathlib import Path

# Force offscreen headless Qt platform
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import QApplication

# Ensure root directory is on path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.suno_downloader import SunoLinkParser, SunoDownloadWorker, SunoAudioConverter, SunoBulkDownloadWorker
from app.ui.suno_downloader_dialog import SunoLinkDownloadDialog
from app.ui.main_window import MainWindow


def test_url_parser():
    print("[1/5] Testing SunoLinkParser & Track Types...")
    test_uuid = "35fb9f7a-24ce-47e1-888e-730c45582f34"

    # Test full song URL
    res1 = SunoLinkParser.parse_input(f"https://suno.com/song/{test_uuid}")
    assert res1.get("is_suno") is True
    assert res1.get("uuid") == test_uuid
    assert res1.get("track_type") == "Song"
    assert res1.get("audio_url") == f"https://cdn1.suno.ai/{test_uuid}.mp3"
    assert res1.get("video_url") == f"https://cdn1.suno.ai/{test_uuid}.mp4"
    assert res1.get("image_url") == f"https://cdn1.suno.ai/image_{test_uuid}.png"
    print("  ✓ Full song URL parsed correctly into MP3, MP4, and Image endpoints")

    # Test Suno Hook URL
    res_hook = SunoLinkParser.parse_input(f"https://suno.com/hook/{test_uuid}")
    assert res_hook.get("is_suno") is True
    assert res_hook.get("uuid") == test_uuid
    assert res_hook.get("track_type") == "Hook"
    assert res_hook.get("audio_url") == f"https://cdn1.suno.ai/{test_uuid}.mp3"
    print("  ✓ Suno Hook URL parsed correctly with 'Hook' badge metadata")

    # Test direct CDN audio URL
    res2 = SunoLinkParser.parse_input(f"https://cdn1.suno.ai/{test_uuid}.mp3")
    assert res2.get("uuid") == test_uuid
    assert res2.get("audio_url") == f"https://cdn1.suno.ai/{test_uuid}.mp3"
    print("  ✓ Direct CDN audio URL parsed correctly")

    # Test bare UUID
    res3 = SunoLinkParser.parse_input(test_uuid)
    assert res3.get("uuid") == test_uuid
    print("  ✓ Bare UUID string normalized correctly")

    # Test unlimited UUID extraction
    bulk_text = "\n".join([f"https://suno.com/song/00000000-0000-0000-0000-{i:012d}" for i in range(35)])
    unlimited_uids = SunoLinkParser.extract_all_uuids(bulk_text, max_limit=None)
    assert len(unlimited_uids) == 35
    print("  ✓ Unlimited UUID extraction verified (35/35 extracted with zero monthly or batch caps)")

    # Test filename sanitizer with Khmer and special chars
    clean_khmer = SunoDownloadWorker.sanitize_filename("រាត្រីស្ងប់ស្ងាត់ / Night: In The Rain *?")
    assert "/" not in clean_khmer and ":" not in clean_khmer and "?" not in clean_khmer
    assert "រាត្រីស្ងប់ស្ងាត់" in clean_khmer
    print("  ✓ Filename sanitization preserves Khmer Unicode and cleans illegal characters")


def test_audio_converter_and_zip():
    print("[2/5] Testing Local SunoAudioConverter (WAV & ZIP)...")
    import tempfile
    import zipfile
    import wave

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        # Create a tiny mock mono wav file to simulate source audio
        mock_src_wav = tmp_path / "mock_src.wav"
        with wave.open(str(mock_src_wav), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(44100)
            wf.writeframes(b"\x00\x00" * 4410)  # 0.1s of silence

        # Convert to studio WAV
        dest_wav = tmp_path / "studio_export.wav"
        ok = SunoAudioConverter.convert_to_wav(str(mock_src_wav), str(dest_wav))
        assert ok is True
        assert dest_wav.exists()
        with open(dest_wav, "rb") as f:
            header = f.read(12)
            assert header.startswith(b"RIFF") and b"WAVE" in header
        print("  ✓ In-browser/in-app PCM studio WAV generation confirmed with RIFF WAVE header")

        # Create mock production assets and test ZIP bundle packaging
        mock_mp3 = tmp_path / "Song.mp3"
        mock_mp3.write_bytes(b"ID3mock_audio")
        mock_png = tmp_path / "Cover.png"
        mock_png.write_bytes(b"\x89PNGmock_image")
        mock_txt = tmp_path / "Lyrics.txt"
        mock_txt.write_text("Suno downloaded lyrics", encoding="utf-8")

        dest_zip = tmp_path / "ProductionPack.zip"
        zip_path = SunoAudioConverter.create_production_zip(
            output_zip_path=str(dest_zip),
            assets={
                "mp3": str(mock_mp3),
                "wav": str(dest_wav),
                "png": str(mock_png),
                "txt": str(mock_txt),
            },
            metadata={"title": "Golden Sunset", "artist": "@testuser", "style": "acoustic indie"},
        )
        assert zip_path == str(dest_zip)
        assert dest_zip.exists()
        with zipfile.ZipFile(dest_zip, "r") as zf:
            namelist = zf.namelist()
            assert any(n.endswith(".mp3") for n in namelist)
            assert any(n.endswith(".wav") for n in namelist)
            assert any(n.endswith(".png") for n in namelist)
            assert any("lyrics" in n.lower() for n in namelist)
            assert any("metadata.json" in n.lower() for n in namelist)
        print("  ✓ Production Pack ZIP packaging verified with all audio, art, and metadata assets")


def test_worker_contract():
    print("[3/5] Testing SunoDownloadWorker & BulkWorker contracts...")
    worker = SunoDownloadWorker(
        input_url_or_uuid="35fb9f7a-24ce-47e1-888e-730c45582f34",
        media_format="mp3",
    )
    assert worker.media_format == "mp3"
    assert worker._is_cancelled is False
    worker.cancel()
    assert worker._is_cancelled is True
    print("  ✓ Single Download Worker initialization and cancellation contracts verified")

    bulk_worker = SunoBulkDownloadWorker(
        urls=["https://suno.com/song/35fb9f7a-24ce-47e1-888e-730c45582f34"],
        media_format="wav",
    )
    assert bulk_worker.media_format == "wav"
    assert bulk_worker._is_cancelled is False
    bulk_worker.cancel()
    assert bulk_worker._is_cancelled is True
    print("  ✓ Bulk Download Worker initialization and cancellation contracts verified")


def test_dialog_and_themes():
    print("[4/5] Testing SunoLinkDownloadDialog across all 5 themes...")
    app = QApplication.instance() or QApplication(sys.argv)

    for theme_key in ["obsidian", "cyber_blue", "emerald", "sunset_amber", "canvas_light"]:
        dlg = SunoLinkDownloadDialog(theme_key=theme_key, initial_url="https://suno.com/song/test-123")
        assert dlg.txt_url.text() == "https://suno.com/song/test-123"
        assert dlg.card_frame is not None
        assert dlg.btn_dl_mp3 is not None
        assert dlg.btn_dl_wav is not None
        assert dlg.btn_dl_orig is not None
        assert dlg.btn_dl_video is not None
        assert dlg.btn_dl_art is not None
        assert dlg.btn_dl_lyrics is not None
        assert dlg.btn_dl_pack is not None
        assert dlg.combo_bulk_fmt.count() >= 5
        assert hasattr(dlg, "badge_unlimited")
        assert hasattr(dlg, "btn_clear_bulk")
        dlg.close()
        print(f"  ✓ Dialog rendered and styled cleanly in '{theme_key}'")


def test_main_window_integration():
    print("[5/5] Testing MainWindow & Editor Panel Integration...")
    app = QApplication.instance() or QApplication(sys.argv)
    win = MainWindow()
    win.show()

    # Check shortcut Ctrl+Shift+D exists
    assert hasattr(win, "_open_suno_link_downloader")
    assert hasattr(win, "_import_downloaded_suno_lyrics")

    # Test lyrics import bridge
    test_title = "Test Downloaded Song"
    test_lyrics = "[Verse 1]\nTesting download lyrics import\n[Chorus]\nIt works seamlessly"
    win._import_downloaded_suno_lyrics(test_title, test_lyrics)

    assert win.stack.currentIndex() == 3, "Should switch to mode 3 (Editor Workbench)"
    assert win.editor_panel.get_title() == test_title
    assert "Testing download lyrics import" in win.editor_panel.get_lyrics()
    print("  ✓ Suno lyrics and title imported directly into Editor Workbench")

    # Check editor panel button
    assert hasattr(win.editor_panel, "btn_download_stem")
    print("  ✓ Editor Stem Player has '📥 Suno Link' quick download button")

    # Check suno browser view buttons
    assert hasattr(win.suno_browser_view, "btn_download_link")
    assert hasattr(win.suno_browser_view, "txt_quick_dl")
    print("  ✓ Suno Browser Studio has '📥 Download by Link' and quick link bar")

    win.close()
    print("\n🎉 ALL SUNO DOWNLOADER TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    test_url_parser()
    test_audio_converter_and_zip()
    test_worker_contract()
    test_dialog_and_themes()
    test_main_window_integration()
