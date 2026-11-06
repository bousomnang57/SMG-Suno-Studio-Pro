"""
Left Sidebar: Global Music Generator Panel with 1-Click Song Formula Presets.
Allows selecting ready-made song blueprints, cultural genres, languages,
song structures, rhyme schemes, and AI controls.
Ultra-compact Studio DAW channel strip with ZERO vertical and ZERO horizontal scrollbars.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QGroupBox, QTextEdit, QSpinBox,
    QScrollArea, QFrame, QSizePolicy
)
from PyQt6.QtCore import pyqtSignal, Qt
from app.music_data import (
    WORLD_REGIONS, SONG_STRUCTURES, MOODS, THEMES,
    RHYME_SCHEMES, LANGUAGES, ONE_CLICK_PRESETS
)

class GeneratorPanel(QWidget):
    generate_requested = pyqtSignal(dict)
    demo_requested = pyqtSignal(dict)
    load_skeleton_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_dark = True
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 2, 4, 2)
        main_layout.setSpacing(3)

        # Scroll Area for responsive sizing on smaller screens - ZERO scrollbars needed
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setStyleSheet("background: transparent;")

        self.content = QWidget()
        layout = QVBoxLayout(self.content)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)

        def _setup_combo(cb: QComboBox) -> QComboBox:
            cb.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
            cb.setMinimumContentsLength(4)
            cb.setFixedHeight(23)
            return cb

        # ── Section 0: 1-Click Formula Presets ──
        self.preset_group = QFrame()
        p_layout = QVBoxLayout(self.preset_group)
        p_layout.setContentsMargins(0, 0, 0, 0)
        p_layout.setSpacing(2)

        lbl_p = QLabel("⚡ 1-CLICK FORMULA • រូបមន្តសម្រេច")
        lbl_p.setStyleSheet("font-size: 9.5px; font-weight: 800; color: #a5b4fc; letter-spacing: 0.5px;")
        p_layout.addWidget(lbl_p)

        self.preset_combo = _setup_combo(QComboBox())
        self.preset_combo.addItem("— ជ្រើសរើសដោយសេរី (Custom Mode) —", None)
        for name in ONE_CLICK_PRESETS.keys():
            self.preset_combo.addItem(name, name)
        self.preset_combo.currentTextChanged.connect(self._on_preset_selected)
        p_layout.addWidget(self.preset_combo)

        self.preset_desc = QLabel("ស្វ័យប្រវត្តិកំណត់ Region, Genre, BPM, Structure & Mood")
        self.preset_desc.setStyleSheet("color: #64748b; font-size: 8.5px; line-height: 1.1;")
        self.preset_desc.setWordWrap(False)
        p_layout.addWidget(self.preset_desc)
        layout.addWidget(self.preset_group)

        # ── Section 1: World Region & Genre ──
        self.genre_group = QFrame()
        g_layout = QVBoxLayout(self.genre_group)
        g_layout.setContentsMargins(0, 0, 0, 0)
        g_layout.setSpacing(2)

        lbl_g = QLabel("🌍 1. STYLE & GENRE • តំបន់ & ចង្វាក់")
        lbl_g.setStyleSheet("font-size: 9.5px; font-weight: 800; color: #38bdf8; letter-spacing: 0.5px;")
        g_layout.addWidget(lbl_g)

        # Region & Genre side-by-side
        rg_row = QHBoxLayout()
        rg_row.setSpacing(3)
        self.region_combo = _setup_combo(QComboBox())
        self.region_combo.addItems(list(WORLD_REGIONS.keys()))
        self.region_combo.currentTextChanged.connect(self._on_region_changed)
        rg_row.addWidget(self.region_combo, 1)

        self.genre_combo = _setup_combo(QComboBox())
        self.genre_combo.addItems(["Pop & Synthpop"])
        self.genre_combo.currentTextChanged.connect(self._on_genre_changed)
        rg_row.addWidget(self.genre_combo, 1)
        g_layout.addLayout(rg_row)

        # Info Card (BPM + Meter + Description in 1 compact frame)
        self.info_frame = QFrame()
        info_layout = QVBoxLayout(self.info_frame)
        info_layout.setContentsMargins(4, 3, 4, 3)
        info_layout.setSpacing(2)

        badges_row = QHBoxLayout()
        badges_row.setSpacing(3)
        self.bpm_badge = QLabel("BPM: 120")
        self.bpm_badge.setFixedHeight(16)
        self.meter_badge = QLabel("Meter: 4/4")
        self.meter_badge.setFixedHeight(16)
        badges_row.addWidget(self.bpm_badge)
        badges_row.addWidget(self.meter_badge)
        badges_row.addStretch()
        info_layout.addLayout(badges_row)

        self.genre_desc = QLabel("Genre characteristics")
        self.genre_desc.setStyleSheet("font-size: 8.5px; color: #94a3b8; line-height: 1.15;")
        self.genre_desc.setWordWrap(False)
        info_layout.addWidget(self.genre_desc)
        g_layout.addWidget(self.info_frame)
        layout.addWidget(self.genre_group)

        # ── Section 2: Language & Vocal Delivery ──
        self.lang_group = QFrame()
        l_layout = QVBoxLayout(self.lang_group)
        l_layout.setContentsMargins(0, 0, 0, 0)
        l_layout.setSpacing(2)

        lbl_l = QLabel("🗣️ 2. CADENCE & LANGUAGE • ភាសា")
        lbl_l.setStyleSheet("font-size: 9.5px; font-weight: 800; color: #c084fc; letter-spacing: 0.5px;")
        l_layout.addWidget(lbl_l)

        # Language + Target BPM in 1 row
        lang_bpm_row = QHBoxLayout()
        lang_bpm_row.setSpacing(3)

        self.lang_combo = _setup_combo(QComboBox())
        for item in LANGUAGES:
            self.lang_combo.addItem(f"{item['name']} ({item['native']})", item["name"])
        lang_bpm_row.addWidget(self.lang_combo, 2)

        self.bpm_spin = QSpinBox()
        self.bpm_spin.setRange(50, 220)
        self.bpm_spin.setValue(120)
        self.bpm_spin.setFixedHeight(23)
        self.bpm_spin.setToolTip("Target Tempo (BPM)")
        lang_bpm_row.addWidget(self.bpm_spin, 1)
        l_layout.addLayout(lang_bpm_row)

        self.rhyme_combo = _setup_combo(QComboBox())
        self.rhyme_combo.addItems(RHYME_SCHEMES)
        l_layout.addWidget(self.rhyme_combo)
        layout.addWidget(self.lang_group)

        # ── Section 3: Song Structure & Concept ──
        self.concept_group = QFrame()
        c_layout = QVBoxLayout(self.concept_group)
        c_layout.setContentsMargins(0, 0, 0, 0)
        c_layout.setSpacing(2)

        lbl_c = QLabel("📖 3. STRUCTURE & MOOD • គ្រោង & រឿង")
        lbl_c.setStyleSheet("font-size: 9.5px; font-weight: 800; color: #34d399; letter-spacing: 0.5px;")
        c_layout.addWidget(lbl_c)

        # Structure & Mood side-by-side
        sm_row = QHBoxLayout()
        sm_row.setSpacing(3)
        self.structure_combo = _setup_combo(QComboBox())
        self.structure_combo.addItems(list(SONG_STRUCTURES.keys()))
        sm_row.addWidget(self.structure_combo, 1)

        self.mood_combo = _setup_combo(QComboBox())
        self.mood_combo.addItems(MOODS)
        sm_row.addWidget(self.mood_combo, 1)
        c_layout.addLayout(sm_row)

        self.theme_combo = _setup_combo(QComboBox())
        self.theme_combo.addItems(THEMES)
        c_layout.addWidget(self.theme_combo)

        self.custom_notes = QTextEdit()
        self.custom_notes.setPlaceholderText("Custom story notes, phrases, artist vibes...")
        self.custom_notes.setFixedHeight(28)
        c_layout.addWidget(self.custom_notes)
        layout.addWidget(self.concept_group)

        # ── Section 4: Primary Actions ──
        action_layout = QVBoxLayout()
        action_layout.setSpacing(3)

        self.btn_generate = QPushButton("✨ Generate Song with Gemini")
        self.btn_generate.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_generate.setFixedHeight(28)
        self.btn_generate.clicked.connect(self._emit_generate)
        action_layout.addWidget(self.btn_generate)

        sub_btns_row = QHBoxLayout()
        sub_btns_row.setSpacing(3)

        self.btn_demo = QPushButton("🎵 Demo Track")
        self.btn_demo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_demo.setFixedHeight(22)
        self.btn_demo.clicked.connect(self._emit_demo)
        sub_btns_row.addWidget(self.btn_demo)

        self.btn_insert_skeleton = QPushButton("📋 Load Outline")
        self.btn_insert_skeleton.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_insert_skeleton.setFixedHeight(22)
        self.btn_insert_skeleton.clicked.connect(self._emit_load_skeleton)
        sub_btns_row.addWidget(self.btn_insert_skeleton)
        action_layout.addLayout(sub_btns_row)

        self.status_label = QLabel("Ready to compose")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFixedHeight(14)
        action_layout.addWidget(self.status_label)

        layout.addLayout(action_layout)
        layout.addStretch()

        self.scroll.setWidget(self.content)
        main_layout.addWidget(self.scroll)

        # Trigger initial genre population
        self._on_region_changed(self.region_combo.currentText())
        self.apply_theme(True)

    def apply_theme(self, is_dark: bool):
        self.is_dark = is_dark
        if is_dark:
            self.setStyleSheet("background-color: #0c0e18;")
            card_qss = "background-color: #111626; border: 1px solid #1f2742; border-radius: 5px; padding: 3px;"
            for gb in [self.preset_group, self.genre_group, self.lang_group, self.concept_group]:
                gb.setStyleSheet(card_qss)

            combo_qss = """
                QComboBox, QSpinBox {
                    background-color: #090c17;
                    color: #f1f5f9;
                    border: 1px solid #232c48;
                    border-radius: 4px;
                    padding: 1px 4px;
                    font-size: 9.5px;
                }
                QComboBox:focus, QSpinBox:focus {
                    border: 1px solid #6366f1;
                }
                QComboBox::drop-down {
                    border: none;
                    width: 14px;
                }
                QComboBox QAbstractItemView {
                    background-color: #0e1222;
                    color: #f1f5f9;
                    selection-background-color: #6d28d9;
                }
            """
            for cb in [self.preset_combo, self.region_combo, self.genre_combo, self.lang_combo, self.rhyme_combo, self.structure_combo, self.mood_combo, self.theme_combo]:
                cb.setStyleSheet(combo_qss)
            self.bpm_spin.setStyleSheet(combo_qss)

            self.info_frame.setStyleSheet("background-color: #080a14; border: 1px solid #192036; border-radius: 4px; padding: 2px 4px;")
            self.bpm_badge.setStyleSheet("background-color: #1e1b4b; color: #a78bfa; border: 1px solid #4338ca; border-radius: 3px; padding: 0 4px; font-size: 8.5px; font-weight: 700;")
            self.meter_badge.setStyleSheet("background-color: #0c2d48; color: #38bdf8; border: 1px solid #0284c7; border-radius: 3px; padding: 0 4px; font-size: 8.5px; font-weight: 700;")
            self.genre_desc.setStyleSheet("color: #94a3b8; font-size: 8.5px; line-height: 1.15;")

            self.custom_notes.setStyleSheet("background-color: #090c17; color: #f1f5f9; border: 1px solid #232c48; border-radius: 4px; padding: 2px 4px; font-size: 9.5px;")

            self.btn_insert_skeleton.setStyleSheet("""
                QPushButton {
                    background-color: #141a2e;
                    color: #93c5fd;
                    border: 1px solid #283354;
                    border-radius: 4px;
                    padding: 1px 4px;
                    font-size: 9px;
                    font-weight: 700;
                }
                QPushButton:hover {
                    background-color: #1e293b;
                    color: #ffffff;
                }
            """)

            self.btn_generate.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7c3aed, stop:1 #4f46e5);
                    color: #ffffff;
                    font-weight: 800;
                    font-size: 10.5px;
                    border: 1px solid #a855f7;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8b5cf6, stop:1 #6366f1);
                }
            """)

            self.btn_demo.setStyleSheet("""
                QPushButton {
                    background-color: #141a2e;
                    color: #38bdf8;
                    border: 1px solid #0284c7;
                    border-radius: 4px;
                    font-weight: 700;
                    font-size: 9px;
                }
                QPushButton:hover {
                    background-color: #0284c7;
                    color: #ffffff;
                }
            """)
            self.status_label.setStyleSheet("color: #64748b; font-size: 9px; font-style: italic;")
        else:
            self.setStyleSheet("background-color: #f8fafc;")
            card_qss = "background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 5px; padding: 3px;"
            for gb in [self.preset_group, self.genre_group, self.lang_group, self.concept_group]:
                gb.setStyleSheet(card_qss)

            combo_qss = """
                QComboBox, QSpinBox {
                    background-color: #ffffff;
                    color: #1e293b;
                    border: 1px solid #cbd5e1;
                    border-radius: 4px;
                    padding: 1px 4px;
                    font-size: 9.5px;
                }
                QComboBox:focus, QSpinBox:focus {
                    border: 1px solid #3b82f6;
                }
                QComboBox::drop-down {
                    border: none;
                    width: 14px;
                }
                QComboBox QAbstractItemView {
                    background-color: #ffffff;
                    color: #1e293b;
                    selection-background-color: #e0e7ff;
                }
            """
            for cb in [self.preset_combo, self.region_combo, self.genre_combo, self.lang_combo, self.rhyme_combo, self.structure_combo, self.mood_combo, self.theme_combo]:
                cb.setStyleSheet(combo_qss)
            self.bpm_spin.setStyleSheet(combo_qss)

            self.info_frame.setStyleSheet("background-color: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 4px; padding: 2px 4px;")
            self.bpm_badge.setStyleSheet("background-color: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe; border-radius: 3px; padding: 0 4px; font-size: 8.5px; font-weight: 700;")
            self.meter_badge.setStyleSheet("background-color: #f0fdf4; color: #16a34a; border: 1px solid #bbf7d0; border-radius: 3px; padding: 0 4px; font-size: 8.5px; font-weight: 700;")
            self.genre_desc.setStyleSheet("color: #475569; font-size: 8.5px; line-height: 1.15;")

            self.custom_notes.setStyleSheet("background-color: #ffffff; color: #1e293b; border: 1px solid #cbd5e1; border-radius: 4px; padding: 2px 4px; font-size: 9.5px;")

            self.btn_insert_skeleton.setStyleSheet("""
                QPushButton {
                    background-color: #f8fafc;
                    color: #2563eb;
                    border: 1px solid #cbd5e1;
                    border-radius: 4px;
                    padding: 1px 4px;
                    font-size: 9px;
                    font-weight: 700;
                }
                QPushButton:hover {
                    background-color: #eff6ff;
                }
            """)

            self.btn_generate.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4f46e5, stop:1 #6366f1);
                    color: #ffffff;
                    font-weight: 800;
                    font-size: 10.5px;
                    border: 1px solid #4338ca;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background: #4338ca;
                }
            """)

            self.btn_demo.setStyleSheet("""
                QPushButton {
                    background-color: #f0f9ff;
                    color: #0284c7;
                    border: 1px solid #7dd3fc;
                    border-radius: 4px;
                    font-weight: 700;
                    font-size: 9px;
                }
                QPushButton:hover {
                    background-color: #0284c7;
                    color: #ffffff;
                }
            """)
            self.status_label.setStyleSheet("color: #94a3b8; font-size: 9px; font-style: italic;")

    def _on_preset_selected(self, preset_name: str):
        if not preset_name or preset_name.startswith("—"):
            self.preset_desc.setText("ជ្រើសរើសទម្រង់ខាងលើ ប្រព័ន្ធនឹងកំណត់ស្វ័យប្រវត្តិ។")
            return

        preset = ONE_CLICK_PRESETS.get(preset_name)
        if not preset:
            return

        self.preset_desc.setText(f"✓ {preset.get('user_notes', '')[:38]}")

        # Set Region
        region = preset.get("region")
        if region:
            idx = self.region_combo.findText(region)
            if idx >= 0:
                self.region_combo.setCurrentIndex(idx)

        # Set Genre
        genre = preset.get("genre")
        if genre:
            idx = self.genre_combo.findText(genre)
            if idx >= 0:
                self.genre_combo.setCurrentIndex(idx)

        # Set Language
        lang = preset.get("language")
        if lang:
            for i in range(self.lang_combo.count()):
                if lang in self.lang_combo.itemText(i) or lang == self.lang_combo.itemData(i):
                    self.lang_combo.setCurrentIndex(i)
                    break

        # Set Structure
        structure = preset.get("structure")
        if structure:
            idx = self.structure_combo.findText(structure)
            if idx >= 0:
                self.structure_combo.setCurrentIndex(idx)

        # Set Mood
        mood = preset.get("mood")
        if mood:
            idx = self.mood_combo.findText(mood)
            if idx >= 0:
                self.mood_combo.setCurrentIndex(idx)

        # Set Theme
        theme = preset.get("theme")
        if theme:
            idx = self.theme_combo.findText(theme)
            if idx >= 0:
                self.theme_combo.setCurrentIndex(idx)

        # Set Rhyme
        rhyme = preset.get("rhyme")
        if rhyme:
            idx = self.rhyme_combo.findText(rhyme)
            if idx >= 0:
                self.rhyme_combo.setCurrentIndex(idx)

        # Set BPM
        bpm_str = preset.get("bpm", "120")
        clean_bpm = "".join(filter(str.isdigit, bpm_str[:4]))
        if clean_bpm:
            self.bpm_spin.setValue(int(clean_bpm))

        # Set Notes
        self.custom_notes.setText(preset.get("user_notes", ""))

    def _emit_load_skeleton(self):
        preset_name = self.preset_combo.currentText()
        preset = ONE_CLICK_PRESETS.get(preset_name)

        if preset and preset.get("skeleton"):
            skeleton_text = preset["skeleton"]
        else:
            structure_name = self.structure_combo.currentText()
            tags = SONG_STRUCTURES.get(structure_name, [])
            skeleton_text = "\n\n".join(tags)

        self.load_skeleton_requested.emit(skeleton_text)
        self.status_label.setText("Loaded structure outline into Editor")

    def _on_region_changed(self, region_name: str):
        self.genre_combo.blockSignals(True)
        self.genre_combo.clear()
        genres = WORLD_REGIONS.get(region_name, {})
        self.genre_combo.addItems(list(genres.keys()))
        self.genre_combo.blockSignals(False)
        if self.genre_combo.count() > 0:
            self._on_genre_changed(self.genre_combo.currentText())

    def _on_genre_changed(self, genre_name: str):
        region_name = self.region_combo.currentText()
        genre_info = WORLD_REGIONS.get(region_name, {}).get(genre_name, {})
        if genre_info:
            bpm_val = genre_info.get("bpm", "120")
            self.bpm_badge.setText(f"BPM: {bpm_val}")
            self.meter_badge.setText(f"Meter: {genre_info.get('meter', '4/4')}")
            desc = genre_info.get("description", "")
            self.genre_desc.setText(desc[:45] + ("..." if len(desc) > 45 else ""))

            clean_bpm = "".join(filter(str.isdigit, bpm_val[:4]))
            if clean_bpm and self.preset_combo.currentIndex() <= 0:
                self.bpm_spin.setValue(int(clean_bpm))

            if not self.custom_notes.toPlainText().strip():
                sample = genre_info.get("sample_prompt", "")
                if sample:
                    self.custom_notes.setPlaceholderText(f"Sample idea: {sample[:40]}...")

    def get_generation_parameters(self) -> dict:
        return {
            "preset": self.preset_combo.currentText(),
            "region": self.region_combo.currentText(),
            "genre": self.genre_combo.currentText(),
            "language": self.lang_combo.currentData() or self.lang_combo.currentText(),
            "rhyme": self.rhyme_combo.currentText(),
            "bpm": f"{self.bpm_spin.value()} BPM",
            "structure": self.structure_combo.currentText(),
            "mood": self.mood_combo.currentText(),
            "theme": self.theme_combo.currentText(),
            "user_notes": self.custom_notes.toPlainText().strip()
        }

    def _emit_generate(self):
        self.status_label.setText("Composing with Gemini...")
        self.generate_requested.emit(self.get_generation_parameters())

    def _emit_demo(self):
        self.status_label.setText("Loaded genre demo track")
        self.demo_requested.emit(self.get_generation_parameters())

    def set_status(self, text: str):
        self.status_label.setText(text)

    def set_loading(self, is_loading: bool):
        self.btn_generate.setEnabled(not is_loading)
        self.btn_demo.setEnabled(not is_loading)
        if is_loading:
            self.btn_generate.setText("⏳ Composing Lyrics...")
        else:
            self.btn_generate.setText("✨ Generate Song with Gemini")
