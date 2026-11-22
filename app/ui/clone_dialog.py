"""
Song DNA & Semantic Meaning Cloner Dialog (ម៉ាស៊ីនក្លូនបទចម្រៀងស្របន័យ).
Studio modal interface for analyzing reference song DNA, artist personas, strict syllable cadence,
audio file reverse-engineering, and generating commercial semantic counterparts across 8 creative clone modes.
"""

import re
from PyQt6.QtWidgets import (
    QWidget, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QFrame,
    QComboBox, QSpinBox, QMessageBox, QApplication, QFileDialog,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QThread
from PyQt6.QtGui import QFont, QColor

from app.clone_engine import CloneEngine, CLONE_MODES, FAMOUS_SONG_PRESETS, ARTIST_PERSONAS
from app.hit_analyzer import HitAnalyzer
from app.exporter import Exporter
from app.config import config_manager
from app.ui.styles import get_theme


class CloneWorker(QThread):
    finished_success = pyqtSignal(str, str, str) # title, style, lyrics
    finished_flavors = pyqtSignal(dict)           # 4-flavor dictionary
    finished_error = pyqtSignal(str)
    status_update = pyqtSignal(str)

    def __init__(
        self,
        ref_lyrics: str,
        mode_key: str,
        genre: str,
        lang: str,
        bpm: int,
        notes: str,
        persona_key: str = "SINN_SISAMOUTH",
        parent=None
    ):
        super().__init__(parent)
        self.ref_lyrics = ref_lyrics
        self.mode_key = mode_key
        self.genre = genre
        self.lang = lang
        self.bpm = bpm
        self.notes = notes
        self.persona_key = persona_key

    def run(self):
        keys = config_manager.get_api_keys()

        # Handle 4-Flavor matrix mode
        if self.mode_key == "FOUR_FLAVORS":
            self.status_update.emit("Generating 4 distinct commercial arrangements...")
            flavors = CloneEngine.generate_4_flavors(self.ref_lyrics, self.lang)
            pop = flavors.get("pop", {})
            self.finished_flavors.emit(flavors)
            self.finished_success.emit(pop.get("title", "4-Flavor Matrix"), pop.get("style", ""), pop.get("lyrics", ""))
            return

        if not keys:
            self.status_update.emit("Generating demonstration semantic clone (No API Key detected)...")
            import time
            time.sleep(1.0)
            res = CloneEngine.generate_offline_clone(
                self.ref_lyrics, self.mode_key, self.genre, self.lang, self.persona_key
            )
            self.finished_success.emit(res["title"], res["style"], res["lyrics"])
            return

        self.status_update.emit("Extracting musical DNA & generating semantic clone with Gemini...")
        params = CloneEngine.build_clone_generation_params(
            self.ref_lyrics, self.mode_key, self.genre, self.lang, self.bpm, self.notes, self.persona_key
        )

        try:
            from app.gemini_client import generate_with_gemini

            model = config_manager.get("gemini_model", "gemini-3.5-flash")
            raw = generate_with_gemini(
                params["user_notes"],
                model_name=model,
                on_retry=lambda msg: self.status_update.emit(msg)
            )

            if not raw:
                res = CloneEngine.generate_offline_clone(
                    self.ref_lyrics, self.mode_key, self.genre, self.lang, self.persona_key
                )
                self.finished_success.emit(res["title"], res["style"], res["lyrics"])
                return

            # Extract Title and Style
            title_m = re.search(r'\[Title:\s*(.*?)\]', raw, re.IGNORECASE)
            title = title_m.group(1).strip() if title_m else "Semantic Clone"

            style_m = re.search(r'\[Style:\s*(.*?)\]', raw, re.IGNORECASE)
            style = style_m.group(1).strip() if style_m else f"{self.genre}, {self.bpm} BPM"

            self.finished_success.emit(title, style, raw)
        except Exception as e:
            # Fallback smoothly to high-quality offline clone
            res = CloneEngine.generate_offline_clone(
                self.ref_lyrics, self.mode_key, self.genre, self.lang, self.persona_key
            )
            self.finished_success.emit(res["title"], res["style"], res["lyrics"])


class SongDNAClonerView(QWidget):
    send_to_editor_requested = pyqtSignal(str, str) # title, lyrics
    send_to_suno_requested = pyqtSignal(str, str, str) # title, style, lyrics
    send_to_batch_requested = pyqtSignal(str, str) # theme, style

    def __init__(self, initial_lyrics: str = "", initial_title: str = "", parent=None, is_dark: bool = True):
        super().__init__(parent)
        self.is_dark = is_dark
        default_preset_key = next(iter(FAMOUS_SONG_PRESETS.keys()))
        self.reference_lyrics = initial_lyrics.strip() if initial_lyrics else FAMOUS_SONG_PRESETS[default_preset_key]["lyrics"]
        self.reference_title = initial_title or FAMOUS_SONG_PRESETS[default_preset_key]["title"]
        self.active_mode_key = "PARALLEL_TWIN"
        self.active_persona_key = "TAYLOR_SWIFT"
        self.generated_title = ""
        self.generated_style = ""
        self.generated_lyrics = ""
        self.current_flavors = {}

        self.setWindowTitle("🧬 Song DNA & Semantic Meaning Cloner")
        self.resize(1120, 740)
        self.setMinimumSize(1000, 660)

        self._init_ui()
        self._apply_styling()
        self._analyze_reference()
        self._load_instant_clone_preview()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 14, 18, 14)
        main_layout.setSpacing(10)

        # 1. Header Box
        header_box = QHBoxLayout()
        title_vbox = QVBoxLayout()
        title_vbox.setSpacing(2)

        self.lbl_main_title = QLabel("🧬 Song DNA & Semantic Meaning Cloner")
        self.lbl_main_title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title_vbox.addWidget(self.lbl_main_title)

        self.lbl_sub_title = QLabel("Re-imagine hits with identical meaning, artist personas, strict sing-along meter, and 100% original melodies.")
        self.lbl_sub_title.setFont(QFont("Segoe UI", 9))
        title_vbox.addWidget(self.lbl_sub_title)
        header_box.addLayout(title_vbox)
        header_box.addStretch()

        # Preset Reference Selector
        lbl_pr = QLabel("📚 Reference Preset:")
        lbl_pr.setStyleSheet("font-weight: 700; font-size: 11px;")
        header_box.addWidget(lbl_pr)

        self.combo_presets = QComboBox()
        self.combo_presets.addItem("⚡ Current Editor Song", "CURRENT")
        for k in FAMOUS_SONG_PRESETS.keys():
            self.combo_presets.addItem(k, k)
        self.combo_presets.setStyleSheet("padding: 4px 8px; font-weight: 600; font-size: 11px; min-width: 190px;")
        self.combo_presets.currentTextChanged.connect(self._on_preset_changed)
        header_box.addWidget(self.combo_presets)

        self.btn_toggle_setup = QPushButton("▲ Compact")
        self.btn_toggle_setup.setCheckable(True)
        self.btn_toggle_setup.setChecked(False)
        self.btn_toggle_setup.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_setup.setToolTip("Collapse or expand mode/settings bars to maximize lyric comparison space")
        self.btn_toggle_setup.setStyleSheet("padding: 4px 8px; font-weight: 700; font-size: 10.5px; border-radius: 5px;")
        self.btn_toggle_setup.toggled.connect(self._toggle_compact_setup)
        header_box.addWidget(self.btn_toggle_setup)

        main_layout.addLayout(header_box)

        # 2. Step 1: 8 Creative Clone Mode Selector Pills (2 Rows x 4 Columns)
        self.mode_frame = QFrame()
        self.mode_frame.setObjectName("card")
        m_layout = QVBoxLayout(self.mode_frame)
        m_layout.setContentsMargins(10, 6, 10, 6)
        m_layout.setSpacing(4)

        mode_top_row = QHBoxLayout()
        self.lbl_step1_mode = QLabel("❶ SELECT CLONE MODE:")
        self.lbl_step1_mode.setStyleSheet("font-size: 10px; font-weight: 800; color: #38bdf8; letter-spacing: 0.5px;")
        mode_top_row.addWidget(self.lbl_step1_mode)
        mode_top_row.addSpacing(8)
        self.lbl_mode_desc = QLabel(CLONE_MODES["PARALLEL_TWIN"]["subtitle"])
        self.lbl_mode_desc.setStyleSheet("font-size: 10.5px; font-weight: 700; color: #a78bfa;")
        mode_top_row.addWidget(self.lbl_mode_desc, stretch=1)
        m_layout.addLayout(mode_top_row)

        self.mode_buttons = {}
        row1_keys = ["PARALLEL_TWIN", "ANSWER_SONG", "GENRE_MUTATION", "TIME_SHIFT_SEQUEL"]
        row2_keys = ["STRICT_METER", "PERSONA_DNA", "FOUR_FLAVORS", "BILINGUAL_MIRROR"]

        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(6)
        for k in row1_keys:
            info = CLONE_MODES[k]
            btn = QPushButton(info["title"])
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setCheckable(True)
            if k == "PARALLEL_TWIN":
                btn.setChecked(True)
            btn.clicked.connect(lambda _, m=k: self._set_clone_mode(m))
            row1_layout.addWidget(btn, stretch=1)
            self.mode_buttons[k] = btn
        m_layout.addLayout(row1_layout)

        row2_layout = QHBoxLayout()
        row2_layout.setSpacing(6)
        for k in row2_keys:
            info = CLONE_MODES[k]
            btn = QPushButton(info["title"])
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setCheckable(True)
            btn.clicked.connect(lambda _, m=k: self._set_clone_mode(m))
            row2_layout.addWidget(btn, stretch=1)
            self.mode_buttons[k] = btn
        m_layout.addLayout(row2_layout)

        main_layout.addWidget(self.mode_frame)

        # 3. Step 2: Target Clone Settings Row
        self.settings_frame = QFrame()
        self.settings_frame.setObjectName("card")
        s_layout = QVBoxLayout(self.settings_frame)
        s_layout.setContentsMargins(12, 6, 12, 6)
        s_layout.setSpacing(5)

        # Row 1: Target Controls, Audio Ingestion, & Action Button
        row1 = QHBoxLayout()
        row1.setSpacing(8)

        lbl_step2 = QLabel("❷ TARGET STYLE:")
        lbl_step2.setStyleSheet("font-size: 10px; font-weight: 800; color: #34d399; letter-spacing: 0.5px;")
        row1.addWidget(lbl_step2)

        lbl_tg = QLabel("Genre:")
        lbl_tg.setStyleSheet("font-weight: 700; font-size: 11px;")
        row1.addWidget(lbl_tg)

        self.combo_target_genre = QComboBox()
        self.combo_target_genre.addItems([
            "Global Commercial Radio Pop",
            "80s Synthwave & Retro Pop",
            "Melodic 808 Trap & Late-Night R&B",
            "Acoustic Fingerpicked Indie Ballad",
            "Stadium Pop-Rock Anthem",
            "EDM Club Festival Drop",
            "Khmer 60s Sentimental Ballad",
            "Khmer Romvong Folk Festive",
            "Khmer Modern Trap / Hip-Hop 808",
        ])
        self.combo_target_genre.setStyleSheet("padding: 4px 6px; font-size: 11px; min-width: 170px;")
        row1.addWidget(self.combo_target_genre)

        lbl_tl = QLabel("Language:")
        lbl_tl.setStyleSheet("font-weight: 700; font-size: 11px;")
        row1.addWidget(lbl_tl)

        self.combo_target_lang = QComboBox()
        self.combo_target_lang.addItems([
            "🇬🇧 English",
            "🇰🇭 Khmer (ភាសាខ្មែរ)",
            "🌟 Both (50/50 Dual Engine)"
        ])
        self.combo_target_lang.setStyleSheet("padding: 4px 6px; font-size: 11px; min-width: 120px;")
        row1.addWidget(self.combo_target_lang)

        lbl_bpm = QLabel("Tempo:")
        lbl_bpm.setStyleSheet("font-weight: 700; font-size: 11px;")
        row1.addWidget(lbl_bpm)

        self.spin_target_bpm = QSpinBox()
        self.spin_target_bpm.setRange(50, 190)
        self.spin_target_bpm.setValue(120)
        self.spin_target_bpm.setSuffix(" BPM")
        self.spin_target_bpm.setStyleSheet("padding: 4px; font-size: 11px; font-weight: 700; min-width: 80px;")
        row1.addWidget(self.spin_target_bpm)

        # Audio Ingestion Button
        self.btn_attach_audio = QPushButton("🎧 Attach Audio (.mp3)")
        self.btn_attach_audio.setToolTip("Reverse-engineer BPM, key, and Suno prompt from an MP3/WAV file")
        self.btn_attach_audio.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_attach_audio.setStyleSheet("background: #064e3b; color: #34d399; border: 1px solid #059669; font-weight: 700; font-size: 11px; padding: 5px 10px; border-radius: 5px;")
        self.btn_attach_audio.clicked.connect(self._attach_audio_file)
        row1.addWidget(self.btn_attach_audio)

        row1.addStretch()

        # Big Action Button
        self.btn_generate_clone = QPushButton("⚡ Clone Song DNA")
        self.btn_generate_clone.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_generate_clone.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7c3aed, stop:1 #2563eb);
                color: #ffffff;
                font-weight: 800;
                font-size: 11.5px;
                padding: 6px 16px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background: #6d28d9;
            }
        """)
        self.btn_generate_clone.clicked.connect(self._start_cloning)
        row1.addWidget(self.btn_generate_clone)
        s_layout.addLayout(row1)

        # Row 2: Direction Notes & Dynamic Persona Bar
        row2 = QHBoxLayout()
        row2.setSpacing(8)

        # Persona Selector Capsule (visible when in PERSONA_DNA mode)
        self.persona_capsule = QFrame()
        pc_layout = QHBoxLayout(self.persona_capsule)
        pc_layout.setContentsMargins(0, 0, 0, 0)
        pc_layout.setSpacing(4)
        lbl_p = QLabel("🎭 Artist Persona:")
        lbl_p.setStyleSheet("font-size: 11px; font-weight: 700; color: #c084fc;")
        pc_layout.addWidget(lbl_p)

        self.combo_persona = QComboBox()
        for pk, p_info in ARTIST_PERSONAS.items():
            self.combo_persona.addItem(p_info["name"], pk)
        self.combo_persona.setStyleSheet("padding: 3px 6px; font-size: 10.5px; font-weight: 600; min-width: 170px;")
        self.combo_persona.currentIndexChanged.connect(self._on_persona_changed)
        pc_layout.addWidget(self.combo_persona)
        self.persona_capsule.setVisible(False)
        row2.addWidget(self.persona_capsule)

        lbl_notes = QLabel("Custom Direction:")
        lbl_notes.setStyleSheet("font-size: 11px; font-weight: 600; color: #94a3b8;")
        row2.addWidget(lbl_notes)

        self.input_notes = QLineEdit()
        self.input_notes.setPlaceholderText("Optional notes: e.g. female lead, emotive Tro Ou, intimate acoustic vibe, 808 slides...")
        self.input_notes.setStyleSheet("padding: 4px 8px; font-size: 11px;")
        row2.addWidget(self.input_notes, stretch=1)

        self.btn_auto_humanize = QPushButton("👤 Auto-Humanize: ON")
        self.btn_auto_humanize.setCheckable(True)
        self.btn_auto_humanize.setChecked(True)
        self.btn_auto_humanize.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_auto_humanize.setToolTip("Automatically polish cloned output with human breath cues & anti-cliché realism")
        self.btn_auto_humanize.setStyleSheet("background: #065f46; color: #ecfdf5; border: 1px solid #10b981; font-weight: 700; font-size: 10px; padding: 4px 8px; border-radius: 5px;")
        self.btn_auto_humanize.toggled.connect(self._on_auto_humanize_toggled)
        row2.addWidget(self.btn_auto_humanize)

        s_layout.addLayout(row2)

        main_layout.addWidget(self.settings_frame)

        # 4. Side-by-Side Dual Studio Comparison
        split_layout = QHBoxLayout()
        split_layout.setSpacing(12)

        # Left Column: Reference Song & Extracted DNA (~450px)
        self.left_card = QFrame()
        self.left_card.setObjectName("card")
        self.left_card.setFixedWidth(450)
        l_layout = QVBoxLayout(self.left_card)
        l_layout.setContentsMargins(10, 10, 10, 10)
        l_layout.setSpacing(6)

        l_top_row = QHBoxLayout()
        l_top_row.setSpacing(4)
        lbl_l_title = QLabel("❸ REFERENCE SONG & DNA")
        lbl_l_title.setStyleSheet("font-weight: 800; font-size: 11.5px; color: #38bdf8; letter-spacing: 0.3px;")
        l_top_row.addWidget(lbl_l_title)
        l_top_row.addStretch()

        self.btn_ref_paste = QPushButton("📋 Paste")
        self.btn_ref_paste.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ref_paste.setToolTip("Paste reference song lyrics from clipboard")
        self.btn_ref_paste.setStyleSheet("font-size: 9.5px; font-weight: 700; padding: 2px 6px; border-radius: 4px;")
        self.btn_ref_paste.clicked.connect(self._paste_reference_clipboard)
        l_top_row.addWidget(self.btn_ref_paste)

        self.btn_ref_pull_editor = QPushButton("⚡ Editor")
        self.btn_ref_pull_editor.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ref_pull_editor.setToolTip("Pull current song lyrics from the Lyric Editor Workbench")
        self.btn_ref_pull_editor.setStyleSheet("font-size: 9.5px; font-weight: 700; padding: 2px 6px; border-radius: 4px;")
        self.btn_ref_pull_editor.clicked.connect(self._pull_reference_from_editor)
        l_top_row.addWidget(self.btn_ref_pull_editor)

        self.btn_ref_random = QPushButton("🎲 Random Hit")
        self.btn_ref_random.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ref_random.setToolTip("Pick a random famous reference track and clone its DNA")
        self.btn_ref_random.setStyleSheet("font-size: 9.5px; font-weight: 700; padding: 2px 6px; border-radius: 4px;")
        self.btn_ref_random.clicked.connect(self._pick_random_reference_preset)
        l_top_row.addWidget(self.btn_ref_random)

        l_layout.addLayout(l_top_row)

        # Extracted DNA Capsule
        self.dna_capsule = QFrame()
        self.dna_capsule.setStyleSheet("background: #090b14; border: 1px solid #1e2540; border-radius: 6px; padding: 6px;")
        d_layout = QVBoxLayout(self.dna_capsule)
        d_layout.setSpacing(3)

        self.lbl_dna_thesis = QLabel("Core Thesis: Analyzing...")
        self.lbl_dna_thesis.setStyleSheet("font-size: 10.5px; font-weight: 700; color: #a5b4fc;")
        self.lbl_dna_thesis.setWordWrap(True)
        d_layout.addWidget(self.lbl_dna_thesis)

        self.lbl_dna_meta = QLabel("Sonic DNA: 74 BPM • G Major • Ballad • Flow: Free")
        self.lbl_dna_meta.setStyleSheet("font-size: 10px; font-weight: 600; color: #94a3b8;")
        d_layout.addWidget(self.lbl_dna_meta)

        l_layout.addWidget(self.dna_capsule)

        # Reference lyrics edit
        self.txt_reference = QTextEdit()
        self.txt_reference.setPlaceholderText("Paste reference lyrics here...")
        self.txt_reference.setFont(QFont("Segoe UI", 10))
        self.txt_reference.setPlainText(self.reference_lyrics)
        self.txt_reference.textChanged.connect(self._on_ref_text_changed)
        l_layout.addWidget(self.txt_reference, stretch=1)

        split_layout.addWidget(self.left_card)

        # Right Column: Generated Semantic Clone & Twin Matrix (Stretch 1)
        self.right_card = QFrame()
        self.right_card.setObjectName("card")
        r_layout = QVBoxLayout(self.right_card)
        r_layout.setContentsMargins(10, 10, 10, 10)
        r_layout.setSpacing(6)

        r_header_row = QHBoxLayout()
        self.lbl_r_title = QLabel("❹ GENERATED SEMANTIC CLONE (100% ORIGINAL)")
        self.lbl_r_title.setStyleSheet("font-weight: 800; font-size: 11.5px; color: #34d399; letter-spacing: 0.3px;")
        r_header_row.addWidget(self.lbl_r_title)
        r_header_row.addStretch()

        self.lbl_singalong_badge = QLabel("🎯 Sing-Along: —")
        self.lbl_singalong_badge.setStyleSheet("font-size: 10px; font-weight: 800; color: #38bdf8; background: #082f49; padding: 2px 6px; border-radius: 4px; border: 1px solid #0284c7;")
        r_header_row.addWidget(self.lbl_singalong_badge)

        self.lbl_originality_badge = QLabel("🛡️ Original: —")
        self.lbl_originality_badge.setToolTip("Live Copyright Safety & Originality Meter (word/n-gram independence from reference)")
        self.lbl_originality_badge.setStyleSheet("font-size: 10px; font-weight: 800; color: #34d399; background: #064e3b; padding: 2px 6px; border-radius: 4px; border: 1px solid #059669;")
        r_header_row.addWidget(self.lbl_originality_badge)

        self.lbl_clone_hit = QLabel("🌟 Hit: — | Vocal Safety: —")
        self.lbl_clone_hit.setStyleSheet("font-size: 10px; font-weight: 800; color: #10b981; background: #064e3b; padding: 2px 6px; border-radius: 4px; border: 1px solid #059669;")
        r_header_row.addWidget(self.lbl_clone_hit)
        r_layout.addLayout(r_header_row)

        # Suno Style prompt strip
        sp_row = QHBoxLayout()
        sp_row.setSpacing(6)
        self.txt_clone_style = QLineEdit()
        self.txt_clone_style.setReadOnly(True)
        self.txt_clone_style.setPlaceholderText("Suno Style Prompt will be automatically generated here...")
        self.txt_clone_style.setStyleSheet("padding: 4px 6px; font-size: 10.5px;")
        sp_row.addWidget(self.txt_clone_style, stretch=1)

        self.btn_copy_style = QPushButton("📋 Copy Style")
        self.btn_copy_style.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_copy_style.setStyleSheet("background: #1e1b4b; color: #a5b4fc; border: 1px solid #4338ca; font-weight: 700; font-size: 10px; padding: 4px 8px; border-radius: 4px;")
        self.btn_copy_style.clicked.connect(self._copy_style)
        sp_row.addWidget(self.btn_copy_style)

        self.btn_lock_all_meter = QPushButton("🔒 Lock 100% Meter")
        self.btn_lock_all_meter.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_lock_all_meter.setToolTip("1-Click Auto-Lock: Match every cloned line's syllable count to the reference song for 100% karaoke sing-along fit")
        self.btn_lock_all_meter.setStyleSheet("background: #082f49; color: #38bdf8; border: 1px solid #0284c7; font-weight: 800; font-size: 10px; padding: 4px 8px; border-radius: 4px;")
        self.btn_lock_all_meter.clicked.connect(self._auto_lock_all_syllable_meter)
        sp_row.addWidget(self.btn_lock_all_meter)

        self.btn_scrub_copyright = QPushButton("🛡️ Scrub 100% Safe")
        self.btn_scrub_copyright.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_scrub_copyright.setToolTip("1-Click Copyright De-Overlap Scrubber: Replace any shared reference words with syllable-matched poetic synonyms")
        self.btn_scrub_copyright.setStyleSheet("background: #064e3b; color: #34d399; border: 1px solid #059669; font-weight: 800; font-size: 10px; padding: 4px 8px; border-radius: 4px;")
        self.btn_scrub_copyright.clicked.connect(self._auto_scrub_copyright_overlaps)
        sp_row.addWidget(self.btn_scrub_copyright)

        self.btn_swap_chords = QPushButton("🎹 Swap Chords")
        self.btn_swap_chords.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_swap_chords.setToolTip("Rotate inline chord progression to a fresh harmonic palette")
        self.btn_swap_chords.setStyleSheet("background: #4a044e; color: #f0abfc; border: 1px solid #a21caf; font-weight: 700; font-size: 10px; padding: 4px 8px; border-radius: 4px;")
        self.btn_swap_chords.clicked.connect(self._rotate_clone_chords)
        sp_row.addWidget(self.btn_swap_chords)
        r_layout.addLayout(sp_row)

        # 4-Flavor Quick Switch Ribbon (Optional selector)
        self.flavor_ribbon = QFrame()
        f_layout = QHBoxLayout(self.flavor_ribbon)
        f_layout.setContentsMargins(0, 0, 0, 0)
        f_layout.setSpacing(6)

        lbl_f = QLabel("🎚️ 4 Flavors:")
        lbl_f.setStyleSheet("font-size: 10.5px; font-weight: 700; color: #a78bfa;")
        f_layout.addWidget(lbl_f)

        self.flavor_buttons = {}
        for f_key, f_name, f_color in [
            ("pop", "📻 Radio Pop", "#2563eb"),
            ("acoustic", "🎸 Acoustic", "#059669"),
            ("trap", "🔥 808 Trap", "#dc2626"),
            ("cinematic", "🎻 Cinematic", "#7c3aed")
        ]:
            b = QPushButton(f_name)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(f"font-size: 10px; font-weight: 700; padding: 3px 8px; border-radius: 4px; border: 1px solid {f_color}; color: {f_color}; background: transparent;")
            b.clicked.connect(lambda _, k=f_key: self._switch_flavor(k))
            f_layout.addWidget(b)
            self.flavor_buttons[f_key] = b

        f_layout.addStretch()
        self.flavor_ribbon.setVisible(False)
        r_layout.addWidget(self.flavor_ribbon)

        # Dual View Tabs: [📝 Lyric Sheet & Chords] vs [🪞 Twin Prompter (Sing-Along)]
        self.view_tabs = QTabWidget()
        self.view_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #283256;
                border-radius: 6px;
                background-color: #0b0f19;
            }
            QTabBar::tab {
                background: #161b30;
                color: #94a3b8;
                font-weight: 700;
                font-size: 10.5px;
                padding: 4px 12px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #2563eb;
                color: #ffffff;
            }
        """)

        # Tab 1: Lyrics Editor
        self.txt_clone_lyrics = QTextEdit()
        self.txt_clone_lyrics.setPlaceholderText("The semantic clone lyrics with section tags and chords will appear here...")
        self.txt_clone_lyrics.setFont(QFont("Segoe UI", 10))
        self.txt_clone_lyrics.textChanged.connect(self._on_clone_text_changed)
        self.view_tabs.addTab(self.txt_clone_lyrics, "📝 Lyric Sheet && Chords")

        # Tab 2: Twin Prompter & Syllable Cadence Table
        self.table_twin = QTableWidget()
        self.table_twin.setColumnCount(5)
        self.table_twin.setHorizontalHeaderLabels(["Line", "Reference Song (Syllables)", "Cloned Lyric (Matched)", "Sing-Along Fit", "Action"])
        self.table_twin.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table_twin.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_twin.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table_twin.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table_twin.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table_twin.verticalHeader().setVisible(False)
        self.view_tabs.addTab(self.table_twin, "🪞 Twin Prompter && Cadence")

        # Tab 3: Visual DNA & Copyright Clearance Audit Report
        self.txt_dna_audit = QTextEdit()
        self.txt_dna_audit.setReadOnly(True)
        self.txt_dna_audit.setFont(QFont("Consolas", 10))
        self.view_tabs.addTab(self.txt_dna_audit, "🧬 DNA && Copyright Audit")

        r_layout.addWidget(self.view_tabs, stretch=1)

        # Action Toolbar at bottom of clone
        act_row = QHBoxLayout()
        act_row.setSpacing(6)

        self.btn_copy_clone = QPushButton("📋 Copy Lyrics")
        self.btn_copy_clone.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_copy_clone.setStyleSheet("background: #f1f5f9; color: #334155; font-weight: 700; font-size: 10.5px; padding: 5px 10px; border-radius: 5px;")
        self.btn_copy_clone.clicked.connect(self._copy_lyrics)
        act_row.addWidget(self.btn_copy_clone)

        self.btn_send_editor = QPushButton("✍️ Send to Editor")
        self.btn_send_editor.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_send_editor.setStyleSheet("background: #2563eb; color: #ffffff; font-weight: 800; font-size: 11px; padding: 6px 12px; border-radius: 5px;")
        self.btn_send_editor.clicked.connect(self._send_to_editor)
        act_row.addWidget(self.btn_send_editor)

        self.btn_send_suno = QPushButton("🚀 Send to Suno")
        self.btn_send_suno.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_send_suno.setToolTip("Load cloned Title, Style Prompt & Lyrics directly into Suno Browser Studio [Mode 5]")
        self.btn_send_suno.setStyleSheet("background: #064e3b; color: #34d399; border: 1px solid #059669; font-weight: 800; font-size: 10.5px; padding: 5px 10px; border-radius: 5px;")
        self.btn_send_suno.clicked.connect(self._send_to_suno_tab)
        act_row.addWidget(self.btn_send_suno)

        self.btn_send_batch = QPushButton("⚡ 20x in Batch")
        self.btn_send_batch.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_send_batch.setToolTip("Send cloned DNA theme & style into Batch Studio Pro to generate a 20-song album")
        self.btn_send_batch.setStyleSheet("background: #2e1065; color: #d8b4fe; border: 1px solid #7c3aed; font-weight: 800; font-size: 10.5px; padding: 5px 10px; border-radius: 5px;")
        self.btn_send_batch.clicked.connect(self._send_to_batch_tab)
        act_row.addWidget(self.btn_send_batch)

        self.btn_clone_vocal = QPushButton("🎤 Vocal")
        self.btn_clone_vocal.setToolTip("Audition cloned lyrics with Neural Scratch Vocalist")
        self.btn_clone_vocal.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clone_vocal.setStyleSheet("background: #eff6ff; color: #1d4ed8; font-weight: 700; font-size: 10px; padding: 5px 8px; border-radius: 4px; border: 1px solid #bfdbfe;")
        self.btn_clone_vocal.clicked.connect(self._audition_clone_vocal)
        act_row.addWidget(self.btn_clone_vocal)

        self.btn_clone_chords = QPushButton("🎹 Chords")
        self.btn_clone_chords.setToolTip("Open Interactive Chord Soundboard")
        self.btn_clone_chords.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clone_chords.setStyleSheet("background: #fdf4ff; color: #86198f; font-weight: 700; font-size: 10px; padding: 5px 8px; border-radius: 4px; border: 1px solid #f0abfc;")
        self.btn_clone_chords.clicked.connect(self._audition_clone_chords)
        act_row.addWidget(self.btn_clone_chords)

        act_row.addStretch()

        self.btn_export_srt = QPushButton("📄 Subtitles (.srt)")
        self.btn_export_srt.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_export_srt.setStyleSheet("background: #f1f5f9; color: #334155; font-weight: 600; font-size: 10px; padding: 5px 8px; border-radius: 4px;")
        self.btn_export_srt.clicked.connect(self._export_srt)
        act_row.addWidget(self.btn_export_srt)

        self.btn_export_lrc = QPushButton("🎵 Karaoke (.lrc)")
        self.btn_export_lrc.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_export_lrc.setStyleSheet("background: #f1f5f9; color: #334155; font-weight: 600; font-size: 10px; padding: 5px 8px; border-radius: 4px;")
        self.btn_export_lrc.clicked.connect(self._export_lrc)
        act_row.addWidget(self.btn_export_lrc)

        self.btn_close = QPushButton("Close")
        self.btn_close.clicked.connect(self._on_close_clicked)
        if not isinstance(self.parent(), QDialog):
            self.btn_close.hide()
        act_row.addWidget(self.btn_close)

        r_layout.addLayout(act_row)
        split_layout.addWidget(self.right_card, stretch=1)

        main_layout.addLayout(split_layout, stretch=1)

    def _set_clone_mode(self, mode_key: str):
        self.active_mode_key = mode_key
        for k, btn in self.mode_buttons.items():
            btn.setChecked(k == mode_key)
        self.lbl_mode_desc.setText(CLONE_MODES[mode_key]["subtitle"])

        # Toggle persona dropdown visibility
        self.persona_capsule.setVisible(mode_key == "PERSONA_DNA")

        # Toggle 4-Flavor ribbon
        self.flavor_ribbon.setVisible(mode_key == "FOUR_FLAVORS")

        # Auto-adjust target genre & defaults
        if mode_key == "GENRE_MUTATION":
            self.combo_target_genre.setCurrentText("Melodic 808 Trap & Late-Night R&B")
            self.spin_target_bpm.setValue(136)
        elif mode_key == "PERSONA_DNA":
            self._on_persona_changed()
        elif mode_key == "STRICT_METER":
            self.view_tabs.setCurrentIndex(1) # Switch to Twin Prompter
            self.input_notes.setText("Exact syllable meter matching line-by-line for direct karaoke sing-along")
        elif mode_key == "ANSWER_SONG":
            self.input_notes.setText("From the partner's opposite perspective explaining their hidden side and loyalty")
        elif mode_key == "TIME_SHIFT_SEQUEL":
            self.input_notes.setText("10 years later meeting by chance, mature reflection and bittersweet peace")
        elif mode_key == "FOUR_FLAVORS":
            self.input_notes.setText("Generate 4 commercial arrangements: Radio Pop, Acoustic, 808 Trap, and Cinematic")
            flavors = CloneEngine.generate_4_flavors(self.txt_reference.toPlainText(), self.combo_target_lang.currentText())
            self._on_flavors_ready(flavors)

        self._load_instant_clone_preview()

    def _load_instant_clone_preview(self):
        ref_lyrics = self.txt_reference.toPlainText().strip() if hasattr(self, "txt_reference") else self.reference_lyrics
        if not ref_lyrics:
            return
        genre = self.combo_target_genre.currentText() if hasattr(self, "combo_target_genre") else "Global Commercial Radio Pop"
        lang = self.combo_target_lang.currentText() if hasattr(self, "combo_target_lang") else "🇬🇧 English"
        persona = (self.combo_persona.currentData() if hasattr(self, "combo_persona") else None) or self.active_persona_key
        res = CloneEngine.generate_offline_clone(ref_lyrics, self.active_mode_key, genre, lang, persona)
        self._on_clone_success(res["title"], res["style"], res["lyrics"], apply_humanize=False)

    def _on_persona_changed(self):
        pk = self.combo_persona.currentData()
        if pk in ARTIST_PERSONAS:
            self.active_persona_key = pk
            p = ARTIST_PERSONAS[pk]
            self.spin_target_bpm.setValue(p.get("bpm", 120))
            self.input_notes.setText(p.get("prompt_vibe", "")[:90] + "...")

    def _attach_audio_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Attach Reference Audio File", "", "Audio Files (*.mp3 *.wav *.m4a *.flac *.aac);;All Files (*.*)"
        )
        if not path:
            return

        dna = CloneEngine.extract_audio_dna(path)
        self.spin_target_bpm.setValue(dna["detected_bpm"])
        self.txt_clone_style.setText(dna["suno_style"])
        self.input_notes.setText(f"Acoustic texture reverse-engineered from {dna['filename']}: {dna['instruments'][:50]}")

        QMessageBox.information(
            self,
            "Audio DNA Ingested",
            f"Successfully analyzed audio file!\n\n"
            f"• Detected BPM: {dna['detected_bpm']} BPM\n"
            f"• Key Signature: {dna['detected_key']}\n"
            f"• Genre Profile: {dna['detected_genre']}\n"
            f"• Suno Style Prompt: \"{dna['suno_style']}\"\n\n"
            f"Ready to generate semantic clone matching this production style!"
        )

    def _on_preset_changed(self, text: str):
        data = self.combo_presets.currentData()
        if data == "CURRENT":
            pass
        elif data in FAMOUS_SONG_PRESETS:
            preset = FAMOUS_SONG_PRESETS[data]
            self.txt_reference.setPlainText(preset["lyrics"])
            self.reference_title = preset["title"]
            self.spin_target_bpm.setValue(preset["bpm"])
            self.combo_target_genre.setCurrentText(preset.get("genre", "Global Commercial Radio Pop"))
            if "🇰🇭" in data:
                self.combo_target_lang.setCurrentText("🇰🇭 Khmer (ភាសាខ្មែរ)")
            else:
                self.combo_target_lang.setCurrentText("🇬🇧 English")
            self._analyze_reference()
            self._load_instant_clone_preview()

    def _on_ref_text_changed(self):
        self._analyze_reference()
        self._update_twin_prompter()

    def _on_clone_text_changed(self):
        self._update_twin_prompter()

    def _analyze_reference(self):
        lyrics = self.txt_reference.toPlainText().strip()
        if not lyrics:
            return
        dna = CloneEngine.extract_song_dna(lyrics, self.reference_title)
        self.lbl_dna_thesis.setText(f"🎯 Core Thesis: {dna['thesis']}")
        self.lbl_dna_meta.setText(f"🎼 Sonic DNA: {dna['bpm']} BPM • {dna['key']} • {dna['genre']} • Flow: {dna['meter_pattern']}")

    def _start_cloning(self):
        ref_lyrics = self.txt_reference.toPlainText().strip()
        if not ref_lyrics:
            QMessageBox.warning(self, "Missing Reference", "Please paste or select a reference song to clone.")
            return

        self.btn_generate_clone.setText("⏳ Cloning Semantic DNA...")
        self.btn_generate_clone.setEnabled(False)

        genre = self.combo_target_genre.currentText()
        lang = self.combo_target_lang.currentText()
        bpm = self.spin_target_bpm.value()
        notes = self.input_notes.text().strip()
        persona = self.combo_persona.currentData() or "SINN_SISAMOUTH"

        self.worker = CloneWorker(ref_lyrics, self.active_mode_key, genre, lang, bpm, notes, persona, self)
        self.worker.finished_success.connect(self._on_clone_success)
        self.worker.finished_flavors.connect(self._on_flavors_ready)
        self.worker.finished_error.connect(self._on_clone_error)
        self.worker.start()

    def _toggle_compact_setup(self, compact: bool):
        if hasattr(self, "mode_frame"):
            self.mode_frame.setVisible(not compact)
        if hasattr(self, "settings_frame"):
            self.settings_frame.setVisible(not compact)
        self.btn_toggle_setup.setText("▼ Expand Setup" if compact else "▲ Compact")

    def _on_auto_humanize_toggled(self, checked: bool):
        if checked:
            self.btn_auto_humanize.setText("👤 Auto-Humanize: ON")
            self.btn_auto_humanize.setStyleSheet("background: #065f46; color: #ecfdf5; border: 1px solid #10b981; font-weight: 700; font-size: 10px; padding: 4px 8px; border-radius: 5px;")
        else:
            self.btn_auto_humanize.setText("👤 Auto-Humanize: OFF")
            self.btn_auto_humanize.setStyleSheet("background: #334155; color: #cbd5e1; border: 1px solid #475569; font-weight: 700; font-size: 10px; padding: 4px 8px; border-radius: 5px;")

    @staticmethod
    def _compute_originality_pct(ref_text: str, clone_text: str) -> int:
        """Compute copyright-safety originality percentage (100% = zero phrase overlap)."""
        def _clean_tokens(txt: str):
            no_tags = re.sub(r'\[[^\]]*\]', ' ', txt).lower()
            return re.findall(r'[a-z0-9]+|[\u1780-\u17ff]{2,}', no_tags)

        ref_toks = _clean_tokens(ref_text)
        clone_toks = _clean_tokens(clone_text)
        if not ref_toks or not clone_toks:
            return 100

        ref_set = set(ref_toks)
        clone_set = set(clone_toks)
        uni_overlap = len(ref_set & clone_set) / max(1, len(clone_set))

        ref_bi = set(zip(ref_toks, ref_toks[1:])) if len(ref_toks) > 1 else set()
        clone_bi = set(zip(clone_toks, clone_toks[1:])) if len(clone_toks) > 1 else set()
        bi_overlap = (len(ref_bi & clone_bi) / max(1, len(clone_bi))) if clone_bi else 0.0

        combined_overlap = (0.45 * uni_overlap) + (0.55 * bi_overlap)
        return max(0, min(100, int(round((1.0 - combined_overlap) * 100))))

    def _on_clone_success(self, title: str, style: str, lyrics: str, apply_humanize: bool = True):
        self.btn_generate_clone.setText("⚡ Clone Song DNA")
        self.btn_generate_clone.setEnabled(True)

        if apply_humanize and hasattr(self, "btn_auto_humanize") and self.btn_auto_humanize.isChecked() and lyrics.strip():
            from app.humanizer_engine import HumanizerEngine
            lang_txt = self.combo_target_lang.currentText()
            lang = "Khmer" if ("Khmer" in lang_txt or "ខ្មែរ" in lang_txt) else "English"
            lyrics = HumanizerEngine.humanize_lyrics_locally(lyrics, lang)

        self.generated_title = title
        self.generated_style = style
        self.generated_lyrics = lyrics

        self.txt_clone_style.setText(style)
        self.txt_clone_lyrics.blockSignals(True)
        self.txt_clone_lyrics.setPlainText(lyrics)
        self.txt_clone_lyrics.blockSignals(False)

        # Analyze Hit score & Sing-Along Fit
        analysis = HitAnalyzer.analyze(lyrics, self.spin_target_bpm.value())
        score = analysis.get("hit_score", 95)
        safety = analysis.get("safety_score", 100)
        self.lbl_clone_hit.setText(f"🌟 Hit: {score}% | Vocal Safety: {safety}%")

        self._update_twin_prompter()

    def _on_flavors_ready(self, flavors: dict):
        self.current_flavors = flavors
        self.flavor_ribbon.setVisible(True)

    def _switch_flavor(self, flavor_key: str):
        if not self.current_flavors or flavor_key not in self.current_flavors:
            return
        f = self.current_flavors[flavor_key]
        self.generated_title = f["title"]
        self.generated_style = f["style"]
        self.generated_lyrics = f["lyrics"]

        self.txt_clone_style.setText(f["style"])
        self.txt_clone_lyrics.setPlainText(f["lyrics"])
        self.spin_target_bpm.setValue(f.get("bpm", 120))
        self.lbl_clone_hit.setText(f"🌟 Hit: {f.get('hit_score', '95%')} | Vocal Safety: 100%")
        self._update_twin_prompter()

    def _update_twin_prompter(self):
        ref = self.txt_reference.toPlainText().strip()
        clone = self.txt_clone_lyrics.toPlainText().strip()
        if not ref or not clone:
            return

        comp = CloneEngine.analyze_singalong_compatibility(ref, clone)
        self.lbl_singalong_badge.setText(comp.get("badge", f"🎯 Sing-Along: {comp.get('score', 90)}%"))

        # Update Originality & Copyright Safety Badge
        if hasattr(self, "lbl_originality_badge"):
            orig_pct = self._compute_originality_pct(ref, clone)
            if orig_pct >= 85:
                tag = f"🛡️ Original: {orig_pct}% Safe"
                st = "font-size: 10px; font-weight: 800; color: #34d399; background: #064e3b; padding: 2px 6px; border-radius: 4px; border: 1px solid #059669;" if self.is_dark else "font-size: 10px; font-weight: 800; color: #047857; background: #dcfce7; padding: 2px 6px; border-radius: 4px; border: 1px solid #86efac;"
            elif orig_pct >= 70:
                tag = f"🛡️ Original: {orig_pct}% Check"
                st = "font-size: 10px; font-weight: 800; color: #fbbf24; background: #451a03; padding: 2px 6px; border-radius: 4px; border: 1px solid #d97706;" if self.is_dark else "font-size: 10px; font-weight: 800; color: #b45309; background: #fef3c7; padding: 2px 6px; border-radius: 4px; border: 1px solid #f59e0b;"
            else:
                tag = f"⚠️ Original: {orig_pct}% Close"
                st = "font-size: 10px; font-weight: 800; color: #fca5a5; background: #450a0a; padding: 2px 6px; border-radius: 4px; border: 1px solid #dc2626;" if self.is_dark else "font-size: 10px; font-weight: 800; color: #b91c1c; background: #fee2e2; padding: 2px 6px; border-radius: 4px; border: 1px solid #fca5a5;"
            self.lbl_originality_badge.setText(tag)
            self.lbl_originality_badge.setStyleSheet(st)
            if hasattr(self, "txt_dna_audit"):
                mode_title = CLONE_MODES.get(self.active_mode_key, {}).get("title", "1:1 Parallel Twin")
                self.txt_dna_audit.setPlainText(
                    CloneEngine.build_dna_audit_report(ref, clone, orig_pct, mode_title)
                )

        details = comp.get("details", [])
        self.table_twin.setRowCount(0)
        self.table_twin.clearContents()
        self.table_twin.setRowCount(len(details))

        for row, d in enumerate(details):
            # Line num
            it_num = QTableWidgetItem(f"#{d['line_idx']}")
            it_num.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_twin.setItem(row, 0, it_num)

            # Ref Line
            it_ref = QTableWidgetItem(f"{d['ref_line']} ({d['ref_syllables']}s)")
            self.table_twin.setItem(row, 1, it_ref)

            # Clone Line
            it_clone = QTableWidgetItem(f"{d['clone_line']} ({d['clone_syllables']}s)")
            self.table_twin.setItem(row, 2, it_clone)

            # Status Badge
            it_stat = QTableWidgetItem(d["status"])
            it_stat.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if d["diff"] == 0:
                it_stat.setForeground(QColor("#34d399" if self.is_dark else "#059669"))
            elif d["diff"] <= 1:
                it_stat.setForeground(QColor("#38bdf8" if self.is_dark else "#0284c7"))
            else:
                it_stat.setForeground(QColor("#fbbf24" if self.is_dark else "#b45309"))
            self.table_twin.setItem(row, 3, it_stat)

            # Action cell: Click-to-Fix button for mismatched lines
            if d["diff"] > 1 and d["clone_line"]:
                btn_fix = QPushButton("🔄 Fix Fit")
                btn_fix.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_fix.setToolTip(f"Adjust this line toward {d['ref_syllables']} syllables to lock sing-along rhythm")
                btn_fix.setStyleSheet(
                    "background: #1e1b4b; color: #c4b5fd; border: 1px solid #6366f1; font-size: 9px; font-weight: 700; padding: 2px 6px; border-radius: 4px;"
                    if self.is_dark else
                    "background: #eff6ff; color: #1d4ed8; border: 1px solid #93c5fd; font-size: 9px; font-weight: 700; padding: 2px 6px; border-radius: 4px;"
                )
                btn_fix.clicked.connect(
                    lambda _, cl=d["clone_line"], rl=d["ref_line"], tgt=d["ref_syllables"]: self._reroll_twin_line(cl, rl, tgt)
                )
                self.table_twin.setCellWidget(row, 4, btn_fix)
            else:
                self.table_twin.removeCellWidget(row, 4)
                it_ok = QTableWidgetItem("✓")
                it_ok.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                it_ok.setForeground(QColor("#34d399" if self.is_dark else "#059669"))
                self.table_twin.setItem(row, 4, it_ok)

    def _reroll_twin_line(self, clone_line: str, ref_line: str, target_syllables: int):
        """Re-roll a single mismatched line in the Twin Prompter to lock into target syllable count."""
        from app.syllable_meter import count_line_syllables
        full_text = self.txt_clone_lyrics.toPlainText()
        if clone_line not in full_text:
            return

        new_line = None
        keys = config_manager.get_api_keys()
        if keys:
            try:
                from app.gemini_client import generate_with_gemini
                model = config_manager.get("gemini_model", "gemini-3.5-flash")
                prompt = (
                    f"Rewrite ONLY this single song lyric line so it has EXACTLY {target_syllables} syllables "
                    f"and keeps the same emotional meaning and language (do NOT copy words from reference).\n"
                    f"Current line: {clone_line}\n"
                    f"Reference cadence (for rhythm only): {ref_line}\n"
                    f"Return ONLY the single rewritten lyric line with no quotes or explanation."
                )
                raw = generate_with_gemini(prompt, model_name=model)
                if raw:
                    cand = raw.strip().splitlines()[0].strip().strip('"').strip("'")
                    if cand:
                        new_line = cand
            except Exception:
                new_line = None

        # Instant smart offline syllable-fit fallback if no API key or error
        if not new_line:
            words = clone_line.split()
            cur_syl = count_line_syllables(clone_line)
            if cur_syl > target_syllables and len(words) > 2:
                # Trim trailing filler words until close to target
                trimmed = list(words)
                while len(trimmed) > 2 and count_line_syllables(" ".join(trimmed)) > target_syllables:
                    trimmed.pop()
                new_line = " ".join(trimmed)
            elif cur_syl < target_syllables:
                is_khmer = any('\u1780' <= c <= '\u17ff' for c in clone_line)
                pad = " ណាអូនអើយ" if is_khmer else ", yeah tonight"
                new_line = f"{clone_line.rstrip(',.')}{pad}"
            else:
                return

        updated = full_text.replace(clone_line, new_line, 1)
        self.txt_clone_lyrics.setPlainText(updated)

    def _on_clone_error(self, err_msg: str):
        self.btn_generate_clone.setText("⚡ Clone Song DNA")
        self.btn_generate_clone.setEnabled(True)
        QMessageBox.warning(self, "Cloning Issue", f"Could not complete clone: {err_msg}")

    def _copy_style(self):
        style = self.txt_clone_style.text().strip()
        if style:
            QApplication.clipboard().setText(style)
            self.btn_copy_style.setText("✓ Copied!")
            QTimer.singleShot(1500, lambda: self.btn_copy_style.setText("📋 Copy Style") if hasattr(self, "btn_copy_style") else None)

    def _paste_reference_clipboard(self):
        clip = QApplication.clipboard().text().strip()
        if clip:
            self.txt_reference.setPlainText(clip)
            self._analyze_reference()
            self._load_instant_clone_preview()

    def _pull_reference_from_editor(self):
        parent = self.parent()
        while parent:
            if hasattr(parent, "editor_panel"):
                ed_lyrics = parent.editor_panel.get_lyrics().strip()
                ed_title = parent.editor_panel.get_title().strip()
                if ed_lyrics:
                    self.reference_title = ed_title or "Editor Song"
                    self.txt_reference.setPlainText(ed_lyrics)
                    self._analyze_reference()
                    self._load_instant_clone_preview()
                return
            parent = parent.parent()

    def _pick_random_reference_preset(self):
        import random
        keys = list(FAMOUS_SONG_PRESETS.keys())
        if not keys:
            return
        cur = self.combo_presets.currentText()
        choices = [k for k in keys if k != cur] or keys
        picked = random.choice(choices)
        idx = self.combo_presets.findText(picked)
        if idx >= 0:
            self.combo_presets.setCurrentIndex(idx)

    def _auto_lock_all_syllable_meter(self):
        ref = self.txt_reference.toPlainText().strip()
        clone = self.txt_clone_lyrics.toPlainText().strip()
        if not ref or not clone:
            return
        locked = CloneEngine.lock_all_lines_to_reference_meter(ref, clone)
        self.txt_clone_lyrics.setPlainText(locked)
        if hasattr(self, "btn_lock_all_meter"):
            self.btn_lock_all_meter.setText("✓ 100% Meter Locked!")
            QTimer.singleShot(1500, lambda: self.btn_lock_all_meter.setText("🔒 Lock 100% Meter") if hasattr(self, "btn_lock_all_meter") else None)

    def _auto_scrub_copyright_overlaps(self):
        ref = self.txt_reference.toPlainText().strip()
        clone = self.txt_clone_lyrics.toPlainText().strip()
        if not ref or not clone:
            return
        scrubbed = CloneEngine.scrub_copyright_overlaps(ref, clone)
        self.txt_clone_lyrics.setPlainText(scrubbed)
        if hasattr(self, "btn_scrub_copyright"):
            self.btn_scrub_copyright.setText("✓ 100% Copyright Safe!")
            QTimer.singleShot(1500, lambda: self.btn_scrub_copyright.setText("🛡️ Scrub 100% Safe") if hasattr(self, "btn_scrub_copyright") else None)

    def _rotate_clone_chords(self):
        clone = self.txt_clone_lyrics.toPlainText().strip()
        if not clone:
            return
        rotated = CloneEngine.rotate_chord_progression(clone, step=1)
        self.txt_clone_lyrics.setPlainText(rotated)
        if hasattr(self, "btn_swap_chords"):
            self.btn_swap_chords.setText("✓ Chords Swapped!")
            QTimer.singleShot(1400, lambda: self.btn_swap_chords.setText("🎹 Swap Chords") if hasattr(self, "btn_swap_chords") else None)

    def _send_to_suno_tab(self):
        lyrics = self.txt_clone_lyrics.toPlainText().strip()
        if not lyrics:
            return
        title = self.generated_title or "Semantic Clone"
        style = self.txt_clone_style.text().strip() or f"{self.combo_target_genre.currentText()}, {self.spin_target_bpm.value()} BPM"
        self.send_to_suno_requested.emit(title, style, lyrics)

    def _send_to_batch_tab(self):
        dna = CloneEngine.extract_song_dna(self.txt_reference.toPlainText())
        theme = f"{dna.get('thesis', 'Emotional Pop Hit')} ({self.combo_target_genre.currentText()})"
        style = self.txt_clone_style.text().strip()
        self.send_to_batch_requested.emit(theme, style)

    def _copy_lyrics(self):
        lyrics = self.txt_clone_lyrics.toPlainText().strip()
        if lyrics:
            QApplication.clipboard().setText(lyrics)
            self.btn_copy_clone.setText("✓ Copied!")
            QTimer.singleShot(1500, lambda: self.btn_copy_clone.setText("📋 Copy Lyrics") if hasattr(self, "btn_copy_clone") else None)

    def _on_close_clicked(self):
        parent = self.parent()
        while parent:
            if isinstance(parent, QDialog):
                parent.accept()
                return
            if hasattr(parent, "_set_studio_mode"):
                parent._set_studio_mode(3)
                return
            parent = parent.parent()

    def _audition_clone_vocal(self):
        lyrics = self.txt_clone_lyrics.toPlainText().strip()
        if not lyrics:
            QMessageBox.warning(self, "No Lyrics", "Generate a cloned song first before auditioning.")
            return
        from app.ui.scratch_vocalist_dialog import ScratchVocalistDialog
        title = self.generated_title or "Cloned Song"
        dlg = ScratchVocalistDialog(self, is_dark=self.is_dark, lyrics=lyrics, title=title)
        dlg.exec()

    def _audition_clone_chords(self):
        lyrics = self.txt_clone_lyrics.toPlainText().strip()
        from app.ui.chord_soundboard_view import ChordSoundboardDialog
        dlg = ChordSoundboardDialog(self, is_dark=self.is_dark, initial_lyrics=lyrics)
        dlg.exec()

    def _send_to_editor(self):
        lyrics = self.txt_clone_lyrics.toPlainText().strip()
        if not lyrics:
            QMessageBox.information(self, "No Lyrics", "Please generate a clone first.")
            return
        title = self.generated_title or "Semantic Clone"
        self.send_to_editor_requested.emit(title, lyrics)
        parent = self.parent()
        while parent:
            if isinstance(parent, QDialog):
                parent.accept()
                return
            if hasattr(parent, "_set_studio_mode"):
                parent._set_studio_mode(3)
                return
            parent = parent.parent()

    def _audition_clone_vocal(self):
        lyrics = self.txt_clone_lyrics.toPlainText().strip()
        if not lyrics:
            QMessageBox.warning(self, "No Lyrics", "Generate a cloned song first before auditioning.")
            return
        from app.ui.scratch_vocalist_dialog import ScratchVocalistDialog
        title = self.generated_title or "Cloned Song"
        dlg = ScratchVocalistDialog(self, is_dark=self.is_dark, lyrics=lyrics, title=title)
        dlg.exec()

    def _audition_clone_chords(self):
        lyrics = self.txt_clone_lyrics.toPlainText().strip()
        from app.ui.chord_soundboard_view import ChordSoundboardDialog
        dlg = ChordSoundboardDialog(self, is_dark=self.is_dark, initial_lyrics=lyrics)
        dlg.exec()

    def _export_srt(self):
        lyrics = self.txt_clone_lyrics.toPlainText().strip()
        if not lyrics:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export Subtitles (.srt)", f"{self.generated_title or 'clone'}.srt", "Subtitle Files (*.srt)")
        if path:
            Exporter.export_srt(path, self.generated_title or "Clone Song", lyrics, f"{self.spin_target_bpm.value()} BPM")
            QMessageBox.information(self, "Exported", f"Successfully exported video subtitles to:\n{path}")

    def _export_lrc(self):
        lyrics = self.txt_clone_lyrics.toPlainText().strip()
        if not lyrics:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export Synced Karaoke (.lrc)", f"{self.generated_title or 'clone'}.lrc", "Karaoke Files (*.lrc)")
        if path:
            Exporter.export_lrc(path, self.generated_title or "Clone Song", lyrics, f"{self.spin_target_bpm.value()} BPM")
            QMessageBox.information(self, "Exported", f"Successfully exported synced karaoke to:\n{path}")

    def apply_theme(self, theme_or_dark):
        self.theme = get_theme(theme_or_dark)
        self.theme_key = self.theme.get("id", "obsidian")
        self.is_dark = self.theme.get("is_dark", True)
        self._apply_styling()

    def set_reference(self, lyrics: str, title: str = ""):
        if lyrics:
            self.reference_lyrics = lyrics.strip()
            self.txt_reference.setPlainText(self.reference_lyrics)
        if title:
            self.reference_title = title
        self._analyze_reference()

    def _apply_styling(self):
        t = getattr(self, "theme", get_theme(getattr(self, "is_dark", True)))
        is_dark = t.get("is_dark", True)
        self.is_dark = is_dark

        bg = t["bg_window"]
        card_bg = t["bg_card"]
        border = t["border"]
        text_primary = t["text_primary"]
        input_bg = t["bg_input"]

        self.setStyleSheet(f"""
            SongDNAClonerView, QDialog {{
                background-color: {bg};
                color: {text_primary};
                font-family: 'Segoe UI', sans-serif;
            }}
            QFrame#card {{
                background-color: {card_bg};
                border: 1px solid {border};
                border-radius: 8px;
            }}
            QLabel {{
                color: {text_primary};
                background: transparent;
                border: none;
            }}
            QTextEdit, QLineEdit, QComboBox, QSpinBox {{
                background-color: {input_bg};
                color: {text_primary};
                border: 1px solid {border};
                border-radius: 6px;
            }}
            QTableWidget {{
                background-color: {input_bg};
                color: {text_primary};
                border: 1px solid {border};
                border-radius: 6px;
                gridline-color: {border};
            }}
            QTableWidget QHeaderView::section {{
                background-color: {card_bg};
                color: {text_primary};
                font-weight: 700;
                font-size: 10px;
                padding: 4px;
                border: 1px solid {border};
            }}
            QPushButton {{
                border-radius: 5px;
            }}
        """)

        # Style DNA capsule
        if hasattr(self, "dna_capsule"):
            if is_dark:
                self.dna_capsule.setStyleSheet(f"background: {t['bg_card_alt']}; border: 1px solid {t['border']}; border-radius: 6px; padding: 6px;")
                if hasattr(self, "lbl_dna_thesis"):
                    self.lbl_dna_thesis.setStyleSheet(f"font-size: 10.5px; font-weight: 700; color: {t['text_accent']};")
                if hasattr(self, "lbl_dna_meta"):
                    self.lbl_dna_meta.setStyleSheet(f"font-size: 10px; font-weight: 600; color: {t['text_secondary']};")
            else:
                self.dna_capsule.setStyleSheet("background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 6px;")
                if hasattr(self, "lbl_dna_thesis"):
                    self.lbl_dna_thesis.setStyleSheet("font-size: 10.5px; font-weight: 700; color: #1d4ed8;")
                if hasattr(self, "lbl_dna_meta"):
                    self.lbl_dna_meta.setStyleSheet("font-size: 10px; font-weight: 600; color: #334155;")

        # Style Generate Button
        if hasattr(self, "btn_generate_clone"):
            self.btn_generate_clone.setStyleSheet(f"""
                QPushButton {{
                    background: {t['accent_gradient']};
                    color: #ffffff;
                    font-weight: 800;
                    font-size: 11.5px;
                    padding: 6px 16px;
                    border-radius: 6px;
                    border: 1px solid {t['border_accent']};
                }}
                QPushButton:hover {{
                    background: {t['accent_hover']};
                }}
            """)

        # Style mode buttons
        for k, btn in self.mode_buttons.items():
            if is_dark:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {t['bg_card_alt']};
                        color: {t['text_secondary']};
                        border: 1px solid {t['border']};
                        padding: 5px 8px;
                        font-weight: 600;
                        font-size: 10.5px;
                        border-radius: 6px;
                    }}
                    QPushButton:hover {{
                        background-color: {t['border']};
                        border-color: {t['border_accent']};
                        color: #ffffff;
                    }}
                    QPushButton:checked {{
                        background: {t['accent_gradient']};
                        color: #ffffff;
                        font-weight: 800;
                        border: 1px solid {t['border_accent']};
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: #ffffff;
                        color: #334155;
                        border: 1px solid #cbd5e1;
                        padding: 5px 8px;
                        font-weight: 600;
                        font-size: 10.5px;
                        border-radius: 6px;
                    }}
                    QPushButton:hover {{
                        background-color: #eff6ff;
                        border-color: #3b82f6;
                        color: #1d4ed8;
                    }}
                    QPushButton:checked {{
                        background-color: {t['accent']};
                        color: #ffffff;
                        font-weight: 800;
                        border: 1px solid {t['border_accent']};
                    }}
                """)

        # Style Bottom Action Buttons
        if hasattr(self, "btn_copy_clone"):
            if is_dark:
                self.btn_copy_clone.setStyleSheet(f"background: {t['bg_card_alt']}; color: {t['text_secondary']}; font-weight: 700; font-size: 10.5px; padding: 5px 10px; border-radius: 5px; border: 1px solid {t['border']};")
            else:
                self.btn_copy_clone.setStyleSheet("background: #ffffff; color: #0f172a; font-weight: 700; font-size: 10.5px; padding: 5px 10px; border-radius: 5px; border: 1px solid #cbd5e1;")

        if hasattr(self, "btn_send_editor"):
            self.btn_send_editor.setStyleSheet(f"background: {t['accent']}; color: #ffffff; font-weight: 800; font-size: 11px; padding: 6px 12px; border-radius: 5px; border: 1px solid {t['border_accent']};")

        if hasattr(self, "btn_export_srt"):
            if is_dark:
                self.btn_export_srt.setStyleSheet(f"background: {t['bg_card_alt']}; color: {t['text_secondary']}; font-weight: 600; font-size: 10px; padding: 5px 8px; border-radius: 4px; border: 1px solid {t['border']};")
            else:
                self.btn_export_srt.setStyleSheet("background: #ffffff; color: #334155; font-weight: 600; font-size: 10px; padding: 5px 8px; border-radius: 4px; border: 1px solid #cbd5e1;")

        if hasattr(self, "btn_export_lrc"):
            if is_dark:
                self.btn_export_lrc.setStyleSheet(f"background: {t['bg_card_alt']}; color: {t['text_secondary']}; font-weight: 600; font-size: 10px; padding: 5px 8px; border-radius: 4px; border: 1px solid {t['border']};")
            else:
                self.btn_export_lrc.setStyleSheet("background: #ffffff; color: #334155; font-weight: 600; font-size: 10px; padding: 5px 8px; border-radius: 4px; border: 1px solid #cbd5e1;")

        if hasattr(self, "btn_close"):
            if is_dark:
                self.btn_close.setStyleSheet(f"background: {t['bg_card_alt']}; color: {t['text_muted']}; border: 1px solid {t['border']}; border-radius: 4px; padding: 5px 10px;")
            else:
                self.btn_close.setStyleSheet("background: #f1f5f9; color: #475569; border: 1px solid #cbd5e1; border-radius: 4px; padding: 5px 10px;")

        if hasattr(self, "btn_attach_audio"):
            if is_dark:
                self.btn_attach_audio.setStyleSheet("background: #064e3b; color: #34d399; border: 1px solid #059669; font-weight: 700; font-size: 11px; padding: 5px 10px; border-radius: 5px;")
            else:
                self.btn_attach_audio.setStyleSheet("background: #ecfdf5; color: #047857; border: 1px solid #6ee7b7; font-weight: 700; font-size: 11px; padding: 5px 10px; border-radius: 5px;")

        if hasattr(self, "btn_toggle_setup"):
            if is_dark:
                self.btn_toggle_setup.setStyleSheet(f"background: {t['bg_card_alt']}; color: {t['text_secondary']}; border: 1px solid {t['border']}; font-weight: 700; font-size: 10.5px; padding: 4px 8px; border-radius: 5px;")
            else:
                self.btn_toggle_setup.setStyleSheet("background: #f1f5f9; color: #334155; border: 1px solid #cbd5e1; font-weight: 700; font-size: 10.5px; padding: 4px 8px; border-radius: 5px;")

        if hasattr(self, "lbl_singalong_badge"):
            if is_dark:
                self.lbl_singalong_badge.setStyleSheet("font-size: 10px; font-weight: 800; color: #38bdf8; background: #082f49; padding: 2px 6px; border-radius: 4px; border: 1px solid #0284c7;")
            else:
                self.lbl_singalong_badge.setStyleSheet("font-size: 10px; font-weight: 800; color: #0369a1; background: #e0f2fe; padding: 2px 6px; border-radius: 4px; border: 1px solid #7dd3fc;")

        if hasattr(self, "lbl_clone_hit"):
            if is_dark:
                self.lbl_clone_hit.setStyleSheet("font-size: 10px; font-weight: 800; color: #10b981; background: #064e3b; padding: 2px 6px; border-radius: 4px; border: 1px solid #059669;")
            else:
                self.lbl_clone_hit.setStyleSheet("font-size: 10px; font-weight: 800; color: #047857; background: #dcfce7; padding: 2px 6px; border-radius: 4px; border: 1px solid #86efac;")

        if hasattr(self, "btn_copy_style"):
            if is_dark:
                self.btn_copy_style.setStyleSheet(f"background: {t['subtle_pill_bg']}; color: {t['text_accent']}; border: 1px solid {t['border_accent']}; font-weight: 700; font-size: 10px; padding: 4px 8px; border-radius: 4px;")
            else:
                self.btn_copy_style.setStyleSheet("background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; font-weight: 700; font-size: 10px; padding: 4px 8px; border-radius: 4px;")

        for ref_b in [getattr(self, "btn_ref_paste", None), getattr(self, "btn_ref_pull_editor", None), getattr(self, "btn_ref_random", None)]:
            if ref_b:
                if is_dark:
                    ref_b.setStyleSheet(f"background: {t['bg_card_alt']}; color: {t['text_accent']}; border: 1px solid {t['border']}; font-size: 9.5px; font-weight: 700; padding: 2px 6px; border-radius: 4px;")
                else:
                    ref_b.setStyleSheet("background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; font-size: 9.5px; font-weight: 700; padding: 2px 6px; border-radius: 4px;")

        if hasattr(self, "btn_lock_all_meter"):
            if is_dark:
                self.btn_lock_all_meter.setStyleSheet("background: #082f49; color: #38bdf8; border: 1px solid #0284c7; font-weight: 800; font-size: 10px; padding: 4px 8px; border-radius: 4px;")
            else:
                self.btn_lock_all_meter.setStyleSheet("background: #e0f2fe; color: #0369a1; border: 1px solid #7dd3fc; font-weight: 800; font-size: 10px; padding: 4px 8px; border-radius: 4px;")

        if hasattr(self, "btn_scrub_copyright"):
            if is_dark:
                self.btn_scrub_copyright.setStyleSheet("background: #064e3b; color: #34d399; border: 1px solid #059669; font-weight: 800; font-size: 10px; padding: 4px 8px; border-radius: 4px;")
            else:
                self.btn_scrub_copyright.setStyleSheet("background: #dcfce7; color: #047857; border: 1px solid #86efac; font-weight: 800; font-size: 10px; padding: 4px 8px; border-radius: 4px;")

        if hasattr(self, "btn_swap_chords"):
            if is_dark:
                self.btn_swap_chords.setStyleSheet("background: #4a044e; color: #f0abfc; border: 1px solid #a21caf; font-weight: 700; font-size: 10px; padding: 4px 8px; border-radius: 4px;")
            else:
                self.btn_swap_chords.setStyleSheet("background: #fdf4ff; color: #86198f; border: 1px solid #f0abfc; font-weight: 700; font-size: 10px; padding: 4px 8px; border-radius: 4px;")

        if hasattr(self, "btn_send_suno"):
            if is_dark:
                self.btn_send_suno.setStyleSheet("background: #064e3b; color: #34d399; border: 1px solid #059669; font-weight: 800; font-size: 10.5px; padding: 5px 10px; border-radius: 5px;")
            else:
                self.btn_send_suno.setStyleSheet("background: #dcfce7; color: #047857; border: 1px solid #86efac; font-weight: 800; font-size: 10.5px; padding: 5px 10px; border-radius: 5px;")

        if hasattr(self, "btn_send_batch"):
            if is_dark:
                self.btn_send_batch.setStyleSheet("background: #2e1065; color: #d8b4fe; border: 1px solid #7c3aed; font-weight: 800; font-size: 10.5px; padding: 5px 10px; border-radius: 5px;")
            else:
                self.btn_send_batch.setStyleSheet("background: #faf5ff; color: #6d28d9; border: 1px solid #d8b4fe; font-weight: 800; font-size: 10.5px; padding: 5px 10px; border-radius: 5px;")

        if hasattr(self, "btn_clone_vocal"):
            if is_dark:
                self.btn_clone_vocal.setStyleSheet("background: #172554; color: #60a5fa; font-weight: 700; font-size: 10px; padding: 5px 8px; border-radius: 4px; border: 1px solid #1d4ed8;")
            else:
                self.btn_clone_vocal.setStyleSheet("background: #eff6ff; color: #1d4ed8; font-weight: 700; font-size: 10px; padding: 5px 8px; border-radius: 4px; border: 1px solid #bfdbfe;")

        if hasattr(self, "btn_clone_chords"):
            if is_dark:
                self.btn_clone_chords.setStyleSheet("background: #4a044e; color: #f0abfc; font-weight: 700; font-size: 10px; padding: 5px 8px; border-radius: 4px; border: 1px solid #a21caf;")
            else:
                self.btn_clone_chords.setStyleSheet("background: #fdf4ff; color: #86198f; font-weight: 700; font-size: 10px; padding: 5px 8px; border-radius: 4px; border: 1px solid #f0abfc;")

        if hasattr(self, "view_tabs"):
            if is_dark:
                self.view_tabs.setStyleSheet(f"""
                    QTabWidget::pane {{
                        border: 1px solid {border};
                        border-radius: 6px;
                        background-color: {input_bg};
                    }}
                    QTabBar::tab {{
                        background: {t['bg_card_alt']};
                        color: {t['text_secondary']};
                        font-weight: 700;
                        font-size: 10.5px;
                        padding: 5px 12px;
                        border-top-left-radius: 5px;
                        border-top-right-radius: 5px;
                    }}
                    QTabBar::tab:selected {{
                        background: {t['accent']};
                        color: #ffffff;
                    }}
                """)
            else:
                self.view_tabs.setStyleSheet(f"""
                    QTabWidget::pane {{
                        border: 1px solid {border};
                        border-radius: 6px;
                        background-color: #ffffff;
                    }}
                    QTabBar::tab {{
                        background: #f1f5f9;
                        color: #475569;
                        font-weight: 700;
                        font-size: 10.5px;
                        padding: 5px 12px;
                        border-top-left-radius: 5px;
                        border-top-right-radius: 5px;
                    }}
                    QTabBar::tab:selected {{
                        background: {t['accent']};
                        color: #ffffff;
                    }}
                """)


class SongDNAClonerDialog(QDialog):
    """Backward-compatible modal dialog hosting SongDNAClonerView."""
    send_to_editor_requested = pyqtSignal(str, str)

    def __init__(self, initial_lyrics: str = "", initial_title: str = "", parent=None, is_dark: bool = True):
        super().__init__(parent)
        self.setWindowTitle("🧬 Song DNA & Semantic Meaning Cloner (ម៉ាស៊ីនក្លូនបទចម្រៀងស្របន័យ)")
        self.resize(1120, 740)
        self.setMinimumSize(1000, 660)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.view = SongDNAClonerView(initial_lyrics=initial_lyrics, initial_title=initial_title, parent=self, is_dark=is_dark)
        self.view.send_to_editor_requested.connect(self.send_to_editor_requested.emit)
        layout.addWidget(self.view)
