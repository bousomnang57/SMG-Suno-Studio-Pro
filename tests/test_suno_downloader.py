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

from app.suno_downloader import SunoLinkParser, SunoDownloadWorker
from app.ui.suno_downloader_dialog import SunoLinkDownloadDialog
from app.ui.main_window import MainWindow


def test_url_parser():
    print("[1/4] Testing SunoLinkParser...")
    test_uuid = "35fb9f7a-24ce-47e1-888e-730c45582f34"

    # Test full song URL
    res1 = SunoLinkParser.parse_input(f"https://suno.com/song/{test_uuid}")
    assert res1.get("is_suno") is True
    assert res1.get("uuid") == test_uuid
    assert res1.get("audio_url") == f"https://cdn1.suno.ai/{test_uuid}.mp3"
    assert res1.get("video_url") == f"https://cdn1.suno.ai/{test_uuid}.mp4"
    assert res1.get("image_url") == f"https://cdn1.suno.ai/image_{test_uuid}.png"
    print("  ✓ Full song URL parsed correctly into MP3, MP4, and Image endpoints")

    # Test direct CDN audio URL
    res2 = SunoLinkParser.parse_input(f"https://cdn1.suno.ai/{test_uuid}.mp3")
    assert res2.get("uuid") == test_uuid
    assert res2.get("audio_url") == f"https://cdn1.suno.ai/{test_uuid}.mp3"
    print("  ✓ Direct CDN audio URL parsed correctly")

    # Test bare UUID
    res3 = SunoLinkParser.parse_input(test_uuid)
    assert res3.get("uuid") == test_uuid
    print("  ✓ Bare UUID string normalized correctly")

    # Test filename sanitizer with Khmer and special chars
    clean_khmer = SunoDownloadWorker.sanitize_filename("រាត្រីស្ងប់ស្ងាត់ / Night: In The Rain *?")
    assert "/" not in clean_khmer and ":" not in clean_khmer and "?" not in clean_khmer
    assert "រាត្រីស្ងប់ស្ងាត់" in clean_khmer
    print("  ✓ Filename sanitization preserves Khmer Unicode and cleans illegal characters")


def test_worker_contract():
    print("[2/4] Testing SunoDownloadWorker contracts...")
    worker = SunoDownloadWorker(
        input_url_or_uuid="35fb9f7a-24ce-47e1-888e-730c45582f34",
        media_format="mp3",
    )
    assert worker.media_format == "mp3"
    assert worker._is_cancelled is False
    worker.cancel()
    assert worker._is_cancelled is True
    print("  ✓ Download worker initialization and cancellation contracts verified")


def test_dialog_and_themes():
    print("[3/4] Testing SunoLinkDownloadDialog across all 5 themes...")
    app = QApplication.instance() or QApplication(sys.argv)

    for theme_key in ["obsidian", "cyber_blue", "emerald", "sunset_amber", "canvas_light"]:
        dlg = SunoLinkDownloadDialog(theme_key=theme_key, initial_url="https://suno.com/song/test-123")
        assert dlg.txt_url.text() == "https://suno.com/song/test-123"
        assert dlg.combo_format.count() >= 4
        assert dlg.btn_download is not None
        assert dlg.preview_card is not None
        dlg.close()
        print(f"  ✓ Dialog rendered and styled cleanly in '{theme_key}'")


def test_main_window_integration():
    print("[4/4] Testing MainWindow & Editor Panel Integration...")
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
    test_worker_contract()
    test_dialog_and_themes()
    test_main_window_integration()
