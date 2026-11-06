"""
Interactive Chord Progression Soundboard & Live Harmonizer Dialog.
Features high-fidelity multi-instrument auditioning (Piano, Rhodes, Guitar, Synth),
Diatonic Pad Matrix, Progression Looper, and Song Chord Ribbon.
"""

from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QSlider, QFrame, QScrollArea,
    QGridLayout, QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor
from typing import List, Optional
from app.chord_soundboard import ChordSoundboardSynthesizer, SEMITONES_SHARP
from app.chord_engine import CHORD_PROGRESSIONS


class ChordSoundboardDialog(QDialog):
    chord_inserted = pyqtSignal(str) # Chord token like '[Am]'

    def __init__(self, parent=None, is_dark: bool = True, initial_lyrics: str = ""):
        super().__init__(parent)
        self.is_dark = is_dark
        self.initial_lyrics = initial_lyrics
        self.setWindowTitle("🎹 Interactive Chord Progression Player & Soundboard")
        self.resize(840, 680)
        self.setMinimumSize(780, 600)

        # Progression looper state
        self.loop_timer = QTimer(self)
        self.loop_timer.timeout.connect(self._on_loop_tick)
        self.loop_chords: List[str] = []
        self.loop_index = 0
        self.is_looping = False

        self._init_ui()
        self.apply_theme(self.is_dark)
        self._refresh_diatonic_pads()
        self._refresh_song_chords()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(14)

        # Header Title and Description
        header_row = QHBoxLayout()
        title_box = QVBoxLayout()
        self.lbl_title = QLabel("🎹 Interactive Chord Soundboard & Progression Player")
        self.lbl_title.setStyleSheet("font-size: 18px; font-weight: 800;")
        self.lbl_subtitle = QLabel("Audition chords in real-time with studio instruments, build progressions, and insert into your lyrics.")
        self.lbl_subtitle.setStyleSheet("font-size: 12px; color: #64748b;")
        title_box.addWidget(self.lbl_title)
        title_box.addWidget(self.lbl_subtitle)
        header_row.addLayout(title_box)
        header_row.addStretch()
        main_layout.addLayout(header_row)

        # Controls Bar: Key, Scale, Instrument, Strum Style, Tempo
        controls_group = QGroupBox("🎛️ Soundboard Configuration")
        c_layout = QHBoxLayout(controls_group)
        c_layout.setContentsMargins(12, 12, 12, 12)
        c_layout.setSpacing(14)

        # 1. Key
        key_box = QVBoxLayout()
        lbl_key = QLabel("Root Key:")
        lbl_key.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748b;")
        self.combo_key = QComboBox()
        self.combo_key.addItems(SEMITONES_SHARP)
        self.combo_key.setCurrentText("C")
        self.combo_key.currentTextChanged.connect(self._refresh_diatonic_pads)
        key_box.addWidget(lbl_key)
        key_box.addWidget(self.combo_key)
        c_layout.addLayout(key_box)

        # 2. Scale
        scale_box = QVBoxLayout()
        lbl_scale = QLabel("Scale / Mode:")
        lbl_scale.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748b;")
        self.combo_scale = QComboBox()
        self.combo_scale.addItems(["Major", "Natural Minor"])
        self.combo_scale.currentTextChanged.connect(self._refresh_diatonic_pads)
        scale_box.addWidget(lbl_scale)
        scale_box.addWidget(self.combo_scale)
        c_layout.addLayout(scale_box)

        # 3. Instrument
        inst_box = QVBoxLayout()
        lbl_inst = QLabel("Instrument:")
        lbl_inst.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748b;")
        self.combo_inst = QComboBox()
        self.combo_inst.addItem("🎹 Acoustic Grand Piano", "acoustic_piano")
        self.combo_inst.addItem("⚡ Electric Rhodes", "electric_rhodes")
        self.combo_inst.addItem("🎸 Acoustic Guitar Strum", "acoustic_guitar")
        self.combo_inst.addItem("🌌 Lush Synth Pad", "synth_pad")
        inst_box.addWidget(lbl_inst)
        inst_box.addWidget(self.combo_inst)
        c_layout.addLayout(inst_box)

        # 4. Strum Style
        style_box = QVBoxLayout()
        lbl_style = QLabel("Strum Style:")
        lbl_style.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748b;")
        self.combo_style = QComboBox()
        self.combo_style.addItem("Sustained Pad", "sustained")
        self.combo_style.addItem("Arpeggio Up", "arpeggio_up")
        self.combo_style.addItem("Down Strum", "strum_down")
        style_box.addWidget(lbl_style)
        style_box.addWidget(self.combo_style)
        c_layout.addLayout(style_box)

        main_layout.addWidget(controls_group)

        # Diatonic Pads Grid Group
        self.pads_group = QGroupBox("🎵 Diatonic Chord Matrix (Click to Audition, Double-Click to Insert)")
        self.pads_layout = QGridLayout(self.pads_group)
        self.pads_layout.setContentsMargins(14, 16, 14, 16)
        self.pads_layout.setSpacing(10)
        main_layout.addWidget(self.pads_group)

        # Song Chords Ribbon (extracted from current lyrics)
        self.song_chords_group = QGroupBox("📜 Chords Found in Current Song Lyrics")
        sc_layout = QVBoxLayout(self.song_chords_group)
        sc_layout.setContentsMargins(12, 10, 12, 10)
        sc_layout.setSpacing(8)

        self.ribbon_row = QHBoxLayout()
        self.ribbon_row.setSpacing(8)
        self.ribbon_container = QWidget()
        self.ribbon_container.setLayout(self.ribbon_row)

        sc_scroll = QScrollArea()
        sc_scroll.setWidgetResizable(True)
        sc_scroll.setWidget(self.ribbon_container)
        sc_scroll.setFixedHeight(64)
        sc_scroll.setStyleSheet("border: none; background: transparent;")
        sc_layout.addWidget(sc_scroll)
        main_layout.addWidget(self.song_chords_group)

        # Progression Looper & Presets Bar
        loop_group = QGroupBox("🔁 Progression Sequencer & Looper")
        l_layout = QHBoxLayout(loop_group)
        l_layout.setContentsMargins(12, 12, 12, 12)
        l_layout.setSpacing(12)

        # Preset progression dropdown
        p_box = QVBoxLayout()
        lbl_preset = QLabel("Formula Preset:")
        lbl_preset.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748b;")
        self.combo_presets = QComboBox()
        self.combo_presets.addItems(list(CHORD_PROGRESSIONS.keys()))
        self.combo_presets.currentTextChanged.connect(self._on_preset_selected)
        p_box.addWidget(lbl_preset)
        p_box.addWidget(self.combo_presets)
        l_layout.addLayout(p_box, stretch=2)

        # BPM Slider
        bpm_box = QVBoxLayout()
        self.lbl_bpm = QLabel("Tempo: 120 BPM")
        self.lbl_bpm.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748b;")
        self.slider_bpm = QSlider(Qt.Orientation.Horizontal)
        self.slider_bpm.setRange(50, 180)
        self.slider_bpm.setValue(120)
        self.slider_bpm.valueChanged.connect(lambda v: self.lbl_bpm.setText(f"Tempo: {v} BPM"))
        bpm_box.addWidget(self.lbl_bpm)
        bpm_box.addWidget(self.slider_bpm)
        l_layout.addLayout(bpm_box, stretch=1)

        # Play / Stop Looper buttons
        btn_box = QHBoxLayout()
        btn_box.setSpacing(8)
        self.btn_play_loop = QPushButton("▶ Play Loop")
        self.btn_play_loop.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_play_loop.setFixedHeight(36)
        self.btn_play_loop.setStyleSheet("background-color: #3b82f6; color: white; font-weight: 700; border-radius: 6px; padding: 0 16px;")
        self.btn_play_loop.clicked.connect(self._toggle_loop)

        self.btn_insert_prog = QPushButton("✍️ Insert Chords")
        self.btn_insert_prog.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_insert_prog.setFixedHeight(36)
        self.btn_insert_prog.setStyleSheet("background-color: #10b981; color: white; font-weight: 700; border-radius: 6px; padding: 0 14px;")
        self.btn_insert_prog.clicked.connect(self._insert_active_progression)

        btn_box.addWidget(self.btn_play_loop)
        btn_box.addWidget(self.btn_insert_prog)
        l_layout.addLayout(btn_box)

        main_layout.addWidget(loop_group)

        # Bottom Bar: Close button
        bottom_row = QHBoxLayout()
        bottom_row.addStretch()
        self.btn_close = QPushButton("Done")
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.setFixedWidth(100)
        self.btn_close.setFixedHeight(34)
        self.btn_close.clicked.connect(self.accept)
        bottom_row.addWidget(self.btn_close)
        main_layout.addLayout(bottom_row)

    def apply_theme(self, is_dark: bool):
        self.is_dark = is_dark
        bg_col = "#0f172a" if is_dark else "#f8fafc"
        card_bg = "#1e293b" if is_dark else "#ffffff"
        text_col = "#f8fafc" if is_dark else "#0f172a"
        border_col = "#334155" if is_dark else "#e2e8f0"

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {bg_col};
                color: {text_col};
            }}
            QGroupBox {{
                font-weight: 700;
                font-size: 12px;
                border: 1px solid {border_col};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 12px;
                background-color: {card_bg};
                color: {text_col};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 6px;
                color: {text_col};
            }}
            QComboBox {{
                background-color: {bg_col};
                color: {text_col};
                border: 1px solid {border_col};
                border-radius: 6px;
                padding: 5px 10px;
                font-size: 12px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QPushButton {{
                background-color: {card_bg};
                color: {text_col};
                border: 1px solid {border_col};
                border-radius: 6px;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                border-color: #3b82f6;
            }}
        """)
        self._refresh_diatonic_pads()

    def _refresh_diatonic_pads(self):
        """Rebuild the interactive diatonic chord grid."""
        # Clear existing pads
        while self.pads_layout.count():
            item = self.pads_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        key = self.combo_key.currentText()
        scale = self.combo_scale.currentText()
        chords = ChordSoundboardSynthesizer.get_diatonic_chords(key, scale)

        col_count = 5
        for i, info in enumerate(chords):
            row = i // col_count
            col = i % col_count

            pad_btn = QPushButton()
            pad_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            pad_btn.setFixedHeight(72)

            # Styling based on role
            is_tonic = "Tonic" in info["role"]
            is_dominant = "Dominant" in info["role"]
            accent_color = "#3b82f6" if is_tonic else ("#f59e0b" if is_dominant else "#6366f1")

            pad_text = f"<b><span style='font-size: 15px; color: {accent_color};'>{info['chord']}</span></b><br>" \
                       f"<span style='font-size: 11px; font-weight: 700; color: #94a3b8;'>{info['roman']}</span><br>" \
                       f"<span style='font-size: 9px; color: #64748b;'>{info['role']}</span>"
            pad_btn.setText(f"{info['chord']}\n{info['roman']}\n{info['role']}")

            chord_symbol = info["chord"]
            pad_btn.clicked.connect(lambda _, c=chord_symbol: self._play_single_chord(c))
            pad_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {'#1e293b' if self.is_dark else '#ffffff'};
                    color: {'#f8fafc' if self.is_dark else '#0f172a'};
                    border: 2px solid {'#334155' if self.is_dark else '#e2e8f0'};
                    border-radius: 8px;
                    font-weight: 700;
                    text-align: center;
                    padding: 4px;
                }}
                QPushButton:hover {{
                    border-color: {accent_color};
                    background-color: {'#273549' if self.is_dark else '#eff6ff'};
                }}
                QPushButton:pressed {{
                    background-color: {accent_color};
                    color: white;
                }}
            """)

            # Context menu to insert
            pad_btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            pad_btn.customContextMenuRequested.connect(lambda pos, c=chord_symbol: self.chord_inserted.emit(f"[{c}]"))

            self.pads_layout.addWidget(pad_btn, row, col)

    def _play_single_chord(self, chord_str: str):
        inst = self.combo_inst.currentData()
        strum = self.combo_style.currentData()
        ChordSoundboardSynthesizer.play_chord_async(chord_str, instrument=inst, duration=1.4, strum_style=strum)

    def _refresh_song_chords(self):
        """Populate the ribbon of chords found in the current lyrics."""
        while self.ribbon_row.count():
            item = self.ribbon_row.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        chords = ChordSoundboardSynthesizer.extract_chords_from_lyrics(self.initial_lyrics)
        if not chords:
            lbl_none = QLabel("No chords detected in lyrics yet (e.g. [Am], [F], [C], [G]). Add bracketed chords to audition them.")
            lbl_none.setStyleSheet("color: #64748b; font-size: 11px; font-style: italic;")
            self.ribbon_row.addWidget(lbl_none)
            self.ribbon_row.addStretch()
            return

        for chord in chords:
            btn = QPushButton(f"🎵 {chord}")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(34)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #3b82f6;
                    color: white;
                    font-weight: 700;
                    border-radius: 17px;
                    padding: 0 14px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #2563eb;
                }
            """)
            btn.clicked.connect(lambda _, c=chord: self._play_single_chord(c))
            self.ribbon_row.addWidget(btn)

        self.ribbon_row.addStretch()

    def _on_preset_selected(self, preset_name: str):
        if preset_name in CHORD_PROGRESSIONS:
            self.loop_chords = CHORD_PROGRESSIONS[preset_name].get("chords_in_c", ["C", "G", "Am", "F"])
        else:
            self.loop_chords = ["C", "G", "Am", "F"]

    def _toggle_loop(self):
        if self.is_looping:
            self.loop_timer.stop()
            self.is_looping = False
            self.btn_play_loop.setText("▶ Play Loop")
            self.btn_play_loop.setStyleSheet("background-color: #3b82f6; color: white; font-weight: 700; border-radius: 6px; padding: 0 16px;")
        else:
            preset = self.combo_presets.currentText()
            self._on_preset_selected(preset)
            if not self.loop_chords:
                return

            self.is_looping = True
            self.loop_index = 0
            bpm = self.slider_bpm.value()
            interval_ms = int((60.0 / bpm) * 2 * 1000) # 2 beats per chord
            self.loop_timer.start(interval_ms)
            self.btn_play_loop.setText("⏹ Stop Loop")
            self.btn_play_loop.setStyleSheet("background-color: #ef4444; color: white; font-weight: 700; border-radius: 6px; padding: 0 16px;")
            self._on_loop_tick()

    def _on_loop_tick(self):
        if not self.loop_chords:
            return
        chord = self.loop_chords[self.loop_index]
        self._play_single_chord(chord)
        self.loop_index = (self.loop_index + 1) % len(self.loop_chords)

    def _insert_active_progression(self):
        preset = self.combo_presets.currentText()
        chords = CHORD_PROGRESSIONS.get(preset, {}).get("chords_in_c", ["C", "G", "Am", "F"])
        chord_tags = " ".join(f"[{c}]" for c in chords)
        self.chord_inserted.emit(chord_tags)
        QMessageBox.information(self, "Chords Inserted", f"Appended {chord_tags} to your lyrics editor.")

    def closeEvent(self, event):
        if self.is_looping:
            self.loop_timer.stop()
        super().closeEvent(event)
