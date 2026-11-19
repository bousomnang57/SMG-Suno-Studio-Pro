"""
Center Workspace: Lyric Editor with Real-Time Syllable Counting Gutter,
Studio Metronome & Tap Tempo, Multi-Take Production Manager, Suno Meta-Tag Toolbar,
Khmer/English Dual Metatag Bar, Inline Chord Studio & Transposer.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QPlainTextEdit, QFrame, QMenu,
    QSpinBox, QComboBox, QApplication, QMessageBox,
    QInputDialog, QSlider, QFileDialog, QStackedWidget
)
from PyQt6.QtCore import Qt, QRect, QSize, pyqtSignal, QTimer, QUrl
from PyQt6.QtGui import QColor, QPainter, QTextFormat, QFont
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from pathlib import Path
from app.syllable_meter import count_line_syllables, LyricMeterAnalyzer
from app.metronome import StudioMetronome
from app.version_manager import VersionManager
from app.song_blueprints import SONG_BLUEPRINTS
from app.ui.styles import get_theme
from app.ui.lyric_highlighter import LyricSyntaxHighlighter
from app.chord_engine import AudioChordSynthesizer, ChordEngine
from app.rhythm_engine import RhythmEngine
from app.hit_analyzer import HitAnalyzer
import re


class SyllableGutterArea(QWidget):
    """Gutter widget displaying line numbers and syllable counts."""
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.gutter_width(), 0)

    def paintEvent(self, event):
        self.editor.gutter_paint_event(event)


class LyricCodeEditor(QPlainTextEdit):
    text_analyzed = pyqtSignal(dict)
    chord_clicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_dark = False
        self.gutter = SyllableGutterArea(self)

        # Attach Professional Lyric & ChordPro Syntax Highlighter
        self.highlighter = LyricSyntaxHighlighter(self, is_dark=False)
        self.highlighter.setDocument(self.document())

        self.blockCountChanged.connect(self.update_gutter_width)
        self.updateRequest.connect(self.update_gutter)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.textChanged.connect(self._on_text_changed)

        self.update_gutter_width(0)
        self.highlight_current_line()

        # Modern monospace coding font with fallback (supports Latin & Khmer)
        font = QFont()
        font.setFamilies(["Cascadia Code", "Consolas", "Courier New", "Khmer OS Battambang", "monospace"])
        font.setPointSize(12)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)

    def set_theme(self, theme_or_dark):
        t = get_theme(theme_or_dark)
        self.theme = t
        self.is_dark = t.get("is_dark", True)
        try:
            if hasattr(self, "highlighter") and self.highlighter:
                self.highlighter.set_dark_mode(self.is_dark)
            else:
                self.highlighter = LyricSyntaxHighlighter(self, is_dark=self.is_dark)
                self.highlighter.setDocument(self.document())
        except (RuntimeError, AttributeError):
            self.highlighter = LyricSyntaxHighlighter(self, is_dark=self.is_dark)
            self.highlighter.setDocument(self.document())
        self.highlight_current_line()
        self.gutter.update()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        # Check if user clicked on a chord tag like [Am], [C#m7], [F]
        cursor = self.cursorForPosition(event.pos())
        block_text = cursor.block().text()
        col = cursor.positionInBlock()

        chord_match = re.search(r'\[([A-G][#b]?(m|maj|min|dim|aug|sus[24]?|[0-9])*(/[A-G][#b]?)?)\]', block_text)
        if chord_match:
            for m in re.finditer(r'\[([A-G][#b]?(m|maj|min|dim|aug|sus[24]?|[0-9])*(/[A-G][#b]?)?)\]', block_text):
                if m.start() <= col <= m.end():
                    chord_token = m.group(1)
                    AudioChordSynthesizer.play_chord(chord_token)
                    self.chord_clicked.emit(chord_token)
                    break

    def gutter_width(self):
        digits = max(1, len(str(self.blockCount())))
        space = 10 + self.fontMetrics().horizontalAdvance('9') * (digits + 5)
        return max(75, space)

    def update_gutter_width(self, _):
        self.setViewportMargins(self.gutter_width(), 0, 0, 0)

    def update_gutter(self, rect, dy):
        if dy:
            self.gutter.scroll(0, dy)
        else:
            self.gutter.update(0, rect.y(), self.gutter.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.update_gutter_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.gutter.setGeometry(QRect(cr.left(), cr.top(), self.gutter_width(), cr.height()))

    def highlight_current_line(self):
        extra_selections = []
        if not self.isReadOnly():
            from PyQt6.QtWidgets import QTextEdit
            selection = QTextEdit.ExtraSelection()
            line_color = QColor("#181c2e") if self.is_dark else QColor("#f1f5f9")
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        self.setExtraSelections(extra_selections)

    def gutter_paint_event(self, event):
        painter = QPainter(self.gutter)
        t = getattr(self, "theme", get_theme(self.is_dark))
        bg_col = QColor(t.get("bg_window", "#090b14" if self.is_dark else "#f8fafc"))
        painter.fillRect(event.rect(), bg_col)

        # Separator line
        sep_col = QColor(t.get("border", "#1c2035" if self.is_dark else "#e2e8f0"))
        painter.setPen(sep_col)
        painter.drawLine(self.gutter.width() - 1, event.rect().top(), self.gutter.width() - 1, event.rect().bottom())

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())

        small_font = QFont("Segoe UI", 9)
        small_font.setBold(True)
        painter.setFont(small_font)

        line_num_col = QColor("#64748b") if self.is_dark else QColor("#94a3b8")

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                line_text = block.text().strip()
                is_header = line_text.startswith("[") and line_text.endswith("]")

                # Draw Line number in muted grey
                painter.setPen(line_num_col)
                painter.drawText(4, top, 24, self.fontMetrics().height(), Qt.AlignmentFlag.AlignRight, str(block_number + 1))

                # Draw Syllable pill or section badge
                if is_header:
                    badge_col = QColor("#c084fc") if self.is_dark else QColor("#7c3aed")
                    painter.setPen(badge_col)
                    painter.drawText(34, top, self.gutter.width() - 38, self.fontMetrics().height(), Qt.AlignmentFlag.AlignRight, "SEC")
                elif line_text:
                    syl_count = count_line_syllables(line_text)
                    if syl_count > 0:
                        if syl_count in [7, 8]:
                            painter.setPen(QColor("#10b981"))  # emerald green: perfect classical Khmer/ballad meter!
                        elif syl_count in [4, 5]:
                            painter.setPen(QColor("#06b6d4"))  # cyan: fast rhythm / Kantrum / Kkak Gatei!
                        elif syl_count > 13:
                            painter.setPen(QColor("#fbbf24" if self.is_dark else "#d97706"))  # amber warning
                        elif syl_count < 4:
                            painter.setPen(QColor("#64748b"))  # slate
                        else:
                            painter.setPen(QColor("#38bdf8" if self.is_dark else "#2563eb"))  # vibrant blue

                        painter.drawText(34, top, self.gutter.width() - 38, self.fontMetrics().height(), Qt.AlignmentFlag.AlignRight, f"{syl_count}s")

            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1

    def _on_text_changed(self):
        self.gutter.update()
        text = self.toPlainText()
        analysis = LyricMeterAnalyzer.analyze(text)
        self.text_analyzed.emit(analysis)


class EditorPanel(QWidget):
    rewrite_requested = pyqtSignal(str, str)  # selected_text, instruction
    metronome_state_changed = pyqtSignal(bool)
    visual_arranger_requested = pyqtSignal()
    transpose_requested = pyqtSignal(int)      # semitones (-1, +1)
    rhyme_search_requested = pyqtSignal(str)   # word
    clone_song_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.metronome = StudioMetronome(120)
        self.version_manager = VersionManager()
        self.current_take_name = "Take 1 (Main)"

        # Media player for attached Suno/Udio audio stem
        self.stem_player = QMediaPlayer()
        self.stem_audio_output = QAudioOutput()
        self.stem_player.setAudioOutput(self.stem_audio_output)
        self.stem_player.positionChanged.connect(self._on_stem_position_changed)
        self.stem_player.durationChanged.connect(self._on_stem_duration_changed)
        self.stem_player.playbackStateChanged.connect(self._on_stem_state_changed)
        self.attached_audio_path = None

        self._init_ui()
        self._connect_metronome()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # ── 1. Top Title, Multi-Take & Quick Copy Bar ──
        top_bar = QHBoxLayout()
        top_bar.setSpacing(5)

        self.title_input = QLineEdit("Untitled Song")
        self.title_input.setMinimumWidth(140)
        self.title_input.setStyleSheet("font-size: 13.5px; font-weight: 700; color: #1e293b; padding: 4px 8px; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 6px;")
        top_bar.addWidget(self.title_input, stretch=2)

        # Multi-Take Controls
        take_box = QHBoxLayout()
        take_box.setSpacing(3)
        self.lbl_take = QLabel("Take:")
        self.lbl_take.setStyleSheet("font-weight: 700; color: #475569; font-size: 11px;")
        take_box.addWidget(self.lbl_take)

        self.take_combo = QComboBox()
        self.take_combo.addItems(self.version_manager.list_takes())
        self.take_combo.setFont(QFont("Segoe UI", 9))
        self.take_combo.setStyleSheet("padding: 3px 6px; font-weight: 600; min-width: 95px;")
        self.take_combo.currentTextChanged.connect(self._on_take_switched)
        take_box.addWidget(self.take_combo)

        self.btn_add_take = QPushButton("+ Take")
        self.btn_add_take.setToolTip("Add New Empty Take")
        self.btn_add_take.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add_take.setStyleSheet("background-color: #eff6ff; color: #1d4ed8; font-weight: 700; font-size: 8.5pt; padding: 3px 7px; border: 1px solid #bfdbfe; border-radius: 4px;")
        self.btn_add_take.clicked.connect(self._on_add_take)
        take_box.addWidget(self.btn_add_take)

        self.btn_dup_take = QPushButton("Dup")
        self.btn_dup_take.setToolTip("Duplicate Current Take (A/B Variations)")
        self.btn_dup_take.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_dup_take.setStyleSheet("background-color: #f0fdf4; color: #15803d; font-weight: 700; font-size: 8.5pt; padding: 3px 7px; border: 1px solid #bbf7d0; border-radius: 4px;")
        self.btn_dup_take.clicked.connect(self._on_dup_take)
        take_box.addWidget(self.btn_dup_take)

        self.btn_del_take = QPushButton("Del")
        self.btn_del_take.setToolTip("Delete Current Take")
        self.btn_del_take.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_del_take.setStyleSheet("background-color: #fef2f2; color: #dc2626; font-weight: 700; font-size: 8.5pt; padding: 3px 7px; border: 1px solid #fecaca; border-radius: 4px;")
        self.btn_del_take.clicked.connect(self._on_del_take)
        take_box.addWidget(self.btn_del_take)

        # Quick Copy & Clean Actions right in top bar for instant access
        self.btn_clean_tags = QPushButton("🧹 Clean")
        self.btn_clean_tags.setToolTip("Strip all [bracket] tags and copy clean lyrics for singers")
        self.btn_clean_tags.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clean_tags.setStyleSheet("background-color: #f8fafc; color: #475569; border: 1px solid #cbd5e1; font-size: 8.5pt; padding: 3px 7px; border-radius: 4px; font-weight: 600;")
        self.btn_clean_tags.clicked.connect(self._copy_clean_lyrics)
        take_box.addWidget(self.btn_clean_tags)

        self.btn_copy_lyrics = QPushButton("📋 Copy All")
        self.btn_copy_lyrics.setToolTip("Copy complete lyric sheet to clipboard")
        self.btn_copy_lyrics.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_copy_lyrics.setStyleSheet("background-color: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0; font-size: 8.5pt; padding: 3px 7px; border-radius: 4px; font-weight: 700;")
        self.btn_copy_lyrics.clicked.connect(self._copy_full_lyrics)
        take_box.addWidget(self.btn_copy_lyrics)

        top_bar.addLayout(take_box)
        layout.addLayout(top_bar)

        # ── 2. Sleek Segmented Studio Sub-Bar Deck (Decluttered Pro DAW UI) ──
        self.tool_deck_frame = QFrame()
        self.tool_deck_frame.setObjectName("toolDeckFrame")
        deck_outer = QVBoxLayout(self.tool_deck_frame)
        deck_outer.setContentsMargins(6, 4, 6, 4)
        deck_outer.setSpacing(4)

        # Segmented Sub-Tab Row + Always-Accessible Chord Audition
        deck_tabs_row = QHBoxLayout()
        deck_tabs_row.setSpacing(4)

        self.btn_sub_tags = QPushButton("🏷️ Tags & Chords")
        self.btn_sub_tags.setCheckable(True)
        self.btn_sub_tags.setChecked(True)
        self.btn_sub_tags.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_sub_tags.clicked.connect(lambda: self._switch_tool_deck(0))

        self.btn_sub_audio = QPushButton("🥁 Tempo & Audio")
        self.btn_sub_audio.setCheckable(True)
        self.btn_sub_audio.setChecked(False)
        self.btn_sub_audio.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_sub_audio.clicked.connect(lambda: self._switch_tool_deck(1))

        self.btn_sub_pro = QPushButton("🎛️ Studio Pro Tools")
        self.btn_sub_pro.setCheckable(True)
        self.btn_sub_pro.setChecked(False)
        self.btn_sub_pro.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_sub_pro.clicked.connect(lambda: self._switch_tool_deck(2))

        for sb in [self.btn_sub_tags, self.btn_sub_audio, self.btn_sub_pro]:
            sb.setFixedHeight(24)
            deck_tabs_row.addWidget(sb)

        deck_tabs_row.addStretch()

        # Quick live chord audition right on sub-header
        self.btn_audition_chords = QPushButton("🔊 Chords")
        self.btn_audition_chords.setToolTip("Audition chords in lyrics using polyphonic audio synth")
        self.btn_audition_chords.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_audition_chords.setFixedHeight(24)
        self.btn_audition_chords.setStyleSheet("background-color: #f5f3ff; color: #7c3aed; border: 1px solid #ddd6fe; font-size: 8.5pt; padding: 2px 8px; border-radius: 4px; font-weight: 700;")
        self.btn_audition_chords.clicked.connect(self._audition_lyrics_chords)
        deck_tabs_row.addWidget(self.btn_audition_chords)

        self.btn_arranger_jump = QPushButton("🎨 Arranger")
        self.btn_arranger_jump.setToolTip("Jump to Visual Arranger (DAW Timeline & Chords)")
        self.btn_arranger_jump.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_arranger_jump.setFixedHeight(24)
        self.btn_arranger_jump.setStyleSheet("background-color: #faf5ff; color: #7c3aed; font-weight: 700; font-size: 8.5pt; padding: 2px 8px; border-radius: 4px; border: 1px solid #d8b4fe;")
        self.btn_arranger_jump.clicked.connect(self.visual_arranger_requested.emit)
        deck_tabs_row.addWidget(self.btn_arranger_jump)

        deck_outer.addLayout(deck_tabs_row)

        self.tool_deck_stack = QStackedWidget()
        self.tool_deck_stack.setFixedHeight(32)
        deck_outer.addWidget(self.tool_deck_stack)
        layout.addWidget(self.tool_deck_frame)

        # ── Deck Page 1 widget (Tempo, Metronome & Audio Stem) ──
        self.metro_frame = QFrame()
        self.metro_frame.setObjectName("metroFrame")
        metro_layout = QHBoxLayout(self.metro_frame)
        metro_layout.setContentsMargins(2, 2, 2, 2)
        metro_layout.setSpacing(4)

        self.metro_led = QLabel("●")
        self.metro_led.setStyleSheet("color: #94a3b8; font-size: 14px; border: none; background: transparent;")
        metro_layout.addWidget(self.metro_led)

        self.btn_metro_toggle = QPushButton("▶ Metro")
        self.btn_metro_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_metro_toggle.setStyleSheet("background-color: #f1f5f9; color: #2563eb; font-weight: 700; font-size: 8.5pt; padding: 3px 6px; border-radius: 4px;")
        self.btn_metro_toggle.clicked.connect(self._toggle_metronome)
        metro_layout.addWidget(self.btn_metro_toggle)

        self.lbl_bpm_tag = QLabel("BPM:")
        self.lbl_bpm_tag.setStyleSheet("font-weight: 700; color: #94a3b8; font-size: 8.5pt; border: none; background: transparent;")
        metro_layout.addWidget(self.lbl_bpm_tag)
        self.metro_bpm_spin = QSpinBox()
        self.metro_bpm_spin.setRange(40, 240)
        self.metro_bpm_spin.setValue(120)
        self.metro_bpm_spin.setStyleSheet("font-weight: 700; padding: 1px 4px;")
        self.metro_bpm_spin.valueChanged.connect(lambda v: self.metronome.set_bpm(v))
        metro_layout.addWidget(self.metro_bpm_spin)

        self.btn_tap = QPushButton("👆 Tap")
        self.btn_tap.setToolTip("Tap Tempo Rhythmically")
        self.btn_tap.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_tap.setStyleSheet("background-color: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; font-size: 8.5pt; padding: 2px 5px; border-radius: 4px; font-weight: 600;")
        self.btn_tap.clicked.connect(self._on_tap_clicked)
        metro_layout.addWidget(self.btn_tap)

        self.metro_sig_combo = QComboBox()
        self.metro_sig_combo.addItems(["4/4", "3/4", "6/8"])
        self.metro_sig_combo.setFont(QFont("Segoe UI", 8))
        self.metro_sig_combo.currentIndexChanged.connect(self._on_time_sig_changed)
        metro_layout.addWidget(self.metro_sig_combo)

        self.lbl_groove = QLabel("🥁")
        self.lbl_groove.setStyleSheet("font-weight: 700; color: #64748b; font-size: 9pt; border: none; background: transparent;")
        metro_layout.addWidget(self.lbl_groove)

        self.combo_groove = QComboBox()
        self.combo_groove.addItems(RhythmEngine.get_available_grooves())
        self.combo_groove.setFont(QFont("Segoe UI", 8))
        self.combo_groove.setMinimumWidth(105)
        self.combo_groove.setMaximumWidth(155)
        self.combo_groove.setToolTip("Play authentic Khmer or Pop rhythm groove loop with tempo")
        self.combo_groove.setStyleSheet("font-weight: 600; padding: 2px 4px;")
        self.combo_groove.currentTextChanged.connect(self._on_groove_changed)
        metro_layout.addWidget(self.combo_groove)

        self.btn_load_stem = QPushButton("📂 Audio")
        self.btn_load_stem.setToolTip("Attach Suno/Udio generated MP3/WAV to play alongside lyrics")
        self.btn_load_stem.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_load_stem.setStyleSheet("background-color: #eff6ff; color: #1d4ed8; font-weight: 700; font-size: 8.5pt; padding: 2px 6px; border: 1px solid #bfdbfe; border-radius: 4px;")
        self.btn_load_stem.clicked.connect(self._attach_audio_stem)
        metro_layout.addWidget(self.btn_load_stem)

        self.btn_play_stem = QPushButton("▶")
        self.btn_play_stem.setEnabled(False)
        self.btn_play_stem.setToolTip("Play / Pause attached audio track")
        self.btn_play_stem.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_play_stem.setFixedWidth(28)
        self.btn_play_stem.setStyleSheet("font-weight: 700; font-size: 8.5pt; padding: 2px 4px; border-radius: 4px;")
        self.btn_play_stem.clicked.connect(self._toggle_stem_playback)
        metro_layout.addWidget(self.btn_play_stem)

        self.lbl_stem_track = QLabel("")
        self.lbl_stem_track.setVisible(False)

        self.stem_slider = QSlider(Qt.Orientation.Horizontal)
        self.stem_slider.setRange(0, 1000)
        self.stem_slider.setEnabled(False)
        self.stem_slider.sliderMoved.connect(self._seek_stem)
        metro_layout.addWidget(self.stem_slider, stretch=1)

        self.lbl_stem_time = QLabel("0:00")
        self.lbl_stem_time.setStyleSheet("font-size: 9.5px; font-weight: 700; color: #475569; border: none; background: transparent;")
        metro_layout.addWidget(self.lbl_stem_time)

        self.btn_remove_stem = QPushButton("✕")
        self.btn_remove_stem.setToolTip("Detach Audio Track")
        self.btn_remove_stem.setVisible(False)
        self.btn_remove_stem.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_remove_stem.setStyleSheet("color: #dc2626; font-weight: 800; border: none; padding: 2px 4px;")
        self.btn_remove_stem.clicked.connect(self._remove_audio_stem)
        metro_layout.addWidget(self.btn_remove_stem)

        # Compatibility dummy ref if stem_frame is referenced
        self.stem_frame = self.metro_frame

        # ── Deck Page 0 widget (Section Tags & Chords) ──
        self.tags_page = QWidget()
        sec_layout = QHBoxLayout(self.tags_page)
        sec_layout.setContentsMargins(2, 2, 2, 2)
        sec_layout.setSpacing(3)

        # Khmer Poetic Section Tags Dropdown
        self.btn_khmer_tags = QPushButton("🇰🇭 ខ្មែរ ▾")
        self.btn_khmer_tags.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_khmer_tags.setToolTip("Authentic Khmer Section Metatags (ស្លាកផ្នែកកំណាព្យ និងបទខ្មែរ)")
        self.btn_khmer_tags.setStyleSheet("background-color: #fdf2f8; color: #be185d; font-weight: 700; font-size: 8.5pt; padding: 3px 5px; border-radius: 4px; border: 1px solid #fbcfe8;")
        kh_menu = QMenu(self)
        kh_menu.setStyleSheet("background-color: #ffffff; color: #1e293b; border: 1px solid #cbd5e1; padding: 4px;")
        kh_tags = [
            "[អារម្ភកថា: Intro - សំឡេងទ្រ និងព្យាណូ]",
            "[វគ្គ១: Verse 1 - សំឡេងស្រទន់]",
            "[វគ្គ២: Verse 2 - ចង្វាក់រលូន]",
            "[តភ្ជាប់: Pre-Chorus - ចង្វាក់កើនឡើង]",
            "[បន្ទរ: Chorus - អារម្មណ៍ឡើងខ្ពស់ ស្គរបុកពេញ]",
            "[បន្ទរបន្ថែម: Post-Chorus]",
            "[តភ្ជាប់ផ្លាស់ប្តូរ: Bridge - សំឡេងកូតទ្រកំសត់]",
            "[ទោល: Solo - ឧបករណ៍ភ្លេងបុរាណ]",
            "[បញ្ចប់: Outro - សំឡេងស្រុតចុះបន្តិចម្តងៗ]",
            "[End]"
        ]
        for kt in kh_tags:
            kh_menu.addAction(kt, lambda t=kt: self.insert_section_tag(t))
        self.btn_khmer_tags.setMenu(kh_menu)
        sec_layout.addWidget(self.btn_khmer_tags)

        # Hit Blueprints Dropdown
        self.btn_blueprints = QPushButton("📐 Hits ▾")
        self.btn_blueprints.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_blueprints.setToolTip("Commercial Hit Blueprints")
        self.btn_blueprints.setStyleSheet("background-color: #f0fdf4; color: #166534; font-weight: 700; font-size: 8.5pt; padding: 3px 5px; border-radius: 4px; border: 1px solid #bbf7d0;")
        bp_menu = QMenu(self)
        bp_menu.setStyleSheet("background-color: #ffffff; color: #1e293b; border: 1px solid #cbd5e1; padding: 4px;")
        for bp_name in SONG_BLUEPRINTS.keys():
            bp_menu.addAction(bp_name, lambda name=bp_name: self._load_blueprint(name))
        self.btn_blueprints.setMenu(bp_menu)
        sec_layout.addWidget(self.btn_blueprints)

        # Vocal & Dynamics Dropdown
        self.btn_dynamics = QPushButton("🎙️ Vocal ▾")
        self.btn_dynamics.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_dynamics.setStyleSheet("background-color: #eff6ff; color: #1d4ed8; font-weight: 700; font-size: 8.5pt; padding: 3px 5px; border-radius: 4px; border: 1px solid #bfdbfe;")
        dyn_menu = QMenu(self)
        dyn_menu.setStyleSheet("background-color: #ffffff; color: #1e293b; border: 1px solid #cbd5e1; padding: 4px;")
        dynamics_tags = [
            "[Whisper - intimate]", "[Belting - powerful peak]", "[Falsetto Run]",
            "[Harmonies & Backing Vocals]", "[Call & Response]", "[Autotune Heavy]",
            "[808 Bass Drop]", "[Key Change +1]", "[Epic Guitar Solo]",
            "[Tape Stop Effect]", "[Vinyl Crackle]", "[Crowd Cheers & Atmosphere]"
        ]
        for tag in dynamics_tags:
            dyn_menu.addAction(tag, lambda t=tag: self.insert_section_tag(t))
        self.btn_dynamics.setMenu(dyn_menu)
        sec_layout.addWidget(self.btn_dynamics)

        # Extra Suno Cues Dropdown
        self.btn_cues = QPushButton("⚡ Cues ▾")
        self.btn_cues.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cues.setStyleSheet("background-color: #faf5ff; color: #7c3aed; font-weight: 700; font-size: 8.5pt; padding: 3px 5px; border-radius: 4px; border: 1px solid #d8b4fe;")
        cues_menu = QMenu(self)
        cues_menu.setStyleSheet("background-color: #ffffff; color: #1e293b; border: 1px solid #cbd5e1; padding: 4px;")
        extra_cues = [
            "[Intro - atmospheric build]", "[Drop - full energy]", "[Bass Drop]",
            "[Guitar Solo]", "[Acoustic Breakdown]", "[Key Change +1]",
            "[Vocal Ad-libs]", "[Fade Out - reverb tail]"
        ]
        for cue in extra_cues:
            cues_menu.addAction(cue, lambda c=cue: self.insert_section_tag(c))
        self.btn_cues.setMenu(cues_menu)
        sec_layout.addWidget(self.btn_cues)

        # Core essential section tags
        for sec in ["[Verse]", "[Chorus]", "[Bridge]", "[Outro]"]:
            btn = QPushButton(sec)
            btn.setObjectName("sectionButton")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("font-size: 8pt; font-weight: 600; padding: 2px 4px;")
            btn.clicked.connect(lambda _, s=sec: self.insert_section_tag(s))
            sec_layout.addWidget(btn)

        # Inline Chord Inserter Dropdown
        self.btn_chords_menu = QPushButton("🎹 Chord ▾")
        self.btn_chords_menu.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_chords_menu.setToolTip("Insert musical chord marker at cursor")
        self.btn_chords_menu.setStyleSheet("background-color: #fdf4ff; color: #86198f; font-weight: 700; font-size: 8.5pt; padding: 3px 5px; border-radius: 4px; border: 1px solid #f0abfc;")
        chord_menu = QMenu(self)
        chord_menu.setStyleSheet("background-color: #ffffff; color: #1e293b; border: 1px solid #cbd5e1; padding: 4px;")
        popular_chords = [
            "Am", "C", "F", "G", "Dm", "Em", "Bb", "D", "A", "E",
            "Cmaj7", "Dm7", "G7", "Am7", "Fmaj7", "E7", "F#m", "Bm", "Gm"
        ]
        for ch in popular_chords:
            chord_menu.addAction(f"[{ch}]", lambda c=ch: self._insert_chord_at_cursor(c))
        chord_menu.addSeparator()
        chord_menu.addAction("✏️ Custom Chord...", self._prompt_custom_chord)
        self.btn_chords_menu.setMenu(chord_menu)
        sec_layout.addWidget(self.btn_chords_menu)

        # Direct Semitone Transpose Buttons
        self.btn_trans_down = QPushButton("♭ -1")
        self.btn_trans_down.setToolTip("Transpose chords in lyrics down -1 semitone")
        self.btn_trans_down.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_trans_down.setStyleSheet("background-color: #f8fafc; color: #334155; border: 1px solid #cbd5e1; border-radius: 4px; font-size: 8.5pt; font-weight: 700; padding: 3px 6px;")
        self.btn_trans_down.clicked.connect(lambda: self._on_transpose(-1))
        sec_layout.addWidget(self.btn_trans_down)

        self.btn_trans_up = QPushButton("♯ +1")
        self.btn_trans_up.setToolTip("Transpose chords in lyrics up +1 semitone")
        self.btn_trans_up.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_trans_up.setStyleSheet("background-color: #f8fafc; color: #334155; border: 1px solid #cbd5e1; border-radius: 4px; font-size: 8.5pt; font-weight: 700; padding: 3px 6px;")
        self.btn_trans_up.clicked.connect(lambda: self._on_transpose(1))
        sec_layout.addWidget(self.btn_trans_up)

        sec_layout.addStretch()

        # ── Deck Page 2 widget (Studio Pro Tools) ──
        self.pro_features_frame = QFrame()
        self.pro_features_frame.setObjectName("proFeaturesFrame")
        pf_layout = QHBoxLayout(self.pro_features_frame)
        pf_layout.setContentsMargins(2, 2, 2, 2)
        pf_layout.setSpacing(6)

        # 1. Vocal Melody Guide
        self.btn_pro_melody = QPushButton("🎼 Melody & Sheet")
        self.btn_pro_melody.setToolTip("Generate vocal topline guide, export MIDI & MusicXML sheet music")
        self.btn_pro_melody.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_pro_melody.setStyleSheet("background-color: #ede9fe; color: #6d28d9; font-weight: 700; font-size: 8.5pt; padding: 3px 8px; border-radius: 4px; border: 1px solid #ddd6fe;")
        self.btn_pro_melody.clicked.connect(self._open_melody_guide)
        pf_layout.addWidget(self.btn_pro_melody)

        # 2. Scratch Vocalist
        self.btn_pro_vocal = QPushButton("🎤 Scratch Vocal")
        self.btn_pro_vocal.setToolTip("Audition lyrics with neural Khmer & international studio singers")
        self.btn_pro_vocal.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_pro_vocal.setStyleSheet("background-color: #eff6ff; color: #1d4ed8; font-weight: 700; font-size: 8.5pt; padding: 3px 8px; border-radius: 4px; border: 1px solid #bfdbfe;")
        self.btn_pro_vocal.clicked.connect(self._open_scratch_vocalist)
        pf_layout.addWidget(self.btn_pro_vocal)

        # 3. Chord Soundboard
        self.btn_pro_chords = QPushButton("🎹 Soundboard")
        self.btn_pro_chords.setToolTip("Interactive Piano/Rhodes/Guitar chord progression player & diatonic pad matrix")
        self.btn_pro_chords.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_pro_chords.setStyleSheet("background-color: #fdf4ff; color: #86198f; font-weight: 700; font-size: 8.5pt; padding: 3px 8px; border-radius: 4px; border: 1px solid #f0abfc;")
        self.btn_pro_chords.clicked.connect(self._open_chord_soundboard)
        pf_layout.addWidget(self.btn_pro_chords)

        # 4. Khmer Poetic Meter
        self.btn_pro_khmer = QPushButton("📜 Khmer Meter")
        self.btn_pro_khmer.setToolTip("Khmer classical poetic meter & rhyme map engine (ពាក្យ៧, ពាក្យ៨, ព្រហ្មគីតិ, កាកគតិ, ភុជង្គលីលា)")
        self.btn_pro_khmer.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_pro_khmer.setStyleSheet("background-color: #f0fdf4; color: #15803d; font-weight: 700; font-size: 8.5pt; padding: 3px 8px; border-radius: 4px; border: 1px solid #bbf7d0;")
        self.btn_pro_khmer.clicked.connect(self._open_khmer_poetry_meter)
        pf_layout.addWidget(self.btn_pro_khmer)

        # 5. Album Cover Art
        self.btn_pro_cover = QPushButton("🖼️ Cover Art")
        self.btn_pro_cover.setToolTip("AI Album Cover & YouTube MV Thumbnail Generator (1:1 & 16:9)")
        self.btn_pro_cover.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_pro_cover.setStyleSheet("background-color: #fff7ed; color: #c2410c; font-weight: 700; font-size: 8.5pt; padding: 3px 8px; border-radius: 4px; border: 1px solid #fed7aa;")
        self.btn_pro_cover.clicked.connect(self._open_cover_art_generator)
        pf_layout.addWidget(self.btn_pro_cover)

        pf_layout.addStretch()

        # Mount all 3 compact pages into the Segmented Studio Sub-Bar Deck
        self.tool_deck_stack.addWidget(self.tags_page)
        self.tool_deck_stack.addWidget(self.metro_frame)
        self.tool_deck_stack.addWidget(self.pro_features_frame)
        self.tool_deck_stack.setCurrentIndex(0)

        # ── 3c. Dynamic Song Chord Ribbon ──
        self.chord_ribbon_frame = QFrame()
        self.chord_ribbon_frame.setObjectName("chordRibbonFrame")
        self.chord_ribbon_frame.setStyleSheet("background-color: #eff6ff; border: 1px solid #bfdbfe; border-radius: 4px; padding: 2px;")
        self.chord_ribbon_frame.setVisible(False)
        self.chord_ribbon_layout = QHBoxLayout(self.chord_ribbon_frame)
        self.chord_ribbon_layout.setContentsMargins(4, 1, 4, 1)
        self.chord_ribbon_layout.setSpacing(4)
        layout.addWidget(self.chord_ribbon_frame)

        # ── 4. Main Code Editor with Syllable Gutter ──
        self.editor = LyricCodeEditor()
        self.editor.text_analyzed.connect(self._on_analysis_updated)
        self.editor.selectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.editor, stretch=1)

        # ── 5. Floating AI Selection Toolbar ──
        self.selection_bar = QFrame()
        self.selection_bar.setObjectName("selectionBarFrame")
        self.selection_bar.setStyleSheet("QFrame#selectionBarFrame { background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; } QFrame#selectionBarFrame QLabel { border: none; background: transparent; }")
        sel_layout = QHBoxLayout(self.selection_bar)
        sel_layout.setContentsMargins(8, 4, 8, 4)
        sel_layout.setSpacing(6)

        self.sel_label = QLabel("✨ Selection Tools:")
        self.sel_label.setToolTip("Highlight lyric lines in the editor to rewrite, elevate, or find rhymes with Gemini")
        self.sel_label.setStyleSheet("color: #475569; font-size: 11px; font-weight: 600;")
        sel_layout.addWidget(self.sel_label, stretch=1)

        # Rhyme lookup button for selected text
        self.btn_rhyme_sel = QPushButton("🎯 Rhymes")
        self.btn_rhyme_sel.setToolTip("Find rhymes and slants for selected word in Rhyme Lab")
        self.btn_rhyme_sel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_rhyme_sel.setEnabled(False)
        self.btn_rhyme_sel.setStyleSheet("background-color: #eff6ff; color: #2563eb; font-weight: 700; font-size: 9pt; padding: 4px 8px; border-radius: 5px; border: 1px solid #bfdbfe;")
        self.btn_rhyme_sel.clicked.connect(self._lookup_rhyme_for_selection)
        sel_layout.addWidget(self.btn_rhyme_sel)

        self.btn_rewrite_menu = QPushButton("Refine with Gemini ▾")
        self.btn_rewrite_menu.setObjectName("accentButton")
        self.btn_rewrite_menu.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_rewrite_menu.setEnabled(False)

        menu = QMenu(self)
        menu.setStyleSheet("background-color: #ffffff; color: #1e293b; border: 1px solid #cbd5e1; padding: 4px;")
        menu.addAction("✨ Make More Rhythmic & Punchy (Tempo-locked)", lambda: self._trigger_rewrite("Make more rhythmic, punchy, and lock tight into musical tempo"))
        menu.addAction("🎨 Elevate Lyrical Poetry & Metaphors", lambda: self._trigger_rewrite("Elevate lyrical poetry, deeper imagery, and vivid sensory metaphors"))
        menu.addAction("🎯 Strengthen End-Rhymes & Couplets", lambda: self._trigger_rewrite("Strengthen end-rhymes and multi-syllabic cadences"))
        menu.addAction("🇰🇭 Adapt to Poetic Khmer (កំណាព្យខ្មែរ)", lambda: self._trigger_rewrite("Adapt and translate into authentic poetic Khmer lyrics (បទកាកគតិ ឬ ពាក្យ៧) preserving song meter"))
        menu.addAction("🇬🇧 Adapt to Billboard English", lambda: self._trigger_rewrite("Translate and culturally adapt into Billboard English radio hit lyrics"))
        menu.addAction("🎙️ Insert Singer Ad-libs & Dynamics", lambda: self._trigger_rewrite("Insert authentic vocal cues, harmonies, and ad-libs in brackets"))
        menu.addSeparator()
        menu.addAction("👤 Humanize Selection (Singer Breath & Realism)", lambda: self._trigger_humanize_selection())
        self.btn_rewrite_menu.setMenu(menu)
        sel_layout.addWidget(self.btn_rewrite_menu)

        self.btn_humanize_full = QPushButton("👤 Humanize Lyrics")
        self.btn_humanize_full.setToolTip("Transform entire lyrics with natural singer breath marks, emotional pauses, and sensory realism")
        self.btn_humanize_full.setStyleSheet("background-color: #ecfdf5; color: #047857; font-weight: 700; font-size: 9pt; padding: 4px 10px; border-radius: 5px; border: 1px solid #a7f3d0;")
        self.btn_humanize_full.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_humanize_full.clicked.connect(self._humanize_entire_lyrics)
        sel_layout.addWidget(self.btn_humanize_full)

        self.btn_clone_meaning = QPushButton("🧬 Clone Song")
        self.btn_clone_meaning.setToolTip("Clone song's emotional thesis and story with 100% original lyrics & chords")
        self.btn_clone_meaning.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clone_meaning.clicked.connect(self.clone_song_requested.emit)
        sel_layout.addWidget(self.btn_clone_meaning)

        layout.addWidget(self.selection_bar)

        # ── 6. Bottom Statistics & Rhythm Meter Bar (Zero Trailing Bullet) ──
        self.stats_frame = QFrame()
        self.stats_frame.setObjectName("editorStatsFrame")
        self.stats_frame.setStyleSheet("QFrame#editorStatsFrame { background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px; } QFrame#editorStatsFrame QLabel { border: none; background: transparent; }")
        stats_layout = QHBoxLayout(self.stats_frame)
        stats_layout.setContentsMargins(8, 4, 8, 4)
        stats_layout.setSpacing(6)

        self.stat_lines = QLabel("Lines: 0")
        self.stat_words = QLabel("Words: 0")
        self.stat_syllables = QLabel("Syllables: 0")
        self.stat_avg = QLabel("Avg/Line: 0.0")
        self.flow_label = QLabel("Flow: 100%")
        self.flow_label.setStyleSheet("color: #2563eb; font-weight: 700; font-size: 11px; border: none; background: transparent;")
        self.stat_duration = QLabel("⏱️ ~0m 00s")
        self.stat_duration.setStyleSheet("color: #059669; font-weight: 800; font-size: 11px; background: #ecfdf5; padding: 1px 6px; border-radius: 3px; border: none;")

        stat_items = [self.stat_lines, self.stat_words, self.stat_syllables, self.stat_avg, self.flow_label, self.stat_duration]
        self.stat_bullets = []
        for i, item in enumerate(stat_items):
            stats_layout.addWidget(item)
            bullet = QLabel("•")
            bullet.setStyleSheet("color: #94a3b8; font-size: 10px; border: none; background: transparent; padding: 0px;")
            self.stat_bullets.append(bullet)
            stats_layout.addWidget(bullet)

        self.btn_hit_score = QPushButton("🌟 Hit: 85%")
        self.btn_hit_score.setToolTip("Click to inspect Commercial Hit Potential & AI Vocal Safety")
        self.btn_hit_score.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_hit_score.setStyleSheet("background: #fdf4ff; color: #9333ea; font-weight: 800; font-size: 11px; padding: 2px 7px; border: 1px solid #e9d5ff; border-radius: 4px;")
        self.btn_hit_score.clicked.connect(self._open_hit_inspector)
        stats_layout.addWidget(self.btn_hit_score)

        stats_layout.addStretch()
        layout.addWidget(self.stats_frame)

    # ── Metronome Event Handlers ──
    def _connect_metronome(self):
        self.metronome.beat_pulse.connect(self._on_metro_beat)
        self.metronome.bpm_changed.connect(lambda bpm: self.metro_bpm_spin.setValue(bpm))

    def _toggle_metronome(self):
        running = self.metronome.toggle()
        groove_name = self.combo_groove.currentText()
        t = getattr(self, "theme", get_theme(getattr(self, "is_dark", True)))
        if running:
            self.btn_metro_toggle.setText("⏹ Stop")
            self.btn_metro_toggle.setStyleSheet("background-color: #7f1d1d; color: #fecaca; font-weight: 700; font-size: 8.5pt; padding: 3px 6px; border-radius: 4px; border: 1px solid #ef4444;")
            if groove_name != "Off (Standard Metronome)":
                RhythmEngine.play_groove(groove_name, self.metro_bpm_spin.value())
        else:
            self.btn_metro_toggle.setText("▶ Metro")
            if getattr(self, "is_dark", True):
                self.btn_metro_toggle.setStyleSheet(f"background-color: {t['subtle_pill_bg']}; color: {t['text_accent']}; font-weight: 700; font-size: 8.5pt; padding: 3px 6px; border-radius: 4px; border: 1px solid {t['border_accent']};")
            else:
                self.btn_metro_toggle.setStyleSheet("background-color: #eff6ff; color: #1d4ed8; font-weight: 700; font-size: 8.5pt; padding: 3px 6px; border-radius: 4px; border: 1px solid #bfdbfe;")
            self.metro_led.setStyleSheet("color: #64748b; font-size: 14px; border: none; background: transparent;")
            RhythmEngine.stop_groove()
        self.metronome_state_changed.emit(running)

    def _on_groove_changed(self, groove_name: str):
        if groove_name != "Off (Standard Metronome)":
            def_bpm = RhythmEngine.get_groove_default_bpm(groove_name)
            self.metro_bpm_spin.setValue(def_bpm)
            if self.metronome.is_running:
                RhythmEngine.play_groove(groove_name, def_bpm)
        else:
            RhythmEngine.stop_groove()

    # ── Stem Player Handlers ──
    def _attach_audio_stem(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Attach Suno / Udio Master Audio", "", "Audio Files (*.mp3 *.wav *.m4a *.ogg);;All Files (*.*)"
        )
        if not path:
            return
        self.attached_audio_path = path
        p = Path(path)
        self.lbl_stem_track.setText(p.name[:24] + ("..." if len(p.name) > 24 else ""))
        self.btn_play_stem.setEnabled(True)
        self.stem_slider.setEnabled(True)
        self.btn_remove_stem.setVisible(True)
        self.stem_player.setSource(QUrl.fromLocalFile(path))

    def _toggle_stem_playback(self):
        from PyQt6.QtMultimedia import QMediaPlayer
        if self.stem_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.stem_player.pause()
        else:
            self.stem_player.play()

    def _on_stem_state_changed(self, state):
        from PyQt6.QtMultimedia import QMediaPlayer
        t = getattr(self, "theme", get_theme(getattr(self, "is_dark", True)))
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.btn_play_stem.setText("⏸")
            self.btn_play_stem.setStyleSheet("background-color: #7f1d1d; color: #fecaca; font-weight: 700; font-size: 8.5pt; padding: 2px 4px; border-radius: 4px; border: 1px solid #ef4444;")
        else:
            self.btn_play_stem.setText("▶")
            if getattr(self, "is_dark", True):
                self.btn_play_stem.setStyleSheet(f"background-color: {t['bg_card_alt']}; color: {t['text_primary']}; font-weight: 700; font-size: 8.5pt; padding: 2px 4px; border: 1px solid {t['border']}; border-radius: 4px;")
            else:
                self.btn_play_stem.setStyleSheet("background-color: #f8fafc; color: #0f172a; font-weight: 700; font-size: 8.5pt; padding: 2px 4px; border: 1px solid #cbd5e1; border-radius: 4px;")

    def _on_stem_position_changed(self, pos: int):
        dur = self.stem_player.duration()
        if dur > 0 and not self.stem_slider.isSliderDown():
            val = int((pos / dur) * 1000)
            self.stem_slider.setValue(val)
        self._update_stem_time(pos, dur)

    def _on_stem_duration_changed(self, dur: int):
        pos = self.stem_player.position()
        self._update_stem_time(pos, dur)

    def _update_stem_time(self, pos: int, dur: int):
        cur_m, cur_s = divmod(pos // 1000, 60)
        tot_m, tot_s = divmod(dur // 1000, 60)
        self.lbl_stem_time.setText(f"{cur_m:02d}:{cur_s:02d} / {tot_m:02d}:{tot_s:02d}")

    def _seek_stem(self, val: int):
        dur = self.stem_player.duration()
        if dur > 0:
            target_pos = int((val / 1000.0) * dur)
            self.stem_player.setPosition(target_pos)

    def _remove_audio_stem(self):
        self.stem_player.stop()
        self.stem_player.setSource(QUrl())
        self.attached_audio_path = None
        self.lbl_stem_track.setText("No track attached")
        self.lbl_stem_time.setText("0:00 / 0:00")
        self.btn_play_stem.setEnabled(False)
        self.stem_slider.setEnabled(False)
        self.btn_remove_stem.setVisible(False)

    def _open_hit_inspector(self):
        from app.ui.hit_analyzer_dialog import HitAnalyzerDialog
        dlg = HitAnalyzerDialog(self.editor.toPlainText(), bpm=self.metro_bpm_spin.value(), is_dark=self.editor.is_dark, parent=self)
        dlg.exec()

    def _on_metro_beat(self, beat: int, total: int):
        if beat == 1:
            self.metro_led.setStyleSheet("color: #ef4444; font-size: 16px;")  # Red pulse on downbeat 1
        elif beat > 1:
            self.metro_led.setStyleSheet("color: #06b6d4; font-size: 16px;")  # Cyan on other beats
        else:
            self.metro_led.setStyleSheet("color: #94a3b8; font-size: 16px;")

    def _on_tap_clicked(self):
        bpm = self.metronome.tap()
        self.btn_tap.setText(f"👆 Tap ({bpm})")

    def _on_time_sig_changed(self, idx: int):
        if idx == 0:
            self.metronome.set_time_signature(4)
        elif idx == 1:
            self.metronome.set_time_signature(3)
        elif idx == 2:
            self.metronome.set_time_signature(6)

    # ── Take Version Management ──
    def _on_take_switched(self, new_take: str):
        if not new_take:
            return
        # Save current take
        self.version_manager.save_take(self.current_take_name, self.editor.toPlainText())
        self.current_take_name = new_take
        # Load new take
        take_content = self.version_manager.get_take(new_take)
        self.editor.setPlainText(take_content)

    def _on_add_take(self):
        name, ok = QInputDialog.getText(self, "New Take", "Enter name for new take:", text=f"Take {len(self.version_manager.list_takes()) + 1}")
        if ok and name.strip():
            created_name = self.version_manager.add_take(name.strip(), "")
            self.take_combo.blockSignals(True)
            self.take_combo.clear()
            self.take_combo.addItems(self.version_manager.list_takes())
            self.take_combo.setCurrentText(created_name)
            self.take_combo.blockSignals(False)
            self._on_take_switched(created_name)

    def _on_dup_take(self):
        dup_name = self.version_manager.duplicate_take(self.current_take_name)
        self.take_combo.blockSignals(True)
        self.take_combo.clear()
        self.take_combo.addItems(self.version_manager.list_takes())
        self.take_combo.setCurrentText(dup_name)
        self.take_combo.blockSignals(False)
        self._on_take_switched(dup_name)

    def _on_del_take(self):
        takes = self.version_manager.list_takes()
        if len(takes) <= 1:
            QMessageBox.information(self, "Cannot Delete", "You must keep at least one take.")
            return
        reply = QMessageBox.question(
            self,
            "Delete Take",
            f"Are you sure you want to delete '{self.current_take_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            to_remove = self.current_take_name
            self.version_manager.delete_take(to_remove)
            remaining = self.version_manager.list_takes()
            next_take = remaining[0]
            self.take_combo.blockSignals(True)
            self.take_combo.clear()
            self.take_combo.addItems(remaining)
            self.take_combo.setCurrentText(next_take)
            self.take_combo.blockSignals(False)
            self._on_take_switched(next_take)

    # ── Chord Insertion & Audition ──
    def _insert_chord_at_cursor(self, chord: str):
        cursor = self.editor.textCursor()
        cursor.insertText(f"[{chord}] ")
        AudioChordSynthesizer.play_chord(chord)
        self.editor.setFocus()

    def _prompt_custom_chord(self):
        chord, ok = QInputDialog.getText(self, "Insert Custom Chord", "Enter chord symbol (e.g. F#m7, Dsus4, G/B):")
        if ok and chord.strip():
            clean = chord.strip().replace("[", "").replace("]", "")
            self._insert_chord_at_cursor(clean)

    def _on_transpose(self, semitones: int):
        cur_text = self.editor.toPlainText()
        if cur_text.strip():
            new_text = ChordEngine.transpose_lyric_sheet(cur_text, semitones)
            self.editor.setPlainText(new_text)
        self.transpose_requested.emit(semitones)

    def _audition_lyrics_chords(self):
        """Extract all unique chords present in the lyrics and audition them in progression."""
        text = self.editor.toPlainText()
        chord_matches = re.findall(r'\[([A-G][#b]?(m|maj|min|dim|aug|sus[24]?|[0-9])*(/[A-G][#b]?)?)\]', text)
        chords = [m[0] for m in chord_matches]
        if not chords:
            # Fallback to standard pop progression
            chords = ["Am", "F", "C", "G"]
        bpm_val = self.metro_bpm_spin.value()
        AudioChordSynthesizer.play_progression(chords[:8], bpm=bpm_val)

    def _copy_clean_lyrics(self):
        """Strip all [bracket] metatags and chords for singers, and copy to clipboard."""
        text = self.editor.toPlainText()
        lines = []
        for line in text.splitlines():
            cleaned = re.sub(r'\[[^\]]*\]', '', line).strip()
            if cleaned:
                lines.append(cleaned)
            elif not line.strip():
                lines.append("")
        clean_text = "\n".join(lines).strip()
        if clean_text:
            QApplication.clipboard().setText(clean_text)
            self.btn_clean_tags.setText("✅ Clean Copied!")
            QTimer.singleShot(2000, lambda: self.btn_clean_tags.setText("🧹 Clean Tags") if hasattr(self, "btn_clean_tags") else None)

    def _copy_full_lyrics(self):
        text = self.editor.toPlainText()
        if text.strip():
            QApplication.clipboard().setText(text)
            self.btn_copy_lyrics.setText("✅ Copied!")
            QTimer.singleShot(2000, lambda: self.btn_copy_lyrics.setText("📋 Copy All") if hasattr(self, "btn_copy_lyrics") else None)

    def insert_section_tag(self, tag: str):
        cursor = self.editor.textCursor()
        cursor.insertText(f"\n{tag}\n")
        self.editor.setFocus()

    def get_title(self) -> str:
        return self.title_input.text().strip() or "Untitled Song"

    def set_title(self, title: str):
        self.title_input.setText(title)
        self.title_input.setCursorPosition(0)

    def get_lyrics(self) -> str:
        return self.editor.toPlainText()

    def set_lyrics(self, lyrics: str):
        self.editor.setPlainText(lyrics)
        self.version_manager.save_take(self.current_take_name, lyrics)

    def get_takes_state(self) -> tuple:
        """Return (takes_dict, current_take_name) with current editor text synced."""
        self.version_manager.save_take(self.current_take_name, self.editor.toPlainText())
        return dict(self.version_manager.takes), self.current_take_name

    def set_takes_state(self, takes: dict, current_take: str = ""):
        """Restore multi-take lyric versions and select the active take."""
        if not takes or not isinstance(takes, dict):
            return
        clean_takes = {str(k): str(v or "") for k, v in takes.items() if str(k).strip()}
        if not clean_takes:
            return
        self.version_manager.takes = clean_takes
        target = current_take if current_take in clean_takes else next(iter(clean_takes.keys()))
        self.current_take_name = target
        self.version_manager.current_take = target
        self.take_combo.blockSignals(True)
        self.take_combo.clear()
        self.take_combo.addItems(self.version_manager.list_takes())
        self.take_combo.setCurrentText(target)
        self.take_combo.blockSignals(False)
        self.editor.setPlainText(clean_takes.get(target, ""))

    def insert_text_at_cursor(self, text: str):
        cursor = self.editor.textCursor()
        cursor.insertText(text)

    def replace_selection(self, new_text: str):
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            cursor.insertText(new_text)

    def _on_selection_changed(self):
        cursor = self.editor.textCursor()
        has_sel = cursor.hasSelection()
        self.btn_rewrite_menu.setEnabled(has_sel)
        self.btn_rhyme_sel.setEnabled(has_sel)
        if has_sel:
            sel_text = cursor.selectedText()
            line_count = len(sel_text.split("\u2029"))
            word_count = len(sel_text.split())
            self.sel_label.setText(f"✨ Selected {len(sel_text)} chars ({word_count} words, {line_count} lines) — Ready to refine")
        else:
            self.sel_label.setText("✨ AI Selection Tools: Select lines to rewrite or refine with Gemini")

    def _lookup_rhyme_for_selection(self):
        cursor = self.editor.textCursor()
        if not cursor.hasSelection():
            return
        sel_text = cursor.selectedText().replace("\u2029", " ").strip()
        words = re.findall(r'[a-zA-Z\u1780-\u17FF]+', sel_text)
        if words:
            last_word = words[-1]
            self.rhyme_search_requested.emit(last_word)

    def _humanize_entire_lyrics(self):
        from app.humanizer_engine import HumanizerEngine
        curr = self.editor.toPlainText()
        if not curr.strip():
            return
        h_lyrics = HumanizerEngine.humanize_lyrics_locally(curr, "English")
        self.editor.setPlainText(h_lyrics)
        self.btn_humanize_full.setText("✅ Humanized!")
        QTimer.singleShot(2000, lambda: self.btn_humanize_full.setText("👤 Humanize Lyrics") if hasattr(self, "btn_humanize_full") else None)

    def _trigger_humanize_selection(self):
        cursor = self.editor.textCursor()
        selected_text = cursor.selectedText()
        if not selected_text.strip():
            return
        from app.humanizer_engine import HumanizerEngine
        h_text = HumanizerEngine.humanize_lyrics_locally(selected_text.replace('\u2029', '\n'), "English")
        cursor.insertText(h_text)

    def _trigger_rewrite(self, instruction: str):
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            text = cursor.selectedText().replace("\u2029", "\n")
            self.rewrite_requested.emit(text, instruction)

    def _on_analysis_updated(self, analysis: dict):
        text = self.editor.toPlainText()
        words = len(text.split()) if text.strip() else 0

        self.stat_lines.setText(f"Lines: {analysis['total_lines']}")
        self.stat_words.setText(f"Words: {words}")
        self.stat_syllables.setText(f"Syllables: {analysis['total_syllables']}")
        self.stat_avg.setText(f"Avg/Line: {analysis['avg_syllables']}")
        self.flow_label.setText(f"Flow: {analysis['flow_score']}%")

        # Live runtime duration calculation
        bpm = self.metro_bpm_spin.value()
        seconds_per_beat = 60.0 / max(40, bpm)
        total_syl = analysis['total_syllables']
        est_bars = max(2, total_syl / 8.0) if total_syl > 0 else 0
        est_seconds = int(est_bars * (4 * seconds_per_beat))
        mins = est_seconds // 60
        secs = est_seconds % 60
        self.stat_duration.setText(f"⏱️ ~{mins}m {secs:02d}s")

        # Dynamic Hit Potential Score Update
        if hasattr(self, "btn_hit_score"):
            hit_data = HitAnalyzer.analyze(text, bpm)
            self.btn_hit_score.setText(f"🌟 Hit: {hit_data['hit_score']}%")

        # Update Live Song Chord Ribbon
        self._update_song_chord_ribbon(text)

    def _update_song_chord_ribbon(self, lyrics_text: str):
        if not hasattr(self, "chord_ribbon_layout"):
            return
        from app.chord_soundboard import ChordSoundboardSynthesizer
        chords = ChordSoundboardSynthesizer.extract_chords_from_lyrics(lyrics_text)

        while self.chord_ribbon_layout.count():
            item = self.chord_ribbon_layout.takeAt(0)
            w = item.widget()
            if w:
                w.hide()
                w.setParent(None)
                w.deleteLater()

        if not chords:
            self.chord_ribbon_frame.setVisible(False)
            return

        self.chord_ribbon_frame.setVisible(True)
        lbl_rib = QLabel("Chords in Song:")
        lbl_rib.setStyleSheet("font-size: 8pt; font-weight: 700; color: #64748b;")
        self.chord_ribbon_layout.addWidget(lbl_rib)

        for chord in chords:
            btn = QPushButton(f"🎵 {chord}")
            btn.setToolTip(f"Click to audition [{chord}] chord")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("background-color: #3b82f6; color: white; font-size: 7.5pt; font-weight: 700; border-radius: 3px; padding: 1px 6px; border: none;")
            btn.clicked.connect(lambda _, c=chord: ChordSoundboardSynthesizer.play_chord_async(c))
            self.chord_ribbon_layout.addWidget(btn)

        self.chord_ribbon_layout.addStretch()

    def _open_melody_guide(self):
        from app.ui.melody_guide_dialog import MelodyGuideDialog
        lyrics = self.editor.toPlainText()
        title = self.title_input.text().strip() or "Untitled Song"
        bpm = self.metro_bpm_spin.value()
        dlg = MelodyGuideDialog(self, is_dark=self.is_dark, lyrics=lyrics, title=title, bpm=bpm)
        dlg.exec()

    def _open_scratch_vocalist(self):
        from app.ui.scratch_vocalist_dialog import ScratchVocalistDialog
        lyrics = self.editor.toPlainText()
        title = self.title_input.text().strip() or "Untitled Song"
        dlg = ScratchVocalistDialog(self, is_dark=self.is_dark, lyrics=lyrics, title=title)
        dlg.exec()

    def _open_chord_soundboard(self):
        from app.ui.chord_soundboard_view import ChordSoundboardDialog
        lyrics = self.editor.toPlainText()
        dlg = ChordSoundboardDialog(self, is_dark=self.is_dark, initial_lyrics=lyrics)
        dlg.chord_inserted.connect(self._insert_chord_at_cursor)
        dlg.exec()

    def _open_khmer_poetry_meter(self):
        from app.ui.khmer_poetry_dialog import KhmerPoetryMeterDialog
        lyrics = self.editor.toPlainText()
        dlg = KhmerPoetryMeterDialog(self, is_dark=self.is_dark, initial_lyrics=lyrics)
        dlg.text_updated.connect(lambda t: self.editor.insertPlainText(t))
        dlg.exec()

    def _open_cover_art_generator(self):
        from app.ui.cover_art_dialog import CoverArtDialog
        lyrics = self.editor.toPlainText()
        title = self.title_input.text().strip() or "Untitled Song"
        dlg = CoverArtDialog(self, is_dark=self.is_dark, title=title, lyrics=lyrics)
        dlg.exec()

    def _load_blueprint(self, name: str):
        bp = SONG_BLUEPRINTS.get(name)
        if not bp:
            return
        current_text = self.editor.toPlainText().strip()
        if current_text:
            reply = QMessageBox.question(
                self,
                "Load Hit Blueprint",
                f"Load the '{name}' hit structure template?\n\n(Tip: Your previous text remains safely preserved in your takes)",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        self.set_lyrics(bp.get("template_lyrics", ""))
        self.title_input.setText(name.split("(")[0].strip())
        bpm_str = bp.get("bpm", "120 BPM")
        try:
            bpm_val = int("".join(filter(str.isdigit, bpm_str[:4])))
            self.metro_bpm_spin.setValue(bpm_val)
        except Exception:
            pass

    def _switch_tool_deck(self, index: int):
        if hasattr(self, "tool_deck_stack"):
            self.tool_deck_stack.setCurrentIndex(index)
        for idx, btn in enumerate([
            getattr(self, "btn_sub_tags", None),
            getattr(self, "btn_sub_audio", None),
            getattr(self, "btn_sub_pro", None),
        ]):
            if btn:
                btn.setChecked(idx == index)

    def apply_theme(self, theme_or_dark):
        t = get_theme(theme_or_dark)
        self.theme = t
        self.theme_key = t.get("id", "obsidian")
        is_dark = t.get("is_dark", True)
        self.is_dark = is_dark
        self.editor.set_theme(theme_or_dark)

        if is_dark:
            self.title_input.setStyleSheet(f"font-size: 13.5px; font-weight: 700; color: {t['text_primary']}; padding: 4px 8px; background: {t['bg_input']}; border: 1px solid {t['border']}; border-radius: 6px;")
            self.take_combo.setStyleSheet(f"background-color: {t['bg_input']}; color: {t['text_primary']}; border: 1px solid {t['border']}; font-weight: 600; padding: 2px 6px; border-radius: 4px; min-width: 95px;")
            if hasattr(self, "lbl_take"):
                self.lbl_take.setStyleSheet(f"font-weight: 700; color: {t['text_muted']}; font-size: 11px;")

            if hasattr(self, "btn_add_take") and self.btn_add_take:
                self.btn_add_take.setStyleSheet(f"background-color: {t['subtle_pill_bg']}; color: {t['text_accent']}; border: 1px solid {t['border_accent']}; border-radius: 4px; padding: 3px 7px; font-size: 8.5pt; font-weight: 700;")
            if hasattr(self, "btn_dup_take") and self.btn_dup_take:
                self.btn_dup_take.setStyleSheet("background-color: #064e3b; color: #34d399; border: 1px solid #059669; border-radius: 4px; padding: 3px 7px; font-size: 8.5pt; font-weight: 700;")
            if hasattr(self, "btn_del_take") and self.btn_del_take:
                self.btn_del_take.setStyleSheet("background-color: #450a0a; color: #f87171; border: 1px solid #991b1b; border-radius: 4px; padding: 3px 7px; font-size: 8.5pt; font-weight: 700;")

            if hasattr(self, "tool_deck_frame"):
                self.tool_deck_frame.setStyleSheet(f"QFrame#toolDeckFrame {{ background-color: {t['bg_card']}; border: 1px solid {t['border']}; border-radius: 8px; }} QFrame#toolDeckFrame QLabel {{ border: none; background: transparent; }}")
            sub_tab_qss = f"""
                QPushButton {{
                    background-color: {t['bg_card_alt']};
                    color: {t['text_secondary']};
                    border: 1px solid {t['border']};
                    border-radius: 5px;
                    font-size: 8.5pt;
                    font-weight: 700;
                    padding: 2px 10px;
                }}
                QPushButton:hover {{
                    color: {t['text_primary']};
                    border-color: {t['accent']};
                }}
                QPushButton:checked {{
                    background-color: {t['accent']};
                    color: #ffffff;
                    border-color: {t['border_accent']};
                }}
            """
            for sb in [getattr(self, "btn_sub_tags", None), getattr(self, "btn_sub_audio", None), getattr(self, "btn_sub_pro", None)]:
                if sb:
                    sb.setStyleSheet(sub_tab_qss)

            self.metro_frame.setStyleSheet("QFrame#metroFrame { background: transparent; border: none; } QFrame#metroFrame QLabel { border: none; background: transparent; }")
            self.btn_metro_toggle.setStyleSheet(f"background-color: {t['subtle_pill_bg']}; color: {t['text_accent']}; font-weight: 700; font-size: 8.5pt; padding: 3px 6px; border-radius: 4px; border: 1px solid {t['border_accent']};")
            if hasattr(self, "lbl_bpm_tag"):
                self.lbl_bpm_tag.setStyleSheet(f"font-weight: 700; color: {t['text_secondary']}; font-size: 8.5pt; background: transparent; border: none;")
            self.metro_bpm_spin.setStyleSheet(f"background-color: {t['bg_input']}; color: {t['text_primary']}; border: 1px solid {t['border']}; font-weight: 700; padding: 1px 4px; border-radius: 4px;")
            self.metro_sig_combo.setStyleSheet(f"background-color: {t['bg_input']}; color: {t['text_secondary']}; border: 1px solid {t['border']}; font-weight: 600; padding: 1px 4px; border-radius: 4px;")
            self.btn_tap.setStyleSheet(f"background-color: {t['subtle_pill_bg']}; color: {t['text_accent']}; border: 1px solid {t['border_accent']}; font-size: 8.5pt; padding: 2px 5px; border-radius: 4px; font-weight: 700;")
            if hasattr(self, "btn_audition_chords"):
                self.btn_audition_chords.setStyleSheet(f"background-color: {t['bg_card_alt']}; color: {t['text_accent']}; border: 1px solid {t['border_accent']}; font-size: 8.5pt; padding: 2px 8px; border-radius: 4px; font-weight: 700;")
            if hasattr(self, "btn_clean_tags"):
                self.btn_clean_tags.setStyleSheet(f"background-color: {t['bg_card_alt']}; color: {t['text_secondary']}; border: 1px solid {t['border']}; font-size: 8.5pt; padding: 3px 7px; border-radius: 4px; font-weight: 600;")
            if hasattr(self, "btn_copy_lyrics"):
                self.btn_copy_lyrics.setStyleSheet("background-color: #064e3b; color: #34d399; border: 1px solid #059669; font-size: 8.5pt; padding: 3px 7px; border-radius: 4px; font-weight: 700;")

            if hasattr(self, "btn_khmer_tags"):
                self.btn_khmer_tags.setStyleSheet("background-color: #500724; color: #f472b6; font-weight: 700; font-size: 8.5pt; padding: 3px 5px; border-radius: 4px; border: 1px solid #be185d;")
            self.btn_blueprints.setStyleSheet("background-color: #064e3b; color: #34d399; font-weight: 700; font-size: 8.5pt; padding: 3px 5px; border-radius: 4px; border: 1px solid #059669;")
            self.btn_dynamics.setStyleSheet(f"background-color: {t['subtle_pill_bg']}; color: {t['text_accent']}; font-weight: 700; font-size: 8.5pt; padding: 3px 5px; border-radius: 4px; border: 1px solid {t['border_accent']};")
            if hasattr(self, "btn_cues"):
                self.btn_cues.setStyleSheet(f"background-color: {t['bg_card_alt']}; color: {t['text_secondary']}; font-weight: 700; font-size: 8.5pt; padding: 3px 5px; border-radius: 4px; border: 1px solid {t['border']};")
            if hasattr(self, "btn_chords_menu"):
                self.btn_chords_menu.setStyleSheet("background-color: #4a044e; color: #f0abfc; font-weight: 700; font-size: 8.5pt; padding: 3px 5px; border-radius: 4px; border: 1px solid #c026d3;")
            for b in [getattr(self, "btn_trans_down", None), getattr(self, "btn_trans_up", None)]:
                if b:
                    b.setStyleSheet(f"background-color: {t['bg_card_alt']}; color: {t['text_secondary']}; border: 1px solid {t['border']}; border-radius: 4px; font-size: 8.5pt; font-weight: 700; padding: 3px 6px;")
            if hasattr(self, "btn_arranger_jump"):
                self.btn_arranger_jump.setStyleSheet(f"background-color: {t['subtle_pill_bg']}; color: {t['text_accent']}; border: 1px solid {t['border_accent']}; border-radius: 4px; padding: 2px 8px; font-size: 8.5pt; font-weight: 700;")

            if hasattr(self, "pro_features_frame"):
                self.pro_features_frame.setStyleSheet("QFrame#proFeaturesFrame { background: transparent; border: none; }")
            pro_btn_styles = [
                (getattr(self, "btn_pro_melody", None), f"background-color: #2e1065; color: #d8b4fe; border: 1px solid #7c3aed;"),
                (getattr(self, "btn_pro_vocal", None), f"background-color: #172554; color: #93c5fd; border: 1px solid #2563eb;"),
                (getattr(self, "btn_pro_chords", None), f"background-color: #4a044e; color: #f0abfc; border: 1px solid #c026d3;"),
                (getattr(self, "btn_pro_khmer", None), f"background-color: #064e3b; color: #6ee7b7; border: 1px solid #059669;"),
                (getattr(self, "btn_pro_cover", None), f"background-color: #431407; color: #fdba74; border: 1px solid #ea580c;"),
            ]
            for pb, style_str in pro_btn_styles:
                if pb:
                    pb.setStyleSheet(f"{style_str} font-weight: 700; font-size: 8.5pt; padding: 3px 8px; border-radius: 4px;")

            self.selection_bar.setStyleSheet(f"QFrame#selectionBarFrame {{ background-color: {t['bg_card']}; border: 1px solid {t['border']}; border-radius: 8px; }} QFrame#selectionBarFrame QLabel {{ border: none; background: transparent; }}")
            self.sel_label.setStyleSheet(f"color: {t['text_accent']}; font-size: 11px; font-weight: 600; background: transparent; border: none;")
            if hasattr(self, "btn_rhyme_sel"):
                self.btn_rhyme_sel.setStyleSheet(f"background-color: {t['subtle_pill_bg']}; color: {t['text_accent']}; border: 1px solid {t['border_accent']}; border-radius: 5px; padding: 4px 8px; font-weight: 700; font-size: 9pt;")
            if hasattr(self, "btn_humanize_full"):
                self.btn_humanize_full.setStyleSheet("background-color: #064e3b; color: #34d399; font-weight: 700; font-size: 9pt; padding: 4px 10px; border-radius: 5px; border: 1px solid #059669;")
            if hasattr(self, "btn_clone_meaning"):
                self.btn_clone_meaning.setStyleSheet(f"background-color: {t['subtle_pill_bg']}; color: {t['text_accent']}; font-weight: 700; font-size: 9pt; padding: 4px 10px; border-radius: 5px; border: 1px solid {t['border_accent']};")

            self.stats_frame.setStyleSheet(f"QFrame#editorStatsFrame {{ background-color: {t['bg_card']}; border: 1px solid {t['border']}; border-radius: 6px; }} QFrame#editorStatsFrame QLabel {{ border: none; background: transparent; }}")
            for stat in [self.stat_lines, self.stat_words, self.stat_syllables, self.stat_avg]:
                stat.setStyleSheet(f"color: {t['text_secondary']}; font-size: 11px; font-weight: 600; background: transparent; border: none;")
            self.flow_label.setStyleSheet(f"color: {t['text_accent']}; font-weight: 700; font-size: 11px; background: transparent; border: none;")
            self.stat_duration.setStyleSheet("color: #34d399; font-weight: 800; font-size: 11px; background: #064e3b; padding: 1px 6px; border-radius: 3px; border: none;")
            if hasattr(self, "combo_groove"):
                self.combo_groove.setStyleSheet(f"background-color: {t['bg_input']}; color: {t['text_primary']}; border: 1px solid {t['border']}; font-weight: 600; padding: 2px 4px; border-radius: 4px;")
            if hasattr(self, "btn_load_stem"):
                self.btn_load_stem.setStyleSheet(f"background-color: {t['subtle_pill_bg']}; color: {t['text_accent']}; font-weight: 700; font-size: 8.5pt; padding: 2px 6px; border: 1px solid {t['border_accent']}; border-radius: 4px;")
            if hasattr(self, "btn_play_stem"):
                self.btn_play_stem.setStyleSheet(f"background-color: {t['bg_card_alt']}; color: {t['text_primary']}; font-weight: 700; font-size: 8.5pt; padding: 2px 4px; border: 1px solid {t['border']}; border-radius: 4px;")
            if hasattr(self, "lbl_stem_time"):
                self.lbl_stem_time.setStyleSheet(f"font-size: 9.5px; font-weight: 700; color: {t['text_primary']}; border: none; background: transparent;")
            if hasattr(self, "btn_hit_score"):
                self.btn_hit_score.setStyleSheet(f"background: {t['subtle_pill_bg']}; color: {t['text_accent']}; font-weight: 800; font-size: 11px; padding: 1px 7px; border: 1px solid {t['border_accent']}; border-radius: 4px;")
            if hasattr(self, "chord_ribbon_frame"):
                self.chord_ribbon_frame.setStyleSheet(f"QFrame#chordRibbonFrame {{ background-color: {t['bg_card']}; border: 1px solid {t['border']}; border-radius: 4px; padding: 2px; }} QFrame#chordRibbonFrame QLabel {{ border: none; background: transparent; }}")

            all_menus = [
                getattr(self, "btn_khmer_tags", None) and self.btn_khmer_tags.menu(),
                self.btn_blueprints.menu(),
                self.btn_dynamics.menu(),
                getattr(self, "btn_cues", None) and self.btn_cues.menu(),
                getattr(self, "btn_chords_menu", None) and self.btn_chords_menu.menu(),
                self.btn_rewrite_menu.menu()
            ]
            for m in all_menus:
                if m:
                    m.setStyleSheet(f"background-color: {t['bg_card']}; color: {t['text_primary']}; border: 1px solid {t['border']}; padding: 4px;")
        else:
            # Modern Studio High-Contrast Light Palette
            self.title_input.setStyleSheet("font-size: 13.5px; font-weight: 700; color: #0f172a; padding: 4px 8px; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 6px;")
            self.take_combo.setStyleSheet("background-color: #ffffff; color: #0f172a; border: 1px solid #cbd5e1; font-weight: 600; padding: 2px 6px; border-radius: 4px; min-width: 95px;")
            if hasattr(self, "lbl_take"):
                self.lbl_take.setStyleSheet("font-weight: 700; color: #334155; font-size: 11px;")

            if hasattr(self, "btn_add_take") and self.btn_add_take:
                self.btn_add_take.setStyleSheet("background-color: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; border-radius: 4px; padding: 3px 7px; font-size: 8.5pt; font-weight: 700;")
            if hasattr(self, "btn_dup_take") and self.btn_dup_take:
                self.btn_dup_take.setStyleSheet("background-color: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0; border-radius: 4px; padding: 3px 7px; font-size: 8.5pt; font-weight: 700;")
            if hasattr(self, "btn_del_take") and self.btn_del_take:
                self.btn_del_take.setStyleSheet("background-color: #fef2f2; color: #dc2626; border: 1px solid #fecaca; border-radius: 4px; padding: 3px 7px; font-size: 8.5pt; font-weight: 700;")

            if hasattr(self, "tool_deck_frame"):
                self.tool_deck_frame.setStyleSheet("QFrame#toolDeckFrame { background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; } QFrame#toolDeckFrame QLabel { border: none; background: transparent; }")
            sub_tab_qss_light = f"""
                QPushButton {{
                    background-color: #f1f5f9;
                    color: #334155;
                    border: 1px solid #cbd5e1;
                    border-radius: 5px;
                    font-size: 8.5pt;
                    font-weight: 700;
                    padding: 2px 10px;
                }}
                QPushButton:hover {{
                    background-color: #e2e8f0;
                    color: #0f172a;
                }}
                QPushButton:checked {{
                    background-color: {t['accent']};
                    color: #ffffff;
                    border-color: {t['border_accent']};
                }}
            """
            for sb in [getattr(self, "btn_sub_tags", None), getattr(self, "btn_sub_audio", None), getattr(self, "btn_sub_pro", None)]:
                if sb:
                    sb.setStyleSheet(sub_tab_qss_light)

            self.metro_frame.setStyleSheet("QFrame#metroFrame { background: transparent; border: none; } QFrame#metroFrame QLabel { border: none; background: transparent; }")
            self.btn_metro_toggle.setStyleSheet("background-color: #eff6ff; color: #1d4ed8; font-weight: 700; font-size: 8.5pt; padding: 3px 6px; border-radius: 4px; border: 1px solid #bfdbfe;")
            if hasattr(self, "lbl_bpm_tag"):
                self.lbl_bpm_tag.setStyleSheet("font-weight: 700; color: #334155; font-size: 8.5pt; background: transparent; border: none;")
            self.metro_bpm_spin.setStyleSheet("background-color: #ffffff; color: #0f172a; border: 1px solid #cbd5e1; font-weight: 700; padding: 1px 4px; border-radius: 4px;")
            self.metro_sig_combo.setStyleSheet("background-color: #ffffff; color: #0f172a; border: 1px solid #cbd5e1; font-weight: 600; padding: 1px 4px; border-radius: 4px;")
            self.btn_tap.setStyleSheet("background-color: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; font-size: 8.5pt; padding: 2px 5px; border-radius: 4px; font-weight: 700;")
            if hasattr(self, "btn_audition_chords"):
                self.btn_audition_chords.setStyleSheet("background-color: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; font-size: 8.5pt; padding: 2px 8px; border-radius: 4px; font-weight: 700;")
            if hasattr(self, "btn_clean_tags"):
                self.btn_clean_tags.setStyleSheet("background-color: #ffffff; color: #334155; border: 1px solid #cbd5e1; font-size: 8.5pt; padding: 3px 7px; border-radius: 4px; font-weight: 600;")
            if hasattr(self, "btn_copy_lyrics"):
                self.btn_copy_lyrics.setStyleSheet("background-color: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0; font-size: 8.5pt; padding: 3px 7px; border-radius: 4px; font-weight: 700;")

            if hasattr(self, "btn_khmer_tags"):
                self.btn_khmer_tags.setStyleSheet("background-color: #fdf2f8; color: #be185d; font-weight: 700; font-size: 8.5pt; padding: 3px 5px; border-radius: 4px; border: 1px solid #fbcfe8;")
            self.btn_blueprints.setStyleSheet("background-color: #f0fdf4; color: #166534; font-weight: 700; font-size: 8.5pt; padding: 3px 5px; border-radius: 4px; border: 1px solid #bbf7d0;")
            self.btn_dynamics.setStyleSheet("background-color: #eff6ff; color: #1d4ed8; font-weight: 700; font-size: 8.5pt; padding: 3px 5px; border-radius: 4px; border: 1px solid #bfdbfe;")
            if hasattr(self, "btn_cues"):
                self.btn_cues.setStyleSheet("background-color: #f8fafc; color: #1e293b; font-weight: 700; font-size: 8.5pt; padding: 3px 5px; border-radius: 4px; border: 1px solid #cbd5e1;")
            if hasattr(self, "btn_chords_menu"):
                self.btn_chords_menu.setStyleSheet("background-color: #fdf4ff; color: #86198f; font-weight: 700; font-size: 8.5pt; padding: 3px 5px; border-radius: 4px; border: 1px solid #f0abfc;")
            for b in [getattr(self, "btn_trans_down", None), getattr(self, "btn_trans_up", None)]:
                if b:
                    b.setStyleSheet("background-color: #ffffff; color: #0f172a; border: 1px solid #cbd5e1; border-radius: 4px; font-size: 8.5pt; font-weight: 700; padding: 3px 6px;")
            if hasattr(self, "btn_arranger_jump"):
                self.btn_arranger_jump.setStyleSheet("background-color: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; border-radius: 4px; padding: 2px 8px; font-size: 8.5pt; font-weight: 700;")

            if hasattr(self, "pro_features_frame"):
                self.pro_features_frame.setStyleSheet("QFrame#proFeaturesFrame { background: transparent; border: none; }")
            pro_btn_styles_light = [
                (getattr(self, "btn_pro_melody", None), "background-color: #ede9fe; color: #6d28d9; border: 1px solid #ddd6fe;"),
                (getattr(self, "btn_pro_vocal", None), "background-color: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe;"),
                (getattr(self, "btn_pro_chords", None), "background-color: #fdf4ff; color: #86198f; border: 1px solid #f0abfc;"),
                (getattr(self, "btn_pro_khmer", None), "background-color: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0;"),
                (getattr(self, "btn_pro_cover", None), "background-color: #fff7ed; color: #c2410c; border: 1px solid #fed7aa;"),
            ]
            for pb, style_str in pro_btn_styles_light:
                if pb:
                    pb.setStyleSheet(f"{style_str} font-weight: 700; font-size: 8.5pt; padding: 3px 8px; border-radius: 4px;")

            self.selection_bar.setStyleSheet("QFrame#selectionBarFrame { background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; } QFrame#selectionBarFrame QLabel { border: none; background: transparent; }")
            self.sel_label.setStyleSheet("color: #1e293b; font-size: 11px; font-weight: 700; background: transparent; border: none;")
            if hasattr(self, "btn_rhyme_sel"):
                self.btn_rhyme_sel.setStyleSheet("background-color: #eff6ff; color: #1d4ed8; font-weight: 700; font-size: 9pt; padding: 4px 8px; border-radius: 5px; border: 1px solid #bfdbfe;")
            if hasattr(self, "btn_humanize_full"):
                self.btn_humanize_full.setStyleSheet("background-color: #ecfdf5; color: #047857; font-weight: 700; font-size: 9pt; padding: 4px 10px; border-radius: 5px; border: 1px solid #a7f3d0;")
            if hasattr(self, "btn_clone_meaning"):
                self.btn_clone_meaning.setStyleSheet("background-color: #f3e8ff; color: #7e22ce; font-weight: 700; font-size: 9pt; padding: 4px 10px; border-radius: 5px; border: 1px solid #d8b4fe;")

            self.stats_frame.setStyleSheet("QFrame#editorStatsFrame { background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 6px; } QFrame#editorStatsFrame QLabel { border: none; background: transparent; }")
            for stat in [self.stat_lines, self.stat_words, self.stat_syllables, self.stat_avg]:
                stat.setStyleSheet("color: #1e293b; font-size: 11px; font-weight: 700; background: transparent; border: none;")
            self.flow_label.setStyleSheet("color: #2563eb; font-weight: 700; font-size: 11px; background: transparent; border: none;")
            self.stat_duration.setStyleSheet("color: #047857; font-weight: 800; font-size: 11px; background: #d1fae5; border: none; padding: 1px 6px; border-radius: 3px;")
            if hasattr(self, "combo_groove"):
                self.combo_groove.setStyleSheet("background-color: #ffffff; color: #0f172a; border: 1px solid #cbd5e1; font-weight: 600; padding: 2px 4px; border-radius: 4px;")
            if hasattr(self, "btn_load_stem"):
                self.btn_load_stem.setStyleSheet("background-color: #eff6ff; color: #1d4ed8; font-weight: 700; font-size: 8.5pt; padding: 2px 6px; border: 1px solid #bfdbfe; border-radius: 4px;")
            if hasattr(self, "btn_play_stem"):
                self.btn_play_stem.setStyleSheet("background-color: #f8fafc; color: #0f172a; font-weight: 700; font-size: 8.5pt; padding: 2px 4px; border: 1px solid #cbd5e1; border-radius: 4px;")
            if hasattr(self, "lbl_stem_time"):
                self.lbl_stem_time.setStyleSheet("font-size: 9.5px; font-weight: 700; color: #0f172a; border: none; background: transparent;")
            if hasattr(self, "btn_hit_score"):
                self.btn_hit_score.setStyleSheet("background: #eff6ff; color: #1d4ed8; font-weight: 800; font-size: 11px; padding: 1px 7px; border: 1px solid #bfdbfe; border-radius: 4px;")
            if hasattr(self, "chord_ribbon_frame"):
                self.chord_ribbon_frame.setStyleSheet("QFrame#chordRibbonFrame { background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 4px; padding: 2px; } QFrame#chordRibbonFrame QLabel { border: none; background: transparent; }")

            all_menus = [
                getattr(self, "btn_khmer_tags", None) and self.btn_khmer_tags.menu(),
                self.btn_blueprints.menu(),
                self.btn_dynamics.menu(),
                getattr(self, "btn_cues", None) and self.btn_cues.menu(),
                getattr(self, "btn_chords_menu", None) and self.btn_chords_menu.menu(),
                self.btn_rewrite_menu.menu()
            ]
            for m in all_menus:
                if m:
                    m.setStyleSheet("background-color: #ffffff; color: #0f172a; border: 1px solid #cbd5e1; padding: 4px;")
