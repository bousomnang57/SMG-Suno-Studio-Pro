"""
Studio Metronome Engine and Real-Time Tap Tempo Calculator.
Features visual beat pulse and audio tick clicks for songwriters and beatmakers.
"""

import time
from PyQt6.QtCore import QObject, QTimer, pyqtSignal, QThread

class AudioBeepThread(QThread):
    def __init__(self, freq: int, duration_ms: int = 25):
        super().__init__()
        self.freq = freq
        self.duration_ms = duration_ms

    def run(self):
        try:
            import winsound
            winsound.Beep(self.freq, self.duration_ms)
        except Exception:
            pass

class StudioMetronome(QObject):
    beat_pulse = pyqtSignal(int, int) # current_beat (1-indexed), total_beats
    bpm_changed = pyqtSignal(int)

    def __init__(self, bpm: int = 120, time_sig: tuple = (4, 4)):
        super().__init__()
        self.bpm = bpm
        self.time_sig = time_sig # (beats_per_bar, beat_unit)
        self.current_beat = 0
        self.is_running = False
        self.audio_enabled = True

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_tick)

        # Tap tempo history
        self.tap_times = []
        self._update_interval()

    def set_bpm(self, bpm: int):
        self.bpm = max(40, min(240, bpm))
        self._update_interval()
        self.bpm_changed.emit(self.bpm)

    def set_time_signature(self, beats_per_bar: int):
        self.time_sig = (beats_per_bar, 4)
        self.current_beat = 0

    def toggle(self) -> bool:
        if self.is_running:
            self.stop()
        else:
            self.start()
        return self.is_running

    def start(self):
        self.current_beat = 0
        self.is_running = True
        self._update_interval()
        self.timer.start()
        self._on_tick()

    def stop(self):
        self.timer.stop()
        self.is_running = False
        self.current_beat = 0
        self.beat_pulse.emit(0, self.time_sig[0])

    def _update_interval(self):
        # Milliseconds per beat = (60 / BPM) * 1000
        ms = int((60.0 / max(30, self.bpm)) * 1000)
        self.timer.setInterval(ms)

    def _on_tick(self):
        beats_per_bar = self.time_sig[0]
        self.current_beat = (self.current_beat % beats_per_bar) + 1

        # Emit visual pulse
        self.beat_pulse.emit(self.current_beat, beats_per_bar)

        # Play audio click
        if self.audio_enabled:
            # Beat 1 = higher frequency 1200 Hz, other beats = 800 Hz
            freq = 1200 if self.current_beat == 1 else 800
            worker = AudioBeepThread(freq, duration_ms=20)
            worker.start()

    def tap(self) -> int:
        """Register a tap and recalculate BPM from moving average interval."""
        now = time.time()
        self.tap_times.append(now)

        # Keep last 5 taps
        if len(self.tap_times) > 5:
            self.tap_times.pop(0)

        # If last tap was more than 2.5s ago, reset
        if len(self.tap_times) >= 2 and (now - self.tap_times[-2]) > 2.5:
            self.tap_times = [now]
            return self.bpm

        if len(self.tap_times) >= 2:
            intervals = [self.tap_times[i] - self.tap_times[i - 1] for i in range(1, len(self.tap_times))]
            avg_interval = sum(intervals) / len(intervals)
            if avg_interval > 0:
                calc_bpm = int(round(60.0 / avg_interval))
                calc_bpm = max(40, min(240, calc_bpm))
                self.set_bpm(calc_bpm)
                return calc_bpm

        return self.bpm
