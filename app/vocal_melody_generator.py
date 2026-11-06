"""
AI Vocal Melody & Topline Pitch Guide Engine.
Generates melodic vocal pitch contours aligned with lyric syllable cadence.
Exports Standard Type 1 MIDI with embedded Lyric Meta-Events (0x05)
and Standard MusicXML 3.1 Sheet Music for MuseScore, Sibelius, Finale, and DAWs.
"""

import os
import re
import math
import struct
import wave
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import numpy as np

# Scale definitions (semitone intervals from root)
SCALES = {
    "Major": [0, 2, 4, 5, 7, 9, 11],
    "Natural Minor": [0, 2, 3, 5, 7, 8, 10],
    "Major Pentatonic": [0, 2, 4, 7, 9],
    "Minor Pentatonic": [0, 3, 5, 7, 10],
    "Khmer Mohori Pentatonic": [0, 2, 5, 7, 9], # Traditional Khmer 5-tone scale
    "Blues": [0, 3, 5, 6, 7, 10],
    "Dorian": [0, 2, 3, 5, 7, 9, 10],
}

ROOT_TO_MIDI = {
    "C": 60, "C#": 61, "Db": 61, "D": 62, "D#": 63, "Eb": 63,
    "E": 64, "F": 65, "F#": 66, "Gb": 66, "G": 67, "G#": 68,
    "Ab": 68, "A": 69, "A#": 70, "Bb": 70, "B": 71
}

MIDI_TO_NOTE_NAME = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def midi_to_step_octave(midi_num: int) -> Tuple[str, int, int]:
    """Convert MIDI number like 60 -> ('C', 4, 0 alter). 61 -> ('C', 4, 1 alter)."""
    octave = (midi_num // 12) - 1
    semi = midi_num % 12
    name = MIDI_TO_NOTE_NAME[semi]
    if len(name) == 2:
        return name[0], octave, 1 # Sharp
    return name, octave, 0


def encode_var_len(val: int) -> bytes:
    """Encode integer as MIDI variable-length quantity."""
    buf = bytearray()
    buf.append(val & 0x7F)
    val >>= 7
    while val > 0:
        buf.append((val & 0x7F) | 0x80)
        val >>= 7
    buf.reverse()
    return bytes(buf)


class VocalToplineGenerator:
    """
    Creates melodic topline guides aligned to lyrics.
    Generates Type 1 MIDI and MusicXML.
    """

    @classmethod
    def generate_melody_events(
        cls,
        lyrics: str,
        key: str = "C",
        scale: str = "Major",
        bpm: int = 120
    ) -> List[Dict]:
        """
        Generates list of note events:
        [{'syllable': 'Love', 'midi': 64, 'beat': 1.0, 'duration_beats': 0.5, 'section': 'Verse'}]
        """
        root_midi = ROOT_TO_MIDI.get(key, 60)
        scale_intervals = SCALES.get(scale, SCALES["Major"])

        lines = [l.strip() for l in lyrics.split("\n") if l.strip()]
        current_section = "Verse"
        current_beat = 1.0
        events = []

        scale_len = len(scale_intervals)

        for line in lines:
            if line.startswith("[") and line.endswith("]"):
                sec_name = line[1:-1].strip()
                current_section = sec_name
                # Pad to next full 4-beat bar
                current_beat = (math.ceil(current_beat / 4.0) * 4.0) + 1.0
                continue

            # Strip bracketed chords from line for vocal topline
            clean_line = re.sub(r"\[.*?\]", "", line).strip()
            if not clean_line:
                continue

            # Syllable segmentation
            from app.khmer_poetry_meter import segment_khmer_syllables
            syllables = segment_khmer_syllables(clean_line)
            if not syllables:
                continue

            # Section register bias
            is_chorus = "chorus" in current_section.lower() or "hook" in current_section.lower()
            base_octave_offset = 12 if is_chorus else 0 # Chorus is 1 octave higher for hook energy!

            step_idx = 0 if not is_chorus else 4 # Start higher in chorus

            for syl_idx, syl in enumerate(syllables):
                # Pitch contour variation
                # Create melodic wave: up then down or hook repetition
                melodic_step = (step_idx + (syl_idx % scale_len)) % scale_len
                interval = scale_intervals[melodic_step]
                note_midi = root_midi + base_octave_offset + interval

                # Duration: Eighth note (0.5 beats) or Quarter note (1.0 beats) for phrase ending
                is_phrase_end = (syl_idx == len(syllables) - 1)
                dur = 1.0 if is_phrase_end else 0.5

                events.append({
                    "syllable": syl,
                    "midi": note_midi,
                    "beat": current_beat,
                    "duration_beats": dur,
                    "section": current_section
                })

                current_beat += dur

            # Breath pause at line end (0.5 or 1 beat rest)
            current_beat += 0.5

        return events

    @classmethod
    def export_midi(
        cls,
        events: List[Dict],
        out_filepath: str,
        bpm: int = 120,
        title: str = "Vocal Topline Guide"
    ) -> str:
        """
        Exports a Type 1 Standard MIDI File with embedded Lyric Meta-Events (0x05).
        DAWs will render notes + lyric text simultaneously.
        """
        ppq = 480 # Pulses per quarter note
        tempo_us = int(60_000_000 / max(40, min(240, bpm)))

        # --- Track 0: Conductor Track (Tempo & Time Signature) ---
        t0_data = bytearray()
        # Track Name
        name_bytes = title.encode("utf-8")
        t0_data.extend(b"\x00\xFF\x03" + bytes([len(name_bytes)]) + name_bytes)
        # Time Signature: 4/4
        t0_data.extend(b"\x00\xFF\x58\x04\x04\x02\x18\x08")
        # Tempo
        t0_data.extend(b"\x00\xFF\x51\x03" + struct.pack(">I", tempo_us)[1:])
        # End of Track
        t0_data.extend(b"\x00\xFF\x2F\x00")

        # --- Track 1: Vocal Melody & Lyrics Track ---
        t1_data = bytearray()
        vocal_name = b"Vocal Topline Lead"
        t1_data.extend(b"\x00\xFF\x03" + bytes([len(vocal_name)]) + vocal_name)
        # Program change: Flute / Lead Synth (Program 73 = Flute, or 54 = Voice Oohs)
        t1_data.extend(b"\x00\xC0\x36") # Voice Oohs (0x36 = 54)

        current_tick = 0
        for ev in events:
            event_tick = int((ev["beat"] - 1.0) * ppq)
            delta_start = max(0, event_tick - current_tick)

            # Lyric Meta-Event (0xFF 0x05)
            syl_bytes = ev["syllable"].encode("utf-8")
            t1_data.extend(encode_var_len(delta_start))
            t1_data.extend(b"\xFF\x05" + bytes([len(syl_bytes)]) + syl_bytes)

            # Note On (Channel 0, Note, Vel 96)
            t1_data.extend(b"\x00\x90" + bytes([ev["midi"], 96]))

            # Note Off
            dur_ticks = int(ev["duration_beats"] * ppq)
            t1_data.extend(encode_var_len(dur_ticks))
            t1_data.extend(b"\x80" + bytes([ev["midi"], 0]))

            current_tick = event_tick + dur_ticks

        # End of Track 1
        t1_data.extend(b"\x00\xFF\x2F\x00")

        # Write MIDI file
        with open(out_filepath, "wb") as f:
            # Header: MThd, len 6, Type 1 (2 tracks), PPQ 480
            f.write(b"MThd\x00\x00\x00\x06\x00\x01\x00\x02" + struct.pack(">H", ppq))
            # Track 0
            f.write(b"MTrk" + struct.pack(">I", len(t0_data)) + bytes(t0_data))
            # Track 1
            f.write(b"MTrk" + struct.pack(">I", len(t1_data)) + bytes(t1_data))

        return out_filepath

    @classmethod
    def export_musicxml(
        cls,
        events: List[Dict],
        out_filepath: str,
        title: str = "Lead Sheet Sheet Music",
        composer: str = "SMG Suno AI Lyric Writer",
        bpm: int = 120
    ) -> str:
        """
        Exports valid MusicXML 3.1 file readable by MuseScore, Sibelius, Finale, Dorico.
        """
        score = ET.Element("score-partwise", version="3.1")

        # Work Title
        work = ET.SubElement(score, "work")
        w_title = ET.SubElement(work, "work-title")
        w_title.text = title

        # Identification
        ident = ET.SubElement(score, "identification")
        creator = ET.SubElement(ident, "creator", type="composer")
        creator.text = composer

        # Part List
        part_list = ET.SubElement(score, "part-list")
        score_part = ET.SubElement(part_list, "score-part", id="P1")
        part_name = ET.SubElement(score_part, "part-name")
        part_name.text = "Vocal Lead"

        # Part
        part = ET.SubElement(score, "part", id="P1")

        # Divisions: 4 divisions per quarter note (16th note = 1 division)
        divisions_val = 4
        beats_per_measure = 4

        current_measure_num = 1
        current_measure_beat = 0.0
        measure = ET.SubElement(part, "measure", number=str(current_measure_num))

        # Attributes in Measure 1
        attrs = ET.SubElement(measure, "attributes")
        divs = ET.SubElement(attrs, "divisions")
        divs.text = str(divisions_val)

        time_elem = ET.SubElement(attrs, "time")
        beats = ET.SubElement(time_elem, "beats")
        beats.text = "4"
        beat_type = ET.SubElement(time_elem, "beat-type")
        beat_type.text = "4"

        clef = ET.SubElement(attrs, "clef")
        sign = ET.SubElement(clef, "sign")
        sign.text = "G"
        line = ET.SubElement(clef, "line")
        line.text = "2"

        for ev in events:
            # Check measure boundary
            event_dur_beats = ev["duration_beats"]

            if current_measure_beat + event_dur_beats > beats_per_measure:
                # Wrap to next measure
                current_measure_num += 1
                current_measure_beat = 0.0
                measure = ET.SubElement(part, "measure", number=str(current_measure_num))

            note_elem = ET.SubElement(measure, "note")
            pitch = ET.SubElement(note_elem, "pitch")
            step, octave, alter = midi_to_step_octave(ev["midi"])

            step_el = ET.SubElement(pitch, "step")
            step_el.text = step
            if alter != 0:
                alter_el = ET.SubElement(pitch, "alter")
                alter_el.text = str(alter)
            oct_el = ET.SubElement(pitch, "octave")
            oct_el.text = str(octave)

            dur_el = ET.SubElement(note_elem, "duration")
            dur_el.text = str(int(event_dur_beats * divisions_val))

            type_el = ET.SubElement(note_elem, "type")
            type_el.text = "quarter" if event_dur_beats >= 1.0 else "eighth"

            # Lyric element
            lyric_el = ET.SubElement(note_elem, "lyric", number="1")
            syl_el = ET.SubElement(lyric_el, "syllabic")
            syl_el.text = "single"
            text_el = ET.SubElement(lyric_el, "text")
            text_el.text = ev["syllable"]

            current_measure_beat += event_dur_beats

        tree = ET.ElementTree(score)
        ET.indent(tree, space="  ", level=0)
        tree.write(out_filepath, encoding="utf-8", xml_declaration=True)
        return out_filepath

    @classmethod
    def synthesize_preview_audio(
        cls,
        events: List[Dict],
        out_filepath: str,
        bpm: int = 120,
        sample_rate: int = 44100
    ) -> str:
        """Synthesize preview wav of the topline vocal pitch guide."""
        sec_per_beat = 60.0 / max(40, min(240, bpm))
        if not events:
            total_sec = 2.0
        else:
            last = events[-1]
            total_sec = (last["beat"] + last["duration_beats"] + 1.0) * sec_per_beat

        num_samples = int(sample_rate * total_sec)
        out_signal = np.zeros(num_samples, dtype=np.float32)

        for ev in events:
            start_sec = (ev["beat"] - 1.0) * sec_per_beat
            start_sample = int(start_sec * sample_rate)
            dur_sec = ev["duration_beats"] * sec_per_beat
            dur_sample = int(dur_sec * sample_rate)

            if start_sample + dur_sample > num_samples:
                break

            t = np.linspace(0, dur_sec, dur_sample, endpoint=False)
            freq = 440.0 * (2.0 ** ((ev["midi"] - 69) / 12.0))
            omega = 2.0 * np.pi * freq

            # Flute / Voice Ooh timbre
            env = np.sin(np.pi * np.clip(t / dur_sec, 0.0, 1.0)) # Smooth bell envelope
            note_wave = (np.sin(omega * t) + 0.3 * np.sin(2.0 * omega * t)) * env

            out_signal[start_sample:start_sample + dur_sample] += note_wave

        # Normalize
        max_val = np.max(np.abs(out_signal))
        if max_val > 0.01:
            out_signal = (out_signal / max_val) * 0.90

        pcm = (out_signal * 32767.0).astype(np.int16)
        with wave.open(out_filepath, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(pcm.tobytes())

        return out_filepath
