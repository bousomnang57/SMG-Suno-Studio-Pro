"""
Right Sidebar: Songwriter's Toolset.
Includes Rhyme & Flow Lab, Suno/Udio Music Prompt Generator,
Vocal Cadence Audio Player (TTS Auditioning), and Chord Studio & Transposer.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QTabWidget, QComboBox, QSlider,
    QProgressBar, QFrame, QApplication, QGroupBox, QFileDialog,
    QMessageBox, QScrollArea, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from app.tts_player import VocalPlayer
from app.chord_engine import CHORD_PROGRESSIONS, VOCAL_RANGES, ChordEngine
from app.midi_exporter import MidiExporter
from app.sensory_thesaurus import SENSORY_CATEGORIES
from app.melody_recorder import MelodyRecorder

class ToolsPanel(QWidget):
    rhyme_requested = pyqtSignal(str) # word
    suno_prompt_requested = pyqtSignal()
    insert_text_requested = pyqtSignal(str)
    transpose_requested = pyqtSignal(int) # semitones

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_dark = False
        self.vocal_player = VocalPlayer()
        self.melody_recorder = MelodyRecorder(self)
        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)

        self.tabs = QTabWidget()
        self.tabs.setUsesScrollButtons(False)

        # Tab 1: Rhyme & Flow
        self.tab_rhymes = self._create_rhyme_tab()
        self.tabs.addTab(self.tab_rhymes, "🎯 Rhyme")

        # Tab 2: Suno / Udio Prompter
        self.tab_suno = self._create_suno_tab()
        self.tabs.addTab(self.tab_suno, "⚡ Suno")

        # Tab 3: Chords & Key Transposer
        self.tab_chords = self._create_chord_tab()
        self.tabs.addTab(self.tab_chords, "🎹 Chords")

        # Tab 4: Sensory Imagery Thesaurus (MasterWriter)
        self.tab_sensory = self._create_sensory_tab()
        self.tabs.addTab(self.tab_sensory, "🌟 Sense")

        # Tab 5: Vocal Cadence Preview
        self.tab_vocal = self._create_vocal_tab()
        self.tabs.addTab(self.tab_vocal, "🎙️ Vocal")

        layout.addWidget(self.tabs)

    def _create_chord_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        # Transpose Section
        trans_box = QGroupBox("1. Semitone Transposition")
        t_layout = QVBoxLayout(trans_box)
        t_layout.setSpacing(6)

        t_lbl = QLabel("Transpose embedded chord markers in lyrics:")
        t_lbl.setStyleSheet("color: #64748b; font-size: 11px;")
        t_layout.addWidget(t_lbl)

        btn_row = QHBoxLayout()
        btn_down = QPushButton("♭ Transpose -1")
        btn_down.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_down.clicked.connect(lambda: self.transpose_requested.emit(-1))

        btn_up = QPushButton("♯ Transpose +1")
        btn_up.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_up.clicked.connect(lambda: self.transpose_requested.emit(1))

        btn_row.addWidget(btn_down)
        btn_row.addWidget(btn_up)
        t_layout.addLayout(btn_row)
        layout.addWidget(trans_box)

        # Progression Presets Section
        prog_box = QGroupBox("2. Musical Progression Formulas & Audio Synth")
        p_layout = QVBoxLayout(prog_box)
        p_layout.setSpacing(6)

        self.prog_combo = QComboBox()
        self.prog_combo.addItems(list(CHORD_PROGRESSIONS.keys()))
        self.prog_combo.currentTextChanged.connect(self._on_progression_changed)
        p_layout.addWidget(self.prog_combo)

        self.prog_desc = QLabel("Progression details will appear here.")
        self.prog_desc.setStyleSheet("color: #64748b; font-size: 11px;")
        self.prog_desc.setWordWrap(True)
        p_layout.addWidget(self.prog_desc)

        # Audio Synth Player controls
        audio_btn_row = QHBoxLayout()
        self.btn_play_synth = QPushButton("▶ Audition Progression (Synth)")
        self.btn_play_synth.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_play_synth.setStyleSheet("background-color: #eff6ff; color: #1d4ed8; font-weight: 700; border: 1px solid #bfdbfe; border-radius: 6px; padding: 6px;")
        self.btn_play_synth.clicked.connect(self._play_current_progression)

        self.btn_stop_synth = QPushButton("⏹ Stop")
        self.btn_stop_synth.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_stop_synth.setStyleSheet("background-color: #f1f5f9; color: #475569; font-weight: 600; border: 1px solid #cbd5e1; border-radius: 6px; padding: 6px;")
        self.btn_stop_synth.clicked.connect(self._stop_current_progression)

        audio_btn_row.addWidget(self.btn_play_synth)
        audio_btn_row.addWidget(self.btn_stop_synth)
        p_layout.addLayout(audio_btn_row)

        # Clickable chord buttons row
        self.chord_buttons_container = QWidget()
        self.chord_buttons_layout = QHBoxLayout(self.chord_buttons_container)
        self.chord_buttons_layout.setContentsMargins(0, 4, 0, 4)
        self.chord_buttons_layout.setSpacing(6)
        p_layout.addWidget(self.chord_buttons_container)

        self.prog_chords = QLabel("Chords: [C] - [G] - [Am] - [F]")
        self.prog_chords.setStyleSheet("font-weight: 700; color: #2563eb; font-size: 13px; background: #eff6ff; padding: 6px; border-radius: 6px;")
        p_layout.addWidget(self.prog_chords)

        btn_insert_prog = QPushButton("📋 Insert Chords at Cursor")
        btn_insert_prog.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_insert_prog.clicked.connect(self._insert_selected_chords)
        p_layout.addWidget(btn_insert_prog)

        self.btn_export_midi = QPushButton("💾 Export Progression as .MID (DAW Ready)")
        self.btn_export_midi.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_export_midi.setStyleSheet("background-color: #f0fdf4; color: #166534; font-weight: 700; border: 1px solid #bbf7d0; border-radius: 6px; padding: 6px;")
        self.btn_export_midi.clicked.connect(self._on_export_midi)
        p_layout.addWidget(self.btn_export_midi)

        self.btn_open_soundboard = QPushButton("🎹 Open Interactive Chord Soundboard")
        self.btn_open_soundboard.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open_soundboard.setStyleSheet("background-color: #fdf4ff; color: #86198f; font-weight: 700; border: 1px solid #f0abfc; border-radius: 6px; padding: 7px;")
        self.btn_open_soundboard.clicked.connect(self._open_chord_soundboard_dialog)
        p_layout.addWidget(self.btn_open_soundboard)
        layout.addWidget(prog_box)

        # Vocal Range Recommender
        vocal_box = QGroupBox("3. Vocal Range & Key Finder")
        v_layout = QVBoxLayout(vocal_box)
        v_layout.setSpacing(6)

        self.vocal_range_combo = QComboBox()
        self.vocal_range_combo.addItems(list(VOCAL_RANGES.keys()))
        self.vocal_range_combo.currentTextChanged.connect(self._on_vocal_range_changed)
        v_layout.addWidget(self.vocal_range_combo)

        self.vocal_range_info = QLabel("Vocal range details will show here.")
        self.vocal_range_info.setStyleSheet("color: #475569; font-size: 11px;")
        self.vocal_range_info.setWordWrap(True)
        v_layout.addWidget(self.vocal_range_info)

        layout.addWidget(vocal_box)

        layout.addStretch()

        # Trigger initial population
        self._on_progression_changed(self.prog_combo.currentText())
        self._on_vocal_range_changed(self.vocal_range_combo.currentText())
        return widget

    def _play_current_progression(self):
        from app.chord_engine import AudioChordSynthesizer
        name = self.prog_combo.currentText()
        info = CHORD_PROGRESSIONS.get(name)
        if info:
            chords = info.get("chords_in_c", ["C", "G", "Am", "F"])
            AudioChordSynthesizer.play_progression(chords, bpm=120)

    def _stop_current_progression(self):
        from app.chord_engine import AudioChordSynthesizer
        AudioChordSynthesizer.stop()

    def _on_export_midi(self):
        name = self.prog_combo.currentText()
        info = CHORD_PROGRESSIONS.get(name)
        if not info:
            return
        chords = info.get("chords_in_c", ["C", "G", "Am", "F"])
        clean_name = "".join(c for c in name if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
        default_file = f"{clean_name}.mid"

        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export MIDI Chord Progression",
            default_file,
            "MIDI Files (*.mid)"
        )
        if filepath:
            try:
                MidiExporter.export_chord_progression(
                    filepath=filepath,
                    progression_name=name,
                    chords=chords,
                    bpm=120,
                    beats_per_chord=4
                )
                QMessageBox.information(
                    self,
                    "MIDI Exported Successfully",
                    f"MIDI Progression saved to:\n{filepath}\n\nYou can drag this file directly into FL Studio, Ableton Live, Logic Pro, or Cubase!"
                )
            except Exception as e:
                QMessageBox.warning(self, "Export Error", f"Failed to export MIDI: {e}")

    def _create_sensory_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        layout.addWidget(QLabel("Sensory & Imagery Thesaurus:"))
        desc = QLabel("Click any sensory word or metaphor to drop it straight into your lyrics:")
        desc.setStyleSheet("color: #64748b; font-size: 11px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        self.sensory_category_combo = QComboBox()
        self.sensory_category_combo.addItems(list(SENSORY_CATEGORIES.keys()))
        self.sensory_category_combo.currentTextChanged.connect(self._on_sensory_category_changed)
        layout.addWidget(self.sensory_category_combo)

        self.sensory_desc = QLabel()
        self.sensory_desc.setStyleSheet("color: #475569; font-size: 11px; font-style: italic;")
        self.sensory_desc.setWordWrap(True)
        layout.addWidget(self.sensory_desc)

        self.sensory_scroll = QScrollArea()
        self.sensory_scroll.setWidgetResizable(True)
        self.sensory_scroll.setStyleSheet("background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;")

        self.sensory_content_widget = QWidget()
        self.sensory_content_layout = QVBoxLayout(self.sensory_content_widget)
        self.sensory_content_layout.setContentsMargins(8, 8, 8, 8)
        self.sensory_content_layout.setSpacing(10)
        self.sensory_scroll.setWidget(self.sensory_content_widget)
        layout.addWidget(self.sensory_scroll, stretch=1)

        self._on_sensory_category_changed(self.sensory_category_combo.currentText())
        return widget

    def _on_sensory_category_changed(self, name: str):
        while self.sensory_content_layout.count():
            item = self.sensory_content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    sub = item.layout().takeAt(0)
                    if sub.widget():
                        sub.widget().deleteLater()

        info = SENSORY_CATEGORIES.get(name)
        if not info:
            return

        self.sensory_desc.setText(info.get("description", ""))

        # English Words Header & Grid
        lbl_en = QLabel("English Poetic Words:")
        lbl_en.setStyleSheet("font-weight: 700; color: #f1f5f9; font-size: 12px;" if self.is_dark else "font-weight: 700; color: #1e293b; font-size: 12px;")
        self.sensory_content_layout.addWidget(lbl_en)

        btn_en_style = """
            QPushButton {
                background-color: #111526;
                color: #e2e8f0;
                border: 1px solid #283256;
                border-radius: 6px;
                padding: 5px 8px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #1e2544;
                border-color: #6366f1;
                color: #ffffff;
            }
        """ if self.is_dark else """
            QPushButton {
                background-color: #ffffff;
                color: #334155;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 5px 8px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #eff6ff;
                border-color: #3b82f6;
                color: #1d4ed8;
            }
        """

        grid_en = QGridLayout()
        grid_en.setSpacing(4)
        for i, word in enumerate(info.get("words_en", [])):
            btn = QPushButton(word)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(btn_en_style)
            btn.clicked.connect(lambda _, w=word: self.insert_text_requested.emit(f" {w} "))
            grid_en.addWidget(btn, i // 2, i % 2)
        self.sensory_content_layout.addLayout(grid_en)

        # Khmer Words Header & Grid
        lbl_km = QLabel("ពាក្យ និងឃ្លារូបារម្មណ៍ខ្មែរ:")
        lbl_km.setStyleSheet("font-weight: 700; color: #5eead4; font-size: 12px; margin-top: 8px;" if self.is_dark else "font-weight: 700; color: #1e293b; font-size: 12px; margin-top: 8px;")
        self.sensory_content_layout.addWidget(lbl_km)

        btn_km_style = """
            QPushButton {
                background-color: #042f2e;
                color: #5eead4;
                border: 1px solid #115e59;
                border-radius: 6px;
                padding: 5px 8px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #134e4a;
                color: #ffffff;
                border-color: #2dd4bf;
            }
        """ if self.is_dark else """
            QPushButton {
                background-color: #ffffff;
                color: #0f766e;
                border: 1px solid #99f6e4;
                border-radius: 6px;
                padding: 5px 8px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #ccfbf1;
                border-color: #0d9488;
            }
        """

        grid_km = QGridLayout()
        grid_km.setSpacing(4)
        for i, word in enumerate(info.get("words_km", [])):
            btn = QPushButton(word)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(btn_km_style)
            btn.clicked.connect(lambda _, w=word: self.insert_text_requested.emit(f" {w} "))
            grid_km.addWidget(btn, i // 2, i % 2)
        self.sensory_content_layout.addLayout(grid_km)
        self.sensory_content_layout.addStretch()

    def _on_progression_changed(self, name: str):
        from app.chord_engine import AudioChordSynthesizer
        info = CHORD_PROGRESSIONS.get(name)
        if info:
            self.prog_desc.setText(f"{info.get('description')} ({info.get('mood')})")
            chords = info.get("chords_in_c", [])
            chord_str = " - ".join(f"[{c}]" for c in chords)
            self.prog_chords.setText(f"Chords (in C): {chord_str}")

            # Rebuild clickable chord pills
            while self.chord_buttons_layout.count():
                item = self.chord_buttons_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            chord_pill_style = """
                QPushButton {
                    background-color: #111526;
                    color: #38bdf8;
                    font-weight: 700;
                    font-size: 11px;
                    border: 1px solid #283256;
                    border-radius: 6px;
                    padding: 4px 8px;
                }
                QPushButton:hover {
                    background-color: #16203c;
                    border-color: #0284c7;
                    color: #ffffff;
                }
            """ if self.is_dark else """
                QPushButton {
                    background-color: #ffffff;
                    color: #2563eb;
                    font-weight: 700;
                    font-size: 11px;
                    border: 1px solid #bfdbfe;
                    border-radius: 6px;
                    padding: 4px 8px;
                }
                QPushButton:hover {
                    background-color: #eff6ff;
                    border-color: #3b82f6;
                }
            """
            for chord in chords:
                c_btn = QPushButton(f"🔊 {chord}")
                c_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                c_btn.setToolTip(f"Click to audition chord {chord} on piano")
                c_btn.setStyleSheet(chord_pill_style)
                c_btn.clicked.connect(lambda _, ch=chord: AudioChordSynthesizer.play_chord(ch))
                self.chord_buttons_layout.addWidget(c_btn)

    def _insert_selected_chords(self):
        name = self.prog_combo.currentText()
        info = CHORD_PROGRESSIONS.get(name)
        if info:
            chord_str = " ".join(f"[{c}]" for c in info.get("chords_in_c", []))
            self.insert_text_requested.emit(f"\n{chord_str}\n")

    def _on_vocal_range_changed(self, name: str):
        info = VOCAL_RANGES.get(name)
        if info:
            keys = ", ".join(info.get("recommended_keys", []))
            artists = info.get("artists", "")
            self.vocal_range_info.setText(f"Range: {info.get('range')}\nRecommended Keys: {keys}\nNotable Artists: {artists}")

    def _create_rhyme_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        layout.addWidget(QLabel("Find Rhymes, Slants & Flow:"))
        input_row = QHBoxLayout()
        self.rhyme_input = QLineEdit()
        self.rhyme_input.setPlaceholderText("Enter word (e.g. night, ocean, fire)...")
        self.rhyme_input.returnPressed.connect(self._on_find_rhymes)
        input_row.addWidget(self.rhyme_input)

        self.btn_find_rhyme = QPushButton("Search")
        self.btn_find_rhyme.setObjectName("accentButton")
        self.btn_find_rhyme.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_find_rhyme.clicked.connect(self._on_find_rhymes)
        input_row.addWidget(self.btn_find_rhyme)
        layout.addLayout(input_row)

        self.rhyme_output = QTextEdit()
        self.rhyme_output.setReadOnly(True)
        self.rhyme_output.setPlaceholderText("Rhyme results categorized into Perfect, Slant, and Multi-syllabic will appear here...")
        layout.addWidget(self.rhyme_output)

        rhyme_btn_row = QHBoxLayout()
        self.btn_insert_rhyme = QPushButton("✏️ Insert at Cursor")
        self.btn_insert_rhyme.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_insert_rhyme.setToolTip("Insert selected rhyme word directly at editor cursor")
        self.btn_insert_rhyme.setStyleSheet("font-weight: 700; font-size: 8.5pt; padding: 4px 6px;")
        self.btn_insert_rhyme.clicked.connect(self._insert_rhyme_selection)
        rhyme_btn_row.addWidget(self.btn_insert_rhyme)

        self.btn_copy_rhyme = QPushButton("📋 Copy Rhyme")
        self.btn_copy_rhyme.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_copy_rhyme.setToolTip("Copy selected rhyme word to clipboard")
        self.btn_copy_rhyme.setStyleSheet("font-weight: 700; font-size: 8.5pt; padding: 4px 6px;")
        self.btn_copy_rhyme.clicked.connect(self._copy_rhyme_selection)
        rhyme_btn_row.addWidget(self.btn_copy_rhyme)

        layout.addLayout(rhyme_btn_row)

        return widget

    def _create_suno_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        layout.addWidget(QLabel("Generate AI Music Engine Prompts:"))

        # Target Engine Mode Selector
        engine_row = QHBoxLayout()
        engine_row.addWidget(QLabel("Target Engine:"))
        self.combo_suno_engine = QComboBox()
        self.combo_suno_engine.addItems(["Suno AI v3.5 (200 Chars)", "Suno AI v3 (120 Chars)", "Udio AI v1.5 (350 Chars)"])
        self.combo_suno_engine.currentIndexChanged.connect(self._on_suno_engine_changed)
        engine_row.addWidget(self.combo_suno_engine)
        layout.addLayout(engine_row)

        desc = QLabel("Generates optimized style tags, BPM, and vocal cues formatted for Suno & Udio.")
        desc.setStyleSheet("color: #64748b; font-size: 11px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        self.btn_gen_suno = QPushButton("⚡ Generate Suno / Udio Prompt")
        self.btn_gen_suno.setObjectName("primaryGenerateButton")
        self.btn_gen_suno.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_gen_suno.clicked.connect(lambda: self.suno_prompt_requested.emit())
        layout.addWidget(self.btn_gen_suno)

        # Output Box with Live Character Gauge
        gauge_row = QHBoxLayout()
        gauge_row.addWidget(QLabel("Generated Style Prompt:"))
        gauge_row.addStretch()
        self.lbl_suno_chars = QLabel("0 / 200 chars")
        self.lbl_suno_chars.setStyleSheet("font-size: 11px; font-weight: 700; color: #059669; background: #ecfdf5; padding: 2px 6px; border-radius: 4px;")
        gauge_row.addWidget(self.lbl_suno_chars)
        layout.addLayout(gauge_row)

        self.suno_output = QTextEdit()
        self.suno_output.setReadOnly(False) # Allow editing
        self.suno_output.textChanged.connect(self._update_suno_gauge)
        self.suno_output.setPlaceholderText("AI music prompt, style tags, and instrumental direction will generate here...")
        layout.addWidget(self.suno_output)

        btn_copy_suno = QPushButton("📋 Copy Style Tags to Clipboard")
        btn_copy_suno.setObjectName("accentButton")
        btn_copy_suno.clicked.connect(self._copy_suno_text)
        layout.addWidget(btn_copy_suno)

        return widget

    def _on_suno_engine_changed(self, idx: int):
        self._update_suno_gauge()

    def _update_suno_gauge(self):
        text = self.suno_output.toPlainText().strip()
        cnt = len(text)
        idx = getattr(self, "combo_suno_engine", None)
        limit = 200
        if idx:
            engine_text = self.combo_suno_engine.currentText()
            if "120" in engine_text:
                limit = 120
            elif "350" in engine_text:
                limit = 350

        self.lbl_suno_chars.setText(f"{cnt} / {limit} chars")
        if cnt > limit:
            self.lbl_suno_chars.setStyleSheet("font-size: 11px; font-weight: 700; color: #dc2626; background: #fee2e2; padding: 2px 6px; border-radius: 4px;")
        elif cnt > limit * 0.85:
            self.lbl_suno_chars.setStyleSheet("font-size: 11px; font-weight: 700; color: #d97706; background: #fef3c7; padding: 2px 6px; border-radius: 4px;")
        else:
            self.lbl_suno_chars.setStyleSheet("font-size: 11px; font-weight: 700; color: #059669; background: #ecfdf5; padding: 2px 6px; border-radius: 4px;")

    def _create_vocal_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        layout.addWidget(QLabel("Vocal Cadence Audition (Text-To-Speech):"))
        desc = QLabel("Audition lyrical cadence and syllable flow out loud to check rhythm before recording.")
        desc.setStyleSheet("color: #64748b; font-size: 11px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Voice selection
        layout.addWidget(QLabel("Audition Voice:"))
        self.voice_combo = QComboBox()
        voices = self.vocal_player.get_available_voices()
        self.voice_combo.addItems(voices)
        layout.addWidget(self.voice_combo)

        # Cadence Rate Slider
        layout.addWidget(QLabel("Speech Tempo / Cadence:"))
        rate_row = QHBoxLayout()
        self.rate_slider = QSlider(Qt.Orientation.Horizontal)
        self.rate_slider.setRange(-5, 5)
        self.rate_slider.setValue(0)
        self.rate_label = QLabel("Normal")
        self.rate_label.setStyleSheet("color: #2563eb; font-weight: 600; min-width: 45px;")
        self.rate_slider.valueChanged.connect(self._on_rate_slider_changed)
        rate_row.addWidget(self.rate_slider)
        rate_row.addWidget(self.rate_label)
        layout.addLayout(rate_row)

        # Playback controls
        btn_row = QHBoxLayout()
        self.btn_play = QPushButton("▶ Audition Lyrics")
        self.btn_play.setObjectName("primaryGenerateButton")
        self.btn_play.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_pause = QPushButton("⏸ Pause")
        self.btn_stop = QPushButton("⏹ Stop")

        btn_row.addWidget(self.btn_play)
        btn_row.addWidget(self.btn_pause)
        btn_row.addWidget(self.btn_stop)
        layout.addLayout(btn_row)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        layout.addWidget(self.progress_bar)

        self.vocal_status = QLabel("Ready to audition")
        self.vocal_status.setStyleSheet("color: #64748b; font-style: italic; font-size: 11px;")
        self.vocal_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.vocal_status)

        self.btn_open_scratch_vocal = QPushButton("🎤 Open Neural Scratch Vocalist Studio")
        self.btn_open_scratch_vocal.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open_scratch_vocal.setStyleSheet("background-color: #eff6ff; color: #1d4ed8; font-weight: 700; border: 1px solid #bfdbfe; border-radius: 6px; padding: 7px;")
        self.btn_open_scratch_vocal.clicked.connect(self._open_scratch_vocalist_dialog)
        layout.addWidget(self.btn_open_scratch_vocal)

        # In-App Microphone Melody Recorder Box
        rec_box = QGroupBox("🎙️ Voice Memo & Scratch Melody (Mic)")
        rec_layout = QVBoxLayout(rec_box)
        rec_layout.setSpacing(6)

        rec_desc = QLabel("Sing or hum melody ideas directly into your mic:")
        rec_desc.setStyleSheet("color: #64748b; font-size: 11px;")
        rec_layout.addWidget(rec_desc)

        rec_btn_row = QHBoxLayout()
        self.btn_mic_rec = QPushButton("🔴 Record Scratch Take")
        self.btn_mic_rec.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mic_rec.setStyleSheet("background-color: #fee2e2; color: #dc2626; font-weight: 700; border: 1px solid #fca5a5; border-radius: 6px; padding: 6px;")
        self.btn_mic_rec.clicked.connect(self._toggle_mic_recording)

        self.btn_play_take = QPushButton("▶ Play Take")
        self.btn_play_take.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_play_take.setEnabled(False)
        self.btn_play_take.clicked.connect(self._play_scratch_take)

        rec_btn_row.addWidget(self.btn_mic_rec)
        rec_btn_row.addWidget(self.btn_play_take)
        rec_layout.addLayout(rec_btn_row)

        self.lbl_rec_timer = QLabel("⏱️ Mic Idle (00:00)")
        self.lbl_rec_timer.setStyleSheet("color: #475569; font-size: 11px; font-weight: 600;")
        rec_layout.addWidget(self.lbl_rec_timer)

        self.lbl_rec_status = QLabel("Ready to record voice scratchpad")
        self.lbl_rec_status.setStyleSheet("color: #64748b; font-size: 10px; font-style: italic;")
        self.lbl_rec_status.setWordWrap(True)
        rec_layout.addWidget(self.lbl_rec_status)

        layout.addWidget(rec_box)

        layout.addStretch()
        return widget

    def _connect_signals(self):
        self.btn_play.clicked.connect(self._on_play_clicked)
        self.btn_pause.clicked.connect(self.vocal_player.pause)
        self.btn_stop.clicked.connect(self.vocal_player.stop)

        self.vocal_player.state_changed.connect(self._on_playback_state)
        self.vocal_player.progress_changed.connect(self._on_playback_progress)
        self.vocal_player.generation_finished.connect(lambda _: self.vocal_status.setText("Auditioning vocal cadence..."))
        self.vocal_player.error_occurred.connect(lambda err: self.vocal_status.setText(f"Vocal Error: {err}"))

        # Melody recorder signals
        self.melody_recorder.recording_tick.connect(self._on_rec_tick)
        self.melody_recorder.recording_stopped.connect(self._on_rec_stopped)
        self.melody_recorder.error_occurred.connect(lambda err: self.lbl_rec_status.setText(f"Mic Error: {err}"))

    def _toggle_mic_recording(self):
        if not self.melody_recorder.is_recording:
            started = self.melody_recorder.start_recording()
            if started:
                self.btn_mic_rec.setText("⏹ Stop Recording")
                self.btn_mic_rec.setStyleSheet("background-color: #dc2626; color: #ffffff; font-weight: 700; border-radius: 6px; padding: 6px;")
                self.lbl_rec_status.setText("Recording from microphone... Sing or hum melody")
                self.btn_play_take.setEnabled(False)
        else:
            self.melody_recorder.stop_recording("LyricScratch")
            self.btn_mic_rec.setText("🔴 Record Scratch Take")
            self.btn_mic_rec.setStyleSheet("background-color: #fee2e2; color: #dc2626; font-weight: 700; border: 1px solid #fca5a5; border-radius: 6px; padding: 6px;")
            self.btn_play_take.setEnabled(True)

    def _play_scratch_take(self):
        self.melody_recorder.play_last_take()
        self.lbl_rec_status.setText("Playing back recorded scratch take...")

    def _on_rec_tick(self, seconds: int):
        mins = seconds // 60
        secs = seconds % 60
        self.lbl_rec_timer.setText(f"🔴 Recording: {mins:02d}:{secs:02d}")

    def _on_rec_stopped(self, path: str):
        from pathlib import Path
        self.lbl_rec_timer.setText("⏱️ Take Saved")
        self.lbl_rec_status.setText(f"Saved: {Path(path).name}")

    def _on_find_rhymes(self):
        word = self.rhyme_input.text().strip()
        if word:
            self.rhyme_output.setText("Searching rhymes & cadences with Gemini...")
            self.rhyme_requested.emit(word)

    def set_rhyme_results(self, text: str):
        self.rhyme_output.setText(text)

    def set_suno_results(self, text: str):
        self.suno_output.setText(text)
        self._update_suno_gauge()

    def _insert_rhyme_selection(self):
        sel = self.rhyme_output.textCursor().selectedText()
        if not sel:
            sel = self.rhyme_output.toPlainText().strip()
        if sel:
            clean_word = sel.strip("•- \t\r\n:;,")
            if clean_word:
                self.insert_text_requested.emit(f" {clean_word} ")

    def _copy_rhyme_selection(self):
        sel = self.rhyme_output.textCursor().selectedText()
        if not sel:
            sel = self.rhyme_output.toPlainText()
        if sel:
            QApplication.clipboard().setText(sel)

    def _copy_suno_text(self):
        text = self.suno_output.toPlainText()
        if text:
            QApplication.clipboard().setText(text)

    def _on_rate_slider_changed(self, val: int):
        if val == 0:
            self.rate_label.setText("Normal")
        elif val > 0:
            self.rate_label.setText(f"+{val}")
        else:
            self.rate_label.setText(str(val))

    def _on_play_clicked(self):
        if hasattr(self, "get_lyrics_func") and self.get_lyrics_func:
            lyrics = self.get_lyrics_func()
            if not lyrics.strip():
                self.vocal_status.setText("No lyrics available to audition.")
                return
            self.vocal_status.setText("Synthesizing vocal cadence...")
            voice_idx = self.voice_combo.currentIndex()
            rate = self.rate_slider.value()
            self.vocal_player.synthesize_and_play(lyrics, voice_index=voice_idx, rate=rate)

    def _on_playback_state(self, is_playing: bool):
        if is_playing:
            self.btn_play.setText("▶ Playing...")
            self.vocal_status.setText("Playing vocal audition...")
        else:
            self.btn_play.setText("▶ Audition Lyrics")
            self.vocal_status.setText("Ready to audition")

    def _on_playback_progress(self, pos: int, dur: int):
        if dur > 0:
            pct = int((pos / dur) * 100)
            self.progress_bar.setValue(pct)
        else:
            self.progress_bar.setValue(0)

    def apply_theme(self, is_dark: bool):
        self.is_dark = is_dark
        if is_dark:
            self.tabs.setStyleSheet("""
                QTabBar::tab {
                    padding: 3px 4px;
                    font-size: 8pt;
                    font-weight: 700;
                    margin: 0px 1px;
                }
            """)
            self.btn_play_synth.setStyleSheet("background-color: #2e1065; color: #d8b4fe; font-weight: 700; border: 1px solid #7c3aed; border-radius: 6px; padding: 6px;")
            self.btn_stop_synth.setStyleSheet("background-color: #161b30; color: #94a3b8; font-weight: 600; border: 1px solid #283256; border-radius: 6px; padding: 6px;")
            self.prog_chords.setStyleSheet("font-weight: 700; color: #38bdf8; font-size: 13px; background: #090b14; border: 1px solid #1e2540; padding: 6px; border-radius: 6px;")
            if hasattr(self, "btn_export_midi"):
                self.btn_export_midi.setStyleSheet("background-color: #064e3b; color: #34d399; font-weight: 700; border: 1px solid #059669; border-radius: 6px; padding: 6px;")
            self.btn_mic_rec.setStyleSheet("background-color: #3b1115; color: #f87171; font-weight: 700; border: 1px solid #7f1d1d; border-radius: 6px; padding: 6px;")
            if hasattr(self, "sensory_scroll"):
                self.sensory_scroll.setStyleSheet("background: #090b14; border: 1px solid #1e2540; border-radius: 8px;")
            if hasattr(self, "lbl_suno_chars"):
                self.lbl_suno_chars.setStyleSheet("font-size: 11px; font-weight: 700; color: #38bdf8; background: #0c2d48; padding: 2px 6px; border-radius: 4px; border: 1px solid #0284c7;")
            if hasattr(self, "btn_insert_rhyme"):
                self.btn_insert_rhyme.setStyleSheet("background-color: #1e1b4b; color: #a5b4fc; font-weight: 700; border: 1px solid #4338ca; border-radius: 5px; padding: 4px 6px; font-size: 8.5pt;")
            if hasattr(self, "btn_copy_rhyme"):
                self.btn_copy_rhyme.setStyleSheet("background-color: #161b30; color: #cbd5e1; font-weight: 600; border: 1px solid #283256; border-radius: 5px; padding: 4px 6px; font-size: 8.5pt;")
        else:
            self.tabs.setStyleSheet("""
                QTabBar::tab {
                    padding: 3px 4px;
                    font-size: 8pt;
                    font-weight: 700;
                    margin: 0px 1px;
                }
            """)
            self.btn_play_synth.setStyleSheet("background-color: #eff6ff; color: #1d4ed8; font-weight: 700; border: 1px solid #bfdbfe; border-radius: 6px; padding: 6px;")
            self.btn_stop_synth.setStyleSheet("background-color: #f1f5f9; color: #475569; font-weight: 600; border: 1px solid #cbd5e1; border-radius: 6px; padding: 6px;")
            self.prog_chords.setStyleSheet("font-weight: 700; color: #2563eb; font-size: 13px; background: #eff6ff; border: 1px solid #bfdbfe; padding: 6px; border-radius: 6px;")
            if hasattr(self, "btn_export_midi"):
                self.btn_export_midi.setStyleSheet("background-color: #f0fdf4; color: #166534; font-weight: 700; border: 1px solid #bbf7d0; border-radius: 6px; padding: 6px;")
            self.btn_mic_rec.setStyleSheet("background-color: #fee2e2; color: #dc2626; font-weight: 700; border: 1px solid #fca5a5; border-radius: 6px; padding: 6px;")
            if hasattr(self, "sensory_scroll"):
                self.sensory_scroll.setStyleSheet("background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;")
            if hasattr(self, "lbl_suno_chars"):
                self.lbl_suno_chars.setStyleSheet("font-size: 11px; font-weight: 700; color: #059669; background: #ecfdf5; padding: 2px 6px; border-radius: 4px; border: 1px solid #a7f3d0;")
            if hasattr(self, "btn_insert_rhyme"):
                self.btn_insert_rhyme.setStyleSheet("background-color: #eff6ff; color: #1d4ed8; font-weight: 700; border: 1px solid #bfdbfe; border-radius: 5px; padding: 4px 6px; font-size: 8.5pt;")
            if hasattr(self, "btn_copy_rhyme"):
                self.btn_copy_rhyme.setStyleSheet("background-color: #f1f5f9; color: #475569; font-weight: 600; border: 1px solid #cbd5e1; border-radius: 5px; padding: 4px 6px; font-size: 8.5pt;")

        if hasattr(self, "prog_combo") and self.prog_combo.currentText():
            self._on_progression_changed(self.prog_combo.currentText())
        if hasattr(self, "sensory_category_combo") and self.sensory_category_combo.currentText():
            self._on_sensory_category_changed(self.sensory_category_combo.currentText())

    def _open_chord_soundboard_dialog(self):
        from app.ui.chord_soundboard_view import ChordSoundboardDialog
        lyrics = self.get_lyrics_func() if hasattr(self, "get_lyrics_func") and self.get_lyrics_func else ""
        dlg = ChordSoundboardDialog(self, is_dark=self.is_dark, initial_lyrics=lyrics)
        dlg.chord_inserted.connect(lambda c: self.insert_text_requested.emit(f" {c} "))
        dlg.exec()

    def _open_scratch_vocalist_dialog(self):
        from app.ui.scratch_vocalist_dialog import ScratchVocalistDialog
        lyrics = self.get_lyrics_func() if hasattr(self, "get_lyrics_func") and self.get_lyrics_func else ""
        dlg = ScratchVocalistDialog(self, is_dark=self.is_dark, lyrics=lyrics)
        dlg.exec()
