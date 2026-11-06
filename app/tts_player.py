"""
Vocal Guide & TTS Playback Engine for Songwriters.
Uses Windows SAPI offline speech synthesis with QMediaPlayer playback,
providing instant line-by-line or full-song cadence previews.
"""

import os
import re
import tempfile
from PyQt6.QtCore import QObject, pyqtSignal, QUrl, QThread
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

def clean_lyrics_for_speech(text: str) -> str:
    """Strip bracketed cues like [Chorus], [Intro], [Guitar Solo] so TTS only speaks lyrics."""
    lines = []
    for line in text.split("\n"):
        stripped = line.strip()
        # Skip section markers like [Verse 1], [Chorus]
        if stripped.startswith("[") and stripped.endswith("]"):
            continue
        # Strip internal parenthetical cues like (whisper), (ad-lib) if desired, or keep as spoken ad-libs
        clean_line = re.sub(r"\[.*?\]", "", line).strip()
        if clean_line:
            lines.append(clean_line)
    return "\n".join(lines)

class TTSWorker(QThread):
    finished = pyqtSignal(str) # wav_path
    error = pyqtSignal(str)

    def __init__(self, text: str, voice_index: int = 0, rate: int = 0):
        super().__init__()
        self.text = text
        self.voice_index = voice_index
        self.rate = rate

    def run(self):
        try:
            import win32com.client
            speaker = win32com.client.Dispatch("SAPI.SpVoice")
            voices = speaker.GetVoices()

            if 0 <= self.voice_index < voices.Count:
                speaker.Voice = voices.Item(self.voice_index)

            # SAPI Rate is from -10 to 10
            speaker.Rate = max(-10, min(10, self.rate))

            clean_text = clean_lyrics_for_speech(self.text)
            if not clean_text.strip():
                clean_text = "No lyrics to read."

            out_dir = os.path.join(tempfile.gettempdir(), "lyric_ai_audio")
            os.makedirs(out_dir, exist_ok=True)
            wav_path = os.path.join(out_dir, "vocal_cadence.wav")

            stream = win32com.client.Dispatch("SAPI.SpFileStream")
            # 3 = SSFMCreateForWrite
            stream.Open(wav_path, 3)
            speaker.AudioOutputStream = stream
            speaker.Speak(clean_text)
            stream.Close()

            self.finished.emit(wav_path)

        except Exception as e:
            self.error.emit(f"Speech synthesis error: {e}")

class VocalPlayer(QObject):
    state_changed = pyqtSignal(bool) # is_playing
    progress_changed = pyqtSignal(int, int) # position_ms, duration_ms
    generation_finished = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(0.9)

        self.current_wav = None
        self.worker = None

        self.player.playbackStateChanged.connect(self._on_playback_state_changed)
        self.player.positionChanged.connect(self._on_position_changed)
        self.player.durationChanged.connect(self._on_duration_changed)

    def get_available_voices(self) -> list:
        try:
            import win32com.client
            speaker = win32com.client.Dispatch("SAPI.SpVoice")
            voices = speaker.GetVoices()
            return [voices.Item(i).GetDescription() for i in range(voices.Count)]
        except Exception:
            return ["Default System Voice"]

    def synthesize_and_play(self, text: str, voice_index: int = 0, rate: int = 0):
        self.stop()
        self.worker = TTSWorker(text, voice_index, rate)
        self.worker.finished.connect(self._on_synth_done)
        self.worker.error.connect(lambda err: self.error_occurred.emit(err))
        self.worker.start()

    def _on_synth_done(self, wav_path: str):
        self.current_wav = wav_path
        self.player.setSource(QUrl.fromLocalFile(wav_path))
        self.player.play()
        self.generation_finished.emit(wav_path)

    def play(self):
        if self.current_wav and os.path.exists(self.current_wav):
            self.player.play()

    def pause(self):
        self.player.pause()

    def stop(self):
        self.player.stop()

    def set_volume(self, val: int):
        # 0 - 100
        self.audio_output.setVolume(val / 100.0)

    def _on_playback_state_changed(self, state):
        is_playing = (state == QMediaPlayer.PlaybackState.PlayingState)
        self.state_changed.emit(is_playing)

    def _on_position_changed(self, pos):
        self.progress_changed.emit(pos, self.player.duration())

    def _on_duration_changed(self, dur):
        self.progress_changed.emit(self.player.position(), dur)
