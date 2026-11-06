"""
Song DNA & Semantic Meaning Cloner Dialog (ម៉ាស៊ីនក្លូនបទចម្រៀងស្របន័យ).
Studio modal interface for analyzing reference song DNA, artist personas, strict syllable cadence,
audio file reverse-engineering, and generating commercial semantic counterparts across 8 creative clone modes.
"""

import re
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QScrollArea, QFrame, QGridLayout,
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

    def __init__(self, initial_lyrics: str = "", initial_title: str = "", parent=None, is_dark: bool = True):
        super().__init__(parent)
        self.is_dark = is_dark
        self.reference_lyrics = initial_lyrics.strip() if initial_lyrics else FAMOUS_SONG_PRESETS["🇰🇭 ចំប៉ាបាត់ដំបង (Champa Battambang)"]["lyrics"]
        self.reference_title = initial_title or "Reference Song"
        self.active_mode_key = "PARALLEL_TWIN"
        self.active_persona_key = "SINN_SISAMOUTH"
        self.generated_title = ""
        self.generated_style = ""
        self.generated_lyrics = ""
        self.current_flavors = {}

        self.setWindowTitle("🧬 Song DNA & Semantic Meaning Cloner (ម៉ាស៊ីនក្លូនបទចម្រៀងស្របន័យ)")
        self.resize(1120, 740)
        self.setMinimumSize(1000, 660)

        self._init_ui()
        self._apply_styling()
        self._analyze_reference()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 14, 18, 14)
        main_layout.setSpacing(10)

        # 1. Header Box
        header_box = QHBoxLayout()
        title_vbox = QVBoxLayout()
        title_vbox.setSpacing(2)

        self.lbl_main_title = QLabel("🧬 Song DNA & Semantic Meaning Cloner (ម៉ាស៊ីនក្លូនបទចម្រៀងស្របន័យ)")
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

        main_layout.addLayout(header_box)

        # 2. 8 Creative Clone Mode Selector Pills (2 Rows x 4 Columns)
        self.mode_frame = QFrame()
        self.mode_frame.setObjectName("card")
        m_layout = QVBoxLayout(self.mode_frame)
        m_layout.setContentsMargins(10, 8, 10, 8)
        m_layout.setSpacing(5)

        self.mode_buttons = {}
        row1_keys = ["PARALLEL_TWIN", "ANSWER_SONG", "GENRE_MUTATION", "TIME_SHIFT_SEQUEL"]
        row2_keys = ["BILINGUAL_MIRROR", "PERSONA_DNA", "STRICT_METER", "FOUR_FLAVORS"]

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

        self.lbl_mode_desc = QLabel(CLONE_MODES["PARALLEL_TWIN"]["subtitle"])
        self.lbl_mode_desc.setStyleSheet("font-size: 11px; font-weight: 600; color: #8b5cf6;")
        m_layout.addWidget(self.lbl_mode_desc)

        main_layout.addWidget(self.mode_frame)

        # 3. Target Clone Settings Row
        settings_frame = QFrame()
        settings_frame.setObjectName("card")
        s_layout = QVBoxLayout(settings_frame)
        s_layout.setContentsMargins(12, 8, 12, 8)
        s_layout.setSpacing(6)

        # Row 1: Target Controls, Audio Ingestion, & Action Button
        row1 = QHBoxLayout()
        row1.setSpacing(8)

        lbl_tg = QLabel("Target Genre:")
        lbl_tg.setStyleSheet("font-weight: 700; font-size: 11px;")
        row1.addWidget(lbl_tg)

        self.combo_target_genre = QComboBox()
        self.combo_target_genre.addItems([
            "Khmer 60s Sentimental Ballad",
            "Khmer Romvong Folk Festive",
            "Khmer Modern Trap / Hip-Hop 808",
            "Modern Khmer Acoustic Pop & R&B",
            "Global Commercial Radio Pop",
            "80s Synthwave & Retro Pop",
            "Acoustic Fingerpicked Indie Ballad",
            "EDM Club Festival Drop"
        ])
        self.combo_target_genre.setStyleSheet("padding: 4px 6px; font-size: 11px; min-width: 170px;")
        row1.addWidget(self.combo_target_genre)

        lbl_tl = QLabel("Language:")
        lbl_tl.setStyleSheet("font-weight: 700; font-size: 11px;")
        row1.addWidget(lbl_tl)

        self.combo_target_lang = QComboBox()
        self.combo_target_lang.addItems([
            "🇰🇭 ខ្មែរ (Khmer)",
            "🇬🇧 English",
            "🌟 Both (50/50 Dual Engine)"
        ])
        self.combo_target_lang.setStyleSheet("padding: 4px 6px; font-size: 11px; min-width: 120px;")
        row1.addWidget(self.combo_target_lang)

        lbl_bpm = QLabel("Tempo:")
        lbl_bpm.setStyleSheet("font-weight: 700; font-size: 11px;")
        row1.addWidget(lbl_bpm)

        self.spin_target_bpm = QSpinBox()
        self.spin_target_bpm.setRange(50, 190)
        self.spin_target_bpm.setValue(74)
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
        self.btn_generate_clone = QPushButton("⚡ បង្កើតបទក្លូនស្របន័យ (Clone Song)")
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
        s_layout.addLayout(row2)

        main_layout.addWidget(settings_frame)

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

        lbl_l_title = QLabel("📄 Reference Song & Extracted DNA")
        lbl_l_title.setStyleSheet("font-weight: 800; font-size: 12px; color: #38bdf8;")
        l_layout.addWidget(lbl_l_title)

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
        self.lbl_r_title = QLabel("✨ Generated Semantic Clone")
        self.lbl_r_title.setStyleSheet("font-weight: 800; font-size: 12px; color: #34d399;")
        r_header_row.addWidget(self.lbl_r_title)
        r_header_row.addStretch()

        self.lbl_singalong_badge = QLabel("🎯 Sing-Along: 93%")
        self.lbl_singalong_badge.setStyleSheet("font-size: 10px; font-weight: 800; color: #38bdf8; background: #082f49; padding: 2px 6px; border-radius: 4px; border: 1px solid #0284c7;")
        r_header_row.addWidget(self.lbl_singalong_badge)

        self.lbl_clone_hit = QLabel("🌟 Hit: 95% | Vocal Safety: 100%")
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
        self.view_tabs.addTab(self.txt_clone_lyrics, "📝 Lyric Sheet & Chords")

        # Tab 2: Twin Prompter & Syllable Cadence Table
        self.table_twin = QTableWidget()
        self.table_twin.setColumnCount(4)
        self.table_twin.setHorizontalHeaderLabels(["Line", "Reference Song (Syllables)", "Cloned Lyric (Matched)", "Sing-Along Fit"])
        self.table_twin.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table_twin.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_twin.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table_twin.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table_twin.verticalHeader().setVisible(False)
        self.view_tabs.addTab(self.table_twin, "🪞 Twin Prompter & Cadence")

        r_layout.addWidget(self.view_tabs, stretch=1)

        # Action Toolbar at bottom of clone
        act_row = QHBoxLayout()
        act_row.setSpacing(6)

        self.btn_copy_clone = QPushButton("📋 Copy Lyrics")
        self.btn_copy_clone.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_copy_clone.setStyleSheet("background: #f1f5f9; color: #334155; font-weight: 700; font-size: 10.5px; padding: 5px 10px; border-radius: 5px;")
        self.btn_copy_clone.clicked.connect(self._copy_lyrics)
        act_row.addWidget(self.btn_copy_clone)

        self.btn_send_editor = QPushButton("✍️ Send to Editor Workbench")
        self.btn_send_editor.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_send_editor.setStyleSheet("background: #2563eb; color: #ffffff; font-weight: 800; font-size: 11px; padding: 6px 12px; border-radius: 5px;")
        self.btn_send_editor.clicked.connect(self._send_to_editor)
        act_row.addWidget(self.btn_send_editor)

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
            self.combo_target_genre.setCurrentText("Khmer Modern Trap / Hip-Hop 808")
            self.spin_target_bpm.setValue(138)
        elif mode_key == "PERSONA_DNA":
            self._on_persona_changed()
        elif mode_key == "STRICT_METER":
            self.view_tabs.setCurrentIndex(1) # Switch to Twin Prompter
            self.input_notes.setText("Exact syllable meter matching line-by-line for direct karaoke sing-along")
        elif mode_key == "ANSWER_SONG":
            self.input_notes.setText("From female lover's perspective explaining her tears and loyalty")
        elif mode_key == "TIME_SHIFT_SEQUEL":
            self.input_notes.setText("10 years later meeting by chance at an airport, bittersweet peace")
        elif mode_key == "FOUR_FLAVORS":
            self.input_notes.setText("Generate 4 commercial arrangements: Pop, Acoustic, Trap, and Cinematic")

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
            self.combo_target_genre.setCurrentText(preset.get("genre", "Khmer 60s Sentimental Ballad"))
            self._analyze_reference()

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

    def _on_clone_success(self, title: str, style: str, lyrics: str):
        self.btn_generate_clone.setText("⚡ បង្កើតបទក្លូនស្របន័យ (Clone Song)")
        self.btn_generate_clone.setEnabled(True)

        self.generated_title = title
        self.generated_style = style
        self.generated_lyrics = lyrics

        self.txt_clone_style.setText(style)
        self.txt_clone_lyrics.setPlainText(lyrics)

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

        details = comp.get("details", [])
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

    def _on_clone_error(self, err_msg: str):
        self.btn_generate_clone.setText("⚡ បង្កើតបទក្លូនស្របន័យ (Clone Song)")
        self.btn_generate_clone.setEnabled(True)
        QMessageBox.warning(self, "Cloning Issue", f"Could not complete clone: {err_msg}")

    def _copy_style(self):
        style = self.txt_clone_style.text().strip()
        if style:
            QApplication.clipboard().setText(style)
            self.btn_copy_style.setText("✓ Copied!")
            QTimer.singleShot(1500, lambda: self.btn_copy_style.setText("📋 Copy Style") if hasattr(self, "btn_copy_style") else None)

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
            QDialog {{
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
