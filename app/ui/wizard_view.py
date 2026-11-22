"""
Easy Song Creation Wizard & Step-by-Step Production Roadmap (ទិសដៅនៃការធ្វើបទចម្រៀង).
Professional DAW-grade Songwriting Wizard guiding creators across 5 intuitive steps:
1. Vibe & Concept (8 Studio Genres, Story Seeds & Language)
2. Harmony & Rhythm (Rhythm Groove Engine, Chords & Vocal Persona)
3. AI Lyrics Studio (Gemini AI, Hit Potential Scorer & Humanizer)
4. Vocal Booth & Prompter (Live Teleprompter, Metronome, Groove & Mic Scratchpad)
5. Master Production Hub (Suno 1-Click Copy & Multi-Format Exporters)
"""

import re
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QFrame, QGridLayout,
    QStackedWidget, QSlider, QComboBox, QMessageBox, QGroupBox,
    QApplication, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

from app.chord_engine import AudioChordSynthesizer, CHORD_PROGRESSIONS, VOCAL_RANGES
from app.rhythm_engine import RhythmEngine
from app.hit_analyzer import HitAnalyzer
from app.ui.hit_analyzer_dialog import HitAnalyzerDialog
from app.exporter import Exporter
from app.humanizer_engine import HumanizerEngine


class SongCreationWizardView(QWidget):
    generate_requested = pyqtSignal(dict)
    open_editor_requested = pyqtSignal()
    open_batch_requested = pyqtSignal(dict)
    export_bundle_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_dark = False
        self.current_step = 0

        # State stored across steps (Default: Clean English Radio Pop Workflow)
        self.state_genre = "Global Radio Pop"
        self.state_language = "English"
        self.state_mood = "Uplifting & Inspiring"
        self.state_theme = "Late night drive through neon city lights, chasing second chances"
        self.state_bpm = 120
        self.state_vocal = "Tenor / Modern Pop Vocal"
        self.state_chords = "Billboard Pop Standard (I - V - vi - IV)"
        self.state_structure = "Commercial Radio Hit (Intro-V1-Pre-Chorus-V2-Chorus-Bridge-Chorus)"
        self.state_rhyme = "AABB (Classic Couplets)"
        self.current_title = "Midnight Neon Lights"
        self.current_lyrics = ""

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 14, 18, 14)
        main_layout.setSpacing(12)

        # Title & Subtitle Header
        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        self.main_title = QLabel("🗺️ Easy Songwriting Roadmap")
        self.main_title.setStyleSheet("font-size: 20px; font-weight: 800; color: #1e293b;")
        title_box.addWidget(self.main_title)

        self.sub_title = QLabel("Create radio-ready songs in 5 guided steps — from initial concept and chords to Suno AI & DAW export")
        self.sub_title.setStyleSheet("font-size: 11.5px; color: #64748b;")
        title_box.addWidget(self.sub_title)

        main_layout.addLayout(title_box)

        # 5-Step Visual Stepper Bar (Clickable Pills)
        self.stepper_frame = self._create_stepper_bar()
        main_layout.addWidget(self.stepper_frame)

        # Main Wizard Stack (5 Steps)
        self.step_stack = QStackedWidget()
        self.step_stack.addWidget(self._create_step1_concept())
        self.step_stack.addWidget(self._create_step2_harmony())
        self.step_stack.addWidget(self._create_step3_lyrics())
        self.step_stack.addWidget(self._create_step4_audition())
        self.step_stack.addWidget(self._create_step5_export())
        main_layout.addWidget(self.step_stack, stretch=1)

        # Bottom Navigation Controls
        self.nav_frame = QFrame()
        self.nav_frame.setStyleSheet("border-top: 1px solid #e2e8f0; padding-top: 8px;")
        nav_layout = QHBoxLayout(self.nav_frame)
        nav_layout.setContentsMargins(0, 8, 0, 0)

        self.btn_prev = QPushButton("⬅ Back")
        self.btn_prev.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_prev.setStyleSheet("background-color: #f1f5f9; color: #475569; font-weight: 600; padding: 8px 16px; border-radius: 6px;")
        self.btn_prev.setEnabled(False)
        self.btn_prev.clicked.connect(self._go_prev)
        nav_layout.addWidget(self.btn_prev)

        nav_layout.addStretch()

        self.lbl_step_indicator = QLabel("Step 1 of 5 : Select Sonic Vibe & Story Concept")
        self.lbl_step_indicator.setStyleSheet("color: #64748b; font-weight: 600; font-size: 12px;")
        nav_layout.addWidget(self.lbl_step_indicator)

        nav_layout.addStretch()

        self.btn_next = QPushButton("Next Step ➔")
        self.btn_next.setObjectName("primaryGenerateButton")
        self.btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_next.setStyleSheet("background: #2563eb; color: #ffffff; font-weight: 700; padding: 8px 20px; border-radius: 6px;")
        self.btn_next.clicked.connect(self._go_next)
        nav_layout.addWidget(self.btn_next)

        main_layout.addWidget(self.nav_frame)

    # --- Stepper Bar Component ---
    def _create_stepper_bar(self) -> QFrame:
        self.stepper_frame = QFrame()
        self.stepper_frame.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 4px;")
        layout = QHBoxLayout(self.stepper_frame)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(6)

        self.step_buttons = []
        steps = [
            "① Concept && Vibe",
            "② Tempo && Chords",
            "③ AI Lyrics Studio",
            "④ Vocal Booth",
            "⑤ Suno && Export"
        ]
        for i, text in enumerate(steps):
            btn = QPushButton(text)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, idx=i: self._jump_to_step(idx))
            btn.setStyleSheet(self._get_step_style(i == 0))
            layout.addWidget(btn, stretch=1)
            self.step_buttons.append(btn)
            if i < len(steps) - 1:
                arrow = QLabel("➔")
                arrow.setStyleSheet("color: #94a3b8; font-weight: 700; font-size: 11px;")
                layout.addWidget(arrow)

        return self.stepper_frame

    def _get_step_style(self, active: bool) -> str:
        from app.ui.styles import get_theme
        t = get_theme(getattr(self, "current_theme", "obsidian"))
        if active:
            return f"background: {t['accent_gradient']}; color: #ffffff; font-weight: 800; font-size: 11px; padding: 6px 10px; border-radius: 6px; border: 1px solid {t['border_accent']};"
        if t["is_dark"]:
            return f"background-color: {t['bg_card']}; color: {t['text_secondary']}; font-weight: 700; font-size: 11px; padding: 6px 10px; border: 1px solid {t['border']}; border-radius: 6px;"
        return "background-color: #ffffff; color: #1e293b; font-weight: 700; font-size: 11px; padding: 6px 10px; border: 1px solid #cbd5e1; border-radius: 6px;"

    def _update_stepper(self):
        for i, btn in enumerate(self.step_buttons):
            btn.setStyleSheet(self._get_step_style(i == self.current_step))

        step_names = [
            "Select Sonic Vibe & Story Concept",
            "Set Tempo (BPM), Drum Groove & Chord Progression",
            "Generate & Refine Lyrics with Gemini AI",
            "Singer Teleprompter & Vocal Scratchpad",
            "Suno AI Station & Multi-Format Export"
        ]
        self.lbl_step_indicator.setText(f"Step {self.current_step + 1} of 5 : {step_names[self.current_step]}")
        self.btn_prev.setEnabled(self.current_step > 0)
        if self.current_step == 4:
            self.btn_next.setText("✍️ Open Full Lyric Editor ➔")
        else:
            self.btn_next.setText("Next Step ➔")

    def _jump_to_step(self, step_idx: int):
        self.current_step = step_idx
        self.step_stack.setCurrentIndex(step_idx)
        self._update_stepper()
        if step_idx == 2:
            self._refresh_step3_summary()
        elif step_idx == 3:
            # Sync teleprompter when opening step 4
            self._sync_teleprompter()
        elif step_idx == 4:
            # Sync export summaries when opening step 5
            self._sync_export_step()

    # --- Step 1: Concept, Genre & Mood ---
    def _create_step1_concept(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        self.step1_header = QLabel("Step 1 : Choose Your Musical Style & Song Concept")
        self.step1_header.setStyleSheet("font-size: 15px; font-weight: 700; color: #1e293b;")
        layout.addWidget(self.step1_header)

        # 8 Rich Genre Cards Grid (4x2) — Clean English-First Order
        grid_genres = QGridLayout()
        grid_genres.setSpacing(8)

        genres = [
            ("🌟 Global Radio Pop", "Catchy international earworm Billboard radio pop", "Global Radio Pop"),
            ("🌃 80s Synthwave && Retro", "Analog Moog bass, LinnDrum, retro neon synth-pop", "Synthwave Pop"),
            ("🎸 Acoustic Folk && Indie", "Warm fingerpicked acoustic guitar & intimate vocal", "Acoustic Indie"),
            ("⚡ EDM && Club Festival", "Mainstage festival drop with euphoric synths", "EDM Dance"),
            ("🔥 Modern Hip-Hop && Trap", "Melodic 808 sub-bass bounce with crisp trap hi-hats", "Modern Trap"),
            ("🎷 Late-Night R&&B Soul", "Lush Rhodes chords, neo-soul groove & silky vocals", "Modern R&B"),
            ("💖 Golden Vintage Ballad", "60s/70s nostalgic orchestral ballad (World / Khmer Classic)", "Khmer pop ballad"),
            ("💃 Festive World Folk Dance", "Upbeat celebratory acoustic rhythm (Romvong / World Folk)", "Khmer Romvong")
        ]

        self.genre_buttons = []
        for i, (title, desc, key) in enumerate(genres):
            card = QPushButton(f"{title}\n{desc}")
            card.setCursor(Qt.CursorShape.PointingHandCursor)
            card.setCheckable(True)
            if i == 0:
                card.setChecked(True)
            card.setStyleSheet("""
                QPushButton {
                    background-color: #ffffff;
                    border: 1px solid #cbd5e1;
                    border-radius: 8px;
                    padding: 9px 12px;
                    text-align: left;
                    font-size: 11.5px;
                    color: #1e293b;
                }
                QPushButton:hover {
                    border-color: #6366f1;
                    background-color: #eff6ff;
                }
                QPushButton:checked {
                    border: 2px solid #2563eb;
                    background-color: #eff6ff;
                    font-weight: 700;
                    color: #1d4ed8;
                }
            """)
            card.clicked.connect(lambda _, k=key, b=card: self._select_genre_card(k, b))
            grid_genres.addWidget(card, i // 2, i % 2)
            self.genre_buttons.append(card)

        layout.addLayout(grid_genres)

        # Story Seed Quick Inspiration Pills
        self.lbl_story_seeds = QLabel("💡 Quick Story Seeds (Click to auto-fill concept):")
        self.lbl_story_seeds.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748b;")
        layout.addWidget(self.lbl_story_seeds)

        seeds_row = QHBoxLayout()
        seeds_row.setSpacing(6)
        story_presets = [
            ("🌃 Midnight Drive", "Late night drive through neon city lights, chasing second chances"),
            ("💔 Heartbreak", "Bittersweet heartbreak after a summer romance fades away"),
            ("☕ Rainy Cafe", "Sitting in a rainy coffee shop remembering our first conversation"),
            ("🚀 Chasing Dreams", "Rising from nothing and overcoming every doubt to reach the stage"),
            ("🌊 Coastal Memories", "Walking along the ocean shore where we promised never to part"),
            ("🎉 Electric Night", "Dancing under festival lights like tomorrow never comes")
        ]
        self.seed_buttons = []
        for label, val in story_presets:
            btn = QPushButton(label)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("background: #f1f5f9; color: #334155; border: 1px solid #cbd5e1; padding: 4px 8px; border-radius: 5px; font-size: 10.5px; font-weight: 600;")
            btn.clicked.connect(lambda _, v=val: self.input_theme.setText(v))
            seeds_row.addWidget(btn)
            self.seed_buttons.append(btn)
        layout.addLayout(seeds_row)

        # Mood, Theme & Language Row
        input_row = QHBoxLayout()
        input_row.setSpacing(8)

        self.input_theme = QLineEdit("Late night drive through neon city lights, chasing second chances")
        self.input_theme.setPlaceholderText("Enter song topic, story concept, or emotional hook...")
        self.input_theme.setStyleSheet("padding: 7px 10px; font-size: 12px; border: 1px solid #cbd5e1; border-radius: 6px;")
        input_row.addWidget(self.input_theme, stretch=2)

        self.combo_mood = QComboBox()
        self.combo_mood.addItems([
            "Uplifting & Inspiring",
            "Heartfelt & Nostalgic",
            "Romantic & Intimate",
            "Energetic & Euphoric",
            "Sad & Melancholic",
            "Dark & Cinematic"
        ])
        self.combo_mood.setStyleSheet("padding: 6px; font-size: 11.5px; border: 1px solid #cbd5e1; border-radius: 6px;")
        input_row.addWidget(self.combo_mood, stretch=1)

        # Language Selector (Default: English)
        self.combo_lang = QComboBox()
        self.combo_lang.addItems([
            "🇬🇧 English",
            "🇰🇭 Khmer (ភាសាខ្មែរ)",
            "🌟 Bilingual (50/50 Dual Engine)"
        ])
        self.combo_lang.setStyleSheet("padding: 6px; font-size: 11.5px; border: 1px solid #cbd5e1; border-radius: 6px;")
        self.combo_lang.currentTextChanged.connect(self._on_language_changed)
        input_row.addWidget(self.combo_lang, stretch=1)

        layout.addLayout(input_row)

        # Human Story DNA & Vocal Persona Row
        dna_row = QHBoxLayout()
        dna_row.setSpacing(8)

        self.lbl_w_vocal_tag = QLabel("🎤 Vocal:")
        self.lbl_w_vocal_tag.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748b;")
        dna_row.addWidget(self.lbl_w_vocal_tag)

        self.combo_w_vocal = QComboBox()
        self.combo_w_vocal.addItems([
            "Auto Vocal",
            "Male Lead Vocal",
            "Female Lead Vocal",
            "Duet (Male + Female)",
            "Soft Intimate Whisper",
            "Raspy Soulful Belt",
        ])
        self.combo_w_vocal.setStyleSheet("padding: 5px 6px; font-size: 11px; border: 1px solid #cbd5e1; border-radius: 6px;")
        dna_row.addWidget(self.combo_w_vocal, stretch=1)

        self.lbl_w_pov_tag = QLabel("👁️ POV:")
        self.lbl_w_pov_tag.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748b;")
        dna_row.addWidget(self.lbl_w_pov_tag)

        self.combo_w_pov = QComboBox()
        self.combo_w_pov.addItems([
            "1st Person (I / Me)",
            "2nd Person (You / Direct)",
            "Storyteller (3rd Person)",
            "Dialogue / Call & Response",
        ])
        self.combo_w_pov.setStyleSheet("padding: 5px 6px; font-size: 11px; border: 1px solid #cbd5e1; border-radius: 6px;")
        dna_row.addWidget(self.combo_w_pov, stretch=1)

        self.btn_w_human_mode = QPushButton("👤 Anti-Cliché Human: ON")
        self.btn_w_human_mode.setCheckable(True)
        self.btn_w_human_mode.setChecked(True)
        self.btn_w_human_mode.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_w_human_mode.setToolTip("Enforce concrete sensory details and ban repetitive AI lyric clichés")
        self.btn_w_human_mode.toggled.connect(self._on_human_mode_toggled)
        self.btn_w_human_mode.setStyleSheet("background: #065f46; color: #ecfdf5; border: 1px solid #10b981; border-radius: 6px; padding: 5px 10px; font-size: 11px; font-weight: 700;")
        dna_row.addWidget(self.btn_w_human_mode)

        self.btn_w_surprise = QPushButton("🎲 Surprise Concept")
        self.btn_w_surprise.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_w_surprise.setToolTip("Roll a brand-new, non-repeating human story concept & mood")
        self.btn_w_surprise.clicked.connect(self._roll_surprise_concept)
        self.btn_w_surprise.setStyleSheet("background: #f5f3ff; color: #7c3aed; border: 1px solid #c4b5fd; border-radius: 6px; padding: 5px 10px; font-size: 11px; font-weight: 700;")
        dna_row.addWidget(self.btn_w_surprise)

        layout.addLayout(dna_row)

        # English Title & Chorus Hook Starter Bar (Clean 1-row songwriting accelerator)
        hook_row = QHBoxLayout()
        hook_row.setSpacing(8)

        self.lbl_w_title_tag = QLabel("🎯 Song Title:")
        self.lbl_w_title_tag.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748b;")
        hook_row.addWidget(self.lbl_w_title_tag)

        self.input_song_title = QLineEdit(self.current_title)
        self.input_song_title.setPlaceholderText("Enter English song title (e.g. Midnight Neon Lights)...")
        self.input_song_title.setStyleSheet("padding: 5px 8px; font-size: 11.5px; font-weight: 700; border: 1px solid #cbd5e1; border-radius: 6px;")
        self.input_song_title.textChanged.connect(self._on_title_input_changed)
        hook_row.addWidget(self.input_song_title, stretch=2)

        self.lbl_w_hook_tag = QLabel("🎤 Hook Style:")
        self.lbl_w_hook_tag.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748b;")
        hook_row.addWidget(self.lbl_w_hook_tag)

        self.combo_w_hook_style = QComboBox()
        self.combo_w_hook_style.addItems([
            "Anthemic Earworm Chorus",
            "Confessional Diary Hook",
            "Melodic Call & Response",
            "Dark Atmospheric Hook",
            "Acoustic Heartfelt Refrain",
        ])
        self.combo_w_hook_style.setStyleSheet("padding: 5px 6px; font-size: 11px; border: 1px solid #cbd5e1; border-radius: 6px;")
        hook_row.addWidget(self.combo_w_hook_style, stretch=1)

        self.btn_w_roll_hook = QPushButton("✨ Roll English Title && Hook")
        self.btn_w_roll_hook.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_w_roll_hook.setToolTip("Generate a catchy English song title and chorus hook idea matching your style")
        self.btn_w_roll_hook.clicked.connect(self._roll_english_title_and_hook)
        self.btn_w_roll_hook.setStyleSheet("background: #eff6ff; color: #1d4ed8; border: 1px solid #93c5fd; border-radius: 6px; padding: 5px 10px; font-size: 11px; font-weight: 700;")
        hook_row.addWidget(self.btn_w_roll_hook)

        layout.addLayout(hook_row)
        layout.addStretch()
        return widget

    def _on_title_input_changed(self, text: str):
        if text.strip():
            self.current_title = text.strip()

    def _roll_english_title_and_hook(self):
        import random
        hooks_pool = [
            ("Midnight Neon Lights", "Late night drive through neon city lights — 'We are burning brighter than the dashboard glow'"),
            ("Echoes in the Rearview", "Leaving old heartbreak behind on an open highway — 'Every mile between us turns the static into gold'"),
            ("Paper Crown in the Rain", "Rising from self-doubt under city streetlights — 'They can wash the sidewalk, never wash away our name'"),
            ("Two Cups of Cold Coffee", "Bittersweet morning-after reflection — 'Your jacket on the chair still remembers who we were'"),
            ("Electric Heartbeat at 2 AM", "Euphoric dancefloor connection — 'Hold the rhythm steady till the skyline starts to break'"),
            ("Wildflowers on Concrete", "Unstoppable ambition and hope — 'Growing through the cracks where nobody thought we'd bloom'"),
            ("Static on Channel Nine", "Nostalgic 80s synthwave romance — 'Rewind the cassette tape to the summer we were fearless'"),
            ("Last Train to Nowhere", "Acoustic indie storytelling — 'Ticket in my pocket and a suitcase full of songs'"),
        ]
        title, concept = random.choice(hooks_pool)
        self.current_title = title
        if hasattr(self, "input_song_title"):
            self.input_song_title.setText(title)
        if hasattr(self, "input_theme"):
            self.input_theme.setText(concept)
        if hasattr(self, "btn_w_roll_hook"):
            self.btn_w_roll_hook.setText("✓ New Title & Hook Set!")
            QTimer.singleShot(1400, lambda: self.btn_w_roll_hook.setText("✨ Roll English Title && Hook") if hasattr(self, "btn_w_roll_hook") else None)

    def _on_human_mode_toggled(self, checked: bool):
        if checked:
            self.btn_w_human_mode.setText("👤 Anti-Cliché Human: ON")
            self.btn_w_human_mode.setStyleSheet("background: #065f46; color: #ecfdf5; border: 1px solid #10b981; border-radius: 6px; padding: 5px 10px; font-size: 11px; font-weight: 700;")
        else:
            self.btn_w_human_mode.setText("👤 Anti-Cliché Human: OFF")
            self.btn_w_human_mode.setStyleSheet("background: #334155; color: #cbd5e1; border: 1px solid #475569; border-radius: 6px; padding: 5px 10px; font-size: 11px; font-weight: 700;")

    def _roll_surprise_concept(self):
        from app.anti_cliche_engine import AntiClicheEngine
        import random
        lang = "Khmer" if ("Khmer" in self.state_language or "ខ្មែរ" in self.state_language) else ("Both" if "Both" in self.state_language else "English")
        concept = AntiClicheEngine.roll_fresh_concept(lang)
        fresh_text = f"{concept.get('theme', '')} — {concept.get('seed', '')}".strip(" —")
        if fresh_text:
            self.input_theme.setText(fresh_text)
        if self.combo_mood.count() > 0:
            self.combo_mood.setCurrentIndex(random.randrange(self.combo_mood.count()))
        if self.combo_w_pov.count() > 0:
            self.combo_w_pov.setCurrentIndex(random.randrange(self.combo_w_pov.count()))
        self.btn_w_surprise.setText("✨ Fresh Idea Rolled!")
        QTimer.singleShot(1400, lambda: self.btn_w_surprise.setText("🎲 Surprise Concept") if hasattr(self, "btn_w_surprise") else None)

    def _select_genre_card(self, genre_key: str, active_btn: QPushButton):
        self.state_genre = genre_key
        for btn in self.genre_buttons:
            btn.setChecked(btn == active_btn)

    def _on_language_changed(self, lang_text: str):
        if "ខ្មែរ" in lang_text:
            self.state_language = "Khmer (ភាសាខ្មែរ)"
        elif "English" in lang_text:
            self.state_language = "English"
        else:
            self.state_language = "Both (Khmer + English 50/50 Dual)"

    # --- Step 2: Harmony, BPM & Rhythm Groove ---
    def _create_step2_harmony(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        self.step2_header = QLabel("Step 2 : Set Tempo (BPM), Rhythm Groove & Chord Progression")
        self.step2_header.setStyleSheet("font-size: 15px; font-weight: 700; color: #1e293b;")
        layout.addWidget(self.step2_header)

        # 1. BPM & Rhythm Groove Engine Box
        self.bpm_box = QGroupBox("1. Tempo (BPM) && Live Drum Groove")
        b_layout = QVBoxLayout(self.bpm_box)
        b_layout.setSpacing(6)

        bpm_header_row = QHBoxLayout()
        self.lbl_bpm_display = QLabel("Current Tempo: 120 BPM (Modern Pop / Dance Groove)")
        self.lbl_bpm_display.setStyleSheet("font-weight: 700; color: #2563eb; font-size: 12.5px;")
        bpm_header_row.addWidget(self.lbl_bpm_display)
        bpm_header_row.addStretch()

        # Rhythm Groove Selector inside Step 2
        lbl_grv = QLabel("🥁 Rhythm Groove:")
        lbl_grv.setStyleSheet("font-weight: 700; font-size: 11px; color: #64748b;")
        bpm_header_row.addWidget(lbl_grv)

        self.combo_w_groove = QComboBox()
        self.combo_w_groove.addItems(RhythmEngine.get_available_grooves())
        self.combo_w_groove.setStyleSheet("padding: 4px 8px; font-size: 11px; font-weight: 600; min-width: 170px;")
        if self.combo_w_groove.count() > 0:
            pop_idx = next((i for i in range(self.combo_w_groove.count()) if "Pop" in self.combo_w_groove.itemText(i) or "120" in self.combo_w_groove.itemText(i)), 0)
            self.combo_w_groove.setCurrentIndex(pop_idx)
        self.combo_w_groove.currentTextChanged.connect(self._on_wizard_groove_changed)
        bpm_header_row.addWidget(self.combo_w_groove)

        self.btn_w_play_groove = QPushButton("▶ Audition Groove")
        self.btn_w_play_groove.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_w_play_groove.setStyleSheet("background: #064e3b; color: #34d399; font-weight: 700; font-size: 10.5px; padding: 4px 10px; border-radius: 4px;")
        self.btn_w_play_groove.clicked.connect(self._toggle_wizard_groove)
        bpm_header_row.addWidget(self.btn_w_play_groove)

        self.btn_w_stop_groove = QPushButton("⏹ Stop")
        self.btn_w_stop_groove.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_w_stop_groove.setStyleSheet("background: #1e2540; color: #cbd5e1; font-weight: 600; font-size: 10.5px; padding: 4px 8px; border-radius: 4px;")
        self.btn_w_stop_groove.clicked.connect(self._stop_wizard_groove)
        bpm_header_row.addWidget(self.btn_w_stop_groove)

        b_layout.addLayout(bpm_header_row)

        # Preset BPM pills
        preset_row = QHBoxLayout()
        self.bpm_preset_btns = []
        presets = [("🐢 Ballad (74 BPM)", 74), ("🚶 Mid-Tempo (96 BPM)", 96), ("🏃 Dance Pop (120 BPM)", 120), ("⚡ Trap / EDM (140 BPM)", 140)]
        for text, val in presets:
            btn = QPushButton(text)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("background: #f1f5f9; border: 1px solid #cbd5e1; padding: 5px 8px; border-radius: 5px; font-size: 11px;")
            btn.clicked.connect(lambda _, v=val: self._set_bpm_val(v))
            preset_row.addWidget(btn)
            self.bpm_preset_btns.append(btn)
        b_layout.addLayout(preset_row)

        self.bpm_slider = QSlider(Qt.Orientation.Horizontal)
        self.bpm_slider.setRange(50, 180)
        self.bpm_slider.setValue(120)
        self.bpm_slider.valueChanged.connect(self._set_bpm_val)
        b_layout.addWidget(self.bpm_slider)
        layout.addWidget(self.bpm_box)

        # 2. Singer Vocal Range & Key
        self.vocal_box = QGroupBox("2. Vocal Range && Key Matching")
        v_layout = QVBoxLayout(self.vocal_box)
        v_layout.setSpacing(5)

        self.combo_vocal = QComboBox()
        self.combo_vocal.addItems(list(VOCAL_RANGES.keys()))
        self.combo_vocal.setCurrentIndex(0)
        self.combo_vocal.setStyleSheet("padding: 6px; font-size: 11.5px; border: 1px solid #cbd5e1; border-radius: 6px;")
        v_layout.addWidget(self.combo_vocal)

        self.lbl_vocal_info = QLabel("Recommended Keys: C Major, G Major, A Minor, F Major (Radio Pop Standard)")
        self.lbl_vocal_info.setStyleSheet("color: #64748b; font-size: 11px;")
        v_layout.addWidget(self.lbl_vocal_info)
        layout.addWidget(self.vocal_box)

        # 3. Chord Progression & Audio Synth
        self.prog_box = QGroupBox("3. Chord Progression && Interactive Audio Synth")
        p_layout = QVBoxLayout(self.prog_box)
        p_layout.setSpacing(6)

        self.combo_chords = QComboBox()
        self.combo_chords.addItems(list(CHORD_PROGRESSIONS.keys()))
        self.combo_chords.setCurrentIndex(0)
        self.combo_chords.setStyleSheet("padding: 6px; font-size: 11.5px; border: 1px solid #cbd5e1; border-radius: 6px;")
        self.combo_chords.currentTextChanged.connect(self._on_chord_selected)
        p_layout.addWidget(self.combo_chords)

        self.lbl_chord_preview = QLabel("Chords: [C] - [G] - [Am] - [F] (Uplifting Pop Anthem)")
        self.lbl_chord_preview.setStyleSheet("font-weight: 700; color: #2563eb; background: #eff6ff; padding: 6px 10px; border-radius: 6px;")
        p_layout.addWidget(self.lbl_chord_preview)

        # Synth audition row
        synth_row = QHBoxLayout()
        self.btn_w_play_chords = QPushButton("🔊 Audition Chords (Audio Synth)")
        self.btn_w_play_chords.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_w_play_chords.setStyleSheet("background-color: #f5f3ff; color: #7c3aed; font-weight: 700; border: 1px solid #ddd6fe; border-radius: 6px; padding: 6px 12px;")
        self.btn_w_play_chords.clicked.connect(self._play_wizard_chords)

        self.btn_w_stop_chords = QPushButton("⏹ Stop Chords")
        self.btn_w_stop_chords.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_w_stop_chords.setStyleSheet("background-color: #f1f5f9; color: #475569; font-weight: 600; border: 1px solid #cbd5e1; border-radius: 6px; padding: 6px 10px;")
        self.btn_w_stop_chords.clicked.connect(self._stop_wizard_chords)

        synth_row.addWidget(self.btn_w_play_chords)
        synth_row.addWidget(self.btn_w_stop_chords)
        synth_row.addStretch()
        p_layout.addLayout(synth_row)

        layout.addWidget(self.prog_box)
        layout.addStretch()
        return widget

    def _on_wizard_groove_changed(self, groove_name: str):
        bpm = RhythmEngine.get_groove_default_bpm(groove_name)
        if bpm:
            self._set_bpm_val(bpm)

    def _toggle_wizard_groove(self):
        grv = self.combo_w_groove.currentText()
        bpm = self.state_bpm
        RhythmEngine.play_groove(grv, bpm)
        self.btn_w_play_groove.setText("▶ Playing...")
        self.btn_w_play_groove.setStyleSheet("background: #047857; color: #ffffff; font-weight: 700; font-size: 10.5px; padding: 4px 10px; border-radius: 4px;")

    def _stop_wizard_groove(self):
        RhythmEngine.stop_groove()
        self.btn_w_play_groove.setText("▶ Audition Groove")
        if self.is_dark:
            self.btn_w_play_groove.setStyleSheet("background: #064e3b; color: #34d399; font-weight: 700; font-size: 10.5px; padding: 4px 10px; border-radius: 4px;")
        else:
            self.btn_w_play_groove.setStyleSheet("background: #ecfdf5; color: #059669; border: 1px solid #a7f3d0; font-weight: 700; font-size: 10.5px; padding: 4px 10px; border-radius: 4px;")

    def _play_wizard_chords(self):
        info = CHORD_PROGRESSIONS.get(self.state_chords)
        if info:
            chords = info.get("chords_in_c", ["Am", "Dm", "E7", "Am"])
            AudioChordSynthesizer.play_progression(chords, bpm=self.state_bpm)

    def _stop_wizard_chords(self):
        AudioChordSynthesizer.stop()

    def _set_bpm_val(self, val: int):
        self.state_bpm = val
        self.bpm_slider.setValue(val)
        self.lbl_bpm_display.setText(f"Current Tempo: {val} BPM")

    def _on_chord_selected(self, name: str):
        self.state_chords = name
        info = CHORD_PROGRESSIONS.get(name)
        if info:
            chords_str = " - ".join(f"[{c}]" for c in info.get("chords_in_c", []))
            self.lbl_chord_preview.setText(f"Chords: {chords_str} ({info.get('mood')})")

    # --- Step 3: AI Lyric Generation & Studio Inspector ---
    def _create_step3_lyrics(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        self.step3_header = QLabel("Step 3 : AI Lyrics Studio — Generate & Refine with Gemini")
        self.step3_header.setStyleSheet("font-size: 15px; font-weight: 700; color: #1e293b;")
        layout.addWidget(self.step3_header)

        # Split: Left Controls / Right Lyrics Editor
        split_row = QHBoxLayout()
        split_row.setSpacing(12)

        # Left Column: Structure, Tone & Generation Controls (~365px)
        left_col = QFrame()
        left_col.setFixedWidth(365)
        l_layout = QVBoxLayout(left_col)
        l_layout.setContentsMargins(0, 0, 0, 0)
        l_layout.setSpacing(8)

        # Summary Badge Capsule
        self.action_card = QFrame()
        self.action_card.setStyleSheet("background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 10px;")
        a_layout = QVBoxLayout(self.action_card)
        a_layout.setSpacing(6)

        self.lbl_gen_summary = QLabel("Song Setup: Global Radio Pop • 120 BPM • C-G-Am-F")
        self.lbl_gen_summary.setStyleSheet("font-weight: 700; color: #1d4ed8; font-size: 11px;")
        self.lbl_gen_summary.setWordWrap(True)
        a_layout.addWidget(self.lbl_gen_summary)

        # Structure Blueprint Selector
        lbl_st = QLabel("Song Structure Blueprint:")
        lbl_st.setStyleSheet("font-size: 10.5px; font-weight: 700; color: #64748b;")
        a_layout.addWidget(lbl_st)

        self.combo_w_structure = QComboBox()
        self.combo_w_structure.addItems([
            "Commercial Radio Hit (Intro-V1-Pre-Chorus-V2-Chorus-Bridge-Chorus)",
            "Suno Fast Hook (<2 Minutes High Impact)",
            "Emotive Duet / Male-Female Dialogue",
            "Golden Vintage Classic (Intro-V1-V2-Chorus-Solo-V3-Outro)"
        ])
        self.combo_w_structure.setStyleSheet("padding: 4px; font-size: 11px;")
        a_layout.addWidget(self.combo_w_structure)

        # Big Trigger Button
        self.btn_wizard_generate = QPushButton("⚡ Generate Full Lyrics")
        self.btn_wizard_generate.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_wizard_generate.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563eb, stop:1 #4f46e5);
                color: #ffffff;
                font-weight: 800;
                font-size: 12.5px;
                padding: 10px;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #1d4ed8;
            }
        """)
        self.btn_wizard_generate.clicked.connect(self._trigger_generate)
        a_layout.addWidget(self.btn_wizard_generate)

        # Humanize Button
        self.btn_wizard_humanize = QPushButton("👤 Humanize && Add Breath Cues")
        self.btn_wizard_humanize.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_wizard_humanize.setToolTip("Transform into a human masterpiece: inject natural breath pauses, sensory realism, and vulnerable bridge revelation")
        self.btn_wizard_humanize.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #0284c7);
                color: #ffffff;
                font-weight: 700;
                font-size: 11px;
                padding: 8px;
                border: 1px solid #10b981;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #10b981;
            }
        """)
        self.btn_wizard_humanize.clicked.connect(self._humanize_wizard_lyrics)
        a_layout.addWidget(self.btn_wizard_humanize)

        l_layout.addWidget(self.action_card)

        # Hit Potential Live Capsule
        self.card_hit_capsule = QFrame()
        self.card_hit_capsule.setStyleSheet("background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px;")
        h_layout = QVBoxLayout(self.card_hit_capsule)
        h_layout.setSpacing(4)

        lbl_h_title = QLabel("🌟 AI Quality & Vocal Delivery Score:")
        lbl_h_title.setStyleSheet("font-size: 10.5px; font-weight: 700; color: #64748b;")
        h_layout.addWidget(lbl_h_title)

        self.lbl_w_hit_score = QLabel("⏳ Awaiting lyrics — generate or type to run live studio scan")
        self.lbl_w_hit_score.setWordWrap(True)
        self.lbl_w_hit_score.setStyleSheet("font-weight: 700; font-size: 11px; color: #64748b;")
        h_layout.addWidget(self.lbl_w_hit_score)

        self.btn_w_open_hit_inspector = QPushButton("🔍 Inspect Hit Potential && Vocal Safety")
        self.btn_w_open_hit_inspector.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_w_open_hit_inspector.setStyleSheet("background: #faf5ff; color: #7c3aed; border: 1px solid #d8b4fe; font-weight: 700; font-size: 10.5px; padding: 4px 8px; border-radius: 4px;")
        self.btn_w_open_hit_inspector.clicked.connect(self._open_hit_dialog)
        h_layout.addWidget(self.btn_w_open_hit_inspector)

        l_layout.addWidget(self.card_hit_capsule)
        l_layout.addStretch()
        split_row.addWidget(left_col)

        # Right Column: Live Lyrics Studio Editor (Stretch 1)
        right_col = QVBoxLayout()
        right_col.setSpacing(6)

        # Toolstrip above lyrics editor
        t_row = QHBoxLayout()
        self.lbl_step3_preview = QLabel("Generated Lyrics Workbench:")
        self.lbl_step3_preview.setStyleSheet("font-weight: 700; font-size: 12px; color: #1e293b;")
        t_row.addWidget(self.lbl_step3_preview)
        t_row.addStretch()

        self.btn_w_load_template = QPushButton("🎵 Load English Hit Template")
        self.btn_w_load_template.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_w_load_template.setToolTip("Instantly load a complete radio-ready English song tailored to your selected genre, title & tempo")
        self.btn_w_load_template.setStyleSheet("background: #eff6ff; color: #1d4ed8; border: 1px solid #93c5fd; font-weight: 700; font-size: 10.5px; padding: 3px 8px; border-radius: 4px;")
        self.btn_w_load_template.clicked.connect(self._load_english_hit_template)
        t_row.addWidget(self.btn_w_load_template)

        self.btn_w_insert_hook = QPushButton("🎤 + Chorus Hook")
        self.btn_w_insert_hook.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_w_insert_hook.setToolTip("Insert a catchy 4-line English chorus hook into your lyrics")
        self.btn_w_insert_hook.setStyleSheet("background: #f0fdf4; color: #15803d; border: 1px solid #86efac; font-weight: 700; font-size: 10.5px; padding: 3px 8px; border-radius: 4px;")
        self.btn_w_insert_hook.clicked.connect(self._insert_english_chorus_hook)
        t_row.addWidget(self.btn_w_insert_hook)

        self.btn_w_copy_lyrics = QPushButton("📋 Copy All")
        self.btn_w_copy_lyrics.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_w_copy_lyrics.setStyleSheet("background: #f1f5f9; color: #334155; font-weight: 700; font-size: 10.5px; padding: 3px 8px; border-radius: 4px;")
        self.btn_w_copy_lyrics.clicked.connect(self._copy_lyrics)
        t_row.addWidget(self.btn_w_copy_lyrics)

        self.btn_w_clean_tags = QPushButton("🧹 Clean Tags")
        self.btn_w_clean_tags.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_w_clean_tags.setStyleSheet("background: #f1f5f9; color: #334155; font-weight: 700; font-size: 10.5px; padding: 3px 8px; border-radius: 4px;")
        self.btn_w_clean_tags.clicked.connect(self._clean_lyrics_tags)
        t_row.addWidget(self.btn_w_clean_tags)

        right_col.addLayout(t_row)

        # Live 2-Step Suno Style Strip right inside Step 3
        s3_style_row = QHBoxLayout()
        s3_style_row.setSpacing(6)
        self.txt_w_step3_style = QLineEdit()
        self.txt_w_step3_style.setPlaceholderText("Live Suno Style Prompt auto-built from Steps 1 & 2...")
        self.txt_w_step3_style.setStyleSheet("background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 5px; padding: 4px 8px; font-size: 10.5px;")
        s3_style_row.addWidget(self.txt_w_step3_style, stretch=1)

        self.btn_w_step3_copy_style = QPushButton("1. Copy Style")
        self.btn_w_step3_copy_style.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_w_step3_copy_style.setStyleSheet("background: #7c3aed; color: #ffffff; font-weight: 700; font-size: 10px; padding: 4px 8px; border-radius: 4px;")
        self.btn_w_step3_copy_style.clicked.connect(self._copy_step3_style_prompt)
        s3_style_row.addWidget(self.btn_w_step3_copy_style)

        right_col.addLayout(s3_style_row)

        self.txt_preview = QTextEdit()
        self.txt_preview.setPlaceholderText("Full structured lyrics ([Intro], [Verse 1], [Pre-Chorus], [Chorus], [Bridge], [Outro]) will appear here after clicking Generate or Load English Hit Template...")
        self.txt_preview.setFont(QFont("Segoe UI", 11))
        self.txt_preview.setStyleSheet("background: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 10px; line-height: 1.4;")
        self.txt_preview.textChanged.connect(self._on_lyrics_edited)
        right_col.addWidget(self.txt_preview, stretch=1)

        split_row.addLayout(right_col, stretch=1)
        layout.addLayout(split_row)
        self._load_english_hit_template(initial=True)
        return widget

    def _load_english_hit_template(self, initial: bool = False):
        title = (self.input_song_title.text().strip() if hasattr(self, "input_song_title") and self.input_song_title.text().strip() else self.current_title) or "Midnight Neon Lights"
        self.current_title = title
        sample = f"""=== {title} ===

[Intro: {self.state_bpm} BPM, {self.state_genre}, Atmospheric Synth & Guitar]
(Instrumentals build around {self.state_chords})

[Verse 1: Intimate Lead Vocal, Conversational Storytelling]
Streetlights flicker on the wet windshield glass
Every mile marker lets the old doubts pass
Coffee on the dashboard, radio turned low
Chasing down a coastline only we would know

[Pre-Chorus: Rising Drum Build, Tight Rhythmic Lift]
Heart beats faster as the skyline clears
Trading all the hesitation for the open years
Hold your breath, count it down from three—

[Chorus: Anthemic Earworm Hook, Full Layered Harmonies]
Underneath the midnight neon lights
We are turning broken yesterdays to flights
Hands up through the sunroof, racing with the dawn
Yeah, we keep on burning long after the storm is gone!

[Verse 2: Bass & Drums Lock In, Vivid Sensory Detail]
Polaroid snapshot tucked inside the door
We don't have to wonder what we're waiting for
Every red stoplight turning into green
Brightest little chapter that this town has ever seen

[Chorus: Anthemic Earworm Hook, Soaring Lead Belt]
Underneath the midnight neon lights
We are turning broken yesterdays to flights
Hands up through the sunroof, racing with the dawn
Yeah, we keep on burning long after the storm is gone!

[Bridge: Stripped Acoustic & Vocal Breakdown -> Crescendo]
(Quiet piano and vocal breath)
Even if the highway runs out of road
We carry the spark that nobody owed
(Drums crash back in — Key Change +1!)

[Final Chorus: Maximum Energy, Stadium Ad-Libs]
Underneath the midnight neon lights! (Neon lights!)
We are turning broken yesterdays to flights!
Hands up through the sunroof, racing with the dawn
Yeah, we keep on burning long after the storm is gone!

[Outro: Fading Synth Arpeggio & Reverb Tail]
(Long after the storm is gone...)
[End]"""
        self.txt_preview.setPlainText(sample)
        if not initial and hasattr(self, "btn_w_load_template"):
            self.btn_w_load_template.setText("✓ Template Loaded!")
            QTimer.singleShot(1400, lambda: self.btn_w_load_template.setText("🎵 Load English Hit Template") if hasattr(self, "btn_w_load_template") else None)

    def _insert_english_chorus_hook(self):
        import random
        hooks = [
            "\n[Chorus: Anthemic Billboard Hook, Full Harmonies]\nWe are dancing on the edge of midnight gold\nEvery secret that we kept is finally told\nTurn the volume up until the speakers shake\nThis is the promise that we'll never break!\n",
            "\n[Chorus: Emotional Melodic Hook, Soaring Vocal]\nI still see your shadow in the rearview glass\nTrying hard to outrun every ghost we passed\nIf the city lights go out before the dawn\nTell me how to love you when the road is gone!\n",
            "\n[Chorus: High-Energy Festival Drop Hook]\nLight it up, let the skyline burn tonight\nEvery heartbeat locking into satellite\nZero gravity, we're rising off the floor\nWe don't look behind us anymore!\n",
        ]
        cursor = self.txt_preview.textCursor()
        cursor.insertText(random.choice(hooks))
        self.txt_preview.setTextCursor(cursor)

    def _copy_lyrics(self):
        text = self.txt_preview.toPlainText().strip()
        if text:
            QApplication.clipboard().setText(text)
            self.btn_w_copy_lyrics.setText("✓ Copied!")
            QTimer.singleShot(1500, lambda: self.btn_w_copy_lyrics.setText("📋 Copy All") if hasattr(self, "btn_w_copy_lyrics") else None)

    def _clean_lyrics_tags(self):
        text = self.txt_preview.toPlainText()
        cleaned = re.sub(r'\[[A-G][b#]?[^\]]*\]', '', text)
        cleaned = re.sub(r'\[.*?\]', '', cleaned)
        cleaned = "\n".join(l.strip() for l in cleaned.split("\n") if l.strip())
        self.txt_preview.setPlainText(cleaned)

    def _build_wizard_style_prompt(self) -> str:
        mood_clean = self.combo_mood.currentText().split("(")[-1].strip(")") if hasattr(self, "combo_mood") else self.state_mood
        vocal = self.combo_w_vocal.currentText() if hasattr(self, "combo_w_vocal") else "Auto Vocal"
        vocal_tag = "" if vocal.startswith("Auto") else f", {vocal.lower()}"
        style = f"{self.state_genre.lower()}, {self.state_bpm} bpm, {mood_clean.lower()}{vocal_tag}, organic studio mix"
        return style[:180]

    def _refresh_step3_summary(self):
        vocal = self.combo_w_vocal.currentText() if hasattr(self, "combo_w_vocal") else "Auto"
        pov = self.combo_w_pov.currentText().split("(")[0].strip() if hasattr(self, "combo_w_pov") else "1st Person"
        if hasattr(self, "lbl_gen_summary"):
            self.lbl_gen_summary.setText(f"Song Setup: {self.state_genre} • {self.state_bpm} BPM • {vocal} • {pov}")
        if hasattr(self, "txt_w_step3_style"):
            self.txt_w_step3_style.setText(self._build_wizard_style_prompt())

    def _copy_step3_style_prompt(self):
        style = self.txt_w_step3_style.text().strip() if hasattr(self, "txt_w_step3_style") else self._build_wizard_style_prompt()
        if style:
            QApplication.clipboard().setText(style)
            self.btn_w_step3_copy_style.setText("✓ Style Copied!")
            QTimer.singleShot(1500, lambda: self.btn_w_step3_copy_style.setText("1. Copy Style") if hasattr(self, "btn_w_step3_copy_style") else None)

    def _on_lyrics_edited(self):
        lyrics = self.txt_preview.toPlainText()
        self.current_lyrics = lyrics
        if len(lyrics.strip()) > 30:
            from app.anti_cliche_engine import AntiClicheEngine
            analysis = HitAnalyzer.analyze(lyrics, self.state_bpm)
            score = analysis.get("hit_score", 85)
            safety = analysis.get("safety_score", 100)
            nov = AntiClicheEngine.calculate_novelty_score(self.current_title or "", lyrics, self.state_language)
            cliche_cnt = len(nov.get("cliche_hits", []))
            cliche_msg = "✓ 0 Clichés (Human Authentic)" if cliche_cnt == 0 else f"⚠️ {cliche_cnt} AI Cliché(s) Found"
            self.lbl_w_hit_score.setText(
                f"Hit: {score}% | Vocal Safety: {safety}% | Novelty: {nov.get('score', 90)}%\n{cliche_msg}"
            )
            color = "#10b981" if cliche_cnt == 0 else "#f59e0b"
            self.lbl_w_hit_score.setStyleSheet(f"font-weight: 800; font-size: 10.5px; color: {color};")
        else:
            self.lbl_w_hit_score.setText("⏳ Awaiting lyrics — generate or type to run live studio scan")
            self.lbl_w_hit_score.setStyleSheet("font-weight: 700; font-size: 11px; color: #64748b;")

    def _open_hit_dialog(self):
        lyrics = self.txt_preview.toPlainText().strip()
        if not lyrics:
            QMessageBox.information(self, "No Lyrics", "Please generate or write lyrics before running hit inspection.")
            return
        dlg = HitAnalyzerDialog(lyrics, bpm=self.state_bpm, is_dark=self.is_dark, parent=self)
        dlg.exec()

    def _humanize_wizard_lyrics(self):
        curr = self.txt_preview.toPlainText().strip()
        if not curr:
            return
        lang = "Khmer" if ("Khmer" in self.state_language or "ខ្មែរ" in self.state_language) else "English"
        h_lyrics = HumanizerEngine.humanize_lyrics_locally(curr, lang)
        self.txt_preview.setPlainText(h_lyrics)
        self.btn_wizard_humanize.setText("✅ Human Breath & Soul Injected!")
        QTimer.singleShot(2500, lambda: self.btn_wizard_humanize.setText("👤 Humanize && Add Breath Cues") if hasattr(self, "btn_wizard_humanize") else None)

    def _trigger_generate(self):
        theme = self.input_theme.text().strip() or "A bittersweet love story"
        mood = self.combo_mood.currentText()
        structure = self.combo_w_structure.currentText() if hasattr(self, "combo_w_structure") else self.state_structure
        vocal = self.combo_w_vocal.currentText() if hasattr(self, "combo_w_vocal") else "Auto Vocal"
        pov = self.combo_w_pov.currentText() if hasattr(self, "combo_w_pov") else "1st Person (I / Me)"
        human_on = self.btn_w_human_mode.isChecked() if hasattr(self, "btn_w_human_mode") else True
        style_prompt = self._build_wizard_style_prompt()
        if hasattr(self, "txt_w_step3_style"):
            self.txt_w_step3_style.setText(style_prompt)

        human_rule = (
            " STRICT HUMAN SONGWRITING: Use concrete everyday sensory details, conversational phrasing, "
            "natural singer breath pauses, and ZERO generic AI clichés."
            if human_on else ""
        )

        params = {
            "genre": self.state_genre,
            "region": "Cambodia & Southeast Asia" if ("Khmer" in self.state_language or "ខ្មែរ" in self.state_language) else "Global Pop",
            "language": self.state_language,
            "mood": mood,
            "theme": theme,
            "structure": structure,
            "rhyme": self.state_rhyme,
            "bpm": f"{self.state_bpm} BPM",
            "style_prompt": style_prompt,
            "user_notes": (
                f"Vocal delivery: {vocal}. Perspective: {pov}. Chords: {self.state_chords}, tempo {self.state_bpm} BPM."
                f"{human_rule}"
            )
        }
        self.btn_wizard_generate.setText("⏳ Generating Lyrics with Gemini...")
        self.btn_wizard_generate.setEnabled(False)
        self.generate_requested.emit(params)

    def set_generated_lyrics(self, title: str, lyrics: str):
        self.btn_wizard_generate.setText("⚡ Regenerate Lyrics")
        self.btn_wizard_generate.setEnabled(True)
        self.current_title = title or "Untitled Song"
        self.current_lyrics = lyrics
        self.txt_preview.setPlainText(f"=== {title} ===\n\n{lyrics}")
        self._on_lyrics_edited()

    # --- Step 4: Audition, Teleprompter & Recording Booth ---
    def _create_step4_audition(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        self.step4_header = QLabel("Step 4 : Vocal Booth — Singer Teleprompter & Melody Scratchpad")
        self.step4_header.setStyleSheet("font-size: 15px; font-weight: 700; color: #1e293b;")
        layout.addWidget(self.step4_header)

        # Split: Left Lyrics Teleprompter / Right Recording Console
        split_row = QHBoxLayout()
        split_row.setSpacing(12)

        # Left Column: Lyrics Teleprompter
        left_prompter = QFrame()
        p_layout = QVBoxLayout(left_prompter)
        p_layout.setContentsMargins(0, 0, 0, 0)
        p_layout.setSpacing(4)

        lbl_pr_title = QLabel("🎤 Singer Teleprompter View:")
        lbl_pr_title.setStyleSheet("font-weight: 700; font-size: 11.5px; color: #1e293b;")
        p_layout.addWidget(lbl_pr_title)

        self.txt_teleprompter = QTextEdit()
        self.txt_teleprompter.setReadOnly(True)
        self.txt_teleprompter.setFont(QFont("Segoe UI", 13))
        self.txt_teleprompter.setStyleSheet("background: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 12px; line-height: 1.6;")
        p_layout.addWidget(self.txt_teleprompter, stretch=1)
        split_row.addWidget(left_prompter, stretch=1)

        # Right Column: Vocal & Rhythm Studio Console (~465px)
        right_console = QFrame()
        right_console.setFixedWidth(465)
        c_layout = QVBoxLayout(right_console)
        c_layout.setContentsMargins(0, 0, 0, 0)
        c_layout.setSpacing(10)

        # 1. Metronome & Rhythm Loop
        self.metro_box = QGroupBox("1. Studio Rhythm Groove && Metronome")
        m_layout = QVBoxLayout(self.metro_box)
        m_layout.setSpacing(6)

        self.lbl_m_info = QLabel("Audition your lyrics over a live drum groove or metronome click to verify syllable flow:")
        self.lbl_m_info.setStyleSheet("color: #64748b; font-size: 11px;")
        m_layout.addWidget(self.lbl_m_info)

        m_btn_row = QHBoxLayout()
        self.btn_w_metro = QPushButton("▶ Metronome")
        self.btn_w_metro.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_w_metro.setStyleSheet("background: #f1f5f9; color: #2563eb; font-weight: 700; padding: 7px 12px; border-radius: 6px;")
        m_btn_row.addWidget(self.btn_w_metro)

        self.btn_w_step4_groove = QPushButton("🥁 Play Groove Loop")
        self.btn_w_step4_groove.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_w_step4_groove.setStyleSheet("background: #064e3b; color: #34d399; font-weight: 700; padding: 7px 12px; border-radius: 6px;")
        self.btn_w_step4_groove.clicked.connect(self._toggle_step4_groove)
        m_btn_row.addWidget(self.btn_w_step4_groove)
        m_layout.addLayout(m_btn_row)

        c_layout.addWidget(self.metro_box)

        # 2. Microphone Scratchpad
        self.voice_box = QGroupBox("2. Microphone Melody Scratchpad")
        v_layout = QVBoxLayout(self.voice_box)
        v_layout.setSpacing(6)

        self.v_desc = QLabel("Record a quick vocal take or hum a topline melody idea straight from your microphone:")
        self.v_desc.setStyleSheet("color: #64748b; font-size: 11px;")
        v_layout.addWidget(self.v_desc)

        btn_row = QHBoxLayout()
        self.btn_w_record = QPushButton("🔴 Record Scratch Melody (Mic)")
        self.btn_w_record.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_w_record.setStyleSheet("background-color: #fee2e2; color: #dc2626; font-weight: 700; border: 1px solid #fca5a5; border-radius: 6px; padding: 9px;")
        btn_row.addWidget(self.btn_w_record)

        self.btn_w_play_rec = QPushButton("▶ Play Recorded Take")
        self.btn_w_play_rec.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_w_play_rec.setEnabled(False)
        self.btn_w_play_rec.setStyleSheet("background: #f1f5f9; color: #334155; font-weight: 600; padding: 9px; border-radius: 6px;")
        btn_row.addWidget(self.btn_w_play_rec)
        v_layout.addLayout(btn_row)

        self.lbl_w_rec_status = QLabel("Ready to record voice take")
        self.lbl_w_rec_status.setStyleSheet("color: #64748b; font-size: 11px; font-style: italic;")
        v_layout.addWidget(self.lbl_w_rec_status)
        c_layout.addWidget(self.voice_box)

        c_layout.addStretch()
        split_row.addWidget(right_console)

        layout.addLayout(split_row)
        return widget

    def _sync_teleprompter(self):
        curr = self.txt_preview.toPlainText().strip() if hasattr(self, "txt_preview") else ""
        if not curr:
            curr = "(No lyrics generated yet. Generate or write your lyrics in Step 3 first.)"
        self.txt_teleprompter.setPlainText(curr)

    def _toggle_step4_groove(self):
        grv = self.combo_w_groove.currentText() if hasattr(self, "combo_w_groove") else "🇰🇭 Romvong (74 BPM)"
        bpm = self.state_bpm
        RhythmEngine.play_groove(grv, bpm)
        self.btn_w_step4_groove.setText("⏹ Stop Groove")
        self.btn_w_step4_groove.setStyleSheet("background: #dc2626; color: #ffffff; font-weight: 700; padding: 7px 12px; border-radius: 6px;")
        self.btn_w_step4_groove.clicked.disconnect()
        self.btn_w_step4_groove.clicked.connect(self._stop_step4_groove)

    def _stop_step4_groove(self):
        RhythmEngine.stop_groove()
        self.btn_w_step4_groove.setText("🥁 Play Groove Loop")
        self.btn_w_step4_groove.setStyleSheet("background: #064e3b; color: #34d399; font-weight: 700; padding: 7px 12px; border-radius: 6px;")
        self.btn_w_step4_groove.clicked.disconnect()
        self.btn_w_step4_groove.clicked.connect(self._toggle_step4_groove)

    # --- Step 5: Publishing & Production Export ---
    def _create_step5_export(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        self.step5_header = QLabel("Step 5 : Suno AI Ready-to-Paste Station & Multi-Format Export")
        self.step5_header.setStyleSheet("font-size: 15px; font-weight: 700; color: #1e293b;")
        layout.addWidget(self.step5_header)

        # 1. Suno AI 1-Click Copy Station Card
        self.suno_card = QFrame()
        self.suno_card.setStyleSheet("background: #faf5ff; border: 1px solid #d8b4fe; border-radius: 8px; padding: 10px;")
        s_layout = QVBoxLayout(self.suno_card)
        s_layout.setSpacing(6)

        lbl_suno_title = QLabel("⚡ Suno & Udio AI Ready-to-Paste Station:")
        lbl_suno_title.setStyleSheet("font-weight: 800; font-size: 12px; color: #7c3aed;")
        s_layout.addWidget(lbl_suno_title)

        # Style prompt row
        sp_row = QHBoxLayout()
        sp_row.setSpacing(6)
        self.txt_suno_style = QLineEdit()
        self.txt_suno_style.setReadOnly(True)
        self.txt_suno_style.setStyleSheet("background: #ffffff; border: 1px solid #cbd5e1; border-radius: 5px; padding: 6px; font-size: 11px;")
        sp_row.addWidget(self.txt_suno_style, stretch=1)

        self.btn_copy_style = QPushButton("📋 Copy Style Prompt")
        self.btn_copy_style.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_copy_style.setStyleSheet("background: #7c3aed; color: #ffffff; font-weight: 700; font-size: 11px; padding: 6px 12px; border-radius: 5px;")
        self.btn_copy_style.clicked.connect(self._copy_style_prompt)
        sp_row.addWidget(self.btn_copy_style)

        self.btn_copy_suno_lyrics = QPushButton("📋 Copy Lyrics (with Tags)")
        self.btn_copy_suno_lyrics.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_copy_suno_lyrics.setStyleSheet("background: #2563eb; color: #ffffff; font-weight: 700; font-size: 11px; padding: 6px 12px; border-radius: 5px;")
        self.btn_copy_suno_lyrics.clicked.connect(self._copy_lyrics)
        sp_row.addWidget(self.btn_copy_suno_lyrics)

        s_layout.addLayout(sp_row)
        layout.addWidget(self.suno_card)

        # 2. Master DAW Multi-Format Export Center
        self.bundle_card = QFrame()
        self.bundle_card.setStyleSheet("background: #f0fdf4; border: 2px solid #86efac; border-radius: 10px; padding: 12px;")
        b_layout = QVBoxLayout(self.bundle_card)
        b_layout.setSpacing(8)

        self.lbl_b_title = QLabel("📦 Master Multi-Format Exporter (DAW, Subtitles, Karaoke & Lead Sheets)")
        self.lbl_b_title.setStyleSheet("font-size: 13.5px; font-weight: 800; color: #166534;")
        b_layout.addWidget(self.lbl_b_title)

        # Grid of Exporters
        ex_grid = QGridLayout()
        ex_grid.setSpacing(6)

        self.btn_ex_zip = QPushButton("📦 Master Production Bundle (.zip)")
        self.btn_ex_zip.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ex_zip.setStyleSheet("background: #16a34a; color: #ffffff; font-weight: 800; font-size: 11.5px; padding: 8px; border-radius: 6px;")
        self.btn_ex_zip.clicked.connect(lambda: self.export_bundle_requested.emit())
        ex_grid.addWidget(self.btn_ex_zip, 0, 0)

        self.btn_ex_srt = QPushButton("📄 Video Subtitles (.srt)")
        self.btn_ex_srt.setToolTip("Export subtitles for CapCut, TikTok, Premiere Pro, and YouTube")
        self.btn_ex_srt.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ex_srt.setStyleSheet("background: #ffffff; color: #166534; border: 1px solid #86efac; font-weight: 700; font-size: 11px; padding: 8px; border-radius: 6px;")
        self.btn_ex_srt.clicked.connect(self._export_srt)
        ex_grid.addWidget(self.btn_ex_srt, 0, 1)

        self.btn_ex_lrc = QPushButton("🎵 Synced Karaoke (.lrc)")
        self.btn_ex_lrc.setToolTip("Export synced karaoke format for Spotify and Apple Music")
        self.btn_ex_lrc.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ex_lrc.setStyleSheet("background: #ffffff; color: #166534; border: 1px solid #86efac; font-weight: 700; font-size: 11px; padding: 8px; border-radius: 6px;")
        self.btn_ex_lrc.clicked.connect(self._export_lrc)
        ex_grid.addWidget(self.btn_ex_lrc, 1, 0)

        self.btn_ex_txt = QPushButton("🎤 Clean Singer Sheet (.txt)")
        self.btn_ex_txt.setToolTip("Strips chords and audio tags for recording vocalists")
        self.btn_ex_txt.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ex_txt.setStyleSheet("background: #ffffff; color: #166534; border: 1px solid #86efac; font-weight: 700; font-size: 11px; padding: 8px; border-radius: 6px;")
        self.btn_ex_txt.clicked.connect(self._export_vocal_sheet)
        ex_grid.addWidget(self.btn_ex_txt, 1, 1)

        self.btn_ex_cho = QPushButton("🎸 ChordPro Lead Sheet (.cho)")
        self.btn_ex_cho.setToolTip("Standard ChordPro format for stage musicians and guitarists")
        self.btn_ex_cho.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ex_cho.setStyleSheet("background: #ffffff; color: #166534; border: 1px solid #86efac; font-weight: 700; font-size: 11px; padding: 8px; border-radius: 6px;")
        self.btn_ex_cho.clicked.connect(self._export_chordpro)
        ex_grid.addWidget(self.btn_ex_cho, 2, 0)

        self.btn_ex_html = QPushButton("📑 Printable HTML Sheet (.html)")
        self.btn_ex_html.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ex_html.setStyleSheet("background: #ffffff; color: #166534; border: 1px solid #86efac; font-weight: 700; font-size: 11px; padding: 8px; border-radius: 6px;")
        self.btn_ex_html.clicked.connect(self._export_html_sheet)
        ex_grid.addWidget(self.btn_ex_html, 2, 1)

        b_layout.addLayout(ex_grid)
        layout.addWidget(self.bundle_card)

        # 3. Action to open in full editor or Batch Pro
        self.lbl_step5_more = QLabel("Continue editing or scale this concept to a 20-song batch:")
        self.lbl_step5_more.setStyleSheet("font-weight: 700; font-size: 11.5px; color: #64748b;")
        layout.addWidget(self.lbl_step5_more)

        w_actions = QHBoxLayout()
        w_actions.setSpacing(10)
        self.btn_open_full = QPushButton("✍️ Open Full Lyric Editor Workbench")
        self.btn_open_full.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open_full.setStyleSheet("background: #eff6ff; color: #1d4ed8; font-weight: 700; border: 1px solid #bfdbfe; padding: 10px; border-radius: 8px;")
        self.btn_open_full.clicked.connect(lambda: self.open_editor_requested.emit())
        w_actions.addWidget(self.btn_open_full)

        self.btn_w_batch = QPushButton("⚡ Produce 20 Variations in Batch Studio Pro")
        self.btn_w_batch.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_w_batch.setStyleSheet("background: #faf5ff; color: #7c3aed; font-weight: 700; border: 1px solid #d8b4fe; padding: 10px; border-radius: 8px;")
        self.btn_w_batch.clicked.connect(self._emit_open_batch)
        w_actions.addWidget(self.btn_w_batch)

        layout.addLayout(w_actions)
        layout.addStretch()
        return widget

    def _sync_export_step(self):
        style = (
            self.txt_w_step3_style.text().strip()
            if hasattr(self, "txt_w_step3_style") and self.txt_w_step3_style.text().strip()
            else self._build_wizard_style_prompt()
        )
        self.txt_suno_style.setText(style)

    def _copy_style_prompt(self):
        style = self.txt_suno_style.text().strip()
        if style:
            QApplication.clipboard().setText(style)
            self.btn_copy_style.setText("✓ Copied Style!")
            QTimer.singleShot(1500, lambda: self.btn_copy_style.setText("📋 Copy Style Prompt") if hasattr(self, "btn_copy_style") else None)

    def _export_srt(self):
        lyrics = self.txt_preview.toPlainText().strip() if hasattr(self, "txt_preview") else ""
        if not lyrics:
            QMessageBox.warning(self, "Missing Lyrics", "Please generate lyrics first.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save Video Subtitles (.srt)", f"{self.current_title}.srt", "Subtitle Files (*.srt)")
        if path:
            Exporter.export_srt(path, self.current_title, lyrics, f"{self.state_bpm} BPM")
            QMessageBox.information(self, "Exported", f"Successfully exported video subtitles to:\n{path}")

    def _export_lrc(self):
        lyrics = self.txt_preview.toPlainText().strip() if hasattr(self, "txt_preview") else ""
        if not lyrics:
            QMessageBox.warning(self, "Missing Lyrics", "Please generate lyrics first.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save Synced Karaoke (.lrc)", f"{self.current_title}.lrc", "Karaoke Files (*.lrc)")
        if path:
            Exporter.export_lrc(path, self.current_title, lyrics, f"{self.state_bpm} BPM")
            QMessageBox.information(self, "Exported", f"Successfully exported synced karaoke file to:\n{path}")

    def _export_vocal_sheet(self):
        lyrics = self.txt_preview.toPlainText().strip() if hasattr(self, "txt_preview") else ""
        if not lyrics:
            QMessageBox.warning(self, "Missing Lyrics", "Please generate lyrics first.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save Clean Singer Sheet (.txt)", f"{self.current_title}_vocals.txt", "Text Files (*.txt)")
        if path:
            Exporter.export_clean_vocal_sheet(path, self.current_title, lyrics)
            QMessageBox.information(self, "Exported", f"Successfully exported singer vocal sheet to:\n{path}")

    def _export_chordpro(self):
        lyrics = self.txt_preview.toPlainText().strip() if hasattr(self, "txt_preview") else ""
        if not lyrics:
            QMessageBox.warning(self, "Missing Lyrics", "Please generate lyrics first.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save ChordPro Lead Sheet (.cho)", f"{self.current_title}.cho", "ChordPro Files (*.cho)")
        if path:
            Exporter.export_chordpro(path, self.current_title, lyrics, {"bpm": f"{self.state_bpm} BPM", "key": self.state_chords})
            QMessageBox.information(self, "Exported", f"Successfully exported ChordPro sheet to:\n{path}")

    def _export_html_sheet(self):
        lyrics = self.txt_preview.toPlainText().strip() if hasattr(self, "txt_preview") else ""
        if not lyrics:
            QMessageBox.warning(self, "Missing Lyrics", "Please generate lyrics first.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save Printable HTML Lead Sheet (.html)", f"{self.current_title}.html", "HTML Files (*.html)")
        if path:
            Exporter.export_html(path, self.current_title, lyrics, {"bpm": f"{self.state_bpm} BPM", "genre": self.state_genre})
            QMessageBox.information(self, "Exported", f"Successfully exported printable HTML sheet to:\n{path}")

    def get_wizard_parameters(self) -> dict:
        return {
            "genre": self.state_genre,
            "region": "Cambodia & Southeast Asia" if ("Khmer" in self.state_language or "ខ្មែរ" in self.state_language) else "Global Pop",
            "language": self.state_language,
            "mood": self.combo_mood.currentText() if hasattr(self, "combo_mood") else self.state_mood,
            "theme": self.input_theme.text().strip() if hasattr(self, "input_theme") else self.state_theme,
            "structure": self.combo_w_structure.currentText() if hasattr(self, "combo_w_structure") else self.state_structure,
            "rhyme": self.state_rhyme,
            "bpm": f"{self.state_bpm} BPM",
            "title": self.current_title or "Untitled Wizard Song",
            "lyrics": self.txt_preview.toPlainText() if hasattr(self, "txt_preview") else ""
        }

    def _emit_open_batch(self):
        params = self.get_wizard_parameters()
        self.open_batch_requested.emit(params)

    # --- Comprehensive Light & Dark Theming ---
    def apply_theme(self, theme_or_dark):
        from app.ui.styles import get_theme
        t = get_theme(theme_or_dark)
        self.current_theme = t['id']
        is_dark = t['is_dark']
        self.is_dark = is_dark
        accent = t['accent']
        accent_sec = t['accent_secondary']
        accent_grad = t['accent_gradient']
        bg_card = t['bg_card']
        border = t['border']
        border_subtle = t['border_subtle']
        text_pri = t['text_primary']
        text_sec = t['text_secondary']
        text_muted = t['text_muted']
        btn_bg = t['bg_btn']
        btn_hover = t['bg_btn_hover']
        bg_input = t['bg_input']

        if is_dark:
            if hasattr(self, 'main_title'):
                self.main_title.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {text_pri};")
            if hasattr(self, 'sub_title'):
                self.sub_title.setStyleSheet(f"font-size: 11.5px; color: {text_sec};")
            if hasattr(self, 'nav_frame'):
                self.nav_frame.setStyleSheet(f"border-top: 1px solid {border}; padding-top: 8px;")
            if hasattr(self, 'lbl_step_indicator'):
                self.lbl_step_indicator.setStyleSheet(f"color: {text_sec}; font-weight: 700; font-size: 12px;")
            if hasattr(self, 'stepper_frame'):
                self.stepper_frame.setStyleSheet(f"background-color: {bg_card}; border: 1px solid {border}; border-radius: 10px; padding: 4px;")
            self.btn_prev.setStyleSheet(f"background-color: {btn_bg}; color: {text_pri}; border: 1px solid {border_subtle}; font-weight: 700; padding: 8px 16px; border-radius: 6px;")
            self.btn_next.setStyleSheet(f"background: {accent_grad}; color: #ffffff; font-weight: 800; padding: 8px 20px; border-radius: 6px; border: 1px solid {t['border_accent']};")

            # Step Headers
            for h in [getattr(self, 'step1_header', None), getattr(self, 'step2_header', None), getattr(self, 'step3_header', None), getattr(self, 'step4_header', None), getattr(self, 'step5_header', None)]:
                if h:
                    h.setStyleSheet(f"font-size: 15px; font-weight: 800; color: {text_pri};")

            # Step 1 Genre Buttons (Sleek Studio Cards in Dark Mode)
            if hasattr(self, 'genre_buttons'):
                for b in self.genre_buttons:
                    b.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {bg_card};
                            border: 1px solid {border};
                            border-radius: 8px;
                            padding: 9px 12px;
                            text-align: left;
                            font-size: 11.5px;
                            color: {text_pri};
                        }}
                        QPushButton:hover {{
                            border-color: {accent};
                            background-color: {btn_hover};
                        }}
                        QPushButton:checked {{
                            border: 2px solid {accent};
                            background: {t['bg_btn_secondary']};
                            font-weight: 800;
                            color: #ffffff;
                        }}
                    """)

            if hasattr(self, 'lbl_story_seeds'):
                self.lbl_story_seeds.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {text_sec};")
            if hasattr(self, 'seed_buttons'):
                for b in self.seed_buttons:
                    b.setStyleSheet(f"background: {btn_bg}; color: {text_sec}; border: 1px solid {border_subtle}; padding: 4px 8px; border-radius: 5px; font-size: 10.5px; font-weight: 700;")
            if hasattr(self, 'input_theme'):
                self.input_theme.setStyleSheet(f"background-color: {bg_input}; color: {text_pri}; border: 1px solid {border_subtle}; border-radius: 6px; padding: 7px 10px; font-size: 12px;")
            if hasattr(self, 'combo_mood'):
                self.combo_mood.setStyleSheet(f"background-color: {bg_input}; color: {text_pri}; border: 1px solid {border_subtle}; border-radius: 6px; padding: 6px; font-size: 11.5px;")
            if hasattr(self, 'combo_lang'):
                self.combo_lang.setStyleSheet(f"background-color: {bg_input}; color: {text_pri}; border: 1px solid {border_subtle}; border-radius: 6px; padding: 6px; font-size: 11.5px;")
            for w_cb in [getattr(self, 'combo_w_vocal', None), getattr(self, 'combo_w_pov', None), getattr(self, 'combo_w_hook_style', None)]:
                if w_cb:
                    w_cb.setStyleSheet(f"background-color: {bg_input}; color: {text_pri}; border: 1px solid {border_subtle}; border-radius: 6px; padding: 5px 6px; font-size: 11px;")
            for w_lbl in [getattr(self, 'lbl_w_vocal_tag', None), getattr(self, 'lbl_w_pov_tag', None), getattr(self, 'lbl_w_title_tag', None), getattr(self, 'lbl_w_hook_tag', None)]:
                if w_lbl:
                    w_lbl.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {text_sec};")
            if hasattr(self, 'input_song_title'):
                self.input_song_title.setStyleSheet(f"background-color: {bg_input}; color: {text_pri}; border: 1px solid {border_subtle}; border-radius: 6px; padding: 5px 8px; font-size: 11.5px; font-weight: 700;")
            if hasattr(self, 'btn_w_roll_hook'):
                self.btn_w_roll_hook.setStyleSheet(f"background: {btn_bg}; color: {accent}; border: 1px solid {accent}; border-radius: 6px; padding: 5px 10px; font-size: 11px; font-weight: 700;")
            if hasattr(self, 'btn_w_surprise'):
                self.btn_w_surprise.setStyleSheet(f"background: {btn_bg}; color: {accent}; border: 1px solid {accent_sec}; border-radius: 6px; padding: 5px 10px; font-size: 11px; font-weight: 700;")
            if hasattr(self, 'txt_w_step3_style'):
                self.txt_w_step3_style.setStyleSheet(f"background: {bg_input}; color: {text_pri}; border: 1px solid {border_subtle}; border-radius: 5px; padding: 4px 8px; font-size: 10.5px;")

            # Step 2 Group Boxes & Inputs
            gb_qss_dark = f"""
                QGroupBox {{
                    font-weight: 800;
                    color: {text_pri};
                    border: 1px solid {border};
                    border-radius: 8px;
                    margin-top: 10px;
                    padding: 10px;
                    background-color: {bg_card};
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 4px;
                    color: {accent};
                }}
            """
            for gb in [getattr(self, 'bpm_box', None), getattr(self, 'vocal_box', None), getattr(self, 'prog_box', None), getattr(self, 'metro_box', None), getattr(self, 'voice_box', None)]:
                if gb:
                    gb.setStyleSheet(gb_qss_dark)

            if hasattr(self, 'lbl_bpm_display'):
                self.lbl_bpm_display.setStyleSheet(f"font-weight: 800; color: {accent}; font-size: 12.5px;")
            if hasattr(self, 'combo_w_groove'):
                self.combo_w_groove.setStyleSheet(f"background-color: {bg_input}; color: {text_pri}; border: 1px solid {border_subtle}; padding: 4px 8px; font-size: 11px; font-weight: 600; min-width: 170px;")
            if hasattr(self, 'btn_w_stop_groove'):
                self.btn_w_stop_groove.setStyleSheet(f"background: {btn_bg}; color: {text_sec}; font-weight: 700; font-size: 10.5px; padding: 4px 8px; border-radius: 4px; border: 1px solid {border_subtle};")
            if hasattr(self, 'bpm_preset_btns'):
                for b in self.bpm_preset_btns:
                    b.setStyleSheet(f"background: {btn_bg}; color: {text_sec}; border: 1px solid {border_subtle}; padding: 5px 8px; border-radius: 5px; font-size: 11px; font-weight: 700;")
            if hasattr(self, 'combo_vocal'):
                self.combo_vocal.setStyleSheet(f"background-color: {bg_input}; color: {text_pri}; border: 1px solid {border_subtle}; border-radius: 6px; padding: 6px; font-size: 11.5px;")
            if hasattr(self, 'lbl_vocal_info'):
                self.lbl_vocal_info.setStyleSheet(f"color: {text_sec}; font-size: 11px;")
            if hasattr(self, 'combo_chords'):
                self.combo_chords.setStyleSheet(f"background-color: {bg_input}; color: {text_pri}; border: 1px solid {border_subtle}; border-radius: 6px; padding: 6px; font-size: 11.5px;")
            if hasattr(self, 'lbl_chord_preview'):
                self.lbl_chord_preview.setStyleSheet(f"font-weight: 800; color: {accent}; background: {bg_input}; border: 1px solid {border}; padding: 6px 10px; border-radius: 6px;")
            if hasattr(self, 'btn_w_play_chords'):
                self.btn_w_play_chords.setStyleSheet(f"background-color: {btn_bg}; color: {accent}; font-weight: 800; border: 1px solid {accent}; border-radius: 6px; padding: 6px 12px;")
            if hasattr(self, 'btn_w_stop_chords'):
                self.btn_w_stop_chords.setStyleSheet(f"background-color: {btn_bg}; color: {text_sec}; font-weight: 600; border: 1px solid {border_subtle}; border-radius: 6px; padding: 6px 10px;")

            # Step 3
            if hasattr(self, 'action_card'):
                self.action_card.setStyleSheet(f"background: {bg_card}; border: 1px solid {border}; border-radius: 8px; padding: 10px;")
            if hasattr(self, 'lbl_gen_summary'):
                self.lbl_gen_summary.setStyleSheet(f"font-weight: 800; color: {accent}; font-size: 11px;")
            if hasattr(self, 'combo_w_structure'):
                self.combo_w_structure.setStyleSheet(f"background-color: {bg_input}; color: {text_pri}; border: 1px solid {border_subtle}; border-radius: 5px; padding: 4px; font-size: 11px;")
            if hasattr(self, 'card_hit_capsule'):
                self.card_hit_capsule.setStyleSheet(f"background: {bg_card}; border: 1px solid {border}; border-radius: 8px; padding: 10px;")
            if hasattr(self, 'lbl_step3_preview'):
                self.lbl_step3_preview.setStyleSheet(f"color: {text_pri}; font-weight: 800; font-size: 12px;")
            if hasattr(self, 'btn_w_copy_lyrics'):
                self.btn_w_copy_lyrics.setStyleSheet(f"background: {btn_bg}; color: {accent}; border: 1px solid {accent_sec}; font-weight: 700; font-size: 10.5px; padding: 3px 8px; border-radius: 4px;")
            if hasattr(self, 'btn_w_load_template'):
                self.btn_w_load_template.setStyleSheet(f"background: {btn_bg}; color: {accent}; border: 1px solid {accent}; font-weight: 700; font-size: 10.5px; padding: 3px 8px; border-radius: 4px;")
            if hasattr(self, 'btn_w_insert_hook'):
                self.btn_w_insert_hook.setStyleSheet(f"background: #064e3b; color: #34d399; border: 1px solid #059669; font-weight: 700; font-size: 10.5px; padding: 3px 8px; border-radius: 4px;")
            if hasattr(self, 'btn_w_clean_tags'):
                self.btn_w_clean_tags.setStyleSheet(f"background: {btn_bg}; color: {text_sec}; border: 1px solid {border_subtle}; font-weight: 700; font-size: 10.5px; padding: 3px 8px; border-radius: 4px;")
            if hasattr(self, 'txt_preview'):
                self.txt_preview.setStyleSheet(f"background: {bg_input}; color: {text_pri}; border: 1px solid {border}; border-radius: 8px; padding: 10px; font-size: 12px;")

            # Step 4
            if hasattr(self, 'txt_teleprompter'):
                self.txt_teleprompter.setStyleSheet(f"background: {bg_input}; color: {text_pri}; border: 1px solid {border}; border-radius: 8px; padding: 12px; line-height: 1.6; font-size: 13px;")
            if hasattr(self, 'lbl_m_info'):
                self.lbl_m_info.setStyleSheet(f"color: {text_sec}; font-size: 11px;")
            if hasattr(self, 'btn_w_metro'):
                self.btn_w_metro.setStyleSheet(f"background: {btn_bg}; color: {accent}; font-weight: 800; padding: 7px 12px; border-radius: 6px; border: 1px solid {accent_sec};")
            if hasattr(self, 'v_desc'):
                self.v_desc.setStyleSheet(f"color: {text_sec}; font-size: 11px;")
            if hasattr(self, 'btn_w_record'):
                self.btn_w_record.setStyleSheet("background-color: #500724; color: #f472b6; font-weight: 800; border: 1px solid #be185d; border-radius: 6px; padding: 9px;")
            if hasattr(self, 'btn_w_play_rec'):
                self.btn_w_play_rec.setStyleSheet(f"background: {btn_bg}; color: {text_pri}; font-weight: 700; padding: 9px; border-radius: 6px; border: 1px solid {border_subtle};")
            if hasattr(self, 'lbl_w_rec_status'):
                self.lbl_w_rec_status.setStyleSheet(f"color: {text_muted}; font-size: 11px; font-style: italic;")

            # Step 5
            if hasattr(self, 'suno_card'):
                self.suno_card.setStyleSheet(f"background: {bg_card}; border: 1px solid {border}; border-radius: 8px; padding: 10px;")
            if hasattr(self, 'txt_suno_style'):
                self.txt_suno_style.setStyleSheet(f"background: {bg_input}; color: {text_pri}; border: 1px solid {border_subtle}; border-radius: 5px; padding: 6px; font-size: 11px;")
            if hasattr(self, 'bundle_card'):
                self.bundle_card.setStyleSheet(f"background: {bg_card}; border: 2px solid {accent}; border-radius: 10px; padding: 12px;")
            if hasattr(self, 'lbl_b_title'):
                self.lbl_b_title.setStyleSheet(f"font-size: 13.5px; font-weight: 800; color: {accent};")
            for btn_ex in [getattr(self, 'btn_ex_srt', None), getattr(self, 'btn_ex_lrc', None), getattr(self, 'btn_ex_txt', None), getattr(self, 'btn_ex_cho', None), getattr(self, 'btn_ex_html', None)]:
                if btn_ex:
                    btn_ex.setStyleSheet(f"background: {btn_bg}; color: {text_pri}; border: 1px solid {border_subtle}; font-weight: 700; font-size: 11px; padding: 8px; border-radius: 6px;")
            if hasattr(self, 'lbl_step5_more'):
                self.lbl_step5_more.setStyleSheet(f"color: {text_pri}; font-weight: 700; font-size: 11.5px;")
            if hasattr(self, 'btn_open_full'):
                self.btn_open_full.setStyleSheet(f"background: {btn_bg}; color: {accent}; font-weight: 800; border: 1px solid {accent}; padding: 10px; border-radius: 8px;")
            if hasattr(self, 'btn_w_batch'):
                self.btn_w_batch.setStyleSheet(f"background: {btn_bg}; color: {accent_sec}; font-weight: 800; border: 1px solid {accent_sec}; padding: 10px; border-radius: 8px;")
        else:
            # Modern Studio Light Palette (Crisp, High Contrast, Perfectly Clear)
            if hasattr(self, 'main_title'):
                self.main_title.setStyleSheet("font-size: 20px; font-weight: 800; color: #0f172a;")
            if hasattr(self, 'sub_title'):
                self.sub_title.setStyleSheet("font-size: 11.5px; color: #1e293b; font-weight: 600;")
            if hasattr(self, 'nav_frame'):
                self.nav_frame.setStyleSheet("border-top: 1px solid #cbd5e1; padding-top: 8px;")
            if hasattr(self, 'lbl_step_indicator'):
                self.lbl_step_indicator.setStyleSheet("color: #0f172a; font-weight: 800; font-size: 12px;")
            if hasattr(self, 'stepper_frame'):
                self.stepper_frame.setStyleSheet("background-color: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 10px; padding: 4px;")
            self.btn_prev.setStyleSheet("background-color: #ffffff; color: #0f172a; border: 1px solid #cbd5e1; font-weight: 700; padding: 8px 16px; border-radius: 6px;")
            self.btn_next.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1d4ed8, stop:1 #2563eb); color: #ffffff; font-weight: 800; padding: 8px 20px; border-radius: 6px; border: 1px solid #1d4ed8;")

            # Step Headers
            for h in [getattr(self, 'step1_header', None), getattr(self, 'step2_header', None), getattr(self, 'step3_header', None), getattr(self, 'step4_header', None), getattr(self, 'step5_header', None)]:
                if h:
                    h.setStyleSheet("font-size: 15px; font-weight: 800; color: #0f172a;")

            # Step 1 Genre Buttons (Sleek Studio Cards in Light Mode)
            if hasattr(self, 'genre_buttons'):
                for b in self.genre_buttons:
                    b.setStyleSheet("""
                        QPushButton {
                            background-color: #ffffff;
                            border: 1px solid #cbd5e1;
                            border-radius: 8px;
                            padding: 9px 12px;
                            text-align: left;
                            font-size: 11.5px;
                            color: #0f172a;
                        }
                        QPushButton:hover {
                            border-color: #2563eb;
                            background-color: #eff6ff;
                        }
                        QPushButton:checked {
                            border: 2px solid #2563eb;
                            background-color: #eff6ff;
                            font-weight: 800;
                            color: #1d4ed8;
                        }
                    """)

            if hasattr(self, 'lbl_story_seeds'):
                self.lbl_story_seeds.setStyleSheet("font-size: 11px; font-weight: 700; color: #1e293b;")
            if hasattr(self, 'seed_buttons'):
                for b in self.seed_buttons:
                    b.setStyleSheet("background: #ffffff; color: #0f172a; border: 1px solid #cbd5e1; padding: 4px 8px; border-radius: 5px; font-size: 10.5px; font-weight: 700;")
            if hasattr(self, 'input_theme'):
                self.input_theme.setStyleSheet("background: #ffffff; color: #0f172a; padding: 7px 10px; font-size: 12px; border: 1px solid #cbd5e1; border-radius: 6px;")
            if hasattr(self, 'combo_mood'):
                self.combo_mood.setStyleSheet("background: #ffffff; color: #0f172a; padding: 6px; font-size: 11.5px; border: 1px solid #cbd5e1; border-radius: 6px;")
            if hasattr(self, 'combo_lang'):
                self.combo_lang.setStyleSheet("background: #ffffff; color: #0f172a; padding: 6px; font-size: 11.5px; border: 1px solid #cbd5e1; border-radius: 6px;")
            for w_cb in [getattr(self, 'combo_w_vocal', None), getattr(self, 'combo_w_pov', None), getattr(self, 'combo_w_hook_style', None)]:
                if w_cb:
                    w_cb.setStyleSheet("background: #ffffff; color: #0f172a; padding: 5px 6px; font-size: 11px; border: 1px solid #cbd5e1; border-radius: 6px;")
            for w_lbl in [getattr(self, 'lbl_w_vocal_tag', None), getattr(self, 'lbl_w_pov_tag', None), getattr(self, 'lbl_w_title_tag', None), getattr(self, 'lbl_w_hook_tag', None)]:
                if w_lbl:
                    w_lbl.setStyleSheet("font-size: 11px; font-weight: 700; color: #1e293b;")
            if hasattr(self, 'input_song_title'):
                self.input_song_title.setStyleSheet("background: #ffffff; color: #0f172a; padding: 5px 8px; font-size: 11.5px; font-weight: 700; border: 1px solid #cbd5e1; border-radius: 6px;")
            if hasattr(self, 'btn_w_roll_hook'):
                self.btn_w_roll_hook.setStyleSheet("background: #eff6ff; color: #1d4ed8; border: 1px solid #93c5fd; border-radius: 6px; padding: 5px 10px; font-size: 11px; font-weight: 700;")
            if hasattr(self, 'btn_w_surprise'):
                self.btn_w_surprise.setStyleSheet("background: #f5f3ff; color: #7c3aed; border: 1px solid #c4b5fd; border-radius: 6px; padding: 5px 10px; font-size: 11px; font-weight: 700;")
            if hasattr(self, 'txt_w_step3_style'):
                self.txt_w_step3_style.setStyleSheet("background: #ffffff; color: #0f172a; border: 1px solid #cbd5e1; border-radius: 5px; padding: 4px 8px; font-size: 10.5px;")

            # Step 2 Group Boxes & Inputs
            gb_qss_light = """
                QGroupBox {
                    font-weight: 800;
                    color: #0f172a;
                    border: 1px solid #cbd5e1;
                    border-radius: 8px;
                    margin-top: 10px;
                    padding: 10px;
                    background-color: #ffffff;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 4px;
                    color: #2563eb;
                }
            """
            for gb in [getattr(self, 'bpm_box', None), getattr(self, 'vocal_box', None), getattr(self, 'prog_box', None), getattr(self, 'metro_box', None), getattr(self, 'voice_box', None)]:
                if gb:
                    gb.setStyleSheet(gb_qss_light)

            if hasattr(self, 'lbl_bpm_display'):
                self.lbl_bpm_display.setStyleSheet("font-weight: 800; color: #2563eb; font-size: 12.5px;")
            if hasattr(self, 'combo_w_groove'):
                self.combo_w_groove.setStyleSheet("padding: 4px 8px; font-size: 11px; font-weight: 700; min-width: 170px; background: #ffffff; color: #0f172a; border: 1px solid #cbd5e1;")
            if hasattr(self, 'btn_w_stop_groove'):
                self.btn_w_stop_groove.setStyleSheet("background: #ffffff; color: #334155; font-weight: 700; font-size: 10.5px; padding: 4px 8px; border-radius: 4px; border: 1px solid #cbd5e1;")
            if hasattr(self, 'bpm_preset_btns'):
                for b in self.bpm_preset_btns:
                    b.setStyleSheet("background: #f1f5f9; color: #0f172a; border: 1px solid #cbd5e1; padding: 5px 8px; border-radius: 5px; font-size: 11px; font-weight: 700;")
            if hasattr(self, 'combo_vocal'):
                self.combo_vocal.setStyleSheet("padding: 6px; font-size: 11.5px; border: 1px solid #cbd5e1; border-radius: 6px; background: #ffffff; color: #0f172a;")
            if hasattr(self, 'lbl_vocal_info'):
                self.lbl_vocal_info.setStyleSheet("color: #334155; font-size: 11px; font-weight: 600;")
            if hasattr(self, 'combo_chords'):
                self.combo_chords.setStyleSheet("padding: 6px; font-size: 11.5px; border: 1px solid #cbd5e1; border-radius: 6px; background: #ffffff; color: #0f172a;")
            if hasattr(self, 'lbl_chord_preview'):
                self.lbl_chord_preview.setStyleSheet("font-weight: 800; color: #2563eb; background: #eff6ff; border: 1px solid #bfdbfe; padding: 6px 10px; border-radius: 6px;")
            if hasattr(self, 'btn_w_play_chords'):
                self.btn_w_play_chords.setStyleSheet("background-color: #eff6ff; color: #2563eb; font-weight: 800; border: 1px solid #93c5fd; border-radius: 6px; padding: 6px 12px;")
            if hasattr(self, 'btn_w_stop_chords'):
                self.btn_w_stop_chords.setStyleSheet("background-color: #ffffff; color: #334155; font-weight: 700; border: 1px solid #cbd5e1; border-radius: 6px; padding: 6px 10px;")

            # Step 3
            if hasattr(self, 'action_card'):
                self.action_card.setStyleSheet("background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 10px;")
            if hasattr(self, 'lbl_gen_summary'):
                self.lbl_gen_summary.setStyleSheet("font-weight: 800; color: #1d4ed8; font-size: 11px;")
            if hasattr(self, 'combo_w_structure'):
                self.combo_w_structure.setStyleSheet("padding: 4px; font-size: 11px; background: #ffffff; color: #0f172a; border: 1px solid #cbd5e1;")
            if hasattr(self, 'card_hit_capsule'):
                self.card_hit_capsule.setStyleSheet("background: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 10px;")
            if hasattr(self, 'lbl_step3_preview'):
                self.lbl_step3_preview.setStyleSheet("color: #0f172a; font-weight: 800; font-size: 12px;")
            if hasattr(self, 'btn_w_copy_lyrics'):
                self.btn_w_copy_lyrics.setStyleSheet("background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; font-weight: 800; font-size: 10.5px; padding: 3px 8px; border-radius: 4px;")
            if hasattr(self, 'btn_w_load_template'):
                self.btn_w_load_template.setStyleSheet("background: #eff6ff; color: #1d4ed8; border: 1px solid #93c5fd; font-weight: 800; font-size: 10.5px; padding: 3px 8px; border-radius: 4px;")
            if hasattr(self, 'btn_w_insert_hook'):
                self.btn_w_insert_hook.setStyleSheet("background: #f0fdf4; color: #15803d; border: 1px solid #86efac; font-weight: 800; font-size: 10.5px; padding: 3px 8px; border-radius: 4px;")
            if hasattr(self, 'btn_w_clean_tags'):
                self.btn_w_clean_tags.setStyleSheet("background: #f1f5f9; color: #0f172a; border: 1px solid #cbd5e1; font-weight: 700; font-size: 10.5px; padding: 3px 8px; border-radius: 4px;")
            if hasattr(self, 'txt_preview'):
                self.txt_preview.setStyleSheet("background: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 10px; font-size: 12px; color: #0f172a;")

            # Step 4
            if hasattr(self, 'txt_teleprompter'):
                self.txt_teleprompter.setStyleSheet("background: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 12px; line-height: 1.6; font-size: 13px; color: #0f172a;")
            if hasattr(self, 'lbl_m_info'):
                self.lbl_m_info.setStyleSheet("color: #334155; font-size: 11px; font-weight: 600;")
            if hasattr(self, 'btn_w_metro'):
                self.btn_w_metro.setStyleSheet("background: #eff6ff; color: #2563eb; font-weight: 800; padding: 7px 12px; border-radius: 6px; border: 1px solid #93c5fd;")
            if hasattr(self, 'v_desc'):
                self.v_desc.setStyleSheet("color: #334155; font-size: 11px; font-weight: 600;")
            if hasattr(self, 'btn_w_record'):
                self.btn_w_record.setStyleSheet("background-color: #fee2e2; color: #dc2626; font-weight: 800; border: 1px solid #fca5a5; border-radius: 6px; padding: 9px;")
            if hasattr(self, 'btn_w_play_rec'):
                self.btn_w_play_rec.setStyleSheet("background: #ffffff; color: #0f172a; font-weight: 700; padding: 9px; border-radius: 6px; border: 1px solid #cbd5e1;")
            if hasattr(self, 'lbl_w_rec_status'):
                self.lbl_w_rec_status.setStyleSheet("color: #475569; font-size: 11px; font-style: italic; font-weight: 600;")

            # Step 5
            if hasattr(self, 'suno_card'):
                self.suno_card.setStyleSheet("background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 10px;")
            if hasattr(self, 'txt_suno_style'):
                self.txt_suno_style.setStyleSheet("background: #ffffff; border: 1px solid #cbd5e1; border-radius: 5px; padding: 6px; font-size: 11px; color: #0f172a;")
            if hasattr(self, 'bundle_card'):
                self.bundle_card.setStyleSheet("background: #f0fdf4; border: 2px solid #86efac; border-radius: 10px; padding: 12px;")
            if hasattr(self, 'lbl_b_title'):
                self.lbl_b_title.setStyleSheet("font-size: 13.5px; font-weight: 800; color: #166534;")
            for btn_ex in [getattr(self, 'btn_ex_srt', None), getattr(self, 'btn_ex_lrc', None), getattr(self, 'btn_ex_txt', None), getattr(self, 'btn_ex_cho', None), getattr(self, 'btn_ex_html', None)]:
                if btn_ex:
                    btn_ex.setStyleSheet("background: #ffffff; color: #166534; border: 1px solid #86efac; font-weight: 700; font-size: 11px; padding: 8px; border-radius: 6px;")
            if hasattr(self, 'lbl_step5_more'):
                self.lbl_step5_more.setStyleSheet("color: #0f172a; font-weight: 800; font-size: 11.5px;")
            if hasattr(self, 'btn_open_full'):
                self.btn_open_full.setStyleSheet("background: #eff6ff; color: #1d4ed8; font-weight: 800; border: 1px solid #93c5fd; padding: 10px; border-radius: 8px;")
            if hasattr(self, 'btn_w_batch'):
                self.btn_w_batch.setStyleSheet("background: #f8fafc; color: #2563eb; font-weight: 800; border: 1px solid #cbd5e1; padding: 10px; border-radius: 8px;")

        self._update_stepper()


    # --- Navigation Logic ---
    def _go_next(self):
        if self.current_step < 4:
            self._jump_to_step(self.current_step + 1)
        else:
            # Step 5 next goes to full editor workbench
            self.open_editor_requested.emit()

    def _go_prev(self):
        if self.current_step > 0:
            self._jump_to_step(self.current_step - 1)
