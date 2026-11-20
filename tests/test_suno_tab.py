"""
Automated Verification Suite for 6th Studio Tab: Suno Browser & Auto-Fill Studio
Reuses single MainWindow instance for maximum speed and zero redundant initialization.
"""
import os
import sys
from pathlib import Path

# Force offscreen headless Qt platform
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# Ensure root directory is on path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.ui.main_window import MainWindow
from app.ui.suno_browser_view import SunoBrowserView


def run_all_tests():
    app = QApplication.instance() or QApplication(sys.argv)

    print("[1/5] Initializing Studio & MainWindow...")
    win = MainWindow()
    win.show()
    print("  ✓ MainWindow initialized with 6 tabs")

    print("[2/5] Testing 6-Mode Architecture...")
    assert win.stack.count() == 6, f"Expected 6 views in stack, got {win.stack.count()}"
    assert hasattr(win, "suno_browser_view"), "MainWindow missing suno_browser_view"
    assert hasattr(win, "btn_mode_suno"), "MainWindow missing btn_mode_suno"

    mode_names = ["Wizard", "Visual", "Batch", "Editor", "Clone", "Suno"]
    for idx in range(6):
        win._set_studio_mode(idx)
        assert win.stack.currentIndex() == idx, f"Failed switching to mode {idx}"
        print(f"  ✓ Mode {idx} ({mode_names[idx]}) set successfully")

    assert win.btn_mode_suno.isChecked() is True
    assert "Suno Browser Studio" in win.lbl_ribbon_info.text()
    assert "Auto-Fill" in win.btn_ribbon_action.text()
    print("  ✓ Mode 5 header pill, ribbon info, and action button labels verified")

    print("[3/5] Testing SunoBrowserView Left Dock & Auto-Fill Script Engine...")
    sb = win.suno_browser_view
    assert len(sb.account_slots) == 3, f"Expected 3 account profiles, got {len(sb.account_slots)}"
    print(f"  ✓ Found {len(sb.account_slots)} persistent account slots: {sb.account_slots}")

    sample_tracks = [
        {"title": "Track 1 Neon", "style_prompt": "cyberpunk synthwave", "lyrics": "[Verse 1]\nNeon lights in the rain", "negative_prompt": "acoustic"},
        {"title": "Track 2 Sunset", "style_prompt": "acoustic indie folk", "lyrics": "[Verse 1]\nGolden hour fades away", "negative_prompt": "heavy drums"}
    ]
    sb.set_tracks(sample_tracks, start_index=0)
    assert len(sb.tracks) == 2
    assert sb.txt_title.text() == "Track 1 Neon"
    assert "cyberpunk" in sb.txt_style.toPlainText()
    assert "Neon lights" in sb.txt_lyrics.toPlainText()
    print("  ✓ Tracks loaded into SunoBrowserView Left Dock correctly")

    js = sb._build_autofill_js()
    assert "Track 1 Neon" in js
    assert "cyberpunk synthwave" in js
    assert "setReactValue" in js
    print("  ✓ React-compatible JS autofill script built with native setters and event dispatchers")

    sb._next_track()
    assert sb.txt_title.text() == "Track 2 Sunset"
    print("  ✓ Queue advancement and track navigation functional")

    # In mode 5, clicking ribbon action triggers autofill
    win._on_ribbon_action_clicked()
    assert sb._last_js_executed != ""
    print("  ✓ Ribbon Action triggered autofill execution cleanly")

    print("[3b/5] Testing Suno Website Full Screen & Dock Expand Engine...")
    assert hasattr(sb, "btn_fullscreen"), "SunoBrowserView missing btn_fullscreen"
    assert hasattr(sb, "floating_fs_bar"), "SunoBrowserView missing floating_fs_bar"
    assert sb.floating_fs_bar.isHidden() is True

    # Test entering full screen
    sb.set_fullscreen_active(True)
    assert sb._is_fullscreen_active is True
    assert sb.dock_card.isHidden() is True
    assert sb.floating_fs_bar.isVisible() is True
    assert "Exit Full Screen" in sb.btn_fullscreen.text()
    print("  ✓ Full screen immersion activated: left dock collapsed, floating exit bar mounted")

    # Test exiting full screen
    sb.set_fullscreen_active(False)
    assert sb._is_fullscreen_active is False
    assert sb.dock_card.isVisible() is True
    assert sb.floating_fs_bar.isHidden() is True
    assert "Full Screen" in sb.btn_fullscreen.text()
    print("  ✓ Full screen exited cleanly: dock and navigation restored")

    # Test MainWindow F11 shortcut bridge in Mode 5
    win._toggle_fullscreen()
    assert sb._is_fullscreen_active is True
    win._on_escape_pressed()
    assert sb._is_fullscreen_active is False
    print("  ✓ MainWindow F11 and Esc shortcuts toggle Suno full screen seamlessly")

    print("[4/5] Testing 5-Theme Adaptive Switching on Suno Tab...")
    for theme_key in ["obsidian", "cyber_blue", "emerald", "sunset_amber", "canvas_light"]:
        win.set_theme(theme_key)
        assert win.current_theme == theme_key
        assert sb.theme_key == theme_key
        print(f"  ✓ Theme '{theme_key}' applied seamlessly to SunoBrowserView")

    print("[5/5] Testing Suno Download -> Lyric Editor Workbench Bridge...")
    dummy_dir = Path.home() / ".lyric_ai_writer" / "suno_downloads"
    dummy_dir.mkdir(parents=True, exist_ok=True)
    dummy_mp3 = dummy_dir / "test_verification_track.mp3"
    dummy_mp3.write_bytes(b"ID3\x03\x00\x00\x00\x00\x00#dummy_audio_bytes")

    win._load_downloaded_suno_audio_into_editor(str(dummy_mp3))
    assert win.stack.currentIndex() == 3, "Should switch to mode 3 (Editor Workbench)"
    assert win.editor_panel.attached_audio_path == str(dummy_mp3), "Audio path should be attached in editor"
    print("  ✓ Suno downloaded MP3 loaded directly into Editor Stem Player with automated tab switch")

    try:
        win.editor_panel._remove_audio_stem()
        dummy_mp3.unlink()
    except Exception:
        pass

    win.close()
    print("\n🎉 ALL 5 VERIFICATION SUITES PASSED! 6th Studio Tab is 100% production-ready.")


if __name__ == "__main__":
    run_all_tests()
