# 🎵 SMG Suno Studio Pro — Professional Lyric & Music Creator DAW

A desktop songwriting, lyric engineering, and AI music production studio built with **Python 3.14**, **PyQt6**, and **Google Gemini AI** (`google-genai`). Designed as an end-to-end **5-stage professional music creator workstation** with native Khmer & Global songwriting support, persistent zero-duplicate batch generation, human-grade anti-cliché lyric polishing, real-time syllable & chord DAW editing, audio/MIDI synthesis, and full production bundle exporting for **Suno AI**, **Udio**, **FL Studio**, **Ableton Live**, and **MuseScore**.

---

## 🎛️ 5-Stage Professional Creator Workflow

Every stage shares live **Song Project State** (Title, Lyrics, Multi-Takes, Suno Style Prompt, BPM, Key, and Genre) and saves natively to **`.smgsong`** studio project files:

```
🗺️ Wizard (Ctrl+1) ──▶ 🎨 Visual Arranger (Ctrl+2) ──▶ ⚡ Batch Studio Pro (Ctrl+3) ──▶ ✍️ DAW Editor (Ctrl+4) ──▶ 🧬 Song DNA Cloner (Ctrl+5)
```

| Mode | Shortcut | Role in Music Production |
|---|---|---|
| **🗺️ Wizard Studio** | `Ctrl+1` | Step-by-step guided songwriting setup (Region, Genre, Formula Presets, Story Seed, Mic Scratchpad) |
| **🎨 Visual Arranger** | `Ctrl+2` | Visual Suno/Udio tag palette, Khmer Studio presets, mood matrix, live character-limited Formula Card |
| **⚡ Batch Studio Pro** | `Ctrl+3` | Multi-track album & catalog generator with **Zero-Duplicate Memory Vault**, **Human Story DNA** slot allocation, **Auto-Humanize**, **2-Step Suno Queue HUD**, and **Album ZIP Production Pack** |
| **✍️ 3-Pane DAW Editor** | `Ctrl+4` | Distraction-free lyric workbench with real-time syllable gutter, multi-take version manager, 3-tab Studio Deck (`Tags & Chords`, `Tempo & Audio`, `Studio Pro Tools`), chord auditioning, Khmer poetry meter, and AI line rewriting |
| **🧬 Song DNA Cloner** | `Ctrl+5` | Reverse-engineers reference song cadence, syllable contour, and structure to generate original semantic counterparts & 4-Flavor commercial arrangements |

---

## ✨ Studio Pro Capabilities

### 🧠 Zero-Duplicate & Authentic Human Lyric Engine
- **Persistent Zero-Repeat Vault** (`~/.lyric_ai_writer/batch_memory_vault.json`): Tracks the last 300 generated titles, hooks, themes, and story angles across sessions so new batches never repeat previous songs.
- **Chunked Micro-Batch Diversity**: Splits large runs into focused 5-track Gemini calls with elevated temperature and unique per-track **Human Story DNA** (POV, concrete micro-setting, physical object anchor, time-of-day, emotional arc, and hook architecture).
- **Strict AI-Cliché Blacklist + Auto-Humanize**: Blocks generic English & Khmer AI filler phrases, deduplicates BPM/Key combos and near-identical hooks, and runs real `HitAnalyzer` + `HumanizerEngine` + `AntiClicheEngine` scoring.

### 🎹 Musicology, Audio & DAW Production Tools
- **Native Studio Projects (`.smgsong`)**: Save (`Ctrl+S`) and reopen (`Ctrl+O`) complete multi-take songwriting sessions with Title, Lyrics, Takes, Suno Style Prompt, Negative Prompt, BPM, Key, Genre, and Chord Progression.
- **Polyphonic Audio Chord Synth & Soundboard**: Zero-latency acoustic piano/Rhodes synthesis with 22 global hit chord progressions, semitone transposer, and metronome/tap-tempo sync.
- **Vocal Auditioning & Sheet Music**: Scratch vocalist melody guide, microphone scratchpad recorder, Windows SAPI cadence audition, **Type 1 Vocal Topline MIDI (`.mid`)**, and **MusicXML (`.musicxml`)** export.
- **MasterWriter-Grade Sensory Thesaurus & Khmer Meter**: 300+ bilingual English/Khmer sensory words plus Khmer classical poetry meter (`កាព្យ`, `កាកគតិ`, `ពាក្យ ៧`) verification.
- **10+ Production Exports**: `.smgsong`, Suno/Udio Production Bundle `.zip`, Album Batch `.zip`, `.srt` video subtitles, `.lrc` synced karaoke, `.cho` ChordPro lead sheet, `.pdf`, `.html`, `.json`, `.mid`, `.musicxml`, and High-Res Album Cover `.png`.

### 🎨 Modern Studio UX & Platform
- **5 Adaptive Studio Themes**: Obsidian Dark, Cyber Blue, Emerald Studio, Sunset Amber, and Canvas Light (`Ctrl+T`) with full Khmer (`Khmer OS Battambang` / `Noto Sans Khmer`) & Latin typography.
- **Multi-Key Gemini API Pool**: Automatic rotation & retry across multiple Google AI Studio keys (`Settings [Ctrl+,]`).
- **Offline License Manager & In-App Auto-Updater**: Hardware-bound offline Pro activation and background GitHub Releases update detection.

---

## ⌨️ Essential Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+1` .. `Ctrl+5` | Switch between Wizard, Visual, Batch, Editor, and Clone studios |
| `Ctrl+S` / `Ctrl+Shift+S` | Save / Save As native Studio Project (`.smgsong`) |
| `Ctrl+O` | Open `.smgsong` project, `.json`, `.txt`, `.lrc`, or `.cho` |
| `Ctrl+N` | Start New Song (or New Batch Project when in Batch mode) |
| `Ctrl+E` | Open Save & Export Production Menu |
| `Ctrl+F` | Toggle Distraction-Free Lyric Focus Mode in Editor |
| `Ctrl+Shift+C` | Quick Copy formatted lyrics for Suno AI |
| `Ctrl+H` / `Ctrl+T` / `Ctrl+,` | Song History / Cycle Studio Theme / Settings & API Pool |
| `F11` | Toggle Fullscreen Studio Mode |

---

## 🏗️ 5-Layer Application Architecture

```
Lyric AI Writer/
├── main.py                          # High-DPI PyQt6 launcher, Khmer font loader & theme bootstrap
├── build_dist.bat                   # Automated PyInstaller + smoke-test + Inno Setup release builder
├── installer.iss                    # Inno Setup Windows installer script (.smgsong & Khmer fonts)
├── SMG_Suno_Studio_Pro.spec         # Portable PyInstaller bundle specification (DLLs, SSL, QtMultimedia)
├── requirements.txt                 # Python dependencies
├── assets/                          # Studio icons, logo, and bundled Khmer/UI fonts
└── app/
    ├── __init__.py                  # Core package metadata & version export
    │
    ├── # Layer 1: Core Platform & Project Lifecycle
    ├── config.py                    # Persistent studio settings, multi-key API pool & history
    ├── project_manager.py           # Native .smgsong studio project Save/Open + legacy loader
    ├── version_manager.py           # Multi-take lyric draft manager
    ├── license_manager.py           # Offline cryptographic Pro license verification
    ├── updater.py                   # Asynchronous GitHub Releases auto-updater
    │
    ├── # Layer 2: AI Composition & Lyric Intelligence
    ├── gemini_client.py             # Gemini SDK client, QThread workers & chunked Batch generator
    ├── anti_cliche_engine.py        # AI-slop blacklist, Human Story DNA slots & BatchMemoryVault
    ├── humanizer_engine.py          # Robotic-phrase polishing & authenticity scoring
    ├── clone_engine.py              # Song DNA analyzer, cadence matcher & 4-Flavor cloner
    ├── hit_analyzer.py              # Commercial hit score, hook density & repetition analytics
    │
    ├── # Layer 3: Musicology, Structure & Language Engines
    ├── music_data.py                # 8 World Regions, 40+ genres, 22 hit formulas & Suno tags
    ├── song_blueprints.py           # Structural song templates & section blueprints
    ├── syllable_meter.py            # Multilingual syllable counter (Latin, Khmer, Thai, CJK)
    ├── khmer_poetry_meter.py        # Classical Khmer prosody & rhyme validator
    ├── sensory_thesaurus.py         # Bilingual English/Khmer sensory imagery thesaurus
    ├── rhythm_engine.py             # Groove pockets, bar estimation & duration engine
    │
    ├── # Layer 4: Audio Synthesis, MIDI & Publishing
    ├── chord_engine.py              # Polyphonic chord audio synth, progressions & transposer
    ├── chord_soundboard.py          # Interactive harmonic soundboard engine
    ├── metronome.py                 # Real-time studio metronome & tap tempo
    ├── melody_recorder.py           # Microphone scratch melody recorder
    ├── tts_player.py                # Offline vocal cadence TTS audition player
    ├── scratch_vocalist.py          # Synthesized vocal melody guide engine
    ├── vocal_melody_generator.py    # Vocal topline MIDI & MusicXML sheet music generator
    ├── midi_exporter.py             # DAW-ready MIDI chord track exporter
    ├── cover_art_generator.py       # High-res programmatic album cover generator
    ├── exporter.py                  # SRT, LRC, Vocal Sheet, ChordPro, TXT, PDF, HTML & JSON
    ├── production_packager.py       # All-in-one Suno/Udio Production ZIP & Album ZIP packager
    │
    └── ui/                          # Layer 5: PyQt6 Studio Views, Panels & Dialogs
        ├── __init__.py
        ├── main_window.py           # Master studio orchestrator, project I/O & pipeline sync
        ├── styles.py                # 5 adaptive studio QSS themes & color tokens
        ├── wizard_view.py           # Mode 0: Guided Song Creation Wizard
        ├── visual_studio_view.py    # Mode 1: Suno Visual Arranger & Formula Card
        ├── batch_generator_view.py  # Mode 2: Batch Multi-Song Studio Pro & Suno Queue HUD
        ├── batch_song_dialog.py     # Full-track Batch Inspector & Quick Humanizer dialog
        ├── generator_panel.py       # Mode 3 Left: AI Composer & Formula Presets
        ├── editor_panel.py          # Mode 3 Center: DAW Lyric Editor, Syllable Gutter & Studio Deck
        ├── tools_panel.py           # Mode 3 Right: Rhymes, Suno Prompt, Chords, Sense & Vocal
        ├── lyric_highlighter.py     # Live syntax highlighter for [Section] & [Chord] tags
        ├── clone_dialog.py          # Mode 4: Song DNA & Semantic Meaning Cloner Workstation
        ├── hit_analyzer_dialog.py   # Commercial Hit Score & Song Diagnostics inspector
        ├── chord_soundboard_view.py # Interactive Chord Soundboard modal
        ├── melody_guide_dialog.py   # Vocal Topline MIDI & MusicXML Studio modal
        ├── scratch_vocalist_dialog.py # Scratch Vocalist Audition modal
        ├── khmer_poetry_dialog.py   # Khmer Poetry Meter Analyzer modal
        ├── cover_art_dialog.py      # Album Cover Artwork Studio modal
        ├── multi_key_dialog.py      # Multi-Key Gemini API Pool manager
        ├── settings_dialog.py       # Studio Preferences, Theme, Updater & License panel
        ├── activation_dialog.py     # Offline Pro License Activation modal
        └── update_dialog.py         # Live Release Notes & Update Installer modal
```

---

## 🚀 Quick Start & Building

### 1. Run from Source
```bash
pip install -r requirements.txt
python main.py
```

### 2. Configure Gemini API Key (Optional)
1. Click **⚙️ Settings** (`Ctrl+,`) in the top header bar.
2. Add one or more Google AI Studio API keys (supports automatic multi-key rotation).
3. Click **Test Connection** and **Save Settings**. *(Demo & offline songwriting tools also work without an API key.)*

### 3. Build Standalone Windows Executable & Installer
Build both the portable `.exe` (with automated frozen smoke-test) and the Windows Inno Setup installer (`dist_installer/SMG_Suno_Studio_Pro_v2.2.0_Setup.exe`):
```bash
build_dist.bat
```
Or run PyInstaller directly:
```bash
python -m PyInstaller --noconfirm --clean SMG_Suno_Studio_Pro.spec
```
