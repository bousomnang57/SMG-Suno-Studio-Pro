"""
In-App Melody Scratchpad Voice Recorder for Songwriters.
Utilizes Windows Multimedia MCI (winmm.dll) for zero-dependency,
CD-quality (44.1kHz 16-bit stereo) vocal recording directly from the computer microphone.
"""

import os
import ctypes
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

class MelodyRecorder(QObject):
    recording_started = pyqtSignal()
    recording_stopped = pyqtSignal(str) # filepath
    recording_tick = pyqtSignal(int)    # elapsed seconds
    playback_started = pyqtSignal()
    playback_stopped = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.winmm = ctypes.windll.winmm
        self.is_recording = False
        self.is_playing = False
        self.elapsed_seconds = 0
        self.current_recording_path = None

        # Timer for duration tracking
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._on_timer_tick)

        # Directory for voice scratch takes
        self.scratch_dir = Path.home() / ".lyric_ai_writer" / "voice_takes"
        self.scratch_dir.mkdir(parents=True, exist_ok=True)

    def _send_mci(self, cmd: str) -> int:
        return self.winmm.mciSendStringW(cmd, None, 0, None)

    def start_recording(self) -> bool:
        """Starts recording audio from microphone."""
        if self.is_recording:
            return False

        # Close any previous instance
        self._send_mci("close lyric_scratch")

        # Open waveaudio device
        res = self._send_mci("open new type waveaudio alias lyric_scratch")
        if res != 0:
            self.error_occurred.emit("Could not open microphone recording device.")
            return False

        # Set 44.1kHz, 16-bit stereo
        self._send_mci("set lyric_scratch time format ms bitspersample 16 channels 2 samplespersec 44100")

        # Start recording
        res = self._send_mci("record lyric_scratch")
        if res != 0:
            self.error_occurred.emit("Could not start recording.")
            return False

        self.is_recording = True
        self.elapsed_seconds = 0
        self.timer.start()
        self.recording_started.emit()
        return True

    def stop_recording(self, song_title: str = "VoiceTake") -> str:
        """Stops recording and saves WAV audio file."""
        if not self.is_recording:
            return ""

        self.timer.stop()
        self._send_mci("stop lyric_scratch")

        safe_name = "".join(c for c in song_title if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
        filename = f"{safe_name}_{int(os.times().elapsed)}.wav"
        save_path = str(self.scratch_dir / filename)

        res = self._send_mci(f'save lyric_scratch "{save_path}"')
        self._send_mci("close lyric_scratch")

        self.is_recording = False
        self.current_recording_path = save_path
        self.recording_stopped.emit(save_path)
        return save_path

    def play_last_take(self):
        """Plays back the most recently recorded scratch take."""
        if not self.current_recording_path or not os.path.exists(self.current_recording_path):
            self.error_occurred.emit("No scratch take recorded yet.")
            return

        import winsound
        winsound.PlaySound(self.current_recording_path, winsound.SND_ASYNC | winsound.SND_FILENAME)
        self.playback_started.emit()

    def stop_playback(self):
        """Stops audio playback."""
        import winsound
        winsound.PlaySound(None, winsound.SND_PURGE)
        self.playback_stopped.emit()

    def _on_timer_tick(self):
        self.elapsed_seconds += 1
        self.recording_tick.emit(self.elapsed_seconds)
