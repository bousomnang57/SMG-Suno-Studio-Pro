"""
Professional AI Scratch Vocalist & Audio Audition Dialog.
Provides studio-grade vocal generation using neural Edge TTS voices,
interactive timeline playback, pitch/tempo tuning, and vocal audio export.
"""

import os
import shutil
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QSlider, QProgressBar, QTextEdit,
    QGroupBox, QFileDialog, QMessageBox, QFrame, QScrollArea,
    QButtonGroup, QRadioButton
)
from PyQt6.QtCore import Qt, pyqtSignal, QUrl, QTimer
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from app.scratch_vocalist import (
    STUDIO_VOCALISTS, VOCAL_STYLES, ScratchVocalWorker, clean_lyrics_for_vocalist
)


class ScratchVocalistDialog(QDialog):
    vocal_ready = pyqtSignal(str) # Path to generated audio file

    def __init__(self, parent=None, is_dark: bool = True, lyrics: str = "", title: str = "Untitled Song"):
        super().__init__(parent)
        self.is_dark = is_dark
        self.lyrics = lyrics
        self.title = title
        self.current_audio_path: Optional[str] = None
        self.worker: Optional[ScratchVocalWorker] = None

        self.setWindowTitle(f"🎤 AI Scratch Vocalist Preview — {self.title}")
        self.resize(860, 680)
        self.setMinimumSize(780, 600)

        # Audio Player setup
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(0.85)

        self.player.playbackStateChanged.connect(self._on_playback_state_changed)
        self.player.positionChanged.connect(self._on_position_changed)
        self.player.durationChanged.connect(self._on_duration_changed)

        self._init_ui()
        self.apply_theme(self.is_dark)

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(14)

        # Header Title
        header_row = QHBoxLayout()
        title_box = QVBoxLayout()
        self.lbl_title = QLabel("🎤 AI Scratch Vocalist & Cadence Preview")
        self.lbl_title.setStyleSheet("font-size: 18px; font-weight: 800;")
        self.lbl_subtitle = QLabel(f"Audition realistic vocal melody & cadence for '{self.title}' using neural studio singers.")
        self.lbl_subtitle.setStyleSheet("font-size: 12px; color: #64748b;")
        title_box.addWidget(self.lbl_title)
        title_box.addWidget(self.lbl_subtitle)
        header_row.addLayout(title_box)
        header_row.addStretch()

        self.lbl_status = QLabel("Ready to synthesize")
        self.lbl_status.setStyleSheet("color: #10b981; font-weight: 700; font-size: 12px;")
        header_row.addWidget(self.lbl_status)
        main_layout.addLayout(header_row)

        # Top Splitter: Vocalist Cards on left, Controls on right
        content_row = QHBoxLayout()
        content_row.setSpacing(14)

        # Left Column: Studio Vocalist Selection
        vocalist_group = QGroupBox("🎙️ Select Studio Singer")
        v_layout = QVBoxLayout(vocalist_group)
        v_layout.setContentsMargins(10, 12, 10, 10)
        v_layout.setSpacing(8)

        v_scroll = QScrollArea()
        v_scroll.setWidgetResizable(True)
        v_scroll.setStyleSheet("border: none; background: transparent;")
        v_scroll_widget = QWidget()
        self.vocalist_list_layout = QVBoxLayout(v_scroll_widget)
        self.vocalist_list_layout.setContentsMargins(0, 0, 0, 0)
        self.vocalist_list_layout.setSpacing(6)

        self.vocalist_btn_group = QButtonGroup(self)
        self.vocalist_radios = {}

        for i, singer in enumerate(STUDIO_VOCALISTS):
            radio_card = QFrame()
            radio_card.setFrameShape(QFrame.Shape.StyledPanel)
            rc_layout = QHBoxLayout(radio_card)
            rc_layout.setContentsMargins(10, 8, 10, 8)
            rc_layout.setSpacing(10)

            radio = QRadioButton()
            self.vocalist_btn_group.addButton(radio, i)
            self.vocalist_radios[singer["id"]] = radio
            if i == 0:
                radio.setChecked(True)

            info_box = QVBoxLayout()
            lbl_name = QLabel(f"<b>{singer['name']}</b>")
            lbl_name.setStyleSheet("font-size: 13px;")
            lbl_desc = QLabel(singer["desc"])
            lbl_desc.setStyleSheet("font-size: 10px; color: #64748b;")
            lbl_desc.setWordWrap(True)
            info_box.addWidget(lbl_name)
            info_box.addWidget(lbl_desc)

            rc_layout.addWidget(radio)
            rc_layout.addLayout(info_box, stretch=1)
            self.vocalist_list_layout.addWidget(radio_card)

        v_scroll.setWidget(v_scroll_widget)
        v_layout.addWidget(v_scroll)
        content_row.addWidget(vocalist_group, stretch=1)

        # Right Column: Vocal Style & Cadence Sliders + Lyrics Preview
        right_box = QVBoxLayout()
        right_box.setSpacing(12)

        # Style & Tuning Group
        tuning_group = QGroupBox("🎛️ Vocal Cadence & Tuning")
        t_layout = QVBoxLayout(tuning_group)
        t_layout.setContentsMargins(12, 12, 12, 12)
        t_layout.setSpacing(10)

        # Style preset dropdown
        style_row = QHBoxLayout()
        lbl_style = QLabel("Vocal Style Preset:")
        lbl_style.setStyleSheet("font-weight: 700; font-size: 11px;")
        self.combo_style = QComboBox()
        for k, v in VOCAL_STYLES.items():
            self.combo_style.addItem(v["name"], k)
        style_row.addWidget(lbl_style)
        style_row.addWidget(self.combo_style, stretch=1)
        t_layout.addLayout(style_row)

        # Pitch Slider
        pitch_row = QHBoxLayout()
        self.lbl_pitch = QLabel("Pitch Offset: +0 Hz")
        self.lbl_pitch.setStyleSheet("font-size: 11px; font-weight: 700;")
        self.slider_pitch = QSlider(Qt.Orientation.Horizontal)
        self.slider_pitch.setRange(-20, 20)
        self.slider_pitch.setValue(0)
        self.slider_pitch.valueChanged.connect(lambda v: self.lbl_pitch.setText(f"Pitch Offset: {v:+d} Hz"))
        pitch_row.addWidget(self.lbl_pitch, stretch=1)
        pitch_row.addWidget(self.slider_pitch, stretch=2)
        t_layout.addLayout(pitch_row)

        # Speed / Pace Slider
        rate_row = QHBoxLayout()
        self.lbl_rate = QLabel("Delivery Speed: Normal (0%)")
        self.lbl_rate.setStyleSheet("font-size: 11px; font-weight: 700;")
        self.slider_rate = QSlider(Qt.Orientation.Horizontal)
        self.slider_rate.setRange(-30, 40)
        self.slider_rate.setValue(0)
        self.slider_rate.valueChanged.connect(lambda v: self.lbl_rate.setText(f"Delivery Speed: {v:+d}%"))
        rate_row.addWidget(self.lbl_rate, stretch=1)
        rate_row.addWidget(self.slider_rate, stretch=2)
        t_layout.addLayout(rate_row)

        right_box.addWidget(tuning_group)

        # Lyrics Preview Box
        lyrics_group = QGroupBox("📜 Lyrics for Scratch Vocal")
        l_layout = QVBoxLayout(lyrics_group)
        l_layout.setContentsMargins(10, 10, 10, 10)
        self.txt_lyrics = QTextEdit()
        clean = clean_lyrics_for_vocalist(self.lyrics)
        self.txt_lyrics.setPlainText(clean if clean.strip() else self.lyrics)
        l_layout.addWidget(self.txt_lyrics)
        right_box.addWidget(lyrics_group, stretch=1)

        content_row.addLayout(right_box, stretch=1)
        main_layout.addLayout(content_row, stretch=1)

        # Bottom Audio Player & Action Controls
        player_group = QGroupBox("🎧 Studio Vocal Audio Player")
        p_layout = QVBoxLayout(player_group)
        p_layout.setContentsMargins(14, 14, 14, 14)
        p_layout.setSpacing(10)

        # Timeline row: [Current Time] [Slider] [Total Duration]
        time_row = QHBoxLayout()
        self.lbl_time_current = QLabel("00:00")
        self.lbl_time_current.setStyleSheet("font-family: monospace; font-weight: 700; color: #64748b;")
        self.timeline_slider = QSlider(Qt.Orientation.Horizontal)
        self.timeline_slider.setRange(0, 0)
        self.timeline_slider.sliderMoved.connect(self._on_seek)
        self.lbl_time_total = QLabel("00:00")
        self.lbl_time_total.setStyleSheet("font-family: monospace; font-weight: 700; color: #64748b;")
        time_row.addWidget(self.lbl_time_current)
        time_row.addWidget(self.timeline_slider, stretch=1)
        time_row.addWidget(self.lbl_time_total)
        p_layout.addLayout(time_row)

        # Action Buttons row: Generate, Play, Pause, Stop, Export Audio, Volume
        act_row = QHBoxLayout()
        act_row.setSpacing(10)

        self.btn_generate = QPushButton("✨ Generate Scratch Vocal")
        self.btn_generate.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_generate.setFixedHeight(38)
        self.btn_generate.setStyleSheet("background-color: #8b5cf6; color: white; font-weight: 700; border-radius: 6px; padding: 0 18px;")
        self.btn_generate.clicked.connect(self._start_vocal_synthesis)

        self.btn_play = QPushButton("▶ Play")
        self.btn_play.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_play.setFixedHeight(38)
        self.btn_play.setEnabled(False)
        self.btn_play.setStyleSheet("background-color: #3b82f6; color: white; font-weight: 700; border-radius: 6px; padding: 0 16px;")
        self.btn_play.clicked.connect(self._play_audio)

        self.btn_pause = QPushButton("⏸ Pause")
        self.btn_pause.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_pause.setFixedHeight(38)
        self.btn_pause.setEnabled(False)
        self.btn_pause.clicked.connect(self._pause_audio)

        self.btn_stop = QPushButton("⏹ Stop")
        self.btn_stop.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_stop.setFixedHeight(38)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._stop_audio)

        self.btn_export = QPushButton("💾 Export Audio (.mp3)")
        self.btn_export.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_export.setFixedHeight(38)
        self.btn_export.setEnabled(False)
        self.btn_export.setStyleSheet("background-color: #10b981; color: white; font-weight: 700; border-radius: 6px; padding: 0 16px;")
        self.btn_export.clicked.connect(self._export_audio)

        act_row.addWidget(self.btn_generate)
        act_row.addWidget(self.btn_play)
        act_row.addWidget(self.btn_pause)
        act_row.addWidget(self.btn_stop)
        act_row.addWidget(self.btn_export)
        act_row.addStretch()

        # Volume slider
        lbl_vol = QLabel("🔊")
        self.slider_vol = QSlider(Qt.Orientation.Horizontal)
        self.slider_vol.setRange(0, 100)
        self.slider_vol.setValue(85)
        self.slider_vol.setFixedWidth(100)
        self.slider_vol.valueChanged.connect(lambda v: self.audio_output.setVolume(v / 100.0))
        act_row.addWidget(lbl_vol)
        act_row.addWidget(self.slider_vol)

        p_layout.addLayout(act_row)
        main_layout.addWidget(player_group)

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
            QTextEdit {{
                background-color: {bg_col};
                color: {text_col};
                border: 1px solid {border_col};
                border-radius: 6px;
                font-size: 13px;
                line-height: 1.5;
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
                border-color: #8b5cf6;
            }}
        """)

    def _get_selected_voice_id(self) -> str:
        idx = self.vocalist_btn_group.checkedId()
        if 0 <= idx < len(STUDIO_VOCALISTS):
            return STUDIO_VOCALISTS[idx]["id"]
        return "km-KH-PisethNeural"

    def _start_vocal_synthesis(self):
        lyrics = self.txt_lyrics.toPlainText().strip()
        if not lyrics:
            QMessageBox.warning(self, "No Lyrics", "Please enter lyrics to generate a scratch vocal.")
            return

        self.lbl_status.setText("⏳ Synthesizing vocal track...")
        self.lbl_status.setStyleSheet("color: #f59e0b; font-weight: 700;")
        self.btn_generate.setEnabled(False)

        voice_id = self._get_selected_voice_id()
        style_key = self.combo_style.currentData()
        pitch = self.slider_pitch.value()
        rate = self.slider_rate.value()

        self.worker = ScratchVocalWorker(
            lyrics=lyrics,
            voice_id=voice_id,
            pitch_hz=pitch,
            rate_percent=rate,
            vocal_style=style_key
        )
        self.worker.finished.connect(self._on_synthesis_finished)
        self.worker.error.connect(self._on_synthesis_error)
        self.worker.start()

    def _on_synthesis_finished(self, audio_path: str):
        self.btn_generate.setEnabled(True)
        self.current_audio_path = audio_path
        self.lbl_status.setText("🟢 Vocal Ready")
        self.lbl_status.setStyleSheet("color: #10b981; font-weight: 700;")

        self.btn_play.setEnabled(True)
        self.btn_stop.setEnabled(True)
        self.btn_export.setEnabled(True)

        self.player.setSource(QUrl.fromLocalFile(audio_path))
        self.vocal_ready.emit(audio_path)
        self._play_audio()

    def _on_synthesis_error(self, err_msg: str):
        self.btn_generate.setEnabled(True)
        self.lbl_status.setText("❌ Synthesis Failed")
        self.lbl_status.setStyleSheet("color: #ef4444; font-weight: 700;")
        QMessageBox.critical(self, "Vocal Synthesis Error", err_msg)

    def _play_audio(self):
        self.player.play()
        self.btn_pause.setEnabled(True)

    def _pause_audio(self):
        self.player.pause()

    def _stop_audio(self):
        self.player.stop()
        self.timeline_slider.setValue(0)
        self.lbl_time_current.setText("00:00")

    def _on_seek(self, position: int):
        self.player.setPosition(position)

    def _on_playback_state_changed(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.lbl_status.setText("🎶 Playing Scratch Vocal")
            self.lbl_status.setStyleSheet("color: #3b82f6; font-weight: 700;")
        elif state == QMediaPlayer.PlaybackState.PausedState:
            self.lbl_status.setText("⏸ Paused")
            self.lbl_status.setStyleSheet("color: #f59e0b; font-weight: 700;")
        else:
            self.lbl_status.setText("⏹ Stopped")
            self.lbl_status.setStyleSheet("color: #64748b; font-weight: 700;")

    def _on_position_changed(self, position_ms: int):
        if not self.timeline_slider.isSliderDown():
            self.timeline_slider.setValue(position_ms)
        sec = position_ms // 1000
        self.lbl_time_current.setText(f"{sec // 60:02d}:{sec % 60:02d}")

    def _on_duration_changed(self, duration_ms: int):
        self.timeline_slider.setRange(0, duration_ms)
        sec = duration_ms // 1000
        self.lbl_time_total.setText(f"{sec // 60:02d}:{sec % 60:02d}")

    def _export_audio(self):
        if not self.current_audio_path or not os.path.exists(self.current_audio_path):
            QMessageBox.warning(self, "No Audio", "Please synthesize a scratch vocal first.")
            return

        ext = Path(self.current_audio_path).suffix or ".mp3"
        safe_title = "".join(c for c in self.title if c.isalnum() or c in (" ", "-", "_")).strip()
        default_name = f"{safe_title}_Scratch_Vocal{ext}"

        dest, _ = QFileDialog.getSaveFileName(
            self,
            "Export Scratch Vocal Audio",
            default_name,
            f"Audio Files (*{ext});;All Files (*.*)"
        )
        if dest:
            try:
                shutil.copy2(self.current_audio_path, dest)
                QMessageBox.information(self, "Export Successful", f"Saved scratch vocal track to:\n{dest}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to save audio file: {e}")

    def closeEvent(self, event):
        self.player.stop()
        super().closeEvent(event)

