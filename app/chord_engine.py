"""
Professional Musical Chord Engine, Progression Presets,
Semitone Transposer, Vocal Range Recommender, and Pure-Python Polyphonic Audio Synthesizer.
"""

import re
import math
import struct
import wave
import tempfile
import winsound
from pathlib import Path
from typing import List, Dict, Optional

SEMITONES_SHARP = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
SEMITONES_FLAT = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]

ENHARMONIC_MAP = {
    "Db": "C#", "Eb": "D#", "Gb": "F#", "Ab": "G#", "Bb": "A#",
    "B#": "C", "E#": "F", "Cb": "B", "Fb": "E"
}

NOTE_FREQS = {
    # Octave 2
    "C2": 65.41, "C#2": 69.30, "Db2": 69.30, "D2": 73.42, "D#2": 77.78, "Eb2": 77.78,
    "E2": 82.41, "F2": 87.31, "F#2": 92.50, "Gb2": 92.50, "G2": 98.00, "G#2": 103.83,
    "Ab2": 103.83, "A2": 110.00, "A#2": 116.54, "Bb2": 116.54, "B2": 123.47,
    # Octave 3
    "C3": 130.81, "C#3": 138.59, "Db3": 138.59, "D3": 146.83, "D#3": 155.56, "Eb3": 155.56,
    "E3": 164.81, "F3": 174.61, "F#3": 185.00, "Gb3": 185.00, "G3": 196.00, "G#3": 207.65,
    "Ab3": 207.65, "A3": 220.00, "A#3": 233.08, "Bb3": 233.08, "B3": 246.94,
    # Octave 4
    "C4": 261.63, "C#4": 277.18, "Db4": 277.18, "D4": 293.66, "D#4": 311.13, "Eb4": 311.13,
    "E4": 329.63, "F4": 349.23, "F#4": 369.99, "Gb4": 369.99, "G4": 392.00, "G#4": 415.30,
    "Ab4": 415.30, "A4": 440.00, "A#4": 466.16, "Bb4": 466.16, "B4": 493.88,
    # Octave 5
    "C5": 523.25, "C#5": 554.37, "Db5": 554.37, "D5": 587.33, "D#5": 622.25, "Eb5": 622.25,
    "E5": 659.25, "F5": 698.46, "F#5": 739.99, "Gb5": 739.99, "G5": 783.99, "G#5": 830.61,
    "Ab5": 830.61, "A5": 880.00, "A#5": 932.33, "Bb5": 932.33, "B5": 987.77,
    # Octave 6
    "C6": 1046.50
}

CHORD_PROGRESSIONS: Dict[str, Dict] = {
    "Pop Standard 4-Chords (I - V - vi - IV)": {
        "formula": "I - V - vi - IV",
        "description": "Used in 500+ global pop hits (Taylor Swift, Ed Sheeran, Maroon 5).",
        "chords_in_c": ["C", "G", "Am", "F"],
        "mood": "Catchy, Uplifting, Universal"
    },
    "Royal Road / Oudou (IV - V - iii - vi)": {
        "formula": "IV - V - iii - vi",
        "description": "The signature sound of K-Pop, J-Pop, Anime OSTs, and modern East Asian hits.",
        "chords_in_c": ["F", "G", "Em", "Am"],
        "mood": "Emotional, Dramatic, Soaring"
    },
    "Khmer Sinn Sisamouth Sentimental (i - iv - V7 - i)": {
        "formula": "i - iv - V7 - i",
        "description": "Golden era 60s/70s romantic ballad progression with timeless emotional depth.",
        "chords_in_c": ["Am", "Dm", "E7", "Am"],
        "mood": "Heartfelt, Bittersweet, Nostalgic"
    },
    "Khmer Romvong Folk Pentatonic (I - ii - IV - V)": {
        "formula": "I - ii - IV - V",
        "description": "Festive Khmer village rhythms blending pentatonic melodies with acoustic joy.",
        "chords_in_c": ["C", "Dm", "F", "G"],
        "mood": "Joyous, Festive, Danceable"
    },
    "Sad Boy / Heartbreak Ballad (vi - IV - I - V)": {
        "formula": "vi - IV - I - V",
        "description": "Deep vulnerability, crying in the rain, emotional peak (Lewis Capaldi, Adele).",
        "chords_in_c": ["Am", "F", "C", "G"],
        "mood": "Tearjerker, Vulnerable, Melancholic"
    },
    "Neo-Soul & R&B Turnaround (ii7 - V7 - Imaj7 - vi7)": {
        "formula": "ii7 - V7 - Imaj7 - vi7",
        "description": "Jazzy, sophisticated, late-night Rhodes chords and silky falsetto vocal runs.",
        "chords_in_c": ["Dm7", "G7", "Cmaj7", "Am7"],
        "mood": "Silky, Intimate, Luxurious"
    },
    "Andalusian Cadence / Flamenco (i - VII - VI - V)": {
        "formula": "i - VII - VI - V",
        "description": "Flamenco, Latin drama, epic cinematic tension, heroic defiance.",
        "chords_in_c": ["Am", "G", "F", "E7"],
        "mood": "Passionate, Fiery, Dramatic"
    },
    "Latin Dem-bow / Reggaeton Groove (i - VI - VII - i)": {
        "formula": "i - VI - VII - i",
        "description": "Hypnotic minor cadence locking with dem-bow drums (Bad Bunny, J Balvin).",
        "chords_in_c": ["Dm", "Bb", "C", "Dm"],
        "mood": "Sensual, Danceable, Street Energy"
    },
    "Bachata Romántica (i - iv - VII - III)": {
        "formula": "i - iv - VII - III",
        "description": "Dominican syncopated acoustic guitar arpeggios full of longing (Romeo Santos).",
        "chords_in_c": ["Am", "Dm", "G", "C"],
        "mood": "Romantic, Passionate, Bouncing"
    },
    "80s City Pop / Plastic Love (IVmaj7 - iii7 - vi7 - ii7 - V7)": {
        "formula": "IVmaj7 - iii7 - vi7 - ii7 - V7",
        "description": "Mariya Takeuchi City Pop groove with lush extensions and sophisticated urban melancholy.",
        "chords_in_c": ["Fmaj7", "Em7", "Am7", "Dm7", "G7"],
        "mood": "Nostalgic, Breezy, Sophisticated"
    },
    "Epic Cinematic Hans Zimmer Minor Arc (i - VI - III - VII)": {
        "formula": "i - VI - III - VII",
        "description": "Massive film trailer swell, heroic strings, thunderous brass building to a climax.",
        "chords_in_c": ["Am", "F", "C", "G"],
        "mood": "Epic, Majestic, Triumphant"
    },
    "Sad 808 Melodic Trap (i - VI - iv - v)": {
        "formula": "i - VI - iv - v",
        "description": "Minor keys filtered over heavy sliding 808 subs (Juice WRLD, Post Malone, Vannda).",
        "chords_in_c": ["Am", "F", "Dm", "Em"],
        "mood": "Dark, Atmospheric, Gritty"
    },
    "Doo-Wop 50s / Stand By Me (I - vi - IV - V)": {
        "formula": "I - vi - IV - V",
        "description": "The timeless golden oldies chord sequence heard in classic vocal group ballads.",
        "chords_in_c": ["C", "Am", "F", "G"],
        "mood": "Warm, Nostalgic, Sweet"
    },
    "Acoustic Coffeehouse Folk / Pachelbel (I - V - vi - iii - IV - I - IV - V)": {
        "formula": "I - V - vi - iii - IV - I - IV - V",
        "description": "Endlessly resolving acoustic guitar fingerpicking and comforting storytelling.",
        "chords_in_c": ["C", "G", "Am", "Em", "F", "C", "F", "G"],
        "mood": "Intimate, Comforting, Reflective"
    },
    "Gospel Soul & Borrowed Minor 4th (I - I7 - IV - iv - I)": {
        "formula": "I - I7 - IV - iv - I",
        "description": "The magical Beatles and Motown emotional trick: resolving through the minor iv chord.",
        "chords_in_c": ["C", "C7", "F", "Fm", "C"],
        "mood": "Soulful, Bittersweet, Hopeful"
    },
    "Modern Synthwave / Neon Retrowave (vi - V - IV - V)": {
        "formula": "vi - V - IV - V",
        "description": "Driving nighttime highway synth bass arpeggio with 80s analog nostalgia.",
        "chords_in_c": ["Am", "G", "F", "G"],
        "mood": "Cinematic, Driving, Euphoric"
    },
    "Afrobeats Syncopated Sunshine (I - IV - vi - V)": {
        "formula": "I - IV - vi - V",
        "description": "Joyous syncopated West African bounce locking with log drums (Burna Boy, Wizkid).",
        "chords_in_c": ["C", "F", "Am", "G"],
        "mood": "Joyous, Danceable, Uplifting"
    },
    "Punjabi Pop & Bhangra Energetic Minor (i - VII - i - VII)": {
        "formula": "i - VII - i - VII",
        "description": "Hypnotic driving dhol rhythm with soaring Punjabi vocal hooks (Diljit Dosanjh).",
        "chords_in_c": ["Am", "G", "Am", "G"],
        "mood": "High Energy, Celebratory, Driving"
    },
    "K-Pop Explosive Climax (vi - V - IV - III7)": {
        "formula": "vi - V - IV - III7",
        "description": "Rising vocal intensity resolving through a dramatic harmonic minor dominant 7th.",
        "chords_in_c": ["Am", "G", "F", "E7"],
        "mood": "Intense, Climactic, Heroic"
    },
    "Classic Rock & Blues 12-Bar (I7 - IV7 - I7 - V7)": {
        "formula": "I7 - IV7 - I7 - V7",
        "description": "The foundational driving groove of blues, classic rock, and grit.",
        "chords_in_c": ["C7", "F7", "C7", "G7"],
        "mood": "Raw, Energetic, Gritty"
    },
    "Khmer Kantrum Folk Fast Dance (i - VII - v - i)": {
        "formula": "i - VII - v - i",
        "description": "Traditional Skor Daey, Tro, and fast folk violin bounce for festive parties.",
        "chords_in_c": ["Am", "G", "Em", "Am"],
        "mood": "Fast, Festive, Energetic"
    },
    "Indie Dream Pop Shoegaze (Imaj7 - IVmaj7 - vi7 - V)": {
        "formula": "Imaj7 - IVmaj7 - vi7 - V",
        "description": "Reverb-drenched, shimmering chorus pedal chords with ethereal nostalgia.",
        "chords_in_c": ["Cmaj7", "Fmaj7", "Am7", "G"],
        "mood": "Dreamy, Atmospheric, Floating"
    }
}

VOCAL_RANGES = {
    "Male Tenor / High Pop Vocal": {
        "range": "C3 - G4 (Belt to B4)",
        "recommended_keys": ["C Major", "D Major", "E Major", "G Minor"],
        "artists": "Bruno Mars, The Weeknd, Vannda, Jungkook"
    },
    "Male Baritone / Deep Chest Vocal": {
        "range": "A2 - F4",
        "recommended_keys": ["G Major", "A Major", "Bb Major", "F Minor"],
        "artists": "Sinn Sisamouth, John Legend, Drake, Hozier"
    },
    "Female Soprano / High Vocal Belt": {
        "range": "C4 - A5 (High C6)",
        "recommended_keys": ["E Major", "F Major", "G Major", "A Minor"],
        "artists": "Ros Sereysothea, Ariana Grande, Taeyeon, IU"
    },
    "Female Alto / Warm Smoky Mezzo": {
        "range": "F3 - D5",
        "recommended_keys": ["C Major", "Db Major", "Eb Major", "D Minor"],
        "artists": "Adele, Dua Lipa, Billie Eilish, Amy Winehouse"
    }
}

class AudioChordSynthesizer:
    """
    Pure Python Polyphonic Audio Chord Synthesizer.
    Generates rich warm electric piano / Rhodes chord tones with acoustic harmonics
    and plays them asynchronously with zero latency on Windows via winsound.
    """
    _temp_dir = Path(tempfile.gettempdir()) / "worldlyric_synth"

    @classmethod
    def _ensure_temp_dir(cls):
        cls._temp_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def parse_chord_to_notes(cls, chord_str: str) -> List[str]:
        """Convert a chord symbol (e.g. 'Cmaj7', 'Am', 'F#m7/C#', 'Bb') to note tokens with octaves."""
        norm_map = ENHARMONIC_MAP
        # Handle slash chord
        main_part = chord_str.split("/")[0].strip()
        slash_part = chord_str.split("/")[1].strip() if "/" in chord_str else ""

        m = re.match(r"^([A-G][#b]?)(.*)$", main_part)
        if not m:
            return ["C3", "C4", "E4", "G4"]

        root, quality = m.groups()
        root = norm_map.get(root, root)
        if root not in SEMITONES_SHARP:
            return ["C3", "C4", "E4", "G4"]

        root_idx = SEMITONES_SHARP.index(root)
        q = quality.lower().strip()

        # Intervals relative to root
        offsets = [0, 4, 7] # Default major triad

        if "m7" in q or "min7" in q:
            offsets = [0, 3, 7, 10]
        elif "maj7" in q or "m7+" in q:
            offsets = [0, 4, 7, 11]
        elif "m" in q or "min" in q:
            offsets = [0, 3, 7]
        elif "dim" in q:
            offsets = [0, 3, 6]
        elif "aug" in q or "+" in q:
            offsets = [0, 4, 8]
        elif "sus4" in q:
            offsets = [0, 5, 7]
        elif "sus2" in q:
            offsets = [0, 2, 7]
        elif "7" in q:
            offsets = [0, 4, 7, 10]
        elif "9" in q:
            offsets = [0, 4, 7, 10, 14]

        notes = []
        # Bass note (octave 2 or 3)
        if slash_part:
            norm_bass = norm_map.get(slash_part, slash_part)
            notes.append(norm_bass + "2")
        else:
            notes.append(SEMITONES_SHARP[root_idx] + "3")

        # Chord triad / 7th in octave 4 / 5
        for off in offsets:
            semi_idx = (root_idx + off) % 12
            octave = 4 if (root_idx + off) < 12 else 5
            notes.append(SEMITONES_SHARP[semi_idx] + str(octave))

        return notes

    @classmethod
    def synthesize_chord_wav(cls, chord_name: str, out_path: Path, duration: float = 1.3, sample_rate: int = 44100):
        """Generate a realistic warm electric piano chord wave file."""
        notes = cls.parse_chord_to_notes(chord_name)
        freqs = [NOTE_FREQS.get(n, 261.63) for n in notes]
        num_samples = int(sample_rate * duration)

        with wave.open(str(out_path), "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            frames = bytearray()
            for i in range(num_samples):
                t = i / float(sample_rate)
                # ADSR acoustic decay: rapid 10ms attack, exponential body decay
                env = math.exp(-2.6 * t) * min(1.0, t * 120.0)
                sample = 0.0
                for f in freqs:
                    # Fundamental + 2nd overtone + 3rd subtle overtone (Rhodes warm timbre)
                    sample += 0.65 * math.sin(2.0 * math.pi * f * t)
                    sample += 0.25 * math.sin(4.0 * math.pi * f * t)
                    sample += 0.10 * math.sin(6.0 * math.pi * f * t)

                sample_norm = (sample / max(1, len(freqs))) * env * 27000.0
                val = int(max(-32767, min(32767, sample_norm)))
                frames.extend(struct.pack("<h", val))
            wav.writeframes(frames)

    @classmethod
    def synthesize_progression_wav(cls, chords: List[str], out_path: Path, bpm: int = 120, beats_per_chord: int = 2, sample_rate: int = 44100):
        """Stitch a sequence of chords into a single continuous audio progression WAV."""
        sec_per_beat = 60.0 / max(40, min(240, bpm))
        chord_duration = beats_per_chord * sec_per_beat
        num_samples_per_chord = int(sample_rate * chord_duration)

        with wave.open(str(out_path), "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            frames = bytearray()

            for chord_name in chords:
                notes = cls.parse_chord_to_notes(chord_name)
                freqs = [NOTE_FREQS.get(n, 261.63) for n in notes]

                for i in range(num_samples_per_chord):
                    t = i / float(sample_rate)
                    env = math.exp(-2.2 * t) * min(1.0, t * 120.0)
                    sample = 0.0
                    for f in freqs:
                        sample += 0.65 * math.sin(2.0 * math.pi * f * t)
                        sample += 0.25 * math.sin(4.0 * math.pi * f * t)
                        sample += 0.10 * math.sin(6.0 * math.pi * f * t)

                    sample_norm = (sample / max(1, len(freqs))) * env * 27000.0
                    val = int(max(-32767, min(32767, sample_norm)))
                    frames.extend(struct.pack("<h", val))

            wav.writeframes(frames)

    @classmethod
    def play_chord(cls, chord_name: str):
        """Play single chord asynchronously."""
        try:
            cls._ensure_temp_dir()
            safe_name = "".join(c for c in chord_name if c.isalnum() or c in ("#", "-")).replace("#", "sharp")
            out_file = cls._temp_dir / f"chord_{safe_name}.wav"
            cls.synthesize_chord_wav(chord_name, out_file, duration=1.2)
            winsound.PlaySound(str(out_file), winsound.SND_FILENAME | winsound.SND_ASYNC)
        except Exception as e:
            print(f"Chord synthesis error: {e}")

    @classmethod
    def play_progression(cls, chords: List[str], bpm: int = 120):
        """Play progression of chords in rhythm asynchronously."""
        try:
            cls._ensure_temp_dir()
            out_file = cls._temp_dir / "progression_live.wav"
            cls.synthesize_progression_wav(chords, out_file, bpm=bpm, beats_per_chord=2)
            winsound.PlaySound(str(out_file), winsound.SND_FILENAME | winsound.SND_ASYNC)
        except Exception as e:
            print(f"Progression synthesis error: {e}")

    @classmethod
    def stop(cls):
        """Halt all audio synthesis output immediately."""
        try:
            winsound.PlaySound(None, 0)
        except Exception:
            pass


class ChordEngine:

    @staticmethod
    def transpose_root(root: str, semitones: int) -> str:
        """Transpose single root note by semitone offset."""
        norm = ENHARMONIC_MAP.get(root, root)
        if norm in SEMITONES_SHARP:
            idx = SEMITONES_SHARP.index(norm)
            new_idx = (idx + semitones) % 12
            return SEMITONES_SHARP[new_idx]
        return root

    @staticmethod
    def transpose_chord(chord: str, semitones: int) -> str:
        """
        Transpose a single chord token (e.g. 'C#m7', 'Bb/D', 'F#dim').
        Preserves chord quality and bass slash note.
        """
        if not chord:
            return ""

        # Check for slash chord (e.g. C/G, D/F#)
        if "/" in chord:
            parts = chord.split("/", 1)
            main_chord = ChordEngine.transpose_chord(parts[0], semitones)
            bass_note = ChordEngine.transpose_root(parts[1], semitones)
            return f"{main_chord}/{bass_note}"

        # Match root note: e.g. C#, Bb, F, G
        match = re.match(r"^([A-G][#b]?)(.*)$", chord)
        if not match:
            return chord

        root, quality = match.groups()
        new_root = ChordEngine.transpose_root(root, semitones)
        return f"{new_root}{quality}"

    @staticmethod
    def transpose_lyrics_with_chords(text: str, semitones: int) -> str:
        """
        Transpose all chords embedded in square brackets (e.g. [C], [Am7], [G/B])
        while skipping structural section tags like [Verse], [Chorus], [Intro].
        """
        section_tags = {
            "intro", "verse", "pre-chorus", "chorus", "bridge", "outro",
            "hook", "solo", "drop", "ad-lib", "whisper", "chant", "coda",
            "វគ្គ", "បន្ទរ", "ឆ្លើយឆ្លង", "បញ្ចប់", "សេចក្ដីផ្ដើម"
        }

        def replace_tag(match):
            inner = match.group(1).strip()
            # If it's a section tag or contains spaces/words, leave intact
            lower = inner.lower()
            if any(sec in lower for sec in section_tags) or " " in inner:
                return match.group(0)

            # Check if it looks like a musical chord (starts with A-G)
            if re.match(r"^[A-G][#b]?(m|maj|min|dim|aug|sus|add|7|9|11|13|b5)?(/([A-G][#b]?))?$", inner):
                transposed = ChordEngine.transpose_chord(inner, semitones)
                return f"[{transposed}]"
            return match.group(0)

        return re.sub(r"\[(.*?)\]", replace_tag, text)
