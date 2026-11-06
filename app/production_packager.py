"""
Professional Suno & Udio 1-Click Production ZIP Packager.
Bundles Style Prompts, Negative Exclusions, Structured Lyrics with audio meta-tags,
DAW MIDI chord progression (.mid), Printable HTML Lead Sheet, Full JSON metadata,
Vocal Topline Guide (.mid with embedded lyrics), MusicXML Sheet Music (.musicxml),
and High-Resolution Album Cover Artwork (.png).
"""

import os
import json
import zipfile
import tempfile
from pathlib import Path
from app.midi_exporter import MidiExporter
from app.exporter import Exporter

class ProductionPackager:
    @staticmethod
    def create_production_bundle(
        output_zip_path: str,
        title: str,
        lyrics: str,
        suno_style_prompt: str,
        negative_prompt: str,
        chord_progression_name: str,
        chords: list,
        metadata: dict
    ) -> str:
        """Creates a professional .zip bundle containing all production assets."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # 1. Suno & Udio Prompt Card
            prompt_file = temp_path / "1_SUNO_UDIO_STYLE_PROMPT.txt"
            with open(prompt_file, "w", encoding="utf-8") as f:
                f.write("=== SUNO v3.5/v4 & UDIO PRODUCTION PROMPT CARD ===\n\n")
                f.write(f"TRACK TITLE: {title}\n")
                f.write(f"GENRE: {metadata.get('genre', 'Unknown')} ({metadata.get('region', 'Global')})\n")
                f.write(f"BPM: {metadata.get('bpm', '120 BPM')}\n")
                f.write(f"CHORDS: {' - '.join(chords)}\n\n")
                from app.humanizer_engine import HumanizerEngine
                scores = HumanizerEngine.score_human_authenticity(lyrics, suno_style_prompt, metadata.get("language", "English"))
                f.write(f"HUMAN AUTHENTICITY RATING: {scores['overall_score']}% ({scores['status_tag']})\n")
                f.write(f"• Sensory Grounding: {scores['sensory_score']}%\n• Vocal Breathability: {scores['breath_score']}%\n• Story Vulnerability: {scores['vulnerability_score']}%\n• Live Groove Warmth: {scores['groove_score']}%\n\n")
                f.write("-" * 50 + "\n")
                f.write("STYLE PROMPT (Copy into Suno 'Style of Music' field):\n")
                f.write(suno_style_prompt.strip() + "\n\n")
                f.write("-" * 50 + "\n")
                f.write("NEGATIVE STYLE (Copy into Suno 'Exclude Styles' field):\n")
                f.write(negative_prompt.strip() + "\n\n")

            # 2. Structured Lyrics with Audio Meta-Tags
            lyrics_file = temp_path / "2_LYRICS_WITH_AUDIO_TAGS.txt"
            with open(lyrics_file, "w", encoding="utf-8") as f:
                f.write(f"=== {title} ===\n\n")
                f.write(lyrics.strip())
                f.write("\n\n---\nCreated with SMG Suno AI Lyric Writer\n")

            # 3. MIDI Chord Progression (.mid for FL Studio, Ableton, Logic Pro)
            midi_file = temp_path / f"3_CHORDS_{chord_progression_name.split()[0]}.mid"
            bpm_val = 120
            try:
                bpm_val = int("".join(filter(str.isdigit, metadata.get("bpm", "120")[:4])))
            except Exception:
                pass
            MidiExporter.export_chord_progression(
                filepath=str(midi_file),
                progression_name=chord_progression_name,
                chords=chords if chords else ["C", "G", "Am", "F"],
                bpm=bpm_val
            )

            # 4. Printable HTML Lead Sheet
            lead_sheet_file = temp_path / "4_STUDIO_LEAD_SHEET.html"
            Exporter.export_html_lead_sheet(
                filepath=str(lead_sheet_file),
                title=title,
                lyrics=lyrics,
                metadata=metadata
            )

            # 5. Full Studio Metadata (JSON)
            json_file = temp_path / "5_PROJECT_METADATA.json"
            Exporter.export_json(
                filepath=str(json_file),
                title=title,
                lyrics=lyrics,
                metadata={
                    **metadata,
                    "suno_style_prompt": suno_style_prompt,
                    "negative_prompt": negative_prompt,
                    "chord_progression": chord_progression_name,
                    "chords": chords
                }
            )

            # 6. Vocal Topline Melody MIDI with embedded lyrics (0x05)
            vocal_midi_file = temp_path / "6_VOCAL_TOPLINE_GUIDE.mid"
            melody_events = []
            try:
                from app.vocal_melody_generator import VocalToplineGenerator
                melody_events = VocalToplineGenerator.generate_melody_events(lyrics, key="C", scale="Major", bpm=bpm_val)
                VocalToplineGenerator.export_midi(melody_events, str(vocal_midi_file), bpm=bpm_val, title=title)
            except Exception as e:
                print(f"Topline MIDI bundling error: {e}")

            # 7. Standard MusicXML Sheet Music
            sheet_music_file = temp_path / "7_SHEET_MUSIC.musicxml"
            try:
                from app.vocal_melody_generator import VocalToplineGenerator
                if melody_events:
                    VocalToplineGenerator.export_musicxml(melody_events, str(sheet_music_file), title=title, bpm=bpm_val)
            except Exception as e:
                print(f"MusicXML bundling error: {e}")

            # 8. High-Res Album Cover Artwork
            cover_art_file = temp_path / "8_ALBUM_COVER.png"
            try:
                from app.cover_art_generator import CoverArtGenerator
                cover_img = CoverArtGenerator.generate_cover_art(
                    title=title,
                    artist=metadata.get("artist", "SMG Suno AI"),
                    style_key="cyberpunk_neon",
                    aspect_ratio="1:1"
                )
                cover_img.save(str(cover_art_file))
            except Exception as e:
                print(f"Album cover bundling error: {e}")

            # Zip everything together
            with zipfile.ZipFile(output_zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                bundle_files = [
                    prompt_file, lyrics_file, midi_file, lead_sheet_file,
                    json_file, vocal_midi_file, sheet_music_file, cover_art_file
                ]
                for file in bundle_files:
                    if file.exists():
                        zipf.write(file, arcname=file.name)

        return output_zip_path
