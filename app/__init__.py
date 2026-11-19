"""
SMG Suno AI Lyric Writer — Global Music Studio Core Package.

Layered architecture:
- Core Platform: config, project_manager, license_manager, updater, version_manager
- AI & Lyric Intelligence: gemini_client, anti_cliche_engine, humanizer_engine, clone_engine, hit_analyzer
- Musicology & Language: music_data, song_blueprints, syllable_meter, khmer_poetry_meter, sensory_thesaurus, rhythm_engine
- Audio & Synthesis: chord_engine, chord_soundboard, metronome, melody_recorder, tts_player, scratch_vocalist, vocal_melody_generator
- Publishing & Assets: exporter, midi_exporter, cover_art_generator, production_packager
"""

from app.config import APP_VERSION

__version__ = APP_VERSION
__all__ = ["__version__"]
