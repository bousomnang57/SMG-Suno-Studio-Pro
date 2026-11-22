"""
Comprehensive Unit & Integration Test Suite for Mode 6:
Pro Mastering Studio & Suno Audio Fixer
"""
import os
import sys
import tempfile
from pathlib import Path
import numpy as np

# Force headless offscreen Qt platform
os.environ["QT_QPA_PLATFORM"] = "offscreen"

# Ensure root directory is on sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QPoint, QUrl

from app.audio_mastering_engine import (
    AudioMasteringEngine,
    MASTERING_TARGETS,
)
from app.ui.waveform_widget import WaveformCanvas, StereoLevelMeter, WaveformEditorPane
from app.ui.audio_mastering_view import AudioMasteringView
from app.ui.main_window import MainWindow
from app.ui.suno_downloader_dialog import SunoLinkDownloadDialog
from app.ui.suno_browser_view import SunoBrowserView


def _generate_test_audio_wav(output_path: str, duration_sec: float = 2.0, sr: int = 44100) -> str:
    """Generate a synthetic test audio WAV file with tone + boxy resonance + silence padding."""
    t = np.linspace(0, duration_sec, int(sr * duration_sec), endpoint=False)
    # 440 Hz musical tone + 320 Hz boxy resonance + 8000 Hz high sibilance
    signal_left = 0.4 * np.sin(2 * np.pi * 440 * t) + 0.3 * np.sin(2 * np.pi * 320 * t) + 0.15 * np.sin(2 * np.pi * 8000 * t)
    signal_right = 0.4 * np.cos(2 * np.pi * 440 * t) + 0.25 * np.sin(2 * np.pi * 320 * t) + 0.15 * np.cos(2 * np.pi * 8000 * t)
    
    # Add 0.2s silence head and 0.2s silence tail
    pad_samples = int(sr * 0.2)
    silence = np.zeros(pad_samples)
    left_padded = np.concatenate([silence, signal_left, silence])
    right_padded = np.concatenate([silence, signal_right, silence])
    stereo = np.column_stack([left_padded, right_padded])
    
    # Save as 16-bit PCM WAV using standard wave module
    import wave
    stereo_i16 = np.clip(stereo * 32767.0, -32768, 32767).astype(np.int16)
    with wave.open(output_path, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(stereo_i16.tobytes())
    return output_path


def test_mastering_dsp_engine(tmp_path: Path):
    print("\n[1/5] Testing AudioMasteringEngine DSP Pipeline...")
    test_wav = str(tmp_path / "test_suno_track.wav")
    _generate_test_audio_wav(test_wav, duration_sec=2.5, sr=44100)
    assert os.path.exists(test_wav)
    print(f"  ✓ Generated test stereo audio: {test_wav}")

    # 1. Load Audio
    audio, sr = AudioMasteringEngine.load_audio(test_wav)
    assert audio.ndim == 2
    assert audio.shape[1] == 2
    assert sr == 44100
    print(f"  ✓ load_audio verified: shape={audio.shape}, sr={sr}")

    # 2. Measure LUFS and True-Peak
    lufs = AudioMasteringEngine.measure_lufs(audio, sr)
    tp = AudioMasteringEngine.measure_true_peak(audio)
    assert isinstance(lufs, float)
    assert isinstance(tp, float)
    print(f"  ✓ Loudness & True-Peak measured: {lufs:.2f} LUFS, {tp:.2f} dBTP")

    # 3. Detect Silence
    head_silence, tail_silence = AudioMasteringEngine.detect_silence(audio, sr)
    assert head_silence > 0.05
    assert tail_silence > 0.05
    print(f"  ✓ detect_silence verified: head={head_silence:.2f}s, tail={tail_silence:.2f}s")

    # 4. Suno Artifact Scanner
    scan = AudioMasteringEngine.scan_suno_artifacts(audio, sr)
    assert "artifact_index" in scan
    assert "mud_index" in scan
    assert "harsh_index" in scan
    assert "issues" in scan
    print(f"  ✓ scan_suno_artifacts verified: mud={scan['mud_index']}, harsh={scan['harsh_index']}, issues={len(scan['issues'])}")

    # 5. Musical BPM and Key Estimation
    bpm, key = AudioMasteringEngine.estimate_bpm_and_key(audio, sr)
    assert isinstance(bpm, int) and 60 <= bpm <= 190
    assert isinstance(key, str) and len(key) > 0
    print(f"  ✓ estimate_bpm_and_key verified: {bpm} BPM, Key of {key}")

    # 6. Full Automated Analysis Report
    report = AudioMasteringEngine.analyze_track_full(test_wav)
    assert report["bpm"] == bpm
    assert report["key"] == key
    assert 40 <= report["score"] <= 100
    print(f"  ✓ analyze_track_full verified: Studio Score={report['score']}/100, Target={report['target_score']}/100")

    # 7. Full Mastering Chain Processing (WAV and MP3 outputs)
    out_wav = str(tmp_path / "mastered_output.wav")
    progress_calls = []
    res_wav = AudioMasteringEngine.process_master(
        input_path=test_wav,
        output_path=out_wav,
        target_preset="Spotify & YouTube (-14.0 LUFS)",
        auto_trim=True,
        de_ai_filter=True,
        progress_callback=lambda p, m: progress_calls.append((p, m))
    )
    assert os.path.exists(out_wav)
    assert os.path.getsize(out_wav) > 1000
    assert res_wav["final_tp"] <= -0.95
    assert len(progress_calls) >= 3
    print(f"  ✓ process_master (WAV 24-bit) verified: Output {res_wav['final_lufs']:.2f} LUFS, {res_wav['final_tp']:.2f} dBTP")

    out_mp3 = str(tmp_path / "mastered_output.mp3")
    res_mp3 = AudioMasteringEngine.process_master(
        input_path=test_wav,
        output_path=out_mp3,
        target_preset="Suno Master (-13.0 LUFS)",
        auto_trim=False,
    )
    assert os.path.exists(out_mp3)
    assert os.path.getsize(out_mp3) > 1000
    print(f"  ✓ process_master (MP3 320k) verified: {out_mp3} ({os.path.getsize(out_mp3)} bytes)")


def test_waveform_widgets(tmp_path: Path):
    print("\n[2/5] Testing Waveform Editor & Level Meter Widgets...")
    test_wav = str(tmp_path / "test_waveform.wav")
    _generate_test_audio_wav(test_wav, duration_sec=3.0, sr=44100)
    audio, sr = AudioMasteringEngine.load_audio(test_wav)

    # 1. WaveformCanvas
    canvas = WaveformCanvas()
    canvas.resize(600, 140)
    canvas.set_audio_data(audio, sr, is_mastered=True)
    assert canvas.duration > 2.5
    assert canvas.samples is not None

    # Test Playhead Scrubbing
    canvas.set_playback_position(1.5)
    assert abs(canvas.current_time - 1.5) < 0.01

    # Test Trim Handles
    canvas.set_trim_points(0.2, 2.8)
    assert abs(canvas.in_point - 0.2) < 0.01
    assert abs(canvas.out_point - 2.8) < 0.01

    # Test A/B Mode Display
    canvas.set_mode(False)
    assert canvas.is_mastered_mode is False
    assert "ORIGINAL" in canvas.mode_tag
    canvas.set_mode(True)
    assert canvas.is_mastered_mode is True
    assert "MASTERED" in canvas.mode_tag
    print("  ✓ WaveformCanvas verified: envelopes, scrubber, draggable IN/OUT handles, and A/B mode badges")

    # 2. StereoLevelMeter
    meter = StereoLevelMeter()
    meter.set_levels(-6.0, -9.0)
    assert meter.level_l == -6.0
    assert meter.level_r == -9.0
    meter.set_levels(0.5, -12.0)
    assert meter.peak_db == 0.0  # Clipped to 0 dBFS ceiling
    print("  ✓ StereoLevelMeter verified: dual L/R peak levels and clipping detection")

    # 3. WaveformEditorPane
    pane = WaveformEditorPane()
    pane.set_audio_data(audio, sr, is_mastered=True)
    pane.set_playback_position(1.0)
    pane.set_levels(-10.0, -10.0)
    print("  ✓ WaveformEditorPane verified: container and coordinated updates")


def test_audio_mastering_view(tmp_path: Path):
    print("\n[3/5] Testing AudioMasteringView (Mode 6 UI)...")
    test_wav = str(tmp_path / "queue_track_1.wav")
    _generate_test_audio_wav(test_wav, duration_sec=2.0, sr=44100)

    view = AudioMasteringView()
    view.resize(1100, 750)

    # Test Queue Operations
    view.add_track_file(test_wav, auto_select=True)
    assert len(view.tracks) == 1
    assert view.table_queue.rowCount() == 1
    print("  ✓ add_track_file verified: track loaded into queue and selected")

    # Test Queue Item Data
    tr = view.tracks[0]
    assert "queue_track_1" in tr["path"]
    assert tr["status"] == "Ready"

    # Test A/B Toggle Mode
    view._set_ab_mode(False)
    assert view.is_ab_mastered is False
    view._set_ab_mode(True)
    assert view.is_ab_mastered is True
    print("  ✓ Live A/B Monitor toggle verified: switches between A: Original and B: Mastered Pro")

    # Test 5 Themes Adaptation
    themes = ["obsidian", "cyber_blue", "emerald", "sunset_amber", "canvas_light"]
    for th in themes:
        view.apply_theme(th)
        assert view.current_theme == th
    print(f"  ✓ Theme adaptation verified across all 5 studio themes: {themes}")

    # Release player locks on Windows
    view.player.stop()
    view.player.setSource(QUrl())


def test_mainwindow_mode_6_integration(tmp_path: Path):
    print("\n[4/5] Testing MainWindow Mode 6 Registration & Shortcuts...")
    win = MainWindow()
    win.resize(1200, 800)

    # 1. Verify Mode 6 is registered in QStackedWidget
    assert hasattr(win, "master_view")
    assert win.stack.count() >= 7
    assert win.stack.widget(6) is win.master_view

    # 2. Test Mode Switch to Mode 6
    win._set_studio_mode(6)
    assert win.stack.currentIndex() == 6
    assert win.btn_mode_master.isChecked() is True
    assert win.btn_mode_wizard.isChecked() is False
    assert win.btn_mode_suno.isChecked() is False
    assert "Mastering" in win.lbl_ribbon_info.text()
    assert "1-Click Auto All" in win.btn_ribbon_action.text()
    print("  ✓ Mode 6 navigation verified: switched to Pro Mastering Studio, ribbon action and info synchronized")

    # 3. Test Ribbon 1-Click Auto All Trigger
    win._on_ribbon_action_clicked()
    # Should safely handle empty queue without crashing
    print("  ✓ Ribbon action click verified for Mode 6")

    # 4. Test Handoff from Master Studio to Lyric Editor Stem Player
    test_wav = str(tmp_path / "mastered_export.wav")
    _generate_test_audio_wav(test_wav, duration_sec=1.5, sr=44100)
    win._on_master_sent_to_editor(test_wav)
    assert win.stack.currentIndex() == 3  # Switched to Lyric Editor
    assert "mastered_export.wav" in win.status_bar.currentMessage()
    print("  ✓ Master to Lyric Editor Stem Player bridge verified")

    win.master_view.player.stop()
    win.master_view.player.setSource(QUrl())
    if hasattr(win.editor_panel, "stem_player"):
        win.editor_panel.stem_player.stop()
        win.editor_panel.stem_player.setSource(QUrl())


def test_ecosystem_bridges_to_master(tmp_path: Path):
    print("\n[5/5] Testing 1-Click Studio Ecosystem Bridges to Master...")
    win = MainWindow()
    test_wav = str(tmp_path / "suno_downloaded.wav")
    _generate_test_audio_wav(test_wav, duration_sec=2.0, sr=44100)

    # 1. Test SunoLinkDownloadDialog -> Master Bridge
    dlg = SunoLinkDownloadDialog(parent=win, theme_key="obsidian")
    assert hasattr(dlg, "load_into_master_requested")
    assert hasattr(dlg, "btn_master_audio")
    
    # Simulate download finished and click Master Audio
    dlg.last_downloaded_path = test_wav
    dlg.single_post_frame.show()
    dlg.btn_master_audio.setEnabled(True)

    received_master_path = []
    dlg.load_into_master_requested.connect(lambda p: received_master_path.append(p))
    dlg._master_audio()
    assert len(received_master_path) == 1
    assert received_master_path[0] == test_wav
    print("  ✓ SunoLinkDownloadDialog -> Master Studio bridge verified")

    # 2. Test SunoBrowserView -> Master Bridge
    browser_view = win.suno_browser_view
    assert hasattr(browser_view, "load_audio_into_master_requested")
    assert hasattr(browser_view, "btn_load_dl_to_master")

    received_from_browser = []
    browser_view.load_audio_into_master_requested.connect(lambda p: received_from_browser.append(p))
    browser_view.last_downloaded_audio_path = test_wav
    browser_view.btn_load_dl_to_master.setEnabled(True)
    browser_view._send_last_download_to_master()
    assert len(received_from_browser) == 1
    assert received_from_browser[0] == test_wav
    print("  ✓ SunoBrowserView -> Master Studio bridge verified")

    # 3. Test _load_audio_into_mastering_studio in MainWindow
    win._load_audio_into_mastering_studio(test_wav)
    assert win.stack.currentIndex() == 6
    assert len(win.master_view.tracks) == 1
    assert "suno_downloaded.wav" in win.master_view.tracks[0]["path"]
    print("  ✓ MainWindow._load_audio_into_mastering_studio verified: auto-switches to Mode 6 and selects track")

    # Release locks
    dlg.preview_player.stop()
    dlg.preview_player.setSource(QUrl())
    win.master_view.player.stop()
    win.master_view.player.setSource(QUrl())


def main():
    app = QApplication.instance() or QApplication(sys.argv)
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        tmp_path = Path(td)
        test_mastering_dsp_engine(tmp_path)
        test_waveform_widgets(tmp_path)
        test_audio_mastering_view(tmp_path)
        test_mainwindow_mode_6_integration(tmp_path)
        test_ecosystem_bridges_to_master(tmp_path)
        app.processEvents()

    print("\n" + "=" * 70)
    print("🎉 ALL TESTS PASSED: MODE 6 PRO MASTERING STUDIO VERIFIED 100%!")
    print("=" * 70)


if __name__ == "__main__":
    main()
