"""
Procedural Audio Rhythm Groove Engine for SMG Suno AI Lyric Writer.
Synthesizes authentic Khmer traditional grooves and modern studio pop/urban drum loops
directly into pure 16-bit PCM WAV loops with zero external audio assets.
Supports seamless looping via Windows audio subsystem.
"""

import math
import struct
import wave
import tempfile
import threading
from pathlib import Path
from typing import Dict, Any, List

try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False


class DrumSynthesizer:
    """Pure mathematical synthesis of acoustic and synthetic drum sounds."""

    @staticmethod
    def synth_kick(sample_rate: int = 44100, duration: float = 0.28, is_808: bool = False) -> List[float]:
        num_samples = int(sample_rate * duration)
        samples = []
        start_freq = 160.0 if not is_808 else 120.0
        end_freq = 42.0 if not is_808 else 35.0
        decay_rate = 14.0 if not is_808 else 5.0

        for i in range(num_samples):
            t = i / float(sample_rate)
            # Pitch drop envelope
            pitch = end_freq + (start_freq - end_freq) * math.exp(-32.0 * t)
            # Amplitude envelope with fast 4ms attack
            amp = math.exp(-decay_rate * t) * min(1.0, t * 250.0)
            # Punchy sub tone + click
            val = math.sin(2.0 * math.pi * pitch * t) * amp
            if t < 0.008:
                val += 0.35 * (math.sin(2.0 * math.pi * 950.0 * t)) * (1.0 - t / 0.008)
            samples.append(val)
        return samples

    @staticmethod
    def synth_snare(sample_rate: int = 44100, duration: float = 0.22, is_clap: bool = False) -> List[float]:
        num_samples = int(sample_rate * duration)
        samples = []
        decay_rate = 16.0 if not is_clap else 18.0

        for i in range(num_samples):
            t = i / float(sample_rate)
            amp = math.exp(-decay_rate * t) * min(1.0, t * 200.0)
            # Pseudo-random noise for snare wire rattle
            noise = ((math.sin(i * 12.9898) * 43758.5453) % 2.0) - 1.0
            # Body tone at 185 Hz
            body = math.sin(2.0 * math.pi * 185.0 * t) * math.exp(-22.0 * t)
            val = (0.7 * noise + 0.3 * body) * amp
            samples.append(val)
        return samples

    @staticmethod
    def synth_chhing(sample_rate: int = 44100, duration: float = 0.35, is_open: bool = True) -> List[float]:
        """Authentic Khmer Chhing (ឈិង) metallic cymbal / bell sound."""
        num_samples = int(sample_rate * duration)
        samples = []
        decay_rate = 6.0 if is_open else 35.0

        # Metallic resonant frequencies (inharmonic spectrum)
        freqs = [2400.0, 3120.0, 4280.0, 5600.0, 7250.0]
        weights = [0.35, 0.25, 0.20, 0.12, 0.08]

        for i in range(num_samples):
            t = i / float(sample_rate)
            amp = math.exp(-decay_rate * t) * min(1.0, t * 400.0)
            val = 0.0
            for f, w in zip(freqs, weights):
                val += w * math.sin(2.0 * math.pi * f * t)
            samples.append(val * amp)
        return samples

    @staticmethod
    def synth_skor_dai(sample_rate: int = 44100, duration: float = 0.32, is_low: bool = True) -> List[float]:
        """Authentic Khmer Skor Dai / Samphor (ស្គរដៃ) acoustic hand drum."""
        num_samples = int(sample_rate * duration)
        samples = []
        base_freq = 95.0 if is_low else 150.0

        for i in range(num_samples):
            t = i / float(sample_rate)
            pitch = base_freq * (1.0 + 0.3 * math.exp(-25.0 * t))
            amp = math.exp(-12.0 * t) * min(1.0, t * 250.0)
            # Warm acoustic membrane harmonic
            val = (0.75 * math.sin(2.0 * math.pi * pitch * t) +
                   0.25 * math.sin(4.0 * math.pi * pitch * 1.58 * t)) * amp
            samples.append(val)
        return samples

    @staticmethod
    def synth_hihat(sample_rate: int = 44100, duration: float = 0.08) -> List[float]:
        num_samples = int(sample_rate * duration)
        samples = []
        for i in range(num_samples):
            t = i / float(sample_rate)
            amp = math.exp(-45.0 * t) * min(1.0, t * 600.0)
            noise = ((math.sin(i * 93.9898) * 23758.5453) % 2.0) - 1.0
            # High frequency metallic tone
            metal = 0.5 * math.sin(2.0 * math.pi * 7800.0 * t)
            val = (0.6 * noise + 0.4 * metal) * amp
            samples.append(val)
        return samples


# ── Preset Groove Definitions (16-step grid per measure) ──
GROOVE_PATTERNS: Dict[str, Dict[str, Any]] = {
    "Off (Standard Metronome)": {
        "description": "Standard silent metronome mode with visual LED indicator",
        "default_bpm": 120,
        "grid_steps": 16,
        "tracks": {}
    },
    "🇰🇭 Romvong (រាំវង់)": {
        "description": "Authentic Khmer swinging folk-pop groove. Low Skor Dai on beats 1 & 3, resonant Chhing on offbeats.",
        "default_bpm": 74,
        "grid_steps": 16,
        "tracks": {
            "skor_low":  [1, 0, 0, 0,  0, 0, 0, 0,  1, 0, 0, 0,  0, 0, 0, 0],
            "skor_high": [0, 0, 0, 0,  1, 0, 0, 1,  0, 0, 0, 0,  1, 0, 1, 0],
            "chhing":    [0, 0, 1, 0,  0, 0, 1, 0,  0, 0, 1, 0,  0, 0, 1, 0]
        }
    },
    "🇰🇭 Kantrum (កន្ត្រឹម)": {
        "description": "Fast energetic Northeast Khmer folk dance. Driving bass, syncopated rimshots, and fast Chhing cadence.",
        "default_bpm": 128,
        "grid_steps": 16,
        "tracks": {
            "kick":      [1, 0, 0, 0,  1, 0, 0, 0,  1, 0, 0, 0,  1, 0, 0, 0],
            "snare":     [0, 0, 1, 0,  0, 1, 0, 1,  0, 0, 1, 0,  0, 1, 1, 0],
            "chhing":    [1, 0, 1, 1,  1, 0, 1, 1,  1, 0, 1, 1,  1, 0, 1, 1]
        }
    },
    "🇰🇭 Saravan (សារាវ៉ាន់)": {
        "description": "Celebratory Khmer dance rhythm with rolling triplet feel and syncopated hand drums.",
        "default_bpm": 102,
        "grid_steps": 16,
        "tracks": {
            "skor_low":  [1, 0, 0, 1,  0, 0, 1, 0,  1, 0, 0, 1,  0, 0, 1, 0],
            "skor_high": [0, 0, 1, 0,  1, 0, 0, 1,  0, 0, 1, 0,  1, 0, 0, 1],
            "chhing":    [1, 0, 0, 0,  1, 0, 0, 0,  1, 0, 0, 0,  1, 0, 0, 0]
        }
    },
    "🌍 Pop 4-on-the-Floor": {
        "description": "Classic radio commercial hit groove: four-on-the-floor kick, backbeat snare, driving hi-hat.",
        "default_bpm": 120,
        "grid_steps": 16,
        "tracks": {
            "kick":      [1, 0, 0, 0,  1, 0, 0, 0,  1, 0, 0, 0,  1, 0, 0, 0],
            "snare":     [0, 0, 0, 0,  1, 0, 0, 0,  0, 0, 0, 0,  1, 0, 0, 0],
            "hihat":     [1, 0, 1, 0,  1, 0, 1, 0,  1, 0, 1, 0,  1, 0, 1, 0]
        }
    },
    "🌍 808 Trap / Hip-Hop": {
        "description": "Deep 808 sub kick, halftime trap snare on beat 3, and rolling hi-hat groove.",
        "default_bpm": 140,
        "grid_steps": 16,
        "tracks": {
            "kick":      [1, 0, 0, 0,  0, 0, 1, 0,  0, 0, 0, 0,  0, 1, 0, 0],
            "snare":     [0, 0, 0, 0,  0, 0, 0, 0,  1, 0, 0, 0,  0, 0, 0, 0],
            "hihat":     [1, 1, 1, 1,  1, 1, 1, 1,  1, 1, 1, 1,  1, 1, 1, 1]
        }
    },
    "🌍 Acoustic Lo-Fi Ballad": {
        "description": "Soft organic kick and warm acoustic snare for gentle ballads and acoustic singer-songwriter tracks.",
        "default_bpm": 80,
        "grid_steps": 16,
        "tracks": {
            "kick":      [1, 0, 0, 0,  0, 0, 0, 0,  0, 0, 1, 0,  0, 0, 0, 0],
            "snare":     [0, 0, 0, 0,  1, 0, 0, 0,  0, 0, 0, 0,  1, 0, 0, 0],
            "hihat":     [1, 0, 1, 0,  1, 0, 1, 0,  1, 0, 1, 0,  1, 0, 1, 0]
        }
    }
}


class RhythmEngine:
    """
    Rhythm Groove Engine that generates, caches, and loops audio rhythm tracks.
    """
    _temp_dir = Path(tempfile.gettempdir()) / "worldlyric_grooves"
    _current_groove: str = "Off (Standard Metronome)"
    _current_bpm: int = 120
    _is_playing: bool = False
    _lock = threading.Lock()

    @classmethod
    def _ensure_dir(cls):
        cls._temp_dir.mkdir(parents=True, exist_ok=True)

    GROOVE_MAP = {
        "Off (Metronome)": "Off (Standard Metronome)",
        "🇰🇭 Romvong (74 BPM)": "🇰🇭 Romvong (រាំវង់)",
        "🇰🇭 Kantrum (128 BPM)": "🇰🇭 Kantrum (កន្ត្រឹម)",
        "🇰🇭 Saravan (102 BPM)": "🇰🇭 Saravan (សារាវ៉ាន់)",
        "🌍 Pop 4-Floor (120)": "🌍 Pop 4-on-the-Floor",
        "🌍 808 Trap (140)": "🌍 808 Trap / Hip-Hop",
        "🌍 Acoustic (80 BPM)": "🌍 Acoustic Lo-Fi Ballad"
    }

    @classmethod
    def get_available_grooves(cls) -> List[str]:
        return list(cls.GROOVE_MAP.keys())

    @classmethod
    def resolve_groove_key(cls, display_name: str) -> str:
        return cls.GROOVE_MAP.get(display_name, display_name)

    @classmethod
    def get_groove_default_bpm(cls, groove_name: str) -> int:
        real_key = cls.resolve_groove_key(groove_name)
        return GROOVE_PATTERNS.get(real_key, {}).get("default_bpm", 120)

    @classmethod
    def synthesize_groove_loop(cls, groove_name: str, bpm: int = 120, sample_rate: int = 44100) -> Path:
        """Render a seamless 1-measure WAV loop of the specified groove pattern."""
        cls._ensure_dir()
        groove_data = GROOVE_PATTERNS.get(groove_name)
        if not groove_data or not groove_data.get("tracks"):
            raise ValueError(f"No audio tracks in groove: {groove_name}")

        safe_name = "".join(c for c in groove_name if c.isalnum() or c in "_- ").strip().replace(" ", "_")
        out_path = cls._temp_dir / f"groove_{safe_name}_{bpm}bpm.wav"

        # Calculate exact length of 1 measure (4 quarter note beats = 16 sixteenth steps)
        sec_per_measure = (60.0 / max(40, min(240, bpm))) * 4.0
        total_samples = int(sample_rate * sec_per_measure)
        mix_buffer = [0.0] * total_samples

        step_duration = sec_per_measure / 16.0
        step_samples = int(sample_rate * step_duration)

        # Pre-synthesize drum sounds
        sound_pool = {
            "kick": DrumSynthesizer.synth_kick(sample_rate),
            "snare": DrumSynthesizer.synth_snare(sample_rate),
            "hihat": DrumSynthesizer.synth_hihat(sample_rate),
            "chhing": DrumSynthesizer.synth_chhing(sample_rate),
            "skor_low": DrumSynthesizer.synth_skor_dai(sample_rate, is_low=True),
            "skor_high": DrumSynthesizer.synth_skor_dai(sample_rate, is_low=False),
        }

        tracks = groove_data["tracks"]
        for instrument_name, pattern in tracks.items():
            drum_sound = sound_pool.get(instrument_name)
            if not drum_sound:
                continue

            for step_idx, hit in enumerate(pattern[:16]):
                if hit:
                    start_sample = step_idx * step_samples
                    for i, smp in enumerate(drum_sound):
                        idx = start_sample + i
                        if idx < total_samples:
                            mix_buffer[idx] += smp
                        else:
                            # Loop wrap-around to prevent clipping at loop boundaries!
                            wrap_idx = idx % total_samples
                            mix_buffer[wrap_idx] += smp

        # Normalize and write 16-bit PCM WAV
        max_val = max(0.001, max(abs(s) for s in mix_buffer))
        with wave.open(str(out_path), "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            frames = bytearray()
            for s in mix_buffer:
                norm_sample = (s / max_val) * 26000.0
                val = int(max(-32767, min(32767, norm_sample)))
                frames.extend(struct.pack("<h", val))
            wav.writeframes(frames)

        return out_path

    @classmethod
    def play_groove(cls, groove_name: str, bpm: int = 120):
        groove_name = cls.resolve_groove_key(groove_name)
        """Start seamless background looping of the groove pattern."""
        if not HAS_WINSOUND or groove_name == "Off (Standard Metronome)":
            cls.stop_groove()
            return

        with cls._lock:
            cls._current_groove = groove_name
            cls._current_bpm = bpm
            cls._is_playing = True

        def _play_worker():
            try:
                loop_file = cls.synthesize_groove_loop(groove_name, bpm)
                winsound.PlaySound(str(loop_file), winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP)
            except Exception as e:
                print(f"[RhythmEngine] Audio loop error: {e}")

        threading.Thread(target=_play_worker, daemon=True).start()

    @classmethod
    def stop_groove(cls):
        """Stop background audio looping immediately."""
        with cls._lock:
            cls._is_playing = False
        if HAS_WINSOUND:
            try:
                winsound.PlaySound(None, winsound.SND_PURGE)
            except Exception:
                pass

    @classmethod
    def is_playing(cls) -> bool:
        return cls._is_playing
