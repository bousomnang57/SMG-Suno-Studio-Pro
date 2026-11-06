"""
Professional AI Scratch Vocalist & Vocal Cadence Engine.
Integrates neural Microsoft Edge TTS with offline Windows SAPI fallback.
Provides diverse Cambodian and international studio singers, pitch/speed tuning,
vocal style presets, and exportable scratch audio tracks.
"""

import os
import re
import asyncio
import tempfile
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from PyQt6.QtCore import QObject, pyqtSignal, QThread

# Pro Studio Vocal Roster
STUDIO_VOCALISTS: List[Dict[str, str]] = [
    # Cambodian Khmer Voices
    {
        "id": "km-KH-PisethNeural",
        "name": "🇰🇭 Piseth (Khmer Expressive Male)",
        "lang": "Khmer",
        "gender": "Male",
        "desc": "Rich, resonant Khmer male voice ideal for Sinn Sisamouth ballads & modern pop."
    },
    {
        "id": "km-KH-SreymomNeural",
        "name": "🇰🇭 Sreymom (Khmer Melodic Female)",
        "lang": "Khmer",
        "gender": "Female",
        "desc": "Clear, melodious Khmer female voice perfect for romantic acoustic & pop."
    },
    # Global Pop & R&B Voices
    {
        "id": "en-US-JennyNeural",
        "name": "🇺🇸 Jenny (Pop Lead Female)",
        "lang": "English",
        "gender": "Female",
        "desc": "Bright, modern Top-40 commercial pop vocal tone."
    },
    {
        "id": "en-US-GuyNeural",
        "name": "🇺🇸 Guy (Acoustic / Indie Male)",
        "lang": "English",
        "gender": "Male",
        "desc": "Warm, natural indie male vocal ideal for ballads and singer-songwriter."
    },
    {
        "id": "en-US-AriaNeural",
        "name": "🇺🇸 Aria (Dynamic Pop Female)",
        "lang": "English",
        "gender": "Female",
        "desc": "Punchy, expressive vocal delivery for upbeat synth-pop and rock."
    },
    {
        "id": "en-US-ChristopherNeural",
        "name": "🇺🇸 Christopher (R&B / Soul Male)",
        "lang": "English",
        "gender": "Male",
        "desc": "Deep, velvety baritone voice for soulful R&B and slow jams."
    },
    {
        "id": "en-GB-SoniaNeural",
        "name": "🇬🇧 Sonia (British Indie Female)",
        "lang": "English (UK)",
        "gender": "Female",
        "desc": "Crisp, elegant British tone with contemporary indie cadence."
    },
    {
        "id": "th-TH-PremwadeeNeural",
        "name": "🇹🇭 Premwadee (T-Pop Female)",
        "lang": "Thai",
        "gender": "Female",
        "desc": "Sweet, vibrant Asian pop timbre with emotional clarity."
    },
    {
        "id": "ja-JP-NanamiNeural",
        "name": "🇯🇵 Nanami (J-Pop / Anime Female)",
        "lang": "Japanese",
        "gender": "Female",
        "desc": "Youthful, energetic anime OST and J-Rock vocal style."
    },
    {
        "id": "ko-KR-SunHiNeural",
        "name": "🇰🇷 Sun-Hi (K-Pop Female)",
        "lang": "Korean",
        "gender": "Female",
        "desc": "Polished, dynamic vocal delivery for modern K-Pop."
    }
]

VOCAL_STYLES = {
    "singing_flow": {
        "name": "🎶 Melodic Singing Flow",
        "rate_offset": 0,
        "pitch_offset": 5,
        "desc": "Smooth legato pacing with slightly raised vocal brightness."
    },
    "ballad_slow": {
        "name": "🕯️ Slow Emotional Ballad",
        "rate_offset": -15,
        "pitch_offset": -5,
        "desc": "Intimate, drawn-out syllables for emotional heartbreak songs."
    },
    "pop_upbeat": {
        "name": "⚡ Upbeat Pop & Dance",
        "rate_offset": 12,
        "pitch_offset": 8,
        "desc": "Snappy rhythm and energetic forward cadence."
    },
    "rap_rhythmic": {
        "name": "🎤 Rhythmic Rap & Flow",
        "rate_offset": 28,
        "pitch_offset": 0,
        "desc": "Fast syllable delivery with sharp percussive consonants."
    }
}


def clean_lyrics_for_vocalist(lyrics_text: str) -> str:
    """
    Cleans lyric text for the scratch vocalist by stripping structural markers
    ([Verse 1], [Chorus], [Guitar Solo], (Whisper), chord brackets [Am], [C], etc.)
    while preserving the actual singing words and natural line cadence.
    """
    cleaned_lines = []
    for raw_line in lyrics_text.split("\n"):
        line = raw_line.strip()
        if not line:
            continue
        # Skip section headers like [Chorus], [Verse 2], [Intro], [Outro]
        if line.startswith("[") and line.endswith("]"):
            # Check if it's an embedded chord or a section header
            inner = line[1:-1].strip()
            # If it's a section header (contains Verse, Chorus, Bridge, Intro, Outro, Solo, Hook, etc.)
            if any(k in inner.lower() for k in ["verse", "chorus", "bridge", "intro", "outro", "solo", "hook", "pre-chorus", "drop"]):
                continue
        # Remove embedded chord tags like [Am], [F#m7], [C/G]
        line = re.sub(r"\[[A-G][#b]?(?:m|maj|min|dim|aug|sus[24]?|[0-9])*(?:/[A-G][#b]?)?\]", "", line)
        # Remove empty brackets or technical notes
        line = re.sub(r"\[.*?\]", "", line)
        line = line.strip()
        if line:
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


class ScratchVocalWorker(QThread):
    finished = pyqtSignal(str) # Path to audio file
    error = pyqtSignal(str)

    def __init__(
        self,
        lyrics: str,
        voice_id: str = "km-KH-PisethNeural",
        pitch_hz: int = 0,
        rate_percent: int = 0,
        vocal_style: str = "singing_flow"
    ):
        super().__init__()
        self.lyrics = lyrics
        self.voice_id = voice_id
        self.pitch_hz = pitch_hz
        self.rate_percent = rate_percent
        self.vocal_style = vocal_style

    def run(self):
        clean_text = clean_lyrics_for_vocalist(self.lyrics)
        if not clean_text.strip():
            self.error.emit("No lyrics to synthesize. Please write or generate lyrics first.")
            return

        # Apply vocal style adjustments
        style_info = VOCAL_STYLES.get(self.vocal_style, VOCAL_STYLES["singing_flow"])
        eff_pitch = self.pitch_hz + style_info["pitch_offset"]
        eff_rate = self.rate_percent + style_info["rate_offset"]

        pitch_str = f"{eff_pitch:+d}Hz" if eff_pitch != 0 else "+0Hz"
        rate_str = f"{eff_rate:+d}%" if eff_rate != 0 else "+0%"

        out_dir = Path(tempfile.gettempdir()) / "worldlyric_vocals"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f"scratch_vocal_{abs(hash(clean_text)) % 100000}.mp3"

        # Attempt neural synthesis with Edge TTS
        try:
            import edge_tts
            communicate = edge_tts.Communicate(
                text=clean_text,
                voice=self.voice_id,
                rate=rate_str,
                pitch=pitch_str
            )
            asyncio.run(communicate.save(str(out_file)))
            self.finished.emit(str(out_file))
            return
        except Exception as neural_err:
            print(f"Edge TTS synthesis error ({neural_err}), attempting offline SAPI fallback...")

        # Offline Fallback using Windows SAPI
        try:
            import win32com.client
            speaker = win32com.client.Dispatch("SAPI.SpVoice")
            wav_fallback = out_dir / f"scratch_vocal_sapi_{abs(hash(clean_text)) % 100000}.wav"
            stream = win32com.client.Dispatch("SAPI.SpFileStream")
            stream.Open(str(wav_fallback), 3) # SSFMCreateForWrite
            speaker.AudioOutputStream = stream
            # SAPI Rate: -10 to 10
            sapi_rate = max(-10, min(10, int(eff_rate / 10)))
            speaker.Rate = sapi_rate
            speaker.Speak(clean_text)
            stream.Close()
            self.finished.emit(str(wav_fallback))
        except Exception as sapi_err:
            self.error.emit(f"Vocal synthesis failed: {sapi_err}")

