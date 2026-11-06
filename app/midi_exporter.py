"""
Professional Pure-Python MIDI Exporter for Chord Progressions.
Generates Standard MIDI Files (.mid Type 0) ready for immediate drag-and-drop
into FL Studio, Ableton Live, Logic Pro, Cubase, and Studio One.
Zero external dependencies required.
"""

from pathlib import Path
from typing import List, Dict

# MIDI Note Numbers (Octave 4)
ROOT_TO_MIDI = {
    "C": 60, "C#": 61, "Db": 61,
    "D": 62, "D#": 63, "Eb": 63,
    "E": 64, "Fb": 64, "E#": 65,
    "F": 65, "F#": 66, "Gb": 66,
    "G": 67, "G#": 68, "Ab": 68,
    "A": 69, "A#": 70, "Bb": 70,
    "B": 71, "Cb": 71, "B#": 60
}

CHORD_INTERVALS = {
    "maj": [0, 4, 7],
    "min": [0, 3, 7],
    "7": [0, 4, 7, 10],
    "maj7": [0, 4, 7, 11],
    "m7": [0, 3, 7, 10],
    "dim": [0, 3, 6],
    "aug": [0, 4, 8],
    "sus4": [0, 5, 7],
    "sus2": [0, 2, 7],
    "add9": [0, 4, 7, 14]
}

def parse_chord_to_midi_notes(chord_symbol: str) -> List[int]:
    """
    Parses a chord string like 'Am', 'C#m7', 'Bb', 'G7', 'Fmaj7'
    and returns a list of MIDI note numbers including a bass note in octave 3
    and triad/seventh in octave 4.
    """
    clean = chord_symbol.strip().strip("[]()")
    if not clean:
        return [60, 64, 67] # Default C Major

    # Check for slash chord (e.g., C/G)
    slash_bass = None
    if "/" in clean:
        parts = clean.split("/")
        clean = parts[0]
        slash_bass = parts[1]

    # Extract root
    if len(clean) >= 2 and clean[1] in ["#", "b"]:
        root_name = clean[:2]
        quality = clean[2:]
    else:
        root_name = clean[:1]
        quality = clean[1:]

    base_midi = ROOT_TO_MIDI.get(root_name, 60)

    # Determine intervals
    if quality in ["m", "min", "minor", "-"]:
        intervals = CHORD_INTERVALS["min"]
    elif quality in ["7", "dom7"]:
        intervals = CHORD_INTERVALS["7"]
    elif quality in ["maj7", "M7", "Δ"]:
        intervals = CHORD_INTERVALS["maj7"]
    elif quality in ["m7", "min7", "-7"]:
        intervals = CHORD_INTERVALS["m7"]
    elif quality in ["dim", "°"]:
        intervals = CHORD_INTERVALS["dim"]
    elif quality in ["sus4", "sus"]:
        intervals = CHORD_INTERVALS["sus4"]
    elif quality in ["sus2"]:
        intervals = CHORD_INTERVALS["sus2"]
    elif quality in ["add9"]:
        intervals = CHORD_INTERVALS["add9"]
    elif quality in ["aug", "+"]:
        intervals = CHORD_INTERVALS["aug"]
    else:
        intervals = CHORD_INTERVALS["maj"]

    # Voicing: Bass note 1 octave down (root - 12) + chord notes in octave 4
    notes = []
    if slash_bass and slash_bass in ROOT_TO_MIDI:
        bass_note = ROOT_TO_MIDI[slash_bass] - 12
    else:
        bass_note = base_midi - 12
    notes.append(bass_note)

    for interval in intervals:
        notes.append(base_midi + interval)

    return notes

def _encode_var_length(val: int) -> bytes:
    """Encode an integer as a MIDI variable length quantity."""
    buf = bytearray()
    buf.append(val & 0x7F)
    val >>= 7
    while val > 0:
        buf.append((val & 0x7F) | 0x80)
        val >>= 7
    buf.reverse()
    return bytes(buf)

class MidiExporter:
    """
    Constructs and writes Standard MIDI Files (.mid Type 0) containing
    chords, bassline, and tempo meta-events.
    """

    @staticmethod
    def export_chord_progression(
        filepath: str,
        progression_name: str,
        chords: List[str],
        bpm: int = 120,
        beats_per_chord: int = 4,
        time_signature: tuple = (4, 4)
    ):
        ticks_per_quarter = 480
        ticks_per_chord = beats_per_chord * ticks_per_quarter

        track_events = bytearray()

        # 1. Track Name Meta-Event: 00 FF 03 len [text]
        track_name = f"Chords - {progression_name}".encode("utf-8")
        track_events.extend(b"\x00\xFF\x03" + _encode_var_length(len(track_name)) + track_name)

        # 2. Time Signature Meta-Event: 00 FF 58 04 nn dd cc bb
        # nn = numerator, dd = denom as power of 2 (4 = 2^2 -> 02)
        num, denom = time_signature
        denom_pow = 2 if denom == 4 else 3
        track_events.extend(b"\x00\xFF\x58\x04" + bytes([num, denom_pow, 24, 8]))

        # 3. Tempo Meta-Event: 00 FF 51 03 [3-byte microseconds per beat]
        microseconds_per_beat = int(60_000_000 / max(30, min(300, bpm)))
        tempo_bytes = microseconds_per_beat.to_bytes(3, byteorder="big")
        track_events.extend(b"\x00\xFF\x51\x03" + tempo_bytes)

        # 4. Generate Chords Events
        velocity = 92 # Studio velocity

        for chord_str in chords:
            midi_notes = parse_chord_to_midi_notes(chord_str)

            # Note On events: first note has delta-time 0, others delta-time 0
            for i, note in enumerate(midi_notes):
                delta = 0
                track_events.extend(_encode_var_length(delta))
                track_events.extend(bytes([0x90, note, velocity]))

            # Note Off events after duration:
            # First note off has delta = ticks_per_chord, subsequent note offs have delta = 0
            for i, note in enumerate(midi_notes):
                delta = ticks_per_chord if i == 0 else 0
                track_events.extend(_encode_var_length(delta))
                track_events.extend(bytes([0x80, note, 0x00]))

        # 5. End of Track Meta-Event: 00 FF 2F 00
        track_events.extend(b"\x00\xFF\x2F\x00")

        # Build Standard MIDI File Header
        # MThd: 4 bytes len (6), format 0 (single track), 1 track, 480 division
        header = bytearray(b"MThd")
        header.extend((6).to_bytes(4, byteorder="big"))
        header.extend((0).to_bytes(2, byteorder="big")) # Format 0
        header.extend((1).to_bytes(2, byteorder="big")) # 1 Track
        header.extend(ticks_per_quarter.to_bytes(2, byteorder="big"))

        # MTrk: 4 bytes len, track_events
        track_chunk = bytearray(b"MTrk")
        track_chunk.extend(len(track_events).to_bytes(4, byteorder="big"))
        track_chunk.extend(track_events)

        with open(filepath, "wb") as f:
            f.write(header)
            f.write(track_chunk)
