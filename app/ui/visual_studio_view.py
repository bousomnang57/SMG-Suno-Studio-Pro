"""
Visual Interactive Studio View for Bisach Suno AI Lyric Writer / WorldLyric Studio.
Provides dynamic clickable pills for 30+ World Genres, Khmer Storylines,
Khmer Traditional Instruments, Master Sound Presets, and a Live Suno Formula Card.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QScrollArea, QFrame, QGridLayout,
    QComboBox, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal
from app.music_data import VISUAL_GENRE_PILLS, KHMER_STUDIO_TAGS, LANGUAGES, ENGLISH_STUDIO_TAGS
from app.chord_engine import ChordEngine, AudioChordSynthesizer, SEMITONES_SHARP
from app.ui.styles import get_theme

# ── 6 Master Studio Sound Presets (Berklee & Commercial Hit Profiles) ──
MASTER_PRESETS = [
    {
        "label": "🌟 Billboard Pop",
        "genre": "Billboard Pop & Synthwave",
        "bpm": "124 BPM",
        "key": "Am",
        "chords": ["Am", "F", "C", "G"],
        "prog_name": "vi - IV - I - V (Pop Axis)",
        "mood": "Euphoric & Uplifting",
        "instruments": "Analog Moog Bass, 80s LinnDrum, Juno-106 Synth Arps, Funk Guitar Strats",
        "vocals": "punchy high-energy lead vocal, soaring vocal belt, layered pop harmonies",
        "story": "Midnight Vintage Drive: Windows down on the coastal highway, city lights bleeding violet",
        "language": "English",
        "prompt": "80s synthpop, 124 BPM, Key: Am, punchy analog Moog bass, LinnDrum, Juno-106 synth arps, soaring female vocal belt, pristine modern radio master"
    },
    {
        "label": "🇰🇭 Kantrum Trap",
        "genre": "Khmer Kantrum Modern Trap Fusion",
        "bpm": "135 BPM",
        "key": "Dm",
        "chords": ["Dm", "Bb", "C", "Dm"],
        "prog_name": "i - VI - VII - i (Trap Minor)",
        "mood": "Fiery & High-Energy",
        "instruments": "Tro Sau, Roneat Ek, sliding 808 sub-bass, snappy hi-hat rolls, Skor Daey",
        "vocals": "dynamic rhythmic Khmer vocal, party ad-libs, festive vocal callouts",
        "story": "បុណ្យភូមិរាំវង់ (Village Festival Dance): សប្បាយរីករាយជួបជុំបងប្អូនរាំលេងកម្សាន្ត",
        "language": "Khmer (ភាសាខ្មែរ)",
        "prompt": "Khmer modern trap, 135 BPM, Key: Dm, Tro Sau, Roneat Ek, 808 sub-bass, snappy trap drums, energetic Khmer vocal chant, festive party bounce"
    },
    {
        "label": "🎙️ 70s Khmer Gold",
        "genre": "Khmer 60s-70s Golden Era Psychedelic Rock",
        "bpm": "118 BPM",
        "key": "Gm",
        "chords": ["Gm", "Cm", "D7", "Gm"],
        "prog_name": "i - iv - V7 - i (Sinn Sisamouth)",
        "mood": "Nostalgic & Romantic",
        "instruments": "Vintage Fuzz Guitar, Farfisa Organ, Warm Brass Horn Section, Analog Drums",
        "vocals": "emotive vintage crooner vocal, Sinn Sisamouth romantic timbre, warm tape slapback",
        "story": "ស្នេហ៍ក្នុងគ្រាអតីត (Golden Era Romance): អនុស្សាវរីយ៍ស្នេហ៍ផ្អែមល្ហែមសម័យសង្គមរាស្ត្រនិយម",
        "language": "Khmer (ភាសាខ្មែរ)",
        "prompt": "1970s Cambodian psychedelic garage rock, 118 BPM, Key: Gm, fuzz guitar riffs, vintage Farfisa organ, emotive male crooner, warm analog tape mastering"
    },
    {
        "label": "🌙 Lofi Midnight",
        "genre": "Lofi Chillhop & Bedroom Soul",
        "bpm": "78 BPM",
        "key": "Cmaj7",
        "chords": ["Dm7", "G7", "Cmaj7", "Am7"],
        "prog_name": "ii7 - V7 - Imaj7 - vi7 (Neo-Soul)",
        "mood": "Melancholic & Dreamy",
        "instruments": "Fender Rhodes MK1, Detuned Muted Guitar, Dusty Vinyl Crackle, Boombap Drums",
        "vocals": "whispered airy lead vocal, intimate bedroom close-mic, tape saturation",
        "story": "Late Night Thoughts: Staring at neon rain reflections outside the window at 2 AM",
        "language": "English",
        "prompt": "lofi hip hop, 78 BPM, Key: Cmaj7, dusty Fender Rhodes, detuned acoustic guitar, vinyl crackle, intimate whispered female vocal, chill aesthetic"
    },
    {
        "label": "⚡ Festival EDM",
        "genre": "Festival Progressive House & Big Room Drop",
        "bpm": "128 BPM",
        "key": "F",
        "chords": ["F", "G", "Am", "Em"],
        "prog_name": "IV - V - vi - iii (Royal Road)",
        "mood": "Triumphant & Euphoric",
        "instruments": "Super-saw Synth Chords, Pounding 4-on-the-floor Kick, White Noise Risers, Pluck Arps",
        "vocals": "soaring female vocal belt, chanted festival anthem hook, reverb stadium tail",
        "story": "Live Forever in the Bass: Unstoppable rush of unity under festival laser beams",
        "language": "English",
        "prompt": "festival progressive house, 128 BPM, Key: F, soaring vocal anthem, huge super-saw leads, emotional piano breakdown, massive stadium bass drop"
    },
    {
        "label": "☕ Indie Acoustic",
        "genre": "Indie Acoustic Folk & Cello",
        "bpm": "76 BPM",
        "key": "C",
        "chords": ["C", "G", "Am", "F"],
        "prog_name": "I - V - vi - IV (Pop Standard)",
        "mood": "Heartfelt & Nostalgic",
        "instruments": "Fingerpicked Martin Acoustic Guitar, Mournful Solo Cello, Foot Stomp Kick, Dulcimer",
        "vocals": "intimate breathy chest voice, vulnerable storytelling cadence, natural dynamic swell",
        "story": "Cardigan in the Cold Rain: Sitting in a roadside diner with memories of what was lost",
        "language": "English",
        "prompt": "indie folk ballad, 76 BPM, Key: C, fingerpicked acoustic guitar, mournful solo cello, intimate female breathy vocal, warm analog room acoustics"
    }
]


class FlowLayoutWidget(QWidget):
    """Container displaying child buttons in a wrapped, responsive grid flow."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_dark = False
        self.layout = QGridLayout(self)
        self.layout.setContentsMargins(2, 2, 2, 2)
        self.layout.setSpacing(6)
        self.col_count = 6

    def add_buttons(self, buttons: list, cols: int = 6):
        self.col_count = cols
        for i, btn in enumerate(buttons):
            row = i // cols
            col = i % cols
            self.layout.addWidget(btn, row, col)


class VisualStudioView(QWidget):
    generate_requested = pyqtSignal(dict)
    demo_requested = pyqtSignal(dict)
    open_editor_requested = pyqtSignal(dict)
    open_batch_requested = pyqtSignal(dict)
    export_bundle_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_dark = False

        # Current formula state (Default to English Billboard Pop)
        self.current_genre = "Billboard Pop & Synthwave"
        self.current_mood = "Euphoric & Uplifting"
        self.current_instruments = "Analog Moog Bass, 80s LinnDrum, Juno-106 Synth Arps, Funk Guitar Strats"
        self.current_vocals = "punchy high-energy lead vocal, soaring vocal belt, layered pop harmonies"
        self.current_bpm = "124 BPM"
        self.current_chords = ["Am", "F", "C", "G"]
        self.current_key = "Am"
        self.current_prog_name = "vi - IV - I - V (Pop Axis)"
        self.current_story = "Midnight Vintage Drive: Windows down on the coastal highway, city lights bleeding violet"
        self.current_language = "English"

        self.info_cards = []
        self.khmer_pill_btns = []
        self.english_style_btns = []
        self.english_story_btns = []
        self.english_mod_btns = []
        self.macro_btns = []
        self.preset_btns = []

        self._init_ui()
        self._update_formula_card()

    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(12)

        # Left/Center Stage: Scrollable exploration areas
        left_stage = QWidget()
        left_layout = QVBoxLayout(left_stage)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        # Main Title Header
        header_row = QHBoxLayout()
        self.title_lbl = QLabel("🎨 Visual Arranger & Sound Designer (ស្ទូឌីយោច្នៃបទ)")
        self.title_lbl.setStyleSheet("font-size: 18px; font-weight: 800; color: #1e293b;")
        header_row.addWidget(self.title_lbl)
        header_row.addStretch()
        left_layout.addLayout(header_row)

        # Top Category Buttons (Tabs)
        self.tab_bar = QFrame()
        self.tab_bar.setStyleSheet("background-color: #f1f5f9; border-radius: 10px; padding: 4px;")
        tab_layout = QHBoxLayout(self.tab_bar)
        tab_layout.setContentsMargins(4, 4, 4, 4)
        tab_layout.setSpacing(6)

        self.btn_tab_explore = QPushButton("🔍 ស្វែងរក (Explore)")
        self.btn_tab_explore.setCheckable(True)
        self.btn_tab_explore.setChecked(False)
        self.btn_tab_explore.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_tab_explore.clicked.connect(lambda: self._switch_tab(0))

        self.btn_tab_khmer = QPushButton("🇰🇭 តន្ត្រីខ្មែរ (Khmer Music)")
        self.btn_tab_khmer.setCheckable(True)
        self.btn_tab_khmer.setChecked(False)
        self.btn_tab_khmer.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_tab_khmer.clicked.connect(lambda: self._switch_tab(1))

        self.btn_tab_english = QPushButton("🌟 បទអង់គ្លេស (Billboard Hits)")
        self.btn_tab_english.setCheckable(True)
        self.btn_tab_english.setChecked(True)
        self.btn_tab_english.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_tab_english.clicked.connect(lambda: self._switch_tab(2))

        for btn in [self.btn_tab_explore, self.btn_tab_khmer, self.btn_tab_english]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #475569;
                    font-weight: 600;
                    padding: 7px 16px;
                    border: none;
                    border-radius: 7px;
                    font-size: 11.5px;
                }
                QPushButton:checked {
                    background-color: #ffffff;
                    color: #1e293b;
                    font-weight: 800;
                    border: 1px solid #cbd5e1;
                }
            """)
            tab_layout.addWidget(btn)

        tab_layout.addStretch()
        left_layout.addWidget(self.tab_bar)

        # Stack/Content Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background-color: transparent;")

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(12)

        # View 1: Explore Genres Grid
        self.view_explore = self._create_explore_view()
        self.content_layout.addWidget(self.view_explore)

        # View 2: Khmer Studio Tag View
        self.view_khmer = self._create_khmer_view()
        self.content_layout.addWidget(self.view_khmer)

        # View 3: English Studio Tag View
        self.view_english = self._create_english_view()
        self.content_layout.addWidget(self.view_english)

        scroll.setWidget(self.content_widget)
        left_layout.addWidget(scroll, stretch=1)
        main_layout.addWidget(left_stage, stretch=1)

        # Right Panel: Scrollable Song Formula Card (រូបមន្តបទរបស់អ្នក)
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setFrameShape(QFrame.Shape.NoFrame)
        right_scroll.setStyleSheet("background-color: transparent;")
        right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        right_scroll.setMinimumWidth(420)
        right_scroll.setMaximumWidth(465)

        right_panel = self._create_formula_panel()
        right_scroll.setWidget(right_panel)
        main_layout.addWidget(right_scroll, stretch=0)

        # Initial view: English Hits Studio
        self._switch_tab(2)

    def _switch_tab(self, index: int):
        self.btn_tab_explore.setChecked(index == 0)
        self.btn_tab_khmer.setChecked(index == 1)
        self.btn_tab_english.setChecked(index == 2)
        self.view_explore.setVisible(index == 0)
        self.view_khmer.setVisible(index == 1)
        self.view_english.setVisible(index == 2)

    # --- View 1: Explore View with 30+ Colorful Genre Pills ---
    def _create_explore_view(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # 3 Summary Cards
        summary_row = QHBoxLayout()
        summary_row.setSpacing(8)

        card1 = self._make_info_card("ស្វែងរកចង្វាក់", "រចនាបថពេញនិយម និងអារម្មណ៍ថ្មីៗ")
        card2 = self._make_info_card("គំនិតអាល់ប៊ុម", "ច្នៃលក្ខណៈ ១០ គំរូសម្រាប់អាល់ប៊ុម")
        card3 = self._make_info_card("ផែនការចេញបទ", "រៀបចំយុទ្ធសាស្ត្រចេញបទចម្រៀង")
        summary_row.addWidget(card1)
        summary_row.addWidget(card2)
        summary_row.addWidget(card3)
        layout.addLayout(summary_row)

        # Genre Title
        g_head = QHBoxLayout()
        self.lbl_g_head = QLabel("📈 ស្វែងរកចង្វាក់តន្ត្រីពិភពលោក (Global Genres)")
        self.lbl_g_head.setStyleSheet("font-size: 14px; font-weight: 700; color: #1e293b;")
        g_head.addWidget(self.lbl_g_head)
        g_head.addStretch()
        layout.addLayout(g_head)

        self.sub_g = QLabel("មិនទាន់មានគំនិត? ជ្រើសរើសប្រភេទមួយ ប្រព័ន្ធនឹងរៀបចំ Style Prompt និង Chords ដោយស្វ័យប្រវត្តិ។")
        self.sub_g.setStyleSheet("color: #64748b; font-size: 11.5px;")
        layout.addWidget(self.sub_g)

        # Pills Grid
        self.grid_frame = QFrame()
        self.grid_frame.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 10px;")
        grid_layout = QGridLayout(self.grid_frame)
        grid_layout.setSpacing(6)

        cols = 5
        for i, item in enumerate(VISUAL_GENRE_PILLS):
            btn = QPushButton(item["name"])
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            bg = item.get("bg", "#3b82f6")
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {bg};
                    color: #ffffff;
                    font-weight: 700;
                    font-size: 11px;
                    padding: 8px 10px;
                    border: none;
                    border-radius: 6px;
                }}
                QPushButton:hover {{
                    opacity: 0.9;
                    border: 2px solid #ffffff;
                }}
                QPushButton:pressed {{
                    background-color: #1e293b;
                }}
            """)
            btn.clicked.connect(lambda _, it=item: self._on_genre_pill_clicked(it))
            row = i // cols
            col = i % cols
            grid_layout.addWidget(btn, row, col)

        layout.addWidget(self.grid_frame)

        # Bottom language & custom text
        self.bottom_box = QFrame()
        self.bottom_box.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 10px;")
        b_layout = QVBoxLayout(self.bottom_box)
        b_layout.setSpacing(6)

        b_layout.addWidget(QLabel("ភាសាបទចម្រៀង (Song Language):"))
        self.lang_picker = QComboBox()
        for l in LANGUAGES:
            self.lang_picker.addItem(f"{l['name']} ({l['native']})", l["name"])
        self.lang_picker.setStyleSheet("padding: 5px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 11.5px;")
        self.lang_picker.currentIndexChanged.connect(lambda _: self._on_lang_changed())
        b_layout.addWidget(self.lang_picker)

        b_layout.addWidget(QLabel("គំនិតរបស់អ្នក (ស្រេចចិត្ត):"))
        self.explore_idea_input = QTextEdit()
        self.explore_idea_input.setPlaceholderText("បញ្ចូលប្រធានបទ គំនិត ឬឃ្លាដែលអ្នកចង់ឱ្យមានក្នុងបទ...")
        self.explore_idea_input.setMaximumHeight(55)
        self.explore_idea_input.setStyleSheet("border: 1px solid #cbd5e1; border-radius: 6px; padding: 5px; font-size: 11px;")
        b_layout.addWidget(self.explore_idea_input)

        layout.addWidget(self.bottom_box)
        return widget

    def _make_info_card(self, title: str, subtitle: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px;")
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(6, 6, 6, 6)
        c_layout.setSpacing(3)
        t = QLabel(title)
        t.setStyleSheet("font-weight: 700; color: #1e293b; font-size: 12px;")
        s = QLabel(subtitle)
        s.setStyleSheet("color: #64748b; font-size: 10.5px;")
        c_layout.addWidget(t)
        c_layout.addWidget(s)
        self.info_cards.append((card, t, s))
        return card

    # --- View 2: Khmer Studio View with Storylines & Instruments ---
    def _create_khmer_view(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Header with Randomize button
        top_bar = QHBoxLayout()
        self.khmer_title = QLabel("🇰🇭 តន្ត្រីខ្មែរ (Khmer Music Studio)")
        self.khmer_title.setStyleSheet("font-size: 15px; font-weight: 800; color: #1e293b;")
        top_bar.addWidget(self.khmer_title)
        top_bar.addStretch()

        self.btn_random_khmer = QPushButton("🎲 Auto-Pick Khmer (ចៃដន្យ)")
        self.btn_random_khmer.setStyleSheet("background-color: #f1f5f9; color: #2563eb; font-weight: 700; border: 1px solid #cbd5e1; border-radius: 6px; padding: 5px 12px; font-size: 11px;")
        self.btn_random_khmer.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_random_khmer.clicked.connect(self._auto_randomize_khmer)
        top_bar.addWidget(self.btn_random_khmer)
        layout.addLayout(top_bar)

        self.sub_text_khmer = QLabel("គ្មានគំនិត? ចុចលើសាច់រឿង និងឧបករណ៍ភ្លេងខាងក្រោម — ប្រព័ន្ធនឹងរៀបចំ Style Prompt និង Chord Progression ដោយស្វ័យប្រវត្តិ!")
        self.sub_text_khmer.setStyleSheet("color: #64748b; font-size: 11.5px;")
        layout.addWidget(self.sub_text_khmer)

        # Section 1: Storylines
        self.khmer_story_box = QFrame()
        self.khmer_story_box.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 10px;")
        s_layout = QVBoxLayout(self.khmer_story_box)
        s_layout.setSpacing(8)

        s_title = QLabel("❶ សាច់រឿងខ្មែរ (បទនេះនិយាយពីអ្វី?)")
        s_title.setStyleSheet("font-weight: 700; color: #1e293b; font-size: 12.5px;")
        s_layout.addWidget(s_title)

        s_layout.addWidget(QLabel("រឿងស្នេហា • Love Stories:"))
        s_layout.addWidget(self._create_pills_flow(
            KHMER_STUDIO_TAGS["storylines"]["love_stories"],
            lambda item: self._on_story_pill_clicked(item)
        ))

        s_layout.addWidget(QLabel("ជីវិត និងគ្រួសារ • Life & Family:"))
        s_layout.addWidget(self._create_pills_flow(
            KHMER_STUDIO_TAGS["storylines"]["life_and_family"],
            lambda item: self._on_story_pill_clicked(item)
        ))

        s_layout.addWidget(QLabel("ពិធីបុណ្យ • Festivals & Occasions:"))
        s_layout.addWidget(self._create_pills_flow(
            KHMER_STUDIO_TAGS["storylines"]["festivals_and_occasions"],
            lambda item: self._on_story_pill_clicked(item)
        ))
        layout.addWidget(self.khmer_story_box)

        # Section 2: Musical Styles & Instruments
        self.khmer_inst_box = QFrame()
        self.khmer_inst_box.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 10px;")
        i_layout = QVBoxLayout(self.khmer_inst_box)
        i_layout.setSpacing(8)

        i_title = QLabel("❷ សំឡេងភ្លេង និងឧបករណ៍បុរាណ-សម័យ (Sound Design & Instruments)")
        i_title.setStyleSheet("font-weight: 700; color: #1e293b; font-size: 12.5px;")
        i_layout.addWidget(i_title)

        i_layout.addWidget(self._create_pills_flow(
            KHMER_STUDIO_TAGS["music_styles_and_instruments"],
            lambda item: self._on_inst_pill_clicked(item)
        ))
        layout.addWidget(self.khmer_inst_box)

        return widget

    def _create_pills_flow(self, items: list, callback) -> QWidget:
        container = QWidget()
        grid = QGridLayout(container)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(6)

        cols = 3
        for i, item in enumerate(items):
            kh_txt = item.get("kh", "")
            en_txt = item.get("en", "")
            btn = QPushButton(f"{kh_txt}\n{en_txt}")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #f8fafc;
                    color: #334155;
                    border: 1px solid #e2e8f0;
                    border-radius: 6px;
                    padding: 5px 8px;
                    font-size: 10.5px;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #eff6ff;
                    border-color: #93c5fd;
                    color: #1d4ed8;
                }
                QPushButton:pressed {
                    background-color: #2563eb;
                    color: #ffffff;
                }
            """)
            btn.clicked.connect(lambda _, it=item: callback(it))
            self.khmer_pill_btns.append(btn)
            row = i // cols
            col = i % cols
            grid.addWidget(btn, row, col)

        return container

    # --- View 3: English Hits Studio with Billboard Styles, Storylines & Pro Modifiers ---
    def _create_english_view(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Header with Randomize button
        top_bar = QHBoxLayout()
        self.en_title = QLabel("🌟 បទអង់គ្លេសលំដាប់ពិភពលោក (English Hits Studio)")
        self.en_title.setStyleSheet("font-size: 15px; font-weight: 800; color: #1e293b;")
        top_bar.addWidget(self.en_title)
        top_bar.addStretch()

        self.btn_random_en = QPushButton("🎲 Auto-Pick Hit (ចៃដន្យ)")
        self.btn_random_en.setStyleSheet("background-color: #eff6ff; color: #2563eb; font-weight: 700; border: 1px solid #bfdbfe; border-radius: 6px; padding: 5px 12px; font-size: 11px;")
        self.btn_random_en.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_random_en.clicked.connect(self._auto_randomize_english)
        top_bar.addWidget(self.btn_random_en)
        layout.addLayout(top_bar)

        self.sub_text_en = QLabel("ជ្រើសរើសរចនាបថតន្ត្រី Billboard (Max Martin, Taylor Swift, Billie Eilish, Coldplay, Adele) និងសាច់រឿង — ប្រព័ន្ធនឹងរៀបចំ Style Prompt សម្រាប់ Suno/Udio ភ្លាមៗ!")
        self.sub_text_en.setStyleSheet("color: #64748b; font-size: 11.5px; line-height: 1.3;")
        self.sub_text_en.setWordWrap(True)
        layout.addWidget(self.sub_text_en)

        # Section 1: Billboard & Suno Production Styles
        self.english_style_box = QFrame()
        self.english_style_box.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 10px;")
        st_layout = QVBoxLayout(self.english_style_box)
        st_layout.setSpacing(8)

        self.st_title = QLabel("❶ រចនាបថតន្ត្រីពេញនិយម (Billboard & Streaming Sound Design)")
        self.st_title.setStyleSheet("font-weight: 800; color: #1e293b; font-size: 12.5px;")
        st_layout.addWidget(self.st_title)

        styles_grid = QWidget()
        s_g_layout = QGridLayout(styles_grid)
        s_g_layout.setContentsMargins(0, 0, 0, 0)
        s_g_layout.setSpacing(6)

        for i, s_item in enumerate(ENGLISH_STUDIO_TAGS["production_styles"]):
            s_btn = QPushButton(f"{s_item['name']}\n{s_item['bpm']} • {s_item['genre']}\nChords: {' - '.join(s_item['chords'])}")
            s_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            s_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f8fafc;
                    color: #1e293b;
                    border: 1px solid #cbd5e1;
                    border-radius: 6px;
                    padding: 6px 8px;
                    font-size: 10.5px;
                    font-weight: 600;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #f0fdf4;
                    border-color: #86efac;
                    color: #15803d;
                }
                QPushButton:pressed {
                    background-color: #16a34a;
                    color: #ffffff;
                }
            """)
            s_btn.clicked.connect(lambda _, it=s_item: self._on_english_style_clicked(it))
            self.english_style_btns.append(s_btn)
            row = i // 2
            col = i % 2
            s_g_layout.addWidget(s_btn, row, col)

        st_layout.addWidget(styles_grid)
        layout.addWidget(self.english_style_box)

        # Section 2: Storylines & Themes
        self.english_story_box = QFrame()
        self.english_story_box.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 10px;")
        s_layout = QVBoxLayout(self.english_story_box)
        s_layout.setSpacing(8)

        self.s_title = QLabel("❷ សាច់រឿងភាសាអង់គ្លេស (Song Themes & Emotional Stories)")
        self.s_title.setStyleSheet("font-weight: 800; color: #1e293b; font-size: 12.5px;")
        s_layout.addWidget(self.s_title)

        s_layout.addWidget(QLabel("💔 Heartbreak, Regrets & Moving On:"))
        s_layout.addWidget(self._create_english_story_flow(ENGLISH_STUDIO_TAGS["storylines"]["heartbreak_and_memories"]))

        s_layout.addWidget(QLabel("✨ Euphoric Romance & Midnight Drives:"))
        s_layout.addWidget(self._create_english_story_flow(ENGLISH_STUDIO_TAGS["storylines"]["romance_and_nightlife"]))

        s_layout.addWidget(QLabel("🔥 Hustle, Ambition & Winning:"))
        s_layout.addWidget(self._create_english_story_flow(ENGLISH_STUDIO_TAGS["storylines"]["ambition_and_confidence"]))

        s_layout.addWidget(QLabel("🌌 Dark Alt-Pop & Late-Night Thoughts:"))
        s_layout.addWidget(self._create_english_story_flow(ENGLISH_STUDIO_TAGS["storylines"]["dark_and_psychological"]))

        s_layout.addWidget(QLabel("🏟️ Stadium Resilience & Triumph:"))
        s_layout.addWidget(self._create_english_story_flow(ENGLISH_STUDIO_TAGS["storylines"]["stadium_resilience_and_hope"]))

        layout.addWidget(self.english_story_box)

        # Section 3: One-Click Suno / Udio Pro Modifiers
        self.english_mod_box = QFrame()
        self.english_mod_box.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 10px;")
        m_layout = QVBoxLayout(self.english_mod_box)
        m_layout.setSpacing(8)

        self.m_title = QLabel("❸ ប៊ូតុងបន្ថែម Tag ពិសេស (Suno / Udio One-Click Vocal & Sound Tags)")
        self.m_title.setStyleSheet("font-weight: 800; color: #1e293b; font-size: 12.5px;")
        m_layout.addWidget(self.m_title)

        tag_flow = QWidget()
        t_grid = QGridLayout(tag_flow)
        t_grid.setContentsMargins(0, 0, 0, 0)
        t_grid.setSpacing(5)

        for i, mod in enumerate(ENGLISH_STUDIO_TAGS["pro_modifiers"]):
            tag_btn = QPushButton(mod["label"])
            tag_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            tag_btn.setStyleSheet("""
                QPushButton {
                    background-color: #fdf4ff;
                    color: #86198f;
                    border: 1px solid #f0abfc;
                    border-radius: 5px;
                    padding: 5px 8px;
                    font-size: 10.5px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #fae8ff;
                    border-color: #d946ef;
                    color: #701a75;
                }
                QPushButton:pressed {
                    background-color: #c026d3;
                    color: #ffffff;
                }
            """)
            tag_btn.clicked.connect(lambda _, t=mod["tag"]: self._on_pro_modifier_clicked(t))
            self.english_mod_btns.append(tag_btn)
            row = i // 4
            col = i % 4
            t_grid.addWidget(tag_btn, row, col)

        m_layout.addWidget(tag_flow)
        layout.addWidget(self.english_mod_box)

        return widget

    def _create_english_story_flow(self, items: list) -> QWidget:
        container = QWidget()
        grid = QGridLayout(container)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(5)

        cols = 3
        for i, item in enumerate(items):
            title = item.get("title", "")
            desc = item.get("desc", "")
            btn = QPushButton(f"{title}\n{desc[:38]}...")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #f8fafc;
                    color: #334155;
                    border: 1px solid #e2e8f0;
                    border-radius: 6px;
                    padding: 5px 8px;
                    font-size: 10px;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #eff6ff;
                    border-color: #93c5fd;
                    color: #1d4ed8;
                }
                QPushButton:pressed {
                    background-color: #2563eb;
                    color: #ffffff;
                }
            """)
            btn.clicked.connect(lambda _, it=item: self._on_english_story_clicked(it))
            self.english_story_btns.append(btn)
            row = i // cols
            col = i % cols
            grid.addWidget(btn, row, col)

        return container

    # --- Right Panel: Live Song Formula Card (រូបមន្តបទរបស់អ្នក) ---
    def _create_formula_panel(self) -> QFrame:
        self.formula_card = QFrame()
        self.formula_card.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 6px 8px;")
        layout = QVBoxLayout(self.formula_card)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        # Header with Pro Auditor Status
        h_row = QHBoxLayout()
        self.lbl_formula_title = QLabel("✨ រូបមន្តបទរបស់អ្នក")
        self.lbl_formula_title.setStyleSheet("font-size: 13.5px; font-weight: 800; color: #1e293b;")
        h_row.addWidget(self.lbl_formula_title)
        h_row.addStretch()

        badge_gemini = QLabel("GMIV-C Pro")
        badge_gemini.setStyleSheet("color: #6366f1; font-weight: 800; font-size: 10px; background: #e0e7ff; padding: 2px 6px; border-radius: 4px;")
        h_row.addWidget(badge_gemini)
        layout.addLayout(h_row)

        # Pro Readiness Score Badge
        self.lbl_pro_status = QLabel("⭐ Pro Ready: Optimal Keyword Density")
        self.lbl_pro_status.setWordWrap(True)
        self.lbl_pro_status.setStyleSheet("background: #ecfdf5; color: #047857; font-weight: 700; font-size: 9.5px; padding: 3px 6px; border-radius: 5px; border: 1px solid #a7f3d0;")
        layout.addWidget(self.lbl_pro_status)

        # ── 1-Click Master Sound Design Presets ──
        self.preset_frame = QFrame()
        self.preset_frame.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 3px;")
        p_layout = QVBoxLayout(self.preset_frame)
        p_layout.setContentsMargins(3, 3, 3, 3)
        p_layout.setSpacing(3)

        self.lbl_presets_head = QLabel("⚡ Master Presets (ចុច ១ ដង):")
        self.lbl_presets_head.setStyleSheet("font-size: 9.5px; font-weight: 800; color: #475569;")
        p_layout.addWidget(self.lbl_presets_head)

        preset_grid = QGridLayout()
        preset_grid.setContentsMargins(0, 0, 0, 0)
        preset_grid.setSpacing(3)

        for idx, p_item in enumerate(MASTER_PRESETS):
            p_btn = QPushButton(p_item["label"])
            p_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            p_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ffffff;
                    color: #1e293b;
                    font-size: 9px;
                    font-weight: 700;
                    border: 1px solid #cbd5e1;
                    border-radius: 4px;
                    padding: 3px 3px;
                }
                QPushButton:hover {
                    background-color: #eff6ff;
                    border-color: #3b82f6;
                    color: #1d4ed8;
                }
            """)
            p_btn.clicked.connect(lambda _, it=p_item: self._load_master_preset(it))
            self.preset_btns.append(p_btn)
            row = idx // 3
            col = idx % 3
            preset_grid.addWidget(p_btn, row, col)

        p_layout.addLayout(preset_grid)
        layout.addWidget(self.preset_frame)

        # G, M, I, V, C rows
        self.lbl_g = self._create_gmiv_row(layout, "G", "Billboard Pop & Synthwave", "#2563eb")
        self.lbl_m = self._create_gmiv_row(layout, "M", "Euphoric & Uplifting", "#7c3aed")
        self.lbl_i = self._create_gmiv_row(layout, "I", "Analog Moog Bass, 80s LinnDrum, Juno-106 Synth Arps", "#059669")
        self.lbl_v = self._create_gmiv_row(layout, "V", "punchy high-energy lead vocal, soaring vocal belt", "#d97706")
        self.lbl_c = self._create_gmiv_row(layout, "C", "[Am] - [F] - [C] - [G]  (vi - IV - I - V Pop Axis)", "#8b5cf6")

        # ── Compact Music Control Bar: Key, Transpose, BPM & Synth Audition ──
        key_bpm_bar = QHBoxLayout()
        key_bpm_bar.setSpacing(4)

        self.lbl_k = QLabel("Key:")
        self.lbl_k.setStyleSheet("font-size: 10px; font-weight: 700; color: #475569;")
        key_bpm_bar.addWidget(self.lbl_k)

        self.key_combo = QComboBox()
        self.key_combo.addItems(["Am", "C", "Dm", "F", "Em", "G", "Bm", "D", "F#m", "A", "C#m", "E", "Gm", "Bb", "Cm", "Eb"])
        self.key_combo.setCurrentText(self.current_key)
        self.key_combo.setStyleSheet("padding: 2px 4px; font-size: 10px; font-weight: 700; border: 1px solid #cbd5e1; border-radius: 4px;")
        self.key_combo.currentTextChanged.connect(self._on_key_selected)
        key_bpm_bar.addWidget(self.key_combo)

        self.btn_trans_down = QPushButton("♭")
        self.btn_trans_down.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_trans_down.setToolTip("Transpose down -1 semitone")
        self.btn_trans_down.setFixedSize(20, 20)
        self.btn_trans_down.setStyleSheet("background-color: #f8fafc; color: #334155; border: 1px solid #cbd5e1; border-radius: 3px; font-size: 10px; font-weight: 700;")
        self.btn_trans_down.clicked.connect(lambda: self._transpose_chords(-1))
        key_bpm_bar.addWidget(self.btn_trans_down)

        self.btn_trans_up = QPushButton("♯")
        self.btn_trans_up.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_trans_up.setToolTip("Transpose up +1 semitone")
        self.btn_trans_up.setFixedSize(20, 20)
        self.btn_trans_up.setStyleSheet("background-color: #f8fafc; color: #334155; border: 1px solid #cbd5e1; border-radius: 3px; font-size: 10px; font-weight: 700;")
        self.btn_trans_up.clicked.connect(lambda: self._transpose_chords(1))
        key_bpm_bar.addWidget(self.btn_trans_up)

        key_bpm_bar.addSpacing(4)

        self.btn_bpm_minus = QPushButton("-")
        self.btn_bpm_minus.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_bpm_minus.setFixedSize(18, 20)
        self.btn_bpm_minus.setStyleSheet("background-color: #f8fafc; color: #334155; border: 1px solid #cbd5e1; border-radius: 3px; font-size: 10px; font-weight: 700;")
        self.btn_bpm_minus.clicked.connect(lambda: self._adjust_bpm(-5))
        key_bpm_bar.addWidget(self.btn_bpm_minus)

        self.lbl_bpm_display = QLabel(self.current_bpm)
        self.lbl_bpm_display.setStyleSheet("font-size: 10.5px; font-weight: 800; color: #2563eb;")
        key_bpm_bar.addWidget(self.lbl_bpm_display)

        self.btn_bpm_plus = QPushButton("+")
        self.btn_bpm_plus.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_bpm_plus.setFixedSize(18, 20)
        self.btn_bpm_plus.setStyleSheet("background-color: #f8fafc; color: #334155; border: 1px solid #cbd5e1; border-radius: 3px; font-size: 10px; font-weight: 700;")
        self.btn_bpm_plus.clicked.connect(lambda: self._adjust_bpm(5))
        key_bpm_bar.addWidget(self.btn_bpm_plus)

        key_bpm_bar.addStretch()

        self.btn_vs_play_chords = QPushButton("🔊 Chords")
        self.btn_vs_play_chords.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_vs_play_chords.setToolTip("Audition progression with live synth")
        self.btn_vs_play_chords.setStyleSheet("background-color: #f5f3ff; color: #7c3aed; font-weight: 700; font-size: 10px; border: 1px solid #ddd6fe; border-radius: 4px; padding: 2px 7px;")
        self.btn_vs_play_chords.clicked.connect(self._play_vs_chords)
        key_bpm_bar.addWidget(self.btn_vs_play_chords)

        self.btn_vs_stop_chords = QPushButton("⏹")
        self.btn_vs_stop_chords.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_vs_stop_chords.setFixedSize(20, 20)
        self.btn_vs_stop_chords.setStyleSheet("background-color: #f1f5f9; color: #475569; font-weight: 600; font-size: 10px; border: 1px solid #cbd5e1; border-radius: 4px;")
        self.btn_vs_stop_chords.clicked.connect(self._stop_vs_chords)
        key_bpm_bar.addWidget(self.btn_vs_stop_chords)

        layout.addLayout(key_bpm_bar)

        # ── Combined Target Engine & Style Prompt Header Bar ──
        suno_head = QHBoxLayout()
        suno_head.setSpacing(4)

        self.eng_lbl = QLabel("Engine:")
        self.eng_lbl.setStyleSheet("font-weight: 700; font-size: 10px; color: #475569;")
        suno_head.addWidget(self.eng_lbl)

        self.vs_engine_combo = QComboBox()
        self.vs_engine_combo.addItems([
            "Suno v6 Master (400c - HDR)",
            "Suno v4.5 (350c - HiFi)",
            "Suno v4 / v3.5 (200c - Fast)",
            "Suno v3 (120c - Legacy)",
            "Udio v1.5 / v2 (350c - Prose)"
        ])
        self.vs_engine_combo.setCurrentIndex(2) # Default Suno v4/v3.5 (200 Chars)
        self.vs_engine_combo.setStyleSheet("padding: 2px 4px; font-size: 10px; font-weight: 600; border: 1px solid #cbd5e1; border-radius: 4px;")
        self.vs_engine_combo.currentIndexChanged.connect(lambda _: self._on_prompt_text_changed())
        suno_head.addWidget(self.vs_engine_combo)

        suno_head.addStretch()

        self.lbl_char_count = QLabel("0 / 200 chars")
        self.lbl_char_count.setStyleSheet("font-size: 10px; font-weight: 800; color: #059669; background: #ecfdf5; padding: 2px 6px; border-radius: 4px;")
        suno_head.addWidget(self.lbl_char_count)
        layout.addLayout(suno_head)

        self.prompt_box_frame = QFrame()
        self.prompt_box_frame.setStyleSheet("background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 3px;")
        p_inner_layout = QVBoxLayout(self.prompt_box_frame)
        p_inner_layout.setContentsMargins(3, 2, 3, 2)
        p_inner_layout.setSpacing(3)

        self.txt_suno_prompt = QTextEdit()
        self.txt_suno_prompt.setReadOnly(False)
        self.txt_suno_prompt.setStyleSheet("background: transparent; border: none; font-size: 11px; color: #334155;")
        self.txt_suno_prompt.setMaximumHeight(42)
        self.txt_suno_prompt.textChanged.connect(self._on_prompt_text_changed)
        p_inner_layout.addWidget(self.txt_suno_prompt)

        # Action Toolbar (Optimize, Cues, Convert, Humanize, Copy)
        # Using tight spacing and compact labels so NO text ever truncates
        prompt_actions = QHBoxLayout()
        prompt_actions.setSpacing(3)

        self.btn_optimize = QPushButton("✨ Optimize")
        self.btn_optimize.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_optimize.setToolTip("Smart-compress prompt into engine sweet spot with zero truncation risk")
        self.btn_optimize.setStyleSheet("background-color: #fdf4ff; color: #86198f; border: 1px solid #f0abfc; border-radius: 4px; padding: 3px 5px; font-size: 9.5px; font-weight: 700;")
        self.btn_optimize.clicked.connect(self._optimize_prompt)
        prompt_actions.addWidget(self.btn_optimize)

        self.btn_studio_cues = QPushButton("⚡ Cues")
        self.btn_studio_cues.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_studio_cues.setToolTip("Inject Suno v6 Studio Cues [Tempo] [Key] [Spatial Stereo] into prompt")
        self.btn_studio_cues.setStyleSheet("background-color: #fefce8; color: #854d0e; border: 1px solid #fde047; border-radius: 4px; padding: 3px 5px; font-size: 9.5px; font-weight: 700;")
        self.btn_studio_cues.clicked.connect(self._inject_studio_cues)
        prompt_actions.addWidget(self.btn_studio_cues)

        self.btn_convert = QPushButton("🔄 Convert")
        self.btn_convert.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_convert.setToolTip("Toggle between Suno dense keyword tags and Udio flowing narrative prose")
        self.btn_convert.setStyleSheet("background-color: #f0fdf4; color: #166534; border: 1px solid #bbf7d0; border-radius: 4px; padding: 3px 5px; font-size: 9.5px; font-weight: 600;")
        self.btn_convert.clicked.connect(self._convert_syntax)
        prompt_actions.addWidget(self.btn_convert)

        self.btn_humanize_style = QPushButton("👤 Humanize")
        self.btn_humanize_style.setToolTip("Inject organic human live pocket, analog tape warmth, and room mic bleed")
        self.btn_humanize_style.setStyleSheet("background-color: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; border-radius: 4px; padding: 3px 5px; font-size: 9.5px; font-weight: 700;")
        self.btn_humanize_style.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_humanize_style.clicked.connect(self._humanize_current_style)
        prompt_actions.addWidget(self.btn_humanize_style)

        self.btn_copy = QPushButton("📋 Copy")
        self.btn_copy.setStyleSheet("background-color: #ffffff; color: #475569; border: 1px solid #cbd5e1; border-radius: 4px; padding: 3px 5px; font-size: 9.5px; font-weight: 600;")
        self.btn_copy.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_copy.clicked.connect(self._copy_prompt)
        prompt_actions.addWidget(self.btn_copy)

        p_inner_layout.addLayout(prompt_actions)
        layout.addWidget(self.prompt_box_frame)

        # Suno Lyrics Metatags & Section Macros Drawer
        self.macro_box = QFrame()
        self.macro_box.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 4px;")
        m_inner = QVBoxLayout(self.macro_box)
        m_inner.setContentsMargins(4, 4, 4, 4)
        m_inner.setSpacing(4)

        m_header = QHBoxLayout()
        self.lbl_macro = QLabel("🏷️ ស្លាកផ្នែកបទ (Section Metatags):")
        self.lbl_macro.setStyleSheet("font-weight: 700; font-size: 10px; color: #1e293b;")
        m_header.addWidget(self.lbl_macro)
        m_header.addStretch()

        self.lbl_macro_status = QLabel("")
        self.lbl_macro_status.setStyleSheet("color: #059669; font-size: 9.5px; font-weight: 600;")
        m_header.addWidget(self.lbl_macro_status)
        m_inner.addLayout(m_header)

        macro_flow = QWidget()
        mf_grid = QGridLayout(macro_flow)
        mf_grid.setContentsMargins(0, 0, 0, 0)
        mf_grid.setSpacing(3)

        macros = [
            "[Intro]", "[Verse 1]", "[Pre-Chorus]", "[Chorus]",
            "[Post-Chorus]", "[Drop]", "[Bridge]", "[Guitar Solo]",
            "[Outro]", "[End]", "[Female Belt]", "[Sub-Bass 808]"
        ]
        for idx, tag in enumerate(macros):
            t_btn = QPushButton(tag)
            t_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            t_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ffffff;
                    color: #475569;
                    border: 1px solid #cbd5e1;
                    border-radius: 3px;
                    padding: 2px 2px;
                    font-size: 8.5px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #eff6ff;
                    border-color: #3b82f6;
                    color: #1d4ed8;
                }
            """)
            t_btn.clicked.connect(lambda _, t=tag: self._copy_macro_tag(t))
            self.macro_btns.append(t_btn)
            mf_grid.addWidget(t_btn, idx // 4, idx % 4)

        m_inner.addWidget(macro_flow)

        self.btn_copy_template = QPushButton("📋 ចម្លងទម្រង់បទ Suno (Copy Template)")
        self.btn_copy_template.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_copy_template.setStyleSheet("background-color: #f0fdf4; color: #15803d; border: 1px solid #86efac; border-radius: 4px; padding: 4px 6px; font-size: 10px; font-weight: 700;")
        self.btn_copy_template.clicked.connect(self._copy_suno_lyric_template)
        m_inner.addWidget(self.btn_copy_template)

        layout.addWidget(self.macro_box)

        # ── Compact Negative Styles Row ──
        neg_row = QHBoxLayout()
        neg_row.setSpacing(4)
        self.lbl_neg_head = QLabel("Neg:")
        self.lbl_neg_head.setStyleSheet("font-weight: 700; font-size: 10px; color: #475569;")
        neg_row.addWidget(self.lbl_neg_head)

        self.txt_negative = QLineEdit("low quality, noisy mixing, distorted, harsh screaming, clipping, muddy bass")
        self.txt_negative.setStyleSheet("background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 4px; font-size: 10px; color: #64748b; padding: 2px 6px;")
        neg_row.addWidget(self.txt_negative)
        layout.addLayout(neg_row)

        # Primary Generate Button (dynamically updated text)
        self.btn_generate = QPushButton("✨ បង្កើតបទចម្រៀង (Generate Lyrics)")
        self.btn_generate.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_generate.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563eb, stop:1 #3b82f6);
                color: #ffffff;
                font-weight: 700;
                font-size: 11px;
                padding: 6px;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #1d4ed8;
            }
        """)
        self.btn_generate.clicked.connect(self._emit_generate)
        layout.addWidget(self.btn_generate)

        # Secondary Actions (4 items with compact width so zero clipping occurs)
        action_row = QHBoxLayout()
        action_row.setSpacing(4)

        self.btn_demo = QPushButton("🎵 បទគំរូ")
        self.btn_demo.setStyleSheet("background-color: #f1f5f9; color: #2563eb; border: 1px solid #cbd5e1; border-radius: 5px; padding: 6px; font-size: 10.5px; font-weight: 600;")
        self.btn_demo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_demo.clicked.connect(self._emit_demo)
        action_row.addWidget(self.btn_demo)

        self.btn_editor = QPushButton("📝 Editor")
        self.btn_editor.setStyleSheet("background-color: #f1f5f9; color: #475569; border: 1px solid #cbd5e1; border-radius: 5px; padding: 6px; font-size: 10.5px; font-weight: 600;")
        self.btn_editor.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_editor.clicked.connect(self._emit_open_editor)
        action_row.addWidget(self.btn_editor)

        self.btn_batch = QPushButton("⚡ Batch Pro")
        self.btn_batch.setToolTip("Produce 20 takes from this formula in Batch Studio Pro")
        self.btn_batch.setStyleSheet("background-color: #faf5ff; color: #7c3aed; border: 1px solid #d8b4fe; border-radius: 5px; padding: 6px; font-size: 10.5px; font-weight: 700;")
        self.btn_batch.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_batch.clicked.connect(self._emit_open_batch)
        action_row.addWidget(self.btn_batch)

        self.btn_pack = QPushButton("📦 Export DAW")
        self.btn_pack.setToolTip("Export Complete DAW Arrangement Project (.zip)")
        self.btn_pack.setStyleSheet("background-color: #f0fdf4; color: #166534; border: 1px solid #bbf7d0; border-radius: 5px; padding: 6px; font-size: 10.5px; font-weight: 700;")
        self.btn_pack.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_pack.clicked.connect(lambda: self.export_bundle_requested.emit())
        action_row.addWidget(self.btn_pack)

        layout.addLayout(action_row)
        layout.addStretch()
        return self.formula_card

    def _create_gmiv_row(self, parent_layout, letter: str, default_val: str, color: str) -> QLabel:
        row = QHBoxLayout()
        row.setSpacing(4)
        row.setContentsMargins(0, 0, 0, 0)

        badge = QLabel(f" {letter} ")
        badge.setStyleSheet(f"background-color: {color}; color: #ffffff; font-weight: 700; font-size: 9.5px; border-radius: 3px; padding: 1px 3px;")
        badge.setFixedWidth(18)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row.addWidget(badge)

        val_label = QLabel(default_val)
        val_label.setStyleSheet("color: #334155; font-size: 10px;")
        val_label.setWordWrap(True)
        row.addWidget(val_label, stretch=1)

        parent_layout.addLayout(row)
        return val_label

    def _get_engine_char_limit(self) -> int:
        if hasattr(self, "vs_engine_combo"):
            eng_txt = self.vs_engine_combo.currentText()
            if "400" in eng_txt:
                return 400
            elif "350" in eng_txt:
                return 350
            elif "120" in eng_txt:
                return 120
            elif "200" in eng_txt:
                return 200
        return 200

    def _load_master_preset(self, p_item: dict):
        """Instantly loads one of the 6 Master Sound Design Presets into the Formula Card."""
        self.current_genre = p_item["genre"]
        self.current_bpm = p_item["bpm"]
        self.current_key = p_item["key"]
        self.current_chords = list(p_item["chords"])
        self.current_prog_name = p_item.get("prog_name", "")
        self.current_mood = p_item["mood"]
        self.current_instruments = p_item["instruments"]
        self.current_vocals = p_item["vocals"]
        self.current_story = p_item["story"]
        self.current_language = p_item["language"]

        # If it's a Khmer preset, switch to Khmer tab for visual alignment
        if "Khmer" in self.current_language and hasattr(self, "btn_tab_khmer"):
            self._switch_tab(1)
        elif "English" in self.current_language and hasattr(self, "btn_tab_english"):
            self._switch_tab(2)

        self._update_formula_card()
        if p_item.get("prompt"):
            self.txt_suno_prompt.setPlainText(p_item["prompt"])
            self._on_prompt_text_changed()

        if hasattr(self, "lbl_macro_status"):
            self.lbl_macro_status.setText(f"⭐ Loaded: {p_item['label']} ({self.current_bpm})!")

    # --- Callbacks when Pills are Clicked ---
    def _on_genre_pill_clicked(self, item: dict):
        self.current_genre = item.get("name", "Pop")
        self.current_bpm = item.get("bpm", "120 BPM")
        self.current_mood = item.get("mood", "Vibrant")
        self.current_instruments = item.get("instruments", "guitars, synths, drums")
        self.current_vocals = item.get("vocals", "melodic lead vocal")

        if "K-Pop" in self.current_genre or "J-Pop" in self.current_genre or "Anime" in self.current_genre:
            self.current_chords = ["F", "G", "Em", "Am"]
            self.current_key = "F"
            self.current_prog_name = "IV - V - iii - vi (Royal Road)"
        elif "Khmer" in self.current_genre:
            self.current_chords = ["Am", "Dm", "E7", "Am"]
            self.current_key = "Am"
            self.current_prog_name = "i - iv - V7 - i (Sinn Sisamouth)"
        elif "R&B" in self.current_genre or "Soul" in self.current_genre:
            self.current_chords = ["Dm7", "G7", "Cmaj7", "Am7"]
            self.current_key = "Dm7"
            self.current_prog_name = "ii7 - V7 - Imaj7 - vi7 (Neo-Soul)"
        elif "Reggaeton" in self.current_genre or "Latin" in self.current_genre:
            self.current_chords = ["Dm", "Bb", "C", "Dm"]
            self.current_key = "Dm"
            self.current_prog_name = "i - VI - VII - i (Dem-bow)"
        elif "Rock" in self.current_genre or "Metal" in self.current_genre:
            self.current_chords = ["Am", "F", "C", "G"]
            self.current_key = "Am"
            self.current_prog_name = "vi - IV - I - V (Axis Minor)"
        else:
            self.current_chords = ["C", "G", "Am", "F"]
            self.current_key = "C"
            self.current_prog_name = "I - V - vi - IV (Pop Standard)"

        self._update_formula_card()

    def _on_story_pill_clicked(self, item: dict):
        self.current_story = f"{item.get('kh', '')} ({item.get('en', '')}): {item.get('prompt', '')}"
        self.current_language = "Khmer (ភាសាខ្មែរ)"
        self._update_formula_card()

    def _on_inst_pill_clicked(self, item: dict):
        self.current_genre = f"Khmer {item.get('kh', '')} Fusion"
        self.current_instruments = item.get("instruments", "Tro, Roneat, Skor Daey")
        self.current_vocals = item.get("vocal", "native Khmer vocal")
        self.current_chords = ["Am", "Dm", "E7", "Am"]
        self.current_key = "Am"
        self.current_prog_name = "i - iv - V7 - i (Traditional Minor)"
        self.current_language = "Khmer (ភាសាខ្មែរ)"
        self._update_formula_card()

    def _on_lang_changed(self):
        self.current_language = self.lang_picker.currentData() or self.lang_picker.currentText()
        self._update_formula_card()

    def _auto_randomize_khmer(self):
        import random
        stories = (
            KHMER_STUDIO_TAGS["storylines"]["love_stories"] +
            KHMER_STUDIO_TAGS["storylines"]["life_and_family"] +
            KHMER_STUDIO_TAGS["storylines"]["festivals_and_occasions"]
        )
        picked_story = random.choice(stories)
        picked_inst = random.choice(KHMER_STUDIO_TAGS["music_styles_and_instruments"])

        self.current_story = f"{picked_story.get('kh')} ({picked_story.get('en')}): {picked_story.get('prompt')}"
        self.current_genre = f"Khmer {picked_inst.get('kh')} Ballad"
        self.current_instruments = picked_inst.get("instruments", "Tro, Skor Daey")
        self.current_vocals = picked_inst.get("vocal", "native Khmer vocal")
        self.current_chords = ["Am", "Dm", "E7", "Am"]
        self.current_key = "Am"
        self.current_prog_name = "i - iv - V7 - i (Sinn Sisamouth)"
        self.current_language = "Khmer (ភាសាខ្មែរ)"
        self._update_formula_card()
        if hasattr(self, "lbl_macro_status"):
            self.lbl_macro_status.setText("🎲 Auto-picked authentic Khmer story & instrumentation!")

    def _on_english_style_clicked(self, item: dict):
        self.current_genre = item.get("genre", "Pop & Synthpop")
        self.current_bpm = item.get("bpm", "120 BPM")
        self.current_mood = item.get("mood", "Euphoric")
        self.current_instruments = item.get("instruments", "guitars, synths, drums")
        self.current_vocals = item.get("vocals", "melodic lead vocal")
        self.current_chords = list(item.get("chords", ["C", "G", "Am", "F"]))
        self.current_key = self.current_chords[0] if self.current_chords else "C"
        self.current_prog_name = "Standard Pop Progression"
        self.current_language = "English"
        self._update_formula_card()

    def _on_english_story_clicked(self, item: dict):
        self.current_story = f"{item.get('title', '')}: {item.get('prompt', '')}"
        self.current_language = "English"
        self._update_formula_card()

    def _on_pro_modifier_clicked(self, tag: str):
        current_text = self.txt_suno_prompt.toPlainText().strip()
        if tag not in current_text:
            new_text = f"{current_text}, {tag}" if current_text else tag
            self.txt_suno_prompt.setText(new_text)
            self._on_prompt_text_changed()

    def _auto_randomize_english(self):
        import random
        all_stories = []
        for cat in ENGLISH_STUDIO_TAGS["storylines"].values():
            all_stories.extend(cat)
        picked_story = random.choice(all_stories)
        picked_style = random.choice(ENGLISH_STUDIO_TAGS["production_styles"])
        picked_mod = random.choice(ENGLISH_STUDIO_TAGS["pro_modifiers"])

        self.current_story = f"{picked_story.get('title')}: {picked_story.get('prompt')}"
        self.current_genre = picked_style.get("genre")
        self.current_bpm = picked_style.get("bpm")
        self.current_mood = picked_style.get("mood")
        self.current_instruments = picked_style.get("instruments")
        self.current_vocals = f"{picked_style.get('vocals')}, {picked_mod.get('tag')}"
        self.current_chords = list(picked_style.get("chords", ["C", "G", "Am", "F"]))
        self.current_key = self.current_chords[0] if self.current_chords else "C"
        self.current_prog_name = "Billboard Standard Progression"
        self.current_language = "English"
        self._update_formula_card()
        if hasattr(self, "lbl_macro_status"):
            self.lbl_macro_status.setText("🎲 Auto-picked Billboard Pop sound design & story!")

    def _adjust_bpm(self, delta: int):
        import re
        m = re.search(r"\d+", self.current_bpm)
        val = int(m.group(0)) if m else 120
        new_val = max(60, min(180, val + delta))
        self.current_bpm = f"{new_val} BPM"
        if hasattr(self, "lbl_bpm_display"):
            self.lbl_bpm_display.setText(self.current_bpm)
        self._update_formula_card()

    def _transpose_chords(self, semitones: int):
        """Transpose current chord progression and tonality by semitone offset."""
        self.current_chords = [ChordEngine.transpose_chord(c, semitones) for c in self.current_chords]
        self.current_key = ChordEngine.transpose_chord(self.current_key, semitones)
        self._update_formula_card()
        if hasattr(self, "lbl_macro_status"):
            sign = f"+{semitones}" if semitones > 0 else f"{semitones}"
            self.lbl_macro_status.setText(f"🎹 Transposed {sign} semitone(s) → Key of {self.current_key}")

    def _on_key_selected(self, new_key: str):
        if not new_key or new_key == self.current_key:
            return
        norm_cur = ChordEngine.transpose_root(self.current_key.replace("m", "").replace("7", "").replace("maj", ""), 0)
        norm_new = ChordEngine.transpose_root(new_key.replace("m", "").replace("7", "").replace("maj", ""), 0)
        if norm_cur in SEMITONES_SHARP and norm_new in SEMITONES_SHARP:
            diff = (SEMITONES_SHARP.index(norm_new) - SEMITONES_SHARP.index(norm_cur)) % 12
            if diff > 6:
                diff -= 12
            self._transpose_chords(diff)
        else:
            self.current_key = new_key
            self._update_formula_card()

    def _optimize_prompt(self):
        """Compress and format the style prompt into optimal sweet spot for current engine."""
        limit = self._get_engine_char_limit()
        clean_genre = self.current_genre.split("&")[0].strip() if "&" in self.current_genre else self.current_genre
        inst_items = [i.strip() for i in self.current_instruments.split(",") if i.strip()]
        voc_items = [v.strip() for v in self.current_vocals.split(",") if v.strip()]
        mood_short = self.current_mood.split("&")[0].strip() if "&" in self.current_mood else self.current_mood

        if limit == 400:  # Suno v6 Master HDR
            top_inst = ", ".join(inst_items[:4])
            top_voc = ", ".join(voc_items[:3])
            optimized = (
                f"{self.current_genre}, {self.current_bpm}, Key: {self.current_key}, "
                f"{top_inst}, {top_voc}, {mood_short.lower()}, "
                f"spatial 3D stereo width, analog SSL tape saturation, pristine broadcast master"
            )
            if len(optimized) > 390:
                optimized = optimized[:387] + "..."
        elif limit == 350:  # Udio or Suno v4.5
            top_inst = ", ".join(inst_items[:3])
            top_voc = ", ".join(voc_items[:2])
            optimized = (
                f"{clean_genre}, {self.current_bpm}, Key: {self.current_key}, "
                f"{top_inst}, {top_voc}, {mood_short.lower()}, "
                f"high-fidelity studio mix, punchy dynamic groove"
            )
            if len(optimized) > 340:
                optimized = optimized[:337] + "..."
        elif limit == 120:  # Suno v3 Legacy
            top_inst = ", ".join(inst_items[:2])
            top_voc = voc_items[0] if voc_items else "lead vocal"
            optimized = f"{clean_genre}, {self.current_bpm}, {top_inst}, {top_voc}"
            if len(optimized) > 115:
                optimized = optimized[:112] + "..."
        else:  # Suno v4 / v3.5 (200 Chars)
            top_inst = ", ".join(inst_items[:3])
            top_voc = ", ".join(voc_items[:2])
            optimized = f"{clean_genre}, {self.current_bpm}, Key: {self.current_key}, {top_inst}, {top_voc}, {mood_short.lower()}"
            if len(optimized) > 195:
                optimized = optimized[:192] + "..."

        self.txt_suno_prompt.setText(optimized)
        self._on_prompt_text_changed()
        if hasattr(self, "lbl_macro_status"):
            self.lbl_macro_status.setText(f"✨ Optimized for {limit} Chars ({len(optimized)} chars)!")

    def _inject_studio_cues(self):
        """Inject Suno v6 / Udio production bracket cues into the prompt."""
        curr = self.txt_suno_prompt.toPlainText().strip()
        cues = f"[Tempo: {self.current_bpm}] [Key: {self.current_key}] [Production: Spatial Stereo, Analog Tape Warmth]"
        if "[Tempo:" in curr or "[Key:" in curr:
            import re
            curr = re.sub(r"\[Tempo:.*?\]", f"[Tempo: {self.current_bpm}]", curr)
            curr = re.sub(r"\[Key:.*?\]", f"[Key: {self.current_key}]", curr)
            self.txt_suno_prompt.setPlainText(curr)
        else:
            new_text = f"{cues}\n{curr}" if curr else cues
            self.txt_suno_prompt.setPlainText(new_text)
        self._on_prompt_text_changed()
        if hasattr(self, "lbl_macro_status"):
            self.lbl_macro_status.setText("⚡ Injected Suno v6 Studio Production Cues!")

    def _convert_syntax(self):
        """Toggle between Suno comma-delimited keyword tags and Udio flowing narrative prose."""
        current = self.txt_suno_prompt.toPlainText().strip()
        is_prose = current.startswith("An ") or current.startswith("A ") or " featuring " in current or " driven by " in current
        if is_prose:
            self.vs_engine_combo.setCurrentIndex(2)  # Suno v4/v3.5
            self._optimize_prompt()
            if hasattr(self, "lbl_macro_status"):
                self.lbl_macro_status.setText("🔄 Converted to Suno Comma-Delimited Syntax!")
        else:
            self.vs_engine_combo.setCurrentIndex(4)  # Udio AI v1.5 / v2
            inst_items = [i.strip() for i in self.current_instruments.split(",") if i.strip()]
            inst_str = ", ".join(inst_items[:3])
            voc_items = [v.strip() for v in self.current_vocals.split(",") if v.strip()]
            voc_str = ", ".join(voc_items[:2])
            prose = (
                f"An {self.current_mood.lower()} {self.current_bpm} {self.current_genre.lower()} track "
                f"in the key of {self.current_key}, driven by {inst_str}, highlighted by {voc_str}, "
                f"with polished commercial radio mastering."
            )
            self.txt_suno_prompt.setText(prose)
            self._on_prompt_text_changed()
            if hasattr(self, "lbl_macro_status"):
                self.lbl_macro_status.setText("🔄 Converted to Udio v1.5/v2 Narrative Prose Syntax!")

    def _copy_macro_tag(self, tag: str):
        QApplication.clipboard().setText(tag)
        if hasattr(self, "lbl_macro_status"):
            self.lbl_macro_status.setText(f"✅ Copied {tag} to Clipboard!")

    def _copy_suno_lyric_template(self):
        """Generate and copy an authentic Suno lyrics skeleton with section metatags (Khmer or English)."""
        clean_genre = self.current_genre.split("&")[0].strip() if "&" in self.current_genre else self.current_genre
        is_khmer = ("Khmer" in self.current_language) or (hasattr(self, "btn_tab_khmer") and self.btn_tab_khmer.isChecked())

        if is_khmer:
            title = self.current_story.split(":")[0] if ":" in self.current_story else "បទចម្រៀងថ្មី"
            template = f"""[Title: {title}]
[Style: {clean_genre}, {self.current_bpm}, Key: {self.current_key}, {self.current_vocals}]

[អារម្ភកថា: Intro - សំឡេងទ្រ និងព្យាណូស្រទន់]
(សំឡេងភ្លេងផ្តើមយ៉ាងរំជួលចិត្ត រៀបចំបរិយាកាសសាច់រឿង)

[វគ្គ១: Verse 1 - សំឡេងច្រៀងទន់ភ្លន់]
ពន្លឺរាត្រីឆ្លុះស្រមោលឯកា
អង្គុយនឹកដល់អនុស្សាវរីយ៍កាលមុន
ស្នាមញញឹមអូននៅចាំក្នុងចិត្ត
តើពេលនេះថ្លៃរស់នៅសុខទុក្ខយ៉ាងណា?

[តភ្ជាប់: Pre-Chorus - ចង្វាក់ចាប់ផ្តើមកើនឡើង]
ខ្យល់រំភើយបក់នាំក្តីនឹករលឹក
បេះដូងលោតញាប់រង់ចាំជួបមុខ
តើមានថ្ងៃណាបានជួបគ្នាវិញ?
ក្តីសង្ឃឹមនៅតែរង់ចាំ...

[បន្ទរ: Chorus - សំឡេងបន្លឺខ្ពស់ ស្គរពេញលេញ]
(ភ្លេងបន្លឺឡើងយ៉ាងរំភើប!)
ស្រលាញ់អូនស្មើជីវិត មិនប្រែប្រួលឡើយ
ទោះមេឃនិងដីផ្លាស់ប្តូរទៅណា
បេះដូងមួយនេះនៅតែមានតែអូន
ចាំជួបគ្រប់វេលា គ្មានថ្ងៃឃ្លាតឆ្ងាយ!

[វគ្គ២: Verse 2 - ចង្វាក់ភ្លេងបន្តរលូន]
ផ្កាយលើមេឃនៅតែភ្លឺចែងចាំង
ដូចកែវភ្នែកស្រស់ដែលធ្លាប់មើលមក
សន្យាពីមុននៅដក់ជាប់ក្នុងទ្រូង
មិនដែលបំភ្លេចសូម្បីតែមួយវិនាទី

[បន្ទរ: Chorus - សំឡេងបន្លឺខ្ពស់ និងបន្ទរបន្ថែម]
ស្រលាញ់អូនស្មើជីវិត មិនប្រែប្រួលឡើយ
ទោះមេឃនិងដីផ្លាស់ប្តូរទៅណា
បេះដូងមួយនេះនៅតែមានតែអូន
ចាំជួបគ្រប់វេលា គ្មានថ្ងៃឃ្លាតឆ្ងាយ!

[តភ្ជាប់ផ្លាស់ប្តូរ: Bridge - សំឡេងកូតទ្រកំសត់ និងស្គរបន្ថយល្បឿន]
(សំឡេងកូតទ្រយ៉ាងស្រទន់...)
បើសិនពេលវេលាអាចត្រឡប់
បងនឹងឱបអូនមិនឱ្យទៅណាឡើយ...
(ស្គរបុកឡើងកម្តៅជាថ្មី!)

[បន្ទរផ្ទុះចុងក្រោយ: Outro Chorus - ថាមពលពេញទំហឹង]
ស្រលាញ់អូនស្មើជីវិត! (Ad-lib: មិនប្រែប្រួលឡើយ!)
ទោះពេលវេលាកន្លងផុតទៅ...
បងនៅតែស្រលាញ់អូនជានិច្ច!

[បញ្ចប់: Outro - សំឡេងភ្លេងស្រុតចុះបន្តិចម្តងៗ]
(Fade out)
[End]"""
        else:
            title = self.current_story.split(":")[0] if ":" in self.current_story else "My Hit Song"
            template = f"""[Title: {title}]
[Style: {clean_genre}, {self.current_bpm}, Key: {self.current_key}, {self.current_vocals}]

[Intro: {self.current_bpm}, Synth Bass & Rhythm Groove]
(Atmospheric instrumental intro establishing chord progression)

[Verse 1: Intimate Lead Vocal]
Walking through the quiet streets tonight
Shadows dancing in the neon light
Every heartbeat keeping time with you
Wondering if you can feel it too

[Pre-Chorus: Rising Tension, Snare Build]
The pressure builds inside the chest
We left no time to take a rest
The spark is catching in the dark
Here comes the beat to leave a mark

[Chorus: Soaring Vocal Belt, Full Wall of Sound]
Shining brighter than the midnight sun
We only stop when the race is won
Take my hand and never look behind
Leaving all the heavy doubts behind!

[Post-Chorus: Catchy Vocal Chops & Bass Groove]
(Yeah, yeah, we rise)
(Never looking back, yeah)

[Verse 2: Dynamic Rhythm Continues]
Colors bleed into the morning sky
No more reasons left to wonder why
Step by step across the open floor
We don't live in shadows anymore

[Chorus: Maximum Energy, Layered Harmonies]
Shining brighter than the midnight sun
We only stop when the race is won
Take my hand and never look behind
Leaving all the heavy doubts behind!

[Bridge: Half-time, Stripped-Back Acoustic]
When the silence falls again...
Will you still remember then?
(Snare drum build-up risers!)

[Bass Drop]

[Chorus: Final Crescendo & Ad-libs]
Shining brighter than the midnight sun!
(Ad-lib: So high above the sky!)
We only stop when the race is won!

[Outro: Reverb Fade, Instruments Decay]
[End]"""

        QApplication.clipboard().setText(template)
        lang_label = "Khmer" if is_khmer else "English Billboard"
        if hasattr(self, "lbl_macro_status"):
            self.lbl_macro_status.setText(f"✅ Copied Full {lang_label} Lyric Template to Clipboard!")

    def _play_vs_chords(self):
        try:
            bpm_val = int("".join(filter(str.isdigit, str(self.current_bpm)[:4])))
        except Exception:
            bpm_val = 120
        AudioChordSynthesizer.play_progression(self.current_chords, bpm=bpm_val)

    def _stop_vs_chords(self):
        AudioChordSynthesizer.stop()

    def _update_formula_card(self):
        self.lbl_g.setText(self.current_genre)
        self.lbl_m.setText(self.current_mood)
        self.lbl_i.setText(self.current_instruments)
        self.lbl_v.setText(self.current_vocals)

        prog_suffix = f"  ({self.current_prog_name})" if hasattr(self, "current_prog_name") and self.current_prog_name else ""
        self.lbl_c.setText(" - ".join(f"[{c}]" for c in self.current_chords) + prog_suffix)

        # Sync Key combo
        if hasattr(self, "key_combo"):
            idx = self.key_combo.findText(self.current_key)
            if idx >= 0:
                self.key_combo.blockSignals(True)
                self.key_combo.setCurrentIndex(idx)
                self.key_combo.blockSignals(False)

        # Sync BPM display
        if hasattr(self, "lbl_bpm_display"):
            self.lbl_bpm_display.setText(self.current_bpm)

        # Update style prompt with Key
        style_prompt = f"{self.current_genre}, {self.current_bpm}, Key: {self.current_key}, {self.current_instruments}, {self.current_vocals}, {self.current_mood}"
        self.txt_suno_prompt.setText(style_prompt)
        self._on_prompt_text_changed()

        # Update dynamic generate button text
        if hasattr(self, "btn_generate"):
            if "English" in self.current_language:
                self.btn_generate.setText("✨ បង្កើតបទអង់គ្លេស (Generate English)")
            elif "Khmer" in self.current_language:
                self.btn_generate.setText("✨ បង្កើតបទខ្មែរ (Generate Khmer)")
            else:
                self.btn_generate.setText(f"✨ បង្កើតបទ ({self.current_language[:10]})")

    def _on_prompt_text_changed(self):
        char_count = len(self.txt_suno_prompt.toPlainText().strip())
        limit = self._get_engine_char_limit()

        self.lbl_char_count.setText(f"{char_count} / {limit} chars")
        if char_count > limit:
            self.lbl_char_count.setStyleSheet("font-size: 10px; font-weight: 800; color: #dc2626; background: #fee2e2; padding: 2px 6px; border-radius: 4px;")
            if hasattr(self, "lbl_pro_status"):
                self.lbl_pro_status.setText(f"⚠️ Truncation Risk: Exceeds {limit} chars! Click 'Optimize'")
                self.lbl_pro_status.setStyleSheet("background: #fef2f2; color: #b91c1c; font-weight: 700; font-size: 10px; padding: 3px 6px; border-radius: 5px; border: 1px solid #fecaca;")
        elif char_count >= int(limit * 0.75):
            self.lbl_char_count.setStyleSheet("font-size: 10px; font-weight: 800; color: #047857; background: #ecfdf5; padding: 2px 6px; border-radius: 4px;")
            if hasattr(self, "lbl_pro_status"):
                self.lbl_pro_status.setText(f"⭐ Pro Ready: Optimal Keyword Density ({char_count}/{limit})")
                self.lbl_pro_status.setStyleSheet("background: #ecfdf5; color: #047857; font-weight: 700; font-size: 10px; padding: 3px 6px; border-radius: 5px; border: 1px solid #a7f3d0;")
        else:
            self.lbl_char_count.setStyleSheet("font-size: 10px; font-weight: 800; color: #059669; background: #ecfdf5; padding: 2px 6px; border-radius: 4px;")
            if hasattr(self, "lbl_pro_status"):
                self.lbl_pro_status.setText(f"⭐ Safe Token Window ({char_count}/{limit} chars)")
                self.lbl_pro_status.setStyleSheet("background: #ecfdf5; color: #047857; font-weight: 700; font-size: 10px; padding: 3px 6px; border-radius: 5px; border: 1px solid #a7f3d0;")

    def _humanize_current_style(self):
        from app.humanizer_engine import HumanizerEngine
        curr = self.txt_suno_prompt.toPlainText().strip()
        h_style = HumanizerEngine.humanize_style_prompt_locally(curr, self.current_language)
        self.txt_suno_prompt.setPlainText(h_style)
        self._on_prompt_text_changed()
        if hasattr(self, "lbl_macro_status"):
            self.lbl_macro_status.setText("👤 Injected Human Live Pocket & Tape Warmth!")

    def _copy_prompt(self):
        text = self.txt_suno_prompt.toPlainText().strip()
        if text:
            QApplication.clipboard().setText(text)
            if hasattr(self, "lbl_macro_status"):
                self.lbl_macro_status.setText("📋 Copied Style Prompt to Clipboard!")

    def get_generation_parameters(self) -> dict:
        return {
            "genre": self.current_genre,
            "region": "Southeast Asia" if "Khmer" in self.current_genre else "Global",
            "language": self.current_language,
            "bpm": self.current_bpm,
            "mood": self.current_mood,
            "theme": self.current_story,
            "structure": "Standard Pop / Global Radio (3-Minute Hit)",
            "rhyme": "AABB (Classic Couplets)",
            "user_notes": f"Style: {self.txt_suno_prompt.toPlainText().strip()}\nKey: {self.current_key}\nChords: {' - '.join(self.current_chords)}\nStoryline: {self.current_story}"
        }

    def _emit_generate(self):
        self.generate_requested.emit(self.get_generation_parameters())

    def _emit_demo(self):
        self.demo_requested.emit(self.get_generation_parameters())

    def _emit_open_editor(self):
        self.open_editor_requested.emit(self.get_generation_parameters())

    def _emit_open_batch(self):
        self.open_batch_requested.emit(self.get_generation_parameters())

    def apply_theme(self, theme_or_dark):
        t = get_theme(theme_or_dark)
        self.theme = t
        self.theme_key = t.get("id", "obsidian")
        is_dark = t.get("is_dark", True)
        self.is_dark = is_dark

        if is_dark:
            # Modern Studio Adaptive Dark Palette
            if hasattr(self, "tab_bar"):
                self.tab_bar.setStyleSheet(f"background-color: {t['bg_window']}; border: 1px solid {t['border']}; border-radius: 10px; padding: 4px;")
            tab_qss = f"""
                QPushButton {{
                    background-color: transparent;
                    color: {t['text_secondary']};
                    font-weight: 600;
                    padding: 7px 16px;
                    border: none;
                    border-radius: 7px;
                    font-size: 11.5px;
                }}
                QPushButton:hover {{
                    color: #ffffff;
                    background-color: {t['bg_card_alt']};
                }}
                QPushButton:checked {{
                    background: {t['accent_gradient']};
                    color: #ffffff;
                    font-weight: 800;
                    border: 1px solid {t['border_accent']};
                }}
            """
            for btn in [getattr(self, "btn_tab_explore", None), getattr(self, "btn_tab_khmer", None), getattr(self, "btn_tab_english", None)]:
                if btn:
                    btn.setStyleSheet(tab_qss)

            if hasattr(self, "title_lbl"):
                self.title_lbl.setStyleSheet(f"font-size: 18px; font-weight: 800; color: {t['text_primary']};")

            if hasattr(self, "info_cards"):
                for card, tc, sc in self.info_cards:
                    card.setStyleSheet(f"background-color: {t['bg_card']}; border: 1px solid {t['border']}; border-radius: 8px; padding: 8px;")
                    tc.setStyleSheet(f"font-weight: 700; color: {t['text_primary']}; font-size: 12px;")
                    sc.setStyleSheet(f"color: {t['text_secondary']}; font-size: 10.5px;")

            if hasattr(self, "lbl_g_head"):
                self.lbl_g_head.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {t['text_primary']};")
            if hasattr(self, "sub_g"):
                self.sub_g.setStyleSheet(f"color: {t['text_secondary']}; font-size: 11.5px;")
            if hasattr(self, "grid_frame"):
                self.grid_frame.setStyleSheet(f"background-color: {t['bg_card']}; border: 1px solid {t['border']}; border-radius: 10px; padding: 10px;")
            if hasattr(self, "bottom_box"):
                self.bottom_box.setStyleSheet(f"background-color: {t['bg_card']}; border: 1px solid {t['border']}; border-radius: 10px; padding: 10px;")
            if hasattr(self, "lang_picker"):
                self.lang_picker.setStyleSheet(f"padding: 5px; background-color: {t['bg_input']}; color: {t['text_primary']}; border: 1px solid {t['border']}; border-radius: 6px; font-size: 11.5px;")
            if hasattr(self, "explore_idea_input"):
                self.explore_idea_input.setStyleSheet(f"background-color: {t['bg_input']}; color: {t['text_primary']}; border: 1px solid {t['border']}; border-radius: 6px; padding: 5px; font-size: 11px;")

            if hasattr(self, "khmer_title"):
                self.khmer_title.setStyleSheet(f"font-size: 15px; font-weight: 800; color: {t['text_primary']};")
            if hasattr(self, "btn_random_khmer"):
                self.btn_random_khmer.setStyleSheet(f"background-color: {t['subtle_pill_bg']}; color: {t['text_accent']}; font-weight: 700; border: 1px solid {t['border_accent']}; border-radius: 6px; padding: 5px 12px; font-size: 11px;")
            if hasattr(self, "sub_text_khmer"):
                self.sub_text_khmer.setStyleSheet(f"color: {t['text_secondary']}; font-size: 11.5px;")
            if hasattr(self, "khmer_story_box"):
                self.khmer_story_box.setStyleSheet(f"background-color: {t['bg_card']}; border: 1px solid {t['border']}; border-radius: 10px; padding: 10px;")
            if hasattr(self, "khmer_inst_box"):
                self.khmer_inst_box.setStyleSheet(f"background-color: {t['bg_card']}; border: 1px solid {t['border']}; border-radius: 10px; padding: 10px;")
            if hasattr(self, "khmer_pill_btns"):
                for b in self.khmer_pill_btns:
                    b.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {t['bg_card_alt']};
                            color: {t['text_primary']};
                            border: 1px solid {t['border']};
                            border-radius: 6px;
                            padding: 5px 8px;
                            font-size: 10.5px;
                            text-align: left;
                        }}
                        QPushButton:hover {{
                            background-color: {t['border']};
                            border-color: {t['border_accent']};
                            color: #ffffff;
                        }}
                        QPushButton:pressed {{
                            background-color: {t['accent']};
                            color: #ffffff;
                        }}
                    """)

            if hasattr(self, "en_title"):
                self.en_title.setStyleSheet(f"font-size: 15px; font-weight: 800; color: {t['text_primary']};")
            if hasattr(self, "btn_random_en"):
                self.btn_random_en.setStyleSheet(f"background-color: {t['subtle_pill_bg']}; color: {t['text_accent']}; font-weight: 700; border: 1px solid {t['border_accent']}; border-radius: 6px; padding: 5px 12px; font-size: 11px;")
            if hasattr(self, "sub_text_en"):
                self.sub_text_en.setStyleSheet(f"color: {t['text_secondary']}; font-size: 11.5px; line-height: 1.3;")
            if hasattr(self, "st_title"):
                self.st_title.setStyleSheet(f"font-weight: 800; color: {t['text_accent']}; font-size: 12.5px;")
            if hasattr(self, "s_title"):
                self.s_title.setStyleSheet(f"font-weight: 800; color: {t['text_accent']}; font-size: 12.5px;")
            if hasattr(self, "m_title"):
                self.m_title.setStyleSheet(f"font-weight: 800; color: {t['text_accent']}; font-size: 12.5px;")

            if hasattr(self, "english_style_box"):
                self.english_style_box.setStyleSheet(f"background-color: {t['bg_card']}; border: 1px solid {t['border']}; border-radius: 10px; padding: 10px;")
            if hasattr(self, "english_story_box"):
                self.english_story_box.setStyleSheet(f"background-color: {t['bg_card']}; border: 1px solid {t['border']}; border-radius: 10px; padding: 10px;")
            if hasattr(self, "english_mod_box"):
                self.english_mod_box.setStyleSheet(f"background-color: {t['bg_card']}; border: 1px solid {t['border']}; border-radius: 10px; padding: 10px;")
            if hasattr(self, "english_style_btns"):
                for b in self.english_style_btns:
                    b.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {t['bg_card_alt']};
                            color: {t['text_primary']};
                            border: 1px solid {t['border']};
                            border-radius: 6px;
                            padding: 6px 8px;
                            font-size: 10.5px;
                            font-weight: 600;
                            text-align: left;
                        }}
                        QPushButton:hover {{
                            background-color: {t['border']};
                            border-color: {t['border_accent']};
                            color: #ffffff;
                        }}
                        QPushButton:pressed {{
                            background-color: {t['accent']};
                            color: #ffffff;
                        }}
                    """)
            if hasattr(self, "english_story_btns"):
                for b in self.english_story_btns:
                    b.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {t['bg_card_alt']};
                            color: {t['text_primary']};
                            border: 1px solid {t['border']};
                            border-radius: 6px;
                            padding: 5px 8px;
                            font-size: 10px;
                            text-align: left;
                        }}
                        QPushButton:hover {{
                            background-color: {t['border']};
                            border-color: {t['border_accent']};
                            color: #ffffff;
                        }}
                        QPushButton:pressed {{
                            background-color: {t['accent']};
                            color: #ffffff;
                        }}
                    """)
            if hasattr(self, "english_mod_btns"):
                for b in self.english_mod_btns:
                    b.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {t['subtle_pill_bg']};
                            color: {t['text_accent']};
                            border: 1px solid {t['border_accent']};
                            border-radius: 5px;
                            padding: 5px 8px;
                            font-size: 10.5px;
                            font-weight: 600;
                        }}
                        QPushButton:hover {{
                            background-color: {t['accent']};
                            color: #ffffff;
                        }}
                    """)

            if hasattr(self, "formula_card"):
                self.formula_card.setStyleSheet(f"background-color: {t['bg_card']}; border: 1px solid {t['border']}; border-radius: 10px; padding: 8px 10px;")
            if hasattr(self, "lbl_formula_title"):
                self.lbl_formula_title.setStyleSheet(f"font-size: 14px; font-weight: 800; color: {t['text_primary']};")

            # Master Presets Box
            if hasattr(self, "preset_frame"):
                self.preset_frame.setStyleSheet(f"background-color: {t['bg_card_alt']}; border: 1px solid {t['border']}; border-radius: 8px; padding: 4px;")
            if hasattr(self, "lbl_presets_head"):
                self.lbl_presets_head.setStyleSheet(f"font-size: 10px; font-weight: 800; color: {t['text_accent']};")
            if hasattr(self, "preset_btns"):
                for pb in self.preset_btns:
                    pb.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {t['bg_card']};
                            color: {t['text_primary']};
                            font-size: 9px;
                            font-weight: 700;
                            border: 1px solid {t['border']};
                            border-radius: 4px;
                            padding: 3px 3px;
                        }}
                        QPushButton:hover {{
                            background-color: {t['bg_card_alt']};
                            border-color: {t['border_accent']};
                            color: #ffffff;
                        }}
                    """)

            for lbl in [getattr(self, "lbl_g", None), getattr(self, "lbl_m", None), getattr(self, "lbl_i", None), getattr(self, "lbl_v", None), getattr(self, "lbl_c", None)]:
                if lbl:
                    lbl.setStyleSheet(f"color: {t['text_primary']}; font-size: 10.5px;")

            for lbl in [getattr(self, "lbl_k", None), getattr(self, "eng_lbl", None), getattr(self, "lbl_macro", None), getattr(self, "lbl_neg_head", None)]:
                if lbl:
                    lbl.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {t['text_secondary']};")

            if hasattr(self, "key_combo"):
                self.key_combo.setStyleSheet(f"padding: 2px 4px; font-size: 10px; font-weight: 700; background-color: {t['bg_input']}; color: {t['text_primary']}; border: 1px solid {t['border']}; border-radius: 4px;")
            for b in [getattr(self, "btn_trans_down", None), getattr(self, "btn_trans_up", None), getattr(self, "btn_bpm_minus", None), getattr(self, "btn_bpm_plus", None)]:
                if b:
                    b.setStyleSheet(f"background-color: {t['bg_card_alt']}; color: {t['text_secondary']}; border: 1px solid {t['border']}; border-radius: 3px; font-size: 10px; font-weight: 700;")
            if hasattr(self, "lbl_bpm_display"):
                self.lbl_bpm_display.setStyleSheet(f"font-size: 10.5px; font-weight: 800; color: {t['text_accent']};")
            if hasattr(self, "btn_vs_play_chords"):
                self.btn_vs_play_chords.setStyleSheet(f"background-color: {t['subtle_pill_bg']}; color: {t['text_accent']}; font-weight: 700; font-size: 10px; border: 1px solid {t['border_accent']}; border-radius: 4px; padding: 2px 7px;")
            if hasattr(self, "btn_vs_stop_chords"):
                self.btn_vs_stop_chords.setStyleSheet(f"background-color: {t['bg_card_alt']}; color: {t['text_secondary']}; font-weight: 600; font-size: 10px; border: 1px solid {t['border']}; border-radius: 4px;")
            if hasattr(self, "vs_engine_combo"):
                self.vs_engine_combo.setStyleSheet(f"padding: 2px 4px; font-size: 10px; font-weight: 600; background-color: {t['bg_input']}; color: {t['text_primary']}; border: 1px solid {t['border']}; border-radius: 4px;")
            if hasattr(self, "prompt_box_frame"):
                self.prompt_box_frame.setStyleSheet(f"background-color: {t['bg_input']}; border: 1px solid {t['border']}; border-radius: 6px; padding: 4px;")
            if hasattr(self, "txt_suno_prompt"):
                self.txt_suno_prompt.setStyleSheet(f"background: transparent; border: none; font-size: 11px; color: {t['text_primary']};")
            if hasattr(self, "btn_optimize"):
                self.btn_optimize.setStyleSheet(f"background-color: {t['subtle_pill_bg']}; color: {t['text_accent']}; border: 1px solid {t['border_accent']}; border-radius: 4px; padding: 3px 5px; font-size: 9.5px; font-weight: 700;")
            if hasattr(self, "btn_studio_cues"):
                self.btn_studio_cues.setStyleSheet("background-color: #422006; color: #fef08a; border: 1px solid #eab308; border-radius: 4px; padding: 3px 5px; font-size: 9.5px; font-weight: 700;")
            if hasattr(self, "btn_convert"):
                self.btn_convert.setStyleSheet("background-color: #064e3b; color: #34d399; border: 1px solid #059669; border-radius: 4px; padding: 3px 5px; font-size: 9.5px; font-weight: 600;")
            if hasattr(self, "btn_humanize_style"):
                self.btn_humanize_style.setStyleSheet("background-color: #042f2e; color: #5eead4; border: 1px solid #0f766e; border-radius: 4px; padding: 3px 5px; font-size: 9.5px; font-weight: 700;")
            if hasattr(self, "btn_copy"):
                self.btn_copy.setStyleSheet(f"background-color: {t['bg_card_alt']}; color: {t['text_secondary']}; border: 1px solid {t['border']}; border-radius: 4px; padding: 3px 5px; font-size: 9.5px; font-weight: 600;")
            if hasattr(self, "macro_box"):
                self.macro_box.setStyleSheet(f"background-color: {t['bg_input']}; border: 1px solid {t['border']}; border-radius: 6px; padding: 4px;")
            if hasattr(self, "macro_btns"):
                for b in self.macro_btns:
                    b.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {t['bg_card_alt']};
                            color: {t['text_secondary']};
                            border: 1px solid {t['border']};
                            border-radius: 3px;
                            padding: 2px 2px;
                            font-size: 8.5px;
                            font-weight: 600;
                        }}
                        QPushButton:hover {{
                            background-color: {t['border']};
                            border-color: {t['border_accent']};
                            color: #ffffff;
                        }}
                    """)
            if hasattr(self, "btn_copy_template"):
                self.btn_copy_template.setStyleSheet("background-color: #064e3b; color: #34d399; border: 1px solid #059669; border-radius: 4px; padding: 4px 6px; font-size: 10px; font-weight: 700;")
            if hasattr(self, "txt_negative"):
                self.txt_negative.setStyleSheet(f"background: {t['bg_input']}; border: 1px solid {t['border']}; border-radius: 4px; font-size: 10px; color: {t['text_secondary']}; padding: 2px 6px;")
            if hasattr(self, "btn_demo"):
                self.btn_demo.setStyleSheet(f"background-color: {t['bg_card_alt']}; color: {t['text_accent']}; border: 1px solid {t['border']}; border-radius: 5px; padding: 6px; font-size: 10.5px; font-weight: 600;")
            if hasattr(self, "btn_editor"):
                self.btn_editor.setStyleSheet(f"background-color: {t['bg_card_alt']}; color: {t['text_primary']}; border: 1px solid {t['border']}; border-radius: 5px; padding: 6px; font-size: 10.5px; font-weight: 600;")
            if hasattr(self, "btn_batch"):
                self.btn_batch.setStyleSheet(f"background: {t['accent_gradient']}; color: #ffffff; border: 1px solid {t['border_accent']}; border-radius: 5px; padding: 6px; font-size: 10.5px; font-weight: 700;")
            if hasattr(self, "btn_pack"):
                self.btn_pack.setStyleSheet("background-color: #064e3b; color: #34d399; border: 1px solid #059669; border-radius: 5px; padding: 6px; font-size: 10.5px; font-weight: 700;")
        else:
            # Modern Studio High-Contrast Light Palette
            if hasattr(self, "tab_bar"):
                self.tab_bar.setStyleSheet("background-color: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 10px; padding: 4px;")
            tab_qss_light = f"""
                QPushButton {{
                    background-color: transparent;
                    color: #475569;
                    font-weight: 600;
                    padding: 7px 16px;
                    border: none;
                    border-radius: 7px;
                    font-size: 11.5px;
                }}
                QPushButton:hover {{
                    color: #0f172a;
                    background-color: #e2e8f0;
                }}
                QPushButton:checked {{
                    background-color: {t['accent']};
                    color: #ffffff;
                    font-weight: 800;
                    border: 1px solid {t['border_accent']};
                }}
            """
            for btn in [getattr(self, "btn_tab_explore", None), getattr(self, "btn_tab_khmer", None), getattr(self, "btn_tab_english", None)]:
                if btn:
                    btn.setStyleSheet(tab_qss_light)

            if hasattr(self, "title_lbl"):
                self.title_lbl.setStyleSheet("font-size: 18px; font-weight: 800; color: #0f172a;")

            if hasattr(self, "info_cards"):
                for card, tc, sc in self.info_cards:
                    card.setStyleSheet("background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 8px;")
                    tc.setStyleSheet("font-weight: 700; color: #0f172a; font-size: 12px;")
                    sc.setStyleSheet("color: #475569; font-size: 10.5px;")

            if hasattr(self, "lbl_g_head"):
                self.lbl_g_head.setStyleSheet("font-size: 14px; font-weight: 700; color: #0f172a;")
            if hasattr(self, "sub_g"):
                self.sub_g.setStyleSheet("color: #475569; font-size: 11.5px;")
            if hasattr(self, "grid_frame"):
                self.grid_frame.setStyleSheet("background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 10px; padding: 10px;")
            if hasattr(self, "bottom_box"):
                self.bottom_box.setStyleSheet("background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 10px; padding: 10px;")
            if hasattr(self, "lang_picker"):
                self.lang_picker.setStyleSheet("padding: 5px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 11.5px; color: #0f172a; background: #ffffff;")
            if hasattr(self, "explore_idea_input"):
                self.explore_idea_input.setStyleSheet("background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 6px; padding: 5px; font-size: 11px; color: #0f172a;")

            if hasattr(self, "khmer_title"):
                self.khmer_title.setStyleSheet("font-size: 15px; font-weight: 800; color: #0f172a;")
            if hasattr(self, "btn_random_khmer"):
                self.btn_random_khmer.setStyleSheet("background-color: #eff6ff; color: #1d4ed8; font-weight: 700; border: 1px solid #bfdbfe; border-radius: 6px; padding: 5px 12px; font-size: 11px;")
            if hasattr(self, "sub_text_khmer"):
                self.sub_text_khmer.setStyleSheet("color: #475569; font-size: 11.5px;")
            if hasattr(self, "khmer_story_box"):
                self.khmer_story_box.setStyleSheet("background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 10px; padding: 10px;")
            if hasattr(self, "khmer_inst_box"):
                self.khmer_inst_box.setStyleSheet("background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 10px; padding: 10px;")
            if hasattr(self, "khmer_pill_btns"):
                for b in self.khmer_pill_btns:
                    b.setStyleSheet("""
                        QPushButton {
                            background-color: #ffffff;
                            color: #1e293b;
                            border: 1px solid #cbd5e1;
                            border-radius: 6px;
                            padding: 5px 8px;
                            font-size: 10.5px;
                            text-align: left;
                        }
                        QPushButton:hover {
                            background-color: #eff6ff;
                            border-color: #3b82f6;
                            color: #1d4ed8;
                        }
                    """)

            if hasattr(self, "en_title"):
                self.en_title.setStyleSheet("font-size: 15px; font-weight: 800; color: #0f172a;")
            if hasattr(self, "btn_random_en"):
                self.btn_random_en.setStyleSheet("background-color: #eff6ff; color: #1d4ed8; font-weight: 700; border: 1px solid #bfdbfe; border-radius: 6px; padding: 5px 12px; font-size: 11px;")
            if hasattr(self, "sub_text_en"):
                self.sub_text_en.setStyleSheet("color: #475569; font-size: 11.5px; line-height: 1.3;")
            if hasattr(self, "st_title"):
                self.st_title.setStyleSheet("font-weight: 800; color: #0f172a; font-size: 12.5px;")
            if hasattr(self, "s_title"):
                self.s_title.setStyleSheet("font-weight: 800; color: #0f172a; font-size: 12.5px;")
            if hasattr(self, "m_title"):
                self.m_title.setStyleSheet("font-weight: 800; color: #0f172a; font-size: 12.5px;")

            if hasattr(self, "english_style_box"):
                self.english_style_box.setStyleSheet("background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 10px; padding: 10px;")
            if hasattr(self, "english_story_box"):
                self.english_story_box.setStyleSheet("background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 10px; padding: 10px;")
            if hasattr(self, "english_mod_box"):
                self.english_mod_box.setStyleSheet("background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 10px; padding: 10px;")
            if hasattr(self, "english_style_btns"):
                for b in self.english_style_btns:
                    b.setStyleSheet("""
                        QPushButton {
                            background-color: #ffffff;
                            color: #0f172a;
                            border: 1px solid #cbd5e1;
                            border-radius: 6px;
                            padding: 6px 8px;
                            font-size: 10.5px;
                            font-weight: 600;
                            text-align: left;
                        }
                        QPushButton:hover {
                            background-color: #eff6ff;
                            border-color: #3b82f6;
                            color: #1d4ed8;
                        }
                        QPushButton:pressed {
                            background-color: #1d4ed8;
                            color: #ffffff;
                        }
                    """)
            if hasattr(self, "english_story_btns"):
                for b in self.english_story_btns:
                    b.setStyleSheet("""
                        QPushButton {
                            background-color: #ffffff;
                            color: #1e293b;
                            border: 1px solid #cbd5e1;
                            border-radius: 6px;
                            padding: 5px 8px;
                            font-size: 10px;
                            text-align: left;
                        }
                        QPushButton:hover {
                            background-color: #eff6ff;
                            border-color: #3b82f6;
                            color: #1d4ed8;
                        }
                    """)
            if hasattr(self, "english_mod_btns"):
                for b in self.english_mod_btns:
                    b.setStyleSheet("""
                        QPushButton {
                            background-color: #eff6ff;
                            color: #1d4ed8;
                            border: 1px solid #bfdbfe;
                            border-radius: 5px;
                            padding: 5px 8px;
                            font-size: 10.5px;
                            font-weight: 600;
                        }
                        QPushButton:hover {
                            background-color: #dbeafe;
                            border-color: #3b82f6;
                            color: #1e40af;
                        }
                    """)

            if hasattr(self, "formula_card"):
                self.formula_card.setStyleSheet("background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 10px; padding: 8px 10px;")
            if hasattr(self, "lbl_formula_title"):
                self.lbl_formula_title.setStyleSheet("font-size: 14px; font-weight: 800; color: #0f172a;")

            # Master Presets Box
            if hasattr(self, "preset_frame"):
                self.preset_frame.setStyleSheet("background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 4px;")
            if hasattr(self, "lbl_presets_head"):
                self.lbl_presets_head.setStyleSheet("font-size: 10px; font-weight: 800; color: #334155;")
            if hasattr(self, "preset_btns"):
                for pb in self.preset_btns:
                    pb.setStyleSheet("""
                        QPushButton {
                            background-color: #ffffff;
                            color: #0f172a;
                            font-size: 9px;
                            font-weight: 700;
                            border: 1px solid #cbd5e1;
                            border-radius: 4px;
                            padding: 3px 3px;
                        }
                        QPushButton:hover {
                            background-color: #eff6ff;
                            border-color: #3b82f6;
                            color: #1d4ed8;
                        }
                    """)

            for lbl in [getattr(self, "lbl_g", None), getattr(self, "lbl_m", None), getattr(self, "lbl_i", None), getattr(self, "lbl_v", None), getattr(self, "lbl_c", None)]:
                if lbl:
                    lbl.setStyleSheet("color: #1e293b; font-size: 10.5px;")

            for lbl in [getattr(self, "lbl_k", None), getattr(self, "eng_lbl", None), getattr(self, "lbl_macro", None), getattr(self, "lbl_neg_head", None)]:
                if lbl:
                    lbl.setStyleSheet("font-size: 10px; font-weight: 700; color: #334155;")

            if hasattr(self, "key_combo"):
                self.key_combo.setStyleSheet("padding: 2px 4px; font-size: 10px; font-weight: 700; border: 1px solid #cbd5e1; border-radius: 4px; background: #ffffff; color: #0f172a;")
            for b in [getattr(self, "btn_trans_down", None), getattr(self, "btn_trans_up", None), getattr(self, "btn_bpm_minus", None), getattr(self, "btn_bpm_plus", None)]:
                if b:
                    b.setStyleSheet("background-color: #ffffff; color: #0f172a; border: 1px solid #cbd5e1; border-radius: 3px; font-size: 10px; font-weight: 700;")
            if hasattr(self, "lbl_bpm_display"):
                self.lbl_bpm_display.setStyleSheet(f"font-size: 10.5px; font-weight: 800; color: {t['accent']};")
            if hasattr(self, "btn_vs_play_chords"):
                self.btn_vs_play_chords.setStyleSheet(f"background-color: #eff6ff; color: #1d4ed8; font-weight: 700; font-size: 10px; border: 1px solid #bfdbfe; border-radius: 4px; padding: 2px 7px;")
            if hasattr(self, "btn_vs_stop_chords"):
                self.btn_vs_stop_chords.setStyleSheet("background-color: #ffffff; color: #475569; font-weight: 600; font-size: 10px; border: 1px solid #cbd5e1; border-radius: 4px;")
            if hasattr(self, "vs_engine_combo"):
                self.vs_engine_combo.setStyleSheet("padding: 2px 4px; font-size: 10px; font-weight: 600; border: 1px solid #cbd5e1; border-radius: 4px; background: #ffffff; color: #0f172a;")
            if hasattr(self, "prompt_box_frame"):
                self.prompt_box_frame.setStyleSheet("background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 6px; padding: 4px;")
            if hasattr(self, "txt_suno_prompt"):
                self.txt_suno_prompt.setStyleSheet("background: transparent; border: none; font-size: 11px; color: #0f172a;")
            if hasattr(self, "btn_optimize"):
                self.btn_optimize.setStyleSheet("background-color: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; border-radius: 4px; padding: 3px 5px; font-size: 9.5px; font-weight: 700;")
            if hasattr(self, "btn_studio_cues"):
                self.btn_studio_cues.setStyleSheet("background-color: #fefce8; color: #a16207; border: 1px solid #fde047; border-radius: 4px; padding: 3px 5px; font-size: 9.5px; font-weight: 700;")
            if hasattr(self, "btn_convert"):
                self.btn_convert.setStyleSheet("background-color: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0; border-radius: 4px; padding: 3px 5px; font-size: 9.5px; font-weight: 600;")
            if hasattr(self, "btn_humanize_style"):
                self.btn_humanize_style.setStyleSheet("background-color: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; border-radius: 4px; padding: 3px 5px; font-size: 9.5px; font-weight: 700;")
            if hasattr(self, "btn_copy"):
                self.btn_copy.setStyleSheet("background-color: #ffffff; color: #334155; border: 1px solid #cbd5e1; border-radius: 4px; padding: 3px 5px; font-size: 9.5px; font-weight: 600;")
            if hasattr(self, "macro_box"):
                self.macro_box.setStyleSheet("background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 6px; padding: 4px;")
            if hasattr(self, "macro_btns"):
                for b in self.macro_btns:
                    b.setStyleSheet("""
                        QPushButton {
                            background-color: #f8fafc;
                            color: #475569;
                            border: 1px solid #cbd5e1;
                            border-radius: 3px;
                            padding: 2px 2px;
                            font-size: 8.5px;
                            font-weight: 600;
                        }
                        QPushButton:hover {
                            background-color: #eff6ff;
                            border-color: #3b82f6;
                            color: #1d4ed8;
                        }
                    """)
            if hasattr(self, "btn_copy_template"):
                self.btn_copy_template.setStyleSheet("background-color: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0; border-radius: 4px; padding: 4px 6px; font-size: 10px; font-weight: 700;")
            if hasattr(self, "txt_negative"):
                self.txt_negative.setStyleSheet("background: #ffffff; border: 1px solid #cbd5e1; border-radius: 4px; font-size: 10px; color: #475569; padding: 2px 6px;")
            if hasattr(self, "btn_demo"):
                self.btn_demo.setStyleSheet("background-color: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; border-radius: 5px; padding: 6px; font-size: 10.5px; font-weight: 600;")
            if hasattr(self, "btn_editor"):
                self.btn_editor.setStyleSheet("background-color: #ffffff; color: #0f172a; border: 1px solid #cbd5e1; border-radius: 5px; padding: 6px; font-size: 10.5px; font-weight: 600;")
            if hasattr(self, "btn_batch"):
                self.btn_batch.setStyleSheet(f"background: {t['accent_gradient']}; color: #ffffff; border: 1px solid {t['border_accent']}; border-radius: 5px; padding: 6px; font-size: 10.5px; font-weight: 700;")
            if hasattr(self, "btn_pack"):
                self.btn_pack.setStyleSheet("background-color: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0; border-radius: 5px; padding: 6px; font-size: 10.5px; font-weight: 700;")
