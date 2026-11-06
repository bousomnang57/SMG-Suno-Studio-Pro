"""
Interactive Chord Soundboard & Multi-Instrument Audio Synthesizer.
Provides realistic polyphonic audio synthesis for Acoustic Grand Piano,
Electric Rhodes, Acoustic Guitar, and Lush Synth Pad.
Supports zero-latency chord auditioning, rhythmic progression looping,
and lyric chord token extraction.
"""

import re
import math
import wave
import tempfile
import threading
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import numpy as np

# Semitones definitions
SEMITONES_SHARP = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
SEMITONES_FLAT = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]

ENHARMONIC_MAP = {
    "Db": "C#", "Eb": "D#", "Gb": "F#", "Ab": "G#", "Bb": "A#",
    "B#": "C", "E#": "F", "Cb": "B", "Fb": "E"
}

# Standard note frequencies (Hz) for Equal Temperament (A4 = 440 Hz)
def note_to_freq(note_str: str) -> float:
    """Calculate frequency for note like 'C4', 'A#3', 'Eb5'."""
    m = re.match(r"^([A-G][#b]?)([0-9])$", note_str.strip())
    if not m:
        return 440.0
    pitch, oct_str = m.groups()
    pitch = ENHARMONIC_MAP.get(pitch, pitch)
    octave = int(oct_str)
    
    if pitch not in SEMITONES_SHARP:
        return 440.0
    semitone_index = SEMITONES_SHARP.index(pitch)
    # MIDI note number: C4 is 60, A4 is 69
    midi_num = (octave + 1) * 12 + semitone_index
    return 440.0 * (2.0 ** ((midi_num - 69) / 12.0))


CHORD_INTERVALS = {
    "": [0, 4, 7],            # Major
    "maj": [0, 4, 7],
    "m": [0, 3, 7],            # Minor
    "min": [0, 3, 7],
    "-": [0, 3, 7],
    "7": [0, 4, 7, 10],        # Dominant 7th
    "dom7": [0, 4, 7, 10],
    "maj7": [0, 4, 7, 11],     # Major 7th
    "m7": [0, 3, 7, 10],       # Minor 7th
    "min7": [0, 3, 7, 10],
    "dim": [0, 3, 6],          # Diminished
    "dim7": [0, 3, 6, 9],
    "m7b5": [0, 3, 6, 10],     # Half-diminished
    "aug": [0, 4, 8],          # Augmented
    "+": [0, 4, 8],
    "sus4": [0, 5, 7],         # Suspended 4th
    "sus2": [0, 2, 7],         # Suspended 2nd
    "add9": [0, 4, 7, 14],     # Add 9
    "9": [0, 4, 7, 10, 14],    # 9th
    "maj9": [0, 4, 7, 11, 14], # Major 9th
    "m9": [0, 3, 7, 10, 14],   # Minor 9th
    "6": [0, 4, 7, 9],         # 6th
    "m6": [0, 3, 7, 9],        # Minor 6th
}


class ChordSoundboardSynthesizer:
    """
    High-fidelity polyphonic synthesizer supporting multiple studio instruments.
    Uses numpy for vectorized synthesis with zero lag.
    """
    SAMPLE_RATE = 44100
    _temp_dir = Path(tempfile.gettempdir()) / "worldlyric_soundboard"
    _cache: Dict[str, Path] = {}
    _lock = threading.Lock()

    @classmethod
    def _ensure_dir(cls):
        cls._temp_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def parse_chord(cls, chord_str: str) -> Tuple[str, str, Optional[str]]:
        """Extract root, quality, and slash bass from 'F#m7/C#'."""
        clean = chord_str.strip().strip("[]()")
        slash_bass = None
        if "/" in clean:
            parts = clean.split("/")
            clean = parts[0].strip()
            slash_bass = parts[1].strip()

        m = re.match(r"^([A-G][#b]?)(.*)$", clean)
        if not m:
            return "C", "", None
        root, quality = m.groups()
        root = ENHARMONIC_MAP.get(root, root)
        if slash_bass:
            slash_bass = ENHARMONIC_MAP.get(slash_bass, slash_bass)
        return root, quality.lower(), slash_bass

    @classmethod
    def get_chord_notes(cls, chord_str: str) -> List[str]:
        """Convert chord symbol to list of note strings with octaves (e.g. ['C3', 'C4', 'E4', 'G4'])."""
        root, quality, slash_bass = cls.parse_chord(chord_str)
        if root not in SEMITONES_SHARP:
            return ["C3", "C4", "E4", "G4"]

        root_idx = SEMITONES_SHARP.index(root)
        intervals = CHORD_INTERVALS.get(quality, CHORD_INTERVALS.get("", [0, 4, 7]))

        notes = []
        # Bass note in Octave 3 (or slash bass in Octave 2/3)
        if slash_bass and slash_bass in SEMITONES_SHARP:
            notes.append(f"{slash_bass}2")
        else:
            notes.append(f"{root}3")

        # Voicing in Octave 4 / 5
        for interval in intervals:
            semi = (root_idx + interval) % 12
            octave = 4 + (root_idx + interval) // 12
            notes.append(f"{SEMITONES_SHARP[semi]}{octave}")

        return notes

    @classmethod
    def generate_instrument_sample(
        cls,
        instrument: str,
        freq: float,
        duration: float,
        t: np.ndarray,
        sample_rate: int
    ) -> np.ndarray:
        """Synthesize a single note with acoustic instrument physics."""
        omega = 2.0 * np.pi * freq

        if instrument == "acoustic_piano":
            # Acoustic Grand: Hammer attack, harmonic inharmonicity, dual decay
            env = np.exp(-3.2 * t) * (1.0 - np.exp(-t * 300.0))
            harmonic_1 = np.sin(omega * t)
            harmonic_2 = 0.50 * np.sin(2.0 * omega * t * 1.001)
            harmonic_3 = 0.25 * np.sin(3.0 * omega * t * 1.002)
            harmonic_4 = 0.12 * np.sin(4.0 * omega * t * 1.003)
            harmonic_5 = 0.05 * np.sin(5.0 * omega * t * 1.005)
            # Hammer thud
            hammer = 0.10 * np.sin(omega * 0.5 * t) * np.exp(-t * 60.0)
            return (harmonic_1 + harmonic_2 + harmonic_3 + harmonic_4 + harmonic_5 + hammer) * env

        elif instrument == "electric_rhodes":
            # Rhodes: Bell tine overtone + smooth sine fundamental + subtle chorus tremolo
            lfo = 1.0 + 0.08 * np.sin(2.0 * np.pi * 4.5 * t)
            env = np.exp(-2.2 * t) * (1.0 - np.exp(-t * 200.0))
            fund = np.sin(omega * t)
            tine = 0.40 * np.sin(omega * 3.0 * t) * np.exp(-t * 8.0) # Fast tine decay
            subtle = 0.15 * np.sin(omega * 2.0 * t)
            return (fund + tine + subtle) * env * lfo

        elif instrument == "acoustic_guitar":
            # Plucked guitar string: Sharp metallic attack, exponential damping
            env = np.exp(-2.8 * t) * (1.0 - np.exp(-t * 400.0))
            h1 = np.sin(omega * t)
            h2 = 0.60 * np.sin(2.0 * omega * t)
            h3 = 0.35 * np.sin(3.0 * omega * t)
            h4 = 0.20 * np.sin(4.0 * omega * t)
            pluck_noise = 0.05 * np.random.uniform(-1, 1, len(t)) * np.exp(-t * 80.0)
            return (h1 + h2 + h3 + h4 + pluck_noise) * env

        elif instrument == "synth_pad":
            # Lush Ambient Pad: Detuned saws and sines with slow swell attack
            env = (1.0 - np.exp(-t * 6.0)) * np.exp(-1.2 * t)
            w1 = np.sin(omega * t)
            w2 = 0.8 * np.sin(omega * 1.005 * t) # Chorus detune
            w3 = 0.8 * np.sin(omega * 0.995 * t)
            sub = 0.4 * np.sin(omega * 0.5 * t)
            return (w1 + w2 + w3 + sub) * env

        else: # Default
            env = np.exp(-3.0 * t) * (1.0 - np.exp(-t * 200.0))
            return np.sin(omega * t) * env

    @classmethod
    def synthesize_chord_audio(
        cls,
        chord_str: str,
        instrument: str = "acoustic_piano",
        duration: float = 1.5,
        strum_style: str = "sustained"
    ) -> Path:
        """
        Synthesize polyphonic audio for a chord and cache to WAV.
        strum_style options: 'sustained', 'arpeggio_up', 'strum_down'
        """
        cls._ensure_dir()
        safe_name = re.sub(r"[^A-Za-z0-9]", "_", chord_str)
        cache_key = f"{safe_name}_{instrument}_{strum_style}_{duration:.1f}"

        with cls._lock:
            if cache_key in cls._cache and cls._cache[cache_key].exists():
                return cls._cache[cache_key]

        notes = cls.get_chord_notes(chord_str)
        sr = cls.SAMPLE_RATE
        total_samples = int(sr * duration)
        t_full = np.linspace(0, duration, total_samples, endpoint=False)
        output_signal = np.zeros(total_samples, dtype=np.float32)

        # Strumming delays
        strum_delay = 0.0
        if strum_style == "strum_down":
            strum_delay = 0.025 # 25ms per string
        elif strum_style == "arpeggio_up":
            strum_delay = 0.090 # 90ms arpeggio step

        for i, note in enumerate(notes):
            freq = note_to_freq(note)
            delay_sec = i * strum_delay
            delay_samples = int(delay_sec * sr)
            if delay_samples >= total_samples:
                break

            note_dur = duration - delay_sec
            t_note = np.linspace(0, note_dur, total_samples - delay_samples, endpoint=False)
            note_wave = cls.generate_instrument_sample(instrument, freq, note_dur, t_note, sr)

            output_signal[delay_samples:] += note_wave

        # Normalize and prevent clipping
        max_val = np.max(np.abs(output_signal))
        if max_val > 0.01:
            output_signal = (output_signal / max_val) * 0.92

        # 16-bit PCM conversion
        pcm_data = (output_signal * 32767.0).astype(np.int16)

        out_path = cls._temp_dir / f"{cache_key}.wav"
        with wave.open(str(out_path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(pcm_data.tobytes())

        with cls._lock:
            cls._cache[cache_key] = out_path

        return out_path

    @classmethod
    def play_chord_async(
        cls,
        chord_str: str,
        instrument: str = "acoustic_piano",
        duration: float = 1.4,
        strum_style: str = "sustained"
    ):
        """Asynchronously synthesizes and plays the chord with zero UI blockage."""
        def _worker():
            try:
                import winsound
                wav_path = cls.synthesize_chord_audio(chord_str, instrument, duration, strum_style)
                winsound.PlaySound(str(wav_path), winsound.SND_FILENAME | winsound.SND_ASYNC)
            except Exception as e:
                print(f"Chord playback error: {e}")

        threading.Thread(target=_worker, daemon=True).start()

    @classmethod
    def extract_chords_from_lyrics(cls, text: str) -> List[str]:
        """Extract all bracketed chord tokens like [Am], [C#m7], [Fmaj7] in order without duplicates."""
        tokens = []
        seen = set()
        # Find all [Chord] pattern
        pattern = r"\[([A-G][#b]?(?:m|maj|min|dim|aug|sus[24]?|[0-9])*(?:/[A-G][#b]?)?)\]"
        for match in re.finditer(pattern, text):
            chord = match.group(1).strip()
            if chord and chord not in seen:
                seen.add(chord)
                tokens.append(chord)
        return tokens

    @classmethod
    def get_diatonic_chords(cls, key: str = "C", scale: str = "Major") -> List[Dict[str, str]]:
        """
        Return the 7 diatonic chords + secondary dominants for a given key.
        Returns list of dicts with 'roman', 'chord', 'role', 'color'.
        """
        root = ENHARMONIC_MAP.get(key, key)
        if root not in SEMITONES_SHARP:
            root = "C"
        root_idx = SEMITONES_SHARP.index(root)

        if scale == "Major":
            # I, ii, iii, IV, V, vi, vii°
            intervals = [0, 2, 4, 5, 7, 9, 11]
            qualities = ["", "m", "m", "", "", "m", "dim"]
            romans = ["I", "ii", "iii", "IV", "V", "vi", "vii°"]
            roles = ["Tonic (Home)", "Supertonic", "Mediant", "Subdominant", "Dominant (Tension)", "Submediant (Relative)", "Leading Tone"]
        else: # Natural Minor
            # i, ii°, III, iv, v/V7, VI, VII
            intervals = [0, 2, 3, 5, 7, 8, 10]
            qualities = ["m", "dim", "", "m", "m", "", ""]
            romans = ["i", "ii°", "III", "iv", "v", "VI", "VII"]
            roles = ["Tonic (Minor)", "Supertonic", "Mediant (Relative)", "Subdominant", "Dominant", "Submediant", "Subtonic"]

        chords = []
        for i in range(7):
            idx = (root_idx + intervals[i]) % 12
            chord_name = f"{SEMITONES_SHARP[idx]}{qualities[i]}"
            chords.append({
                "roman": romans[i],
                "chord": chord_name,
                "role": roles[i]
            })

        # Add Secondary / Borrowed pop chords: V/V, bVII, iv (minor 4)
        if scale == "Major":
            v_of_v_idx = (root_idx + 2) % 12 # II7
            b_vii_idx = (root_idx + 10) % 12 # bVII
            iv_min_idx = (root_idx + 5) % 12 # iv minor
            chords.append({"roman": "bVII", "chord": f"{SEMITONES_SHARP[b_vii_idx]}", "role": "Epic Mixolydian / Rock"})
            chords.append({"roman": "iv", "chord": f"{SEMITONES_SHARP[iv_min_idx]}m", "role": "Emotional Minor Plagal"})
            chords.append({"roman": "V/V", "chord": f"{SEMITONES_SHARP[v_of_v_idx]}7", "role": "Secondary Dominant Lift"})
        else:
            # Major V7 for harmonic minor drama
            v7_idx = (root_idx + 7) % 12
            chords.append({"roman": "V7", "chord": f"{SEMITONES_SHARP[v7_idx]}7", "role": "Harmonic Minor Dominant"})

        return chords

