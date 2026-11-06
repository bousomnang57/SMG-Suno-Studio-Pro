"""
AI Vocal Melody & Topline Pitch Guide Dialog.
Visual pitch roll and exporter for Standard Type 1 MIDI and MusicXML sheet music.
"""

import os
import shutil
import tempfile
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QSlider, QGroupBox, QScrollArea,
    QFrame, QMessageBox, QFileDialog, QTableWidget, QTableWidgetItem,
    QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal, QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from app.vocal_melody_generator import (
    VocalToplineGenerator, SCALES, ROOT_TO_MIDI, MIDI_TO_NOTE_NAME
)


class MelodyGuideDialog(QDialog):
    def __init__(self, parent=None, is_dark: bool = True, lyrics: str = "", title: str = "Untitled Track", bpm: int = 120):
        super().__init__(parent)
        self.is_dark = is_dark
        self.lyrics = lyrics
        self.title = title
        self.bpm = bpm
        self.events = []
        self.temp_wav_path = None

        self.setWindowTitle(f"🎼 AI Vocal Melody & Topline Pitch Guide — {self.title}")
        self.resize(860, 680)
        self.setMinimumSize(800, 600)

        # Audio Player
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(0.85)

        self._init_ui()
        self.apply_theme(self.is_dark)
        self._generate_melody()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(14)

        # Header Title
        header_row = QHBoxLayout()
        title_box = QVBoxLayout()
        self.lbl_title = QLabel("🎼 AI Vocal Melody & Topline Pitch Guide")
        self.lbl_title.setStyleSheet("font-size: 18px; font-weight: 800;")
        self.lbl_subtitle = QLabel(f"Generate vocal melodic contours matching syllable cadence for '{self.title}'. Export MIDI & MusicXML.")
        self.lbl_subtitle.setStyleSheet("font-size: 12px; color: #64748b;")
        title_box.addWidget(self.lbl_title)
        title_box.addWidget(self.lbl_subtitle)
        header_row.addLayout(title_box)
        header_row.addStretch()
        main_layout.addLayout(header_row)

        # Controls Bar: Key, Scale, Tempo
        ctrl_group = QGroupBox("🎛️ Melody & Scale Settings")
        c_layout = QHBoxLayout(ctrl_group)
        c_layout.setContentsMargins(12, 12, 12, 12)
        c_layout.setSpacing(14)

        # Key
        key_box = QVBoxLayout()
        lbl_k = QLabel("Key:")
        lbl_k.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748b;")
        self.combo_key = QComboBox()
        self.combo_key.addItems(list(ROOT_TO_MIDI.keys()))
        self.combo_key.setCurrentText("C")
        self.combo_key.currentTextChanged.connect(self._generate_melody)
        key_box.addWidget(lbl_k)
        key_box.addWidget(self.combo_key)
        c_layout.addLayout(key_box)

        # Scale
        scale_box = QVBoxLayout()
        lbl_s = QLabel("Musical Scale / Mode:")
        lbl_s.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748b;")
        self.combo_scale = QComboBox()
        self.combo_scale.addItems(list(SCALES.keys()))
        self.combo_scale.setCurrentText("Major")
        self.combo_scale.currentTextChanged.connect(self._generate_melody)
        scale_box.addWidget(lbl_s)
        scale_box.addWidget(self.combo_scale)
        c_layout.addLayout(scale_box, stretch=1)

        # BPM Slider
        bpm_box = QVBoxLayout()
        self.lbl_bpm = QLabel(f"Tempo: {self.bpm} BPM")
        self.lbl_bpm.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748b;")
        self.slider_bpm = QSlider(Qt.Orientation.Horizontal)
        self.slider_bpm.setRange(60, 180)
        self.slider_bpm.setValue(self.bpm)
        self.slider_bpm.valueChanged.connect(self._on_bpm_changed)
        bpm_box.addWidget(self.lbl_bpm)
        bpm_box.addWidget(self.slider_bpm)
        c_layout.addLayout(bpm_box, stretch=1)

        main_layout.addWidget(ctrl_group)

        # Note Events Table / Visual Score
        table_group = QGroupBox("🎵 Syllable-to-Pitch Topline Score")
        t_layout = QVBoxLayout(table_group)
        t_layout.setContentsMargins(10, 10, 10, 10)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Section", "Syllable / Word", "Pitch Note", "Beat Position", "Duration"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        t_layout.addWidget(self.table)
        main_layout.addWidget(table_group, stretch=1)

        # Audio Player Bar
        audio_group = QGroupBox("🎧 Topline Melodic Audio Audition")
        a_layout = QHBoxLayout(audio_group)
        a_layout.setContentsMargins(12, 10, 12, 10)
        a_layout.setSpacing(12)

        self.btn_play_audio = QPushButton("▶ Audition Melody")
        self.btn_play_audio.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_play_audio.setFixedHeight(36)
        self.btn_play_audio.setStyleSheet("background-color: #3b82f6; color: white; font-weight: 700; border-radius: 6px; padding: 0 16px;")
        self.btn_play_audio.clicked.connect(self._toggle_audio)

        self.btn_stop_audio = QPushButton("⏹ Stop")
        self.btn_stop_audio.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_stop_audio.setFixedHeight(36)
        self.btn_stop_audio.clicked.connect(self._stop_audio)

        self.lbl_audio_status = QLabel("Ready to audition")
        self.lbl_audio_status.setStyleSheet("color: #64748b; font-size: 11px;")

        a_layout.addWidget(self.btn_play_audio)
        a_layout.addWidget(self.btn_stop_audio)
        a_layout.addWidget(self.lbl_audio_status)
        a_layout.addStretch()
        main_layout.addWidget(audio_group)

        # Bottom Bar: DAW & Sheet Music Exports
        export_row = QHBoxLayout()
        export_row.setSpacing(10)

        self.btn_export_midi = QPushButton("🎹 Export MIDI (.mid)")
        self.btn_export_midi.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_export_midi.setFixedHeight(38)
        self.btn_export_midi.setStyleSheet("background-color: #8b5cf6; color: white; font-weight: 700; border-radius: 6px; padding: 0 16px;")
        self.btn_export_midi.clicked.connect(self._export_midi_file)

        self.btn_export_xml = QPushButton("🎼 Export MusicXML Sheet (.musicxml)")
        self.btn_export_xml.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_export_xml.setFixedHeight(38)
        self.btn_export_xml.setStyleSheet("background-color: #10b981; color: white; font-weight: 700; border-radius: 6px; padding: 0 16px;")
        self.btn_export_xml.clicked.connect(self._export_musicxml_file)

        self.btn_close = QPushButton("Close")
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.setFixedHeight(38)
        self.btn_close.setFixedWidth(80)
        self.btn_close.clicked.connect(self.accept)

        export_row.addWidget(self.btn_export_midi)
        export_row.addWidget(self.btn_export_xml)
        export_row.addStretch()
        export_row.addWidget(self.btn_close)
        main_layout.addLayout(export_row)

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
            QTableWidget {{
                background-color: {bg_col};
                color: {text_col};
                border: 1px solid {border_col};
                border-radius: 6px;
                gridline-color: {border_col};
            }}
            QHeaderView::section {{
                background-color: {card_bg};
                color: {text_col};
                border: 1px solid {border_col};
                font-weight: 700;
                padding: 4px;
            }}
            QComboBox {{
                background-color: {bg_col};
                color: {text_col};
                border: 1px solid {border_col};
                border-radius: 6px;
                padding: 5px 10px;
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

    def _on_bpm_changed(self, v: int):
        self.bpm = v
        self.lbl_bpm.setText(f"Tempo: {v} BPM")

    def _generate_melody(self):
        key = self.combo_key.currentText()
        scale = self.combo_scale.currentText()
        self.events = VocalToplineGenerator.generate_melody_events(self.lyrics, key=key, scale=scale, bpm=self.bpm)

        # Update table
        self.table.setRowCount(len(self.events))
        for row, ev in enumerate(self.events):
            semi = ev["midi"] % 12
            octave = (ev["midi"] // 12) - 1
            note_name = f"{MIDI_TO_NOTE_NAME[semi]}{octave}"

            self.table.setItem(row, 0, QTableWidgetItem(ev["section"]))
            self.table.setItem(row, 1, QTableWidgetItem(ev["syllable"]))
            self.table.setItem(row, 2, QTableWidgetItem(f"{note_name} (MIDI {ev['midi']})"))
            self.table.setItem(row, 3, QTableWidgetItem(f"Beat {ev['beat']:.1f}"))
            self.table.setItem(row, 4, QTableWidgetItem(f"{ev['duration_beats']} beats"))

        self.lbl_audio_status.setText(f"Generated {len(self.events)} topline notes.")

    def _toggle_audio(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
            self.btn_play_audio.setText("▶ Audition Melody")
            return

        # Synthesize preview WAV
        if not self.temp_wav_path:
            out_dir = Path(tempfile.gettempdir()) / "worldlyric_topline"
            out_dir.mkdir(parents=True, exist_ok=True)
            self.temp_wav_path = str(out_dir / f"melody_preview_{abs(hash(self.title)) % 100000}.wav")

        VocalToplineGenerator.synthesize_preview_audio(self.events, self.temp_wav_path, bpm=self.bpm)
        self.player.setSource(QUrl.fromLocalFile(self.temp_wav_path))
        self.player.play()
        self.btn_play_audio.setText("⏸ Pause")
        self.lbl_audio_status.setText("🎶 Playing vocal topline guide...")

    def _stop_audio(self):
        self.player.stop()
        self.btn_play_audio.setText("▶ Audition Melody")
        self.lbl_audio_status.setText("⏹ Stopped")

    def _export_midi_file(self):
        if not self.events:
            QMessageBox.warning(self, "No Notes", "No vocal notes generated.")
            return

        safe_title = "".join(c for c in self.title if c.isalnum() or c in (" ", "-", "_")).strip()
        dest, _ = QFileDialog.getSaveFileName(
            self,
            "Export Standard MIDI Topline Guide",
            f"{safe_title}_Vocal_Topline.mid",
            "MIDI Files (*.mid);;All Files (*.*)"
        )
        if dest:
            try:
                VocalToplineGenerator.export_midi(self.events, dest, bpm=self.bpm, title=self.title)
                QMessageBox.information(self, "MIDI Exported", f"Successfully exported Type 1 MIDI with lyric events to:\n{dest}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export MIDI: {e}")

    def _export_musicxml_file(self):
        if not self.events:
            QMessageBox.warning(self, "No Notes", "No vocal notes generated.")
            return

        safe_title = "".join(c for c in self.title if c.isalnum() or c in (" ", "-", "_")).strip()
        dest, _ = QFileDialog.getSaveFileName(
            self,
            "Export MusicXML Sheet Music",
            f"{safe_title}_Sheet_Music.musicxml",
            "MusicXML Files (*.musicxml *.xml);;All Files (*.*)"
        )
        if dest:
            try:
                VocalToplineGenerator.export_musicxml(self.events, dest, title=self.title, bpm=self.bpm)
                QMessageBox.information(self, "MusicXML Exported", f"Successfully exported sheet music to:\n{dest}\n\nOpen in MuseScore, Sibelius, or Dorico.")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export MusicXML: {e}")

    def closeEvent(self, event):
        self.player.stop()
        super().closeEvent(event)

