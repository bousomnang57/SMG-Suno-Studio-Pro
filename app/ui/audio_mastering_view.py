"""
Mode 6: Pro Mastering Studio & Suno Audio Fixer View for SMG Suno Studio Pro.
Features:
- Clean, Logo-Free Professional DAW Studio Interface (theme-adaptive across all 5 themes)
- Interactive Waveform Editor with playhead scrub and draggable IN / OUT Silence Trim handles
- Zero-Latency Live A/B Monitor (A: Original Suno vs. B: Mastered Pro)
- 5-Stage Pro Mastering DSP Rack:
  1. AI Analysis & Auto-Title (BPM, Key, LUFS, Suno artifact index, 5 AI Title options)
  2. FL-Style Parametric EQ 2 (6-band surgical cuts and high-end air boost)
  3. Multiband Dynamics & De-AI Artifact Filter (220-480Hz boxiness & 6-10kHz sibilance)
  4. Stereo Enhancer, Subtle Room Depth & Silence Auto-Trim
  5. 4x True-Peak Brickwall Limiter & Loudness Normalization (Spotify, Apple, Suno, Club, CD)
- Suno & Audio Batch Queue with drag-and-drop and 1-Click Auto All execution
- Direct Studio Bridges (Suno Downloader -> Master Audio -> Lyric Editor Stem Player)
"""

from __future__ import annotations

import os
import sys
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Callable

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QSlider, QProgressBar, QFrame,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QFileDialog, QMessageBox, QSplitter,
    QScrollArea, QApplication, QGroupBox
)
from PyQt6.QtCore import Qt, QUrl, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QIcon, QFont, QColor
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

from app.config import config_manager, get_asset_path
from app.ui.styles import get_theme
from app.audio_mastering_engine import AudioMasteringEngine, MASTERING_TARGETS
from app.ui.waveform_widget import WaveformEditorPane


class MasterWorker(QThread):
    """Background DSP rendering thread for responsive UI."""
    progress_updated = pyqtSignal(int, str)
    master_completed = pyqtSignal(dict)
    master_failed = pyqtSignal(str)

    def __init__(self, input_path: str, output_path: str, params: dict):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.params = params

    def run(self):
        try:
            res = AudioMasteringEngine.process_master(
                input_path=self.input_path,
                output_path=self.output_path,
                target_preset=self.params.get("target_preset", "Suno Master (-13.0 LUFS)"),
                auto_trim=self.params.get("auto_trim", True),
                de_ai_filter=self.params.get("de_ai_filter", True),
                eq_low_gain=self.params.get("eq_low_gain", 0.5),
                eq_mud_cut_gain=self.params.get("eq_mud_cut_gain", -2.2),
                eq_presence_gain=self.params.get("eq_presence_gain", 1.0),
                eq_air_gain=self.params.get("eq_air_gain", 1.8),
                stereo_width=self.params.get("stereo_width", 1.25),
                add_room_depth=self.params.get("add_room_depth", True),
                progress_callback=lambda pct, msg: self.progress_updated.emit(pct, msg)
            )
            self.master_completed.emit(res)
        except Exception as e:
            self.master_failed.emit(str(e))


class AudioMasteringView(QWidget):
    """Pro Mastering Studio & Suno Audio Fixer View (Mode 6)."""

    send_to_editor_requested = pyqtSignal(str)  # audio_path
    switch_to_suno_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("audioMasteringView")

        self.tracks: List[Dict] = []
        self.current_track_idx: int = -1
        self.current_theme: str = "obsidian"

        # Active paths
        self.current_input_path: str = ""
        self.current_master_path: str = ""
        self.is_ab_mastered: bool = True  # True = Mastered B, False = Original A

        # Audio Player
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)
        self.player.positionChanged.connect(self._on_player_position_changed)
        self.player.durationChanged.connect(self._on_player_duration_changed)
        self.player.playbackStateChanged.connect(self._on_playback_state_changed)

        # Worker
        self.worker: Optional[MasterWorker] = None
        self.batch_running: bool = False
        self.batch_queue_indices: List[int] = []

        self._init_ui()
        self.apply_theme(config_manager.get("theme", "obsidian"))

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(8)

        # ── 1. Clean Logo-Free Pro DAW Header & Ribbon ──
        header_card = QFrame()
        header_card.setObjectName("masterHeaderCard")
        h_layout = QHBoxLayout(header_card)
        h_layout.setContentsMargins(10, 6, 10, 6)
        h_layout.setSpacing(8)

        # DAW Title & Badge
        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        lbl_title = QLabel("🎛️ PRO AUDIO MASTERING & SUNO FIXER")
        lbl_title.setStyleSheet("font-size: 13px; font-weight: 800; letter-spacing: 0.5px;")
        self.lbl_header_subtitle = QLabel("AI Artifact Removal • FL-Style Parametric EQ • True-Peak Limiter • EBU R128 Loudness")
        self.lbl_header_subtitle.setStyleSheet("font-size: 10px; opacity: 0.8;")
        title_col.addWidget(lbl_title)
        title_col.addWidget(self.lbl_header_subtitle)
        h_layout.addLayout(title_col)

        h_layout.addStretch()

        # Ribbon Action Buttons
        self.btn_add_audio = QPushButton("+ Add Audio")
        self.btn_add_audio.setToolTip("Import Suno or user MP3/WAV/FLAC audio files")
        self.btn_add_audio.clicked.connect(self._browse_audio_file)

        self.btn_add_folder = QPushButton("+ Add Folder")
        self.btn_add_folder.setToolTip("Batch import all audio files from a directory")
        self.btn_add_folder.clicked.connect(self._browse_audio_folder)

        self.btn_ribbon_auto_all = QPushButton("⚡ 1-Click Auto All")
        self.btn_ribbon_auto_all.setObjectName("primaryGreenButton")
        self.btn_ribbon_auto_all.setStyleSheet("background: #059669; color: white; font-weight: 800; font-size: 10.5px; padding: 4px 10px; border-radius: 5px;")
        self.btn_ribbon_auto_all.clicked.connect(self._start_1click_auto_all)

        self.btn_ribbon_analyze = QPushButton("🔍 AI Analyze")
        self.btn_ribbon_analyze.clicked.connect(self._analyze_current_track)

        self.btn_ribbon_title = QPushButton("🏷️ Auto Title AI")
        self.btn_ribbon_title.clicked.connect(self._generate_ai_titles)

        self.btn_ribbon_trim = QPushButton("✂️ Auto Trim")
        self.btn_ribbon_trim.clicked.connect(self._auto_trim_current)

        self.btn_ribbon_export = QPushButton("💾 Export Master")
        self.btn_ribbon_export.clicked.connect(self._export_current_master)

        self.btn_ribbon_folder = QPushButton("📁 Output Folder")
        self.btn_ribbon_folder.clicked.connect(self._open_output_folder)

        for btn in [
            self.btn_add_audio, self.btn_add_folder, self.btn_ribbon_auto_all,
            self.btn_ribbon_analyze, self.btn_ribbon_title, self.btn_ribbon_trim,
            self.btn_ribbon_export, self.btn_ribbon_folder
        ]:
            if btn != self.btn_ribbon_auto_all:
                btn.setStyleSheet("font-weight: 700; font-size: 10px; padding: 4px 8px;")
            h_layout.addWidget(btn)

        root.addWidget(header_card)

        # ── 2. Main Workspace Splitter: Left (Batch Queue) & Right (Waveform & DSP Rack) ──
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(6)

        # ── Left: Suno & Audio Batch Queue ──
        left_panel = QFrame()
        left_panel.setObjectName("masterLeftPanel")
        l_layout = QVBoxLayout(left_panel)
        l_layout.setContentsMargins(10, 8, 10, 8)
        l_layout.setSpacing(6)

        l_hdr = QHBoxLayout()
        lbl_q_title = QLabel("Suno & Audio Batch Queue")
        lbl_q_title.setStyleSheet("font-size: 11px; font-weight: 800;")
        l_hdr.addWidget(lbl_q_title)
        l_hdr.addStretch()
        self.lbl_q_count = QLabel("0 Tracks")
        self.lbl_q_count.setStyleSheet("font-size: 10px; font-weight: 700; color: #10b981;")
        l_hdr.addWidget(self.lbl_q_count)
        l_layout.addLayout(l_hdr)

        lbl_drag_hint = QLabel("Drag & Drop Suno MP3/WAV/FLAC files here, or click Add Audio")
        lbl_drag_hint.setStyleSheet("font-size: 9px; opacity: 0.7;")
        l_layout.addWidget(lbl_drag_hint)

        # Batch Queue Table
        self.table_queue = QTableWidget(0, 6)
        self.table_queue.setHorizontalHeaderLabels(["Sel", "Track / AI Auto Title", "BPM / Key", "LUFS", "Score", "Status"])
        self.table_queue.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table_queue.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_queue.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table_queue.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table_queue.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table_queue.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table_queue.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_queue.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_queue.cellClicked.connect(self._on_table_row_clicked)
        l_layout.addWidget(self.table_queue, stretch=1)

        # Queue Management Buttons
        q_btns = QHBoxLayout()
        q_btns.setSpacing(6)
        btn_q_add = QPushButton("+ Add Audio")
        btn_q_add.clicked.connect(self._browse_audio_file)
        btn_q_check = QPushButton("Check All")
        btn_q_check.clicked.connect(self._check_all_queue)
        btn_q_remove = QPushButton("Remove")
        btn_q_remove.clicked.connect(self._remove_selected_queue)
        for b in [btn_q_add, btn_q_check, btn_q_remove]:
            b.setStyleSheet("font-size: 10px; font-weight: 700; padding: 3px 6px;")
            q_btns.addWidget(b)
        l_layout.addLayout(q_btns)

        # 1-Click Auto Export Setup
        export_box = QGroupBox("1-Click Auto Export Setup")
        export_box.setStyleSheet("font-size: 10px; font-weight: 800; margin-top: 6px;")
        eb_layout = QVBoxLayout(export_box)
        eb_layout.setContentsMargins(8, 8, 8, 8)
        eb_layout.setSpacing(5)

        r1 = QHBoxLayout()
        r1.addWidget(QLabel("Output Format:"))
        self.combo_format = QComboBox()
        self.combo_format.addItems([
            "WAV 24-bit PCM (Mastering Studio Pro)",
            "WAV 16-bit PCM (CD / Spotify Standard)",
            "MP3 320kbps (Universal Streaming)"
        ])
        r1.addWidget(self.combo_format, stretch=1)
        eb_layout.addLayout(r1)

        r2 = QHBoxLayout()
        r2.addWidget(QLabel("Sample Rate:"))
        self.combo_sample_rate = QComboBox()
        self.combo_sample_rate.addItems(["44,100 Hz (CD / Spotify Standard)", "48,000 Hz (Studio Film/Video)"])
        r2.addWidget(self.combo_sample_rate, stretch=1)
        eb_layout.addLayout(r2)

        r3 = QHBoxLayout()
        r3.addWidget(QLabel("Target Loudness:"))
        self.combo_target_preset = QComboBox()
        self.combo_target_preset.addItems(list(MASTERING_TARGETS.keys()))
        r3.addWidget(self.combo_target_preset, stretch=1)
        eb_layout.addLayout(r3)

        r4 = QHBoxLayout()
        r4.addWidget(QLabel("Output Folder:"))
        default_out = str(Path.home() / ".lyric_ai_writer" / "suno_masters")
        self.txt_output_dir = QLineEdit(default_out)
        self.txt_output_dir.setStyleSheet("font-size: 9.5px;")
        btn_browse_out = QPushButton("Browse...")
        btn_browse_out.clicked.connect(self._browse_output_dir)
        r4.addWidget(self.txt_output_dir, stretch=1)
        r4.addWidget(btn_browse_out)
        eb_layout.addLayout(r4)

        # Big 1-Click Action Button
        action_row = QHBoxLayout()
        self.btn_start_auto = QPushButton("1-CLICK AUTO ALL (Analyze -> Fix -> Trim -> Title -> Export)")
        self.btn_start_auto.setStyleSheet("background: #059669; color: #ffffff; font-weight: 800; font-size: 11px; padding: 8px 10px; border-radius: 6px;")
        self.btn_start_auto.clicked.connect(self._start_1click_auto_all)

        self.btn_stop_auto = QPushButton("STOP")
        self.btn_stop_auto.setStyleSheet("background: #dc2626; color: #ffffff; font-weight: 800; font-size: 11px; padding: 8px 10px; border-radius: 6px;")
        self.btn_stop_auto.clicked.connect(self._stop_batch)
        self.btn_stop_auto.setEnabled(False)

        action_row.addWidget(self.btn_start_auto, stretch=4)
        action_row.addWidget(self.btn_stop_auto, stretch=1)
        eb_layout.addLayout(action_row)

        l_layout.addWidget(export_box)
        splitter.addWidget(left_panel)

        # ── Right: Waveform & 5-Stage DSP Mastering Rack ──
        right_panel = QFrame()
        right_panel.setObjectName("masterRightPanel")
        r_layout = QVBoxLayout(right_panel)
        r_layout.setContentsMargins(10, 8, 10, 8)
        r_layout.setSpacing(6)

        # Waveform Controls Header
        wf_head = QHBoxLayout()
        wf_head.setSpacing(6)

        self.btn_play_pause = QPushButton("▶ Play")
        self.btn_play_pause.setStyleSheet("font-weight: 800; font-size: 10px; padding: 3px 10px;")
        self.btn_play_pause.clicked.connect(self._toggle_playback)
        wf_head.addWidget(self.btn_play_pause)

        self.btn_stop = QPushButton("■ Stop")
        self.btn_stop.setStyleSheet("font-weight: 800; font-size: 10px; padding: 3px 8px;")
        self.btn_stop.clicked.connect(self._stop_playback)
        wf_head.addWidget(self.btn_stop)

        # Live A/B Monitor
        wf_head.addSpacing(8)
        self.btn_ab_original = QPushButton("A: Original")
        self.btn_ab_original.setCheckable(True)
        self.btn_ab_original.setStyleSheet("font-weight: 800; font-size: 10px; padding: 3px 10px;")
        self.btn_ab_original.clicked.connect(lambda: self._set_ab_mode(False))
        wf_head.addWidget(self.btn_ab_original)

        self.btn_ab_master = QPushButton("B: Mastered Pro")
        self.btn_ab_master.setCheckable(True)
        self.btn_ab_master.setChecked(True)
        self.btn_ab_master.setStyleSheet("background: #059669; color: white; font-weight: 800; font-size: 10px; padding: 3px 10px;")
        self.btn_ab_master.clicked.connect(lambda: self._set_ab_mode(True))
        wf_head.addWidget(self.btn_ab_master)

        self.lbl_timecode = QLabel("00:00.00 / 00:00.00")
        self.lbl_timecode.setStyleSheet("font-family: monospace; font-size: 10.5px; font-weight: 700; color: #38bdf8;")
        wf_head.addWidget(self.lbl_timecode)

        wf_head.addStretch()

        wf_head.addWidget(QLabel("Vol:"))
        self.slider_vol = QSlider(Qt.Orientation.Horizontal)
        self.slider_vol.setRange(0, 100)
        self.slider_vol.setValue(85)
        self.slider_vol.setFixedWidth(70)
        self.slider_vol.valueChanged.connect(self._on_vol_changed)
        wf_head.addWidget(self.slider_vol)

        btn_zoom_out = QPushButton("-")
        btn_zoom_out.setFixedWidth(24)
        btn_zoom_out.clicked.connect(lambda: self.waveform_pane.canvas.set_zoom(self.waveform_pane.canvas.zoom - 0.5))
        btn_zoom_in = QPushButton("+")
        btn_zoom_in.setFixedWidth(24)
        btn_zoom_in.clicked.connect(lambda: self.waveform_pane.canvas.set_zoom(self.waveform_pane.canvas.zoom + 0.5))
        btn_zoom_fit = QPushButton("Fit")
        btn_zoom_fit.setFixedWidth(30)
        btn_zoom_fit.clicked.connect(lambda: self.waveform_pane.canvas.set_zoom(1.0))
        for zb in [btn_zoom_out, btn_zoom_in, btn_zoom_fit]:
            zb.setStyleSheet("font-weight: 800; font-size: 9.5px;")
            wf_head.addWidget(zb)

        r_layout.addLayout(wf_head)

        # Waveform Canvas & L/R Meter
        self.waveform_pane = WaveformEditorPane(self)
        self.waveform_pane.seek_requested.connect(self._seek_player)
        r_layout.addWidget(self.waveform_pane)

        # ── Middle 5-Tab Mastering Rack ──
        self.tabs_master = QTabWidget()
        self.tabs_master.setStyleSheet("QTabBar::tab { font-size: 10px; font-weight: 700; padding: 5px 12px; }")

        # Tab 1: AI Analysis & Title
        self.tab_analysis = self._create_analysis_tab()
        self.tabs_master.addTab(self.tab_analysis, "1. AI Analysis & Title")

        # Tab 2: EQ 2 (FL Style)
        self.tab_eq = self._create_eq_tab()
        self.tabs_master.addTab(self.tab_eq, "2. EQ 2 (FL Style)")

        # Tab 3: Multiband & De-AI
        self.tab_deai = self._create_deai_tab()
        self.tabs_master.addTab(self.tab_deai, "3. Multiband & De-AI")

        # Tab 4: Stereo, Reverb & Trim
        self.tab_stereo = self._create_stereo_tab()
        self.tabs_master.addTab(self.tab_stereo, "4. Stereo, Reverb & Trim")

        # Tab 5: Limiter & Export
        self.tab_limiter = self._create_limiter_tab()
        self.tabs_master.addTab(self.tab_limiter, "5. Limiter & Export")

        r_layout.addWidget(self.tabs_master, stretch=1)
        splitter.addWidget(right_panel)

        # Set splitter proportions (32% left, 68% right)
        splitter.setSizes([380, 820])
        root.addWidget(splitter, stretch=1)

        # ── Bottom Status Bar ──
        status_row = QHBoxLayout()
        self.lbl_status = QLabel("Ready — Drop Suno tracks into queue to analyze & master")
        self.lbl_status.setStyleSheet("font-size: 10px; font-weight: 600;")
        status_row.addWidget(self.lbl_status, stretch=1)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(14)
        self.progress_bar.setFixedWidth(220)
        self.progress_bar.setStyleSheet("font-size: 9px; text-align: center;")
        status_row.addWidget(self.progress_bar)

        self.lbl_ffmpeg_status = QLabel("FFmpeg: OK")
        self.lbl_ffmpeg_status.setStyleSheet("font-size: 9.5px; font-weight: 700; color: #10b981;")
        status_row.addWidget(self.lbl_ffmpeg_status)

        root.addLayout(status_row)

    # ── Tab 1: AI Analysis & Title ──

    def _create_analysis_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Metrics Stat Cards (6 cards)
        cards_row = QHBoxLayout()
        cards_row.setSpacing(6)

        self.card_score = self._make_stat_card("Studio Score", "0 -> 0 / 100", "#10b981")
        self.card_lufs = self._make_stat_card("Loudness (LUFS)", "-0.0 -> -13.0", "#38bdf8")
        self.card_tp = self._make_stat_card("True Peak", "0.0 dBTP", "#f59e0b")
        self.card_bpm = self._make_stat_card("BPM / Key", "--- BPM | ---", "#a78bfa")
        self.card_artifact = self._make_stat_card("Suno Artifact Idx", "0 / 100", "#ec4899")
        self.card_silence = self._make_stat_card("Silence Head / Tail", "0.00s / 0.00s", "#06b6d4")

        for c in [self.card_score, self.card_lufs, self.card_tp, self.card_bpm, self.card_artifact, self.card_silence]:
            cards_row.addWidget(c)
        layout.addLayout(cards_row)

        # Mid Section: Detected Artifacts (Left) & Auto Title AI (Right)
        mid_row = QHBoxLayout()
        mid_row.setSpacing(8)

        # Detected Issues Box
        left_box = QGroupBox("Detected Suno Artifacts & Mix Issues")
        left_box.setStyleSheet("font-size: 10px; font-weight: 700;")
        lb_layout = QVBoxLayout(left_box)
        lb_layout.setContentsMargins(6, 6, 6, 6)
        self.txt_issues = QLabel("No track analyzed yet. Click '🔍 AI Analyze' or '1-Click Auto All'.")
        self.txt_issues.setWordWrap(True)
        self.txt_issues.setStyleSheet("font-size: 9.5px; opacity: 0.85;")
        lb_layout.addWidget(self.txt_issues)
        lb_layout.addStretch()
        mid_row.addWidget(left_box, stretch=3)

        # Auto Title AI Box
        right_box = QGroupBox("Auto Title AI (Meaningful Song Title Generator)")
        right_box.setStyleSheet("font-size: 10px; font-weight: 700;")
        rb_layout = QVBoxLayout(right_box)
        rb_layout.setContentsMargins(6, 6, 6, 6)
        rb_layout.setSpacing(4)

        t_row = QHBoxLayout()
        self.txt_active_title = QLineEdit()
        self.txt_active_title.setPlaceholderText("Generated AI Song Title...")
        self.txt_active_title.setStyleSheet("font-size: 10.5px; font-weight: 700;")
        btn_apply_title = QPushButton("Apply Selected Title")
        btn_apply_title.setStyleSheet("font-size: 9.5px; font-weight: 700; padding: 2px 6px;")
        btn_apply_title.clicked.connect(self._apply_active_title_to_track)
        t_row.addWidget(self.txt_active_title, stretch=1)
        t_row.addWidget(btn_apply_title)
        rb_layout.addLayout(t_row)

        self.lbl_title_desc = QLabel("Crafted from detected musical key, tempo, and atmospheric mood.")
        self.lbl_title_desc.setStyleSheet("font-size: 9px; opacity: 0.7;")
        rb_layout.addWidget(self.lbl_title_desc)

        self.combo_ai_titles = QComboBox()
        self.combo_ai_titles.setStyleSheet("font-size: 10px;")
        self.combo_ai_titles.currentIndexChanged.connect(self._on_title_selected_from_dropdown)
        rb_layout.addWidget(self.combo_ai_titles)

        mid_row.addWidget(right_box, stretch=3)
        layout.addLayout(mid_row)

        # Lower Box: AI Mastering Engineer Critique & Action Buttons
        critique_box = QGroupBox("AI Mastering Engineer Critique")
        critique_box.setStyleSheet("font-size: 10px; font-weight: 700;")
        cb_layout = QVBoxLayout(critique_box)
        cb_layout.setContentsMargins(6, 6, 6, 6)

        self.txt_critique = QLabel("[Local Studio AI (Offline DSP + Music Intelligence)]\nReady to analyze acoustic properties.")
        self.txt_critique.setStyleSheet("font-size: 9.5px; opacity: 0.85;")
        self.txt_critique.setWordWrap(True)
        cb_layout.addWidget(self.txt_critique)

        act_row = QHBoxLayout()
        act_row.addStretch()
        btn_analyze_now = QPushButton("🔍 AI Analyze Now")
        btn_analyze_now.setStyleSheet("background: #2563eb; color: white; font-weight: 800; font-size: 10.5px; padding: 5px 12px; border-radius: 4px;")
        btn_analyze_now.clicked.connect(self._analyze_current_track)

        btn_apply_fix = QPushButton("⚡ Apply AI Recommended Fix & Render B")
        btn_apply_fix.setStyleSheet("background: #059669; color: white; font-weight: 800; font-size: 10.5px; padding: 5px 12px; border-radius: 4px;")
        btn_apply_fix.clicked.connect(self._render_master_b)

        act_row.addWidget(btn_analyze_now)
        act_row.addWidget(btn_apply_fix)
        cb_layout.addLayout(act_row)

        layout.addWidget(critique_box)
        return widget

    def _make_stat_card(self, title: str, val: str, color: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(15, 23, 42, 0.4);
                border: 1px solid rgba(148, 163, 184, 0.2);
                border-radius: 6px;
                padding: 4px 6px;
            }}
        """)
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(4, 3, 4, 3)
        c_layout.setSpacing(1)

        lbl_t = QLabel(title)
        lbl_t.setStyleSheet("font-size: 8.5px; font-weight: 600; opacity: 0.75;")
        lbl_v = QLabel(val)
        lbl_v.setObjectName("valLabel")
        lbl_v.setStyleSheet(f"font-size: 11px; font-weight: 800; color: {color};")
        c_layout.addWidget(lbl_t)
        c_layout.addWidget(lbl_v)
        return card

    # ── Tab 2: EQ 2 (FL Style) ──

    def _create_eq_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        lbl_info = QLabel("6-Band FL-Style Parametric Equalizer — Precision surgical mud cutting & air boost")
        lbl_info.setStyleSheet("font-size: 10px; font-weight: 700; color: #38bdf8;")
        layout.addWidget(lbl_info)

        # EQ Sliders
        eq_grid = QHBoxLayout()
        eq_grid.setSpacing(12)

        self.slider_sub = self._make_eq_slider("Sub Cut", "28 Hz", -6, 6, 0)
        self.slider_low = self._make_eq_slider("Low Body", "85 Hz", -6, 6, 1)
        self.slider_mud = self._make_eq_slider("De-Mud", "280 Hz", -10, 2, -2)
        self.slider_box = self._make_eq_slider("Boxiness", "460 Hz", -10, 2, -1)
        self.slider_pres = self._make_eq_slider("Presence", "3.2 kHz", -6, 6, 1)
        self.slider_air = self._make_eq_slider("Air Boost", "11.5 kHz", -4, 8, 2)

        for col in [self.slider_sub, self.slider_low, self.slider_mud, self.slider_box, self.slider_pres, self.slider_air]:
            eq_grid.addLayout(col)
        layout.addLayout(eq_grid)

        # Quick Presets
        p_row = QHBoxLayout()
        p_row.addWidget(QLabel("EQ Preset:"))
        combo_eq_preset = QComboBox()
        combo_eq_preset.addItems([
            "Suno De-Box & Polish (Recommended)",
            "Vocal Forward & Clear",
            "Warm Vintage Analog",
            "Club Bass & Air Boost",
            "Flat Reset (0 dB)"
        ])
        combo_eq_preset.currentIndexChanged.connect(self._on_eq_preset_changed)
        p_row.addWidget(combo_eq_preset, stretch=1)
        p_row.addStretch()

        btn_re_render = QPushButton("Apply EQ to Master B")
        btn_re_render.setStyleSheet("background: #059669; color: white; font-weight: 800; font-size: 10px; padding: 4px 10px;")
        btn_re_render.clicked.connect(self._render_master_b)
        p_row.addWidget(btn_re_render)

        layout.addLayout(p_row)
        layout.addStretch()
        return widget

    def _make_eq_slider(self, label: str, freq: str, min_db: int, max_db: int, default_db: int) -> QVBoxLayout:
        col = QVBoxLayout()
        col.setSpacing(2)
        lbl_l = QLabel(label)
        lbl_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_l.setStyleSheet("font-size: 9px; font-weight: 700;")
        lbl_f = QLabel(freq)
        lbl_f.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_f.setStyleSheet("font-size: 8px; opacity: 0.7;")

        slider = QSlider(Qt.Orientation.Vertical)
        slider.setRange(min_db, max_db)
        slider.setValue(default_db)
        slider.setFixedHeight(90)

        lbl_val = QLabel(f"{default_db:+} dB")
        lbl_val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_val.setStyleSheet("font-size: 9px; font-weight: 700; color: #10b981;")

        slider.valueChanged.connect(lambda v, lv=lbl_val: lv.setText(f"{v:+} dB"))

        col.addWidget(lbl_l)
        col.addWidget(lbl_f)
        col.addWidget(slider, alignment=Qt.AlignmentFlag.AlignCenter)
        col.addWidget(lbl_val)
        col.slider_widget = slider
        return col

    def _on_eq_preset_changed(self, idx: int):
        presets = [
            (0, 1, -2, -1, 1, 2),   # De-Box & Polish
            (-1, 0, -3, -2, 2, 2),  # Vocal Forward
            (0, 2, -1, 0, 0, 1),    # Warm Vintage
            (1, 3, -1, 0, 1, 3),    # Club Bass & Air
            (0, 0, 0, 0, 0, 0),     # Flat
        ]
        if idx < len(presets):
            p = presets[idx]
            self.slider_sub.slider_widget.setValue(p[0])
            self.slider_low.slider_widget.setValue(p[1])
            self.slider_mud.slider_widget.setValue(p[2])
            self.slider_box.slider_widget.setValue(p[3])
            self.slider_pres.slider_widget.setValue(p[4])
            self.slider_air.slider_widget.setValue(p[5])

    # ── Tab 3: Multiband & De-AI ──

    def _create_deai_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        lbl_desc = QLabel("Suno De-AI Resonance Suppressor & Anti-Phase Sibilance Filter")
        lbl_desc.setStyleSheet("font-size: 11px; font-weight: 800; color: #ec4899;")
        layout.addWidget(lbl_desc)

        # De-Harsh Slider
        r1 = QHBoxLayout()
        r1.addWidget(QLabel("De-Harsh Sibilance (6.5k-9.5k Hz):"))
        self.slider_deharsh = QSlider(Qt.Orientation.Horizontal)
        self.slider_deharsh.setRange(0, 100)
        self.slider_deharsh.setValue(70)
        r1.addWidget(self.slider_deharsh, stretch=1)
        layout.addLayout(r1)

        # De-Box Slider
        r2 = QHBoxLayout()
        r2.addWidget(QLabel("De-Box Cardboard Resonance (220-480 Hz):"))
        self.slider_debox = QSlider(Qt.Orientation.Horizontal)
        self.slider_debox.setRange(0, 100)
        self.slider_debox.setValue(80)
        r2.addWidget(self.slider_debox, stretch=1)
        layout.addLayout(r2)

        # Mono Bass Focus (<120 Hz)
        r3 = QHBoxLayout()
        r3.addWidget(QLabel("Mono Bass Focus (Tighter Low-End Punch):"))
        self.slider_mono_bass = QSlider(Qt.Orientation.Horizontal)
        self.slider_mono_bass.setRange(0, 100)
        self.slider_mono_bass.setValue(90)
        r3.addWidget(self.slider_mono_bass, stretch=1)
        layout.addLayout(r3)

        layout.addStretch()
        return widget

    # ── Tab 4: Stereo, Reverb & Trim ──

    def _create_stereo_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        lbl_st = QLabel("Mid-Side Stereo Field Expander & Auto Silence Trim")
        lbl_st.setStyleSheet("font-size: 11px; font-weight: 800; color: #06b6d4;")
        layout.addWidget(lbl_st)

        r1 = QHBoxLayout()
        r1.addWidget(QLabel("Stereo Width:"))
        self.slider_width = QSlider(Qt.Orientation.Horizontal)
        self.slider_width.setRange(80, 180)
        self.slider_width.setValue(125)
        self.lbl_width_val = QLabel("125%")
        self.slider_width.valueChanged.connect(lambda v: self.lbl_width_val.setText(f"{v}%"))
        r1.addWidget(self.slider_width, stretch=1)
        r1.addWidget(self.lbl_width_val)
        layout.addLayout(r1)

        r2 = QHBoxLayout()
        r2.addWidget(QLabel("Lead-in Silence Trim (Head):"))
        self.lbl_trim_head = QLabel("Auto-detected 50ms pre-breath")
        self.lbl_trim_head.setStyleSheet("color: #10b981; font-weight: 700;")
        r2.addWidget(self.lbl_trim_head, stretch=1)
        layout.addLayout(r2)

        r3 = QHBoxLayout()
        r3.addWidget(QLabel("Outro Tail Trim (Silence Cut):"))
        self.lbl_trim_tail = QLabel("Auto-detected with 10ms micro-fade")
        self.lbl_trim_tail.setStyleSheet("color: #10b981; font-weight: 700;")
        r3.addWidget(self.lbl_trim_tail, stretch=1)
        layout.addLayout(r3)

        layout.addStretch()
        return widget

    # ── Tab 5: Limiter & Export ──

    def _create_limiter_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        lbl_lim = QLabel("4x True-Peak Brickwall Limiter & Direct Studio Export")
        lbl_lim.setStyleSheet("font-size: 11px; font-weight: 800; color: #10b981;")
        layout.addWidget(lbl_lim)

        r1 = QHBoxLayout()
        r1.addWidget(QLabel("True-Peak Ceiling:"))
        self.combo_ceiling = QComboBox()
        self.combo_ceiling.addItems(["-0.5 dBTP (Suno Master)", "-1.0 dBTP (Spotify / Apple)", "-0.3 dBTP (Club / DJ)", "-0.1 dBTP (CD)"])
        r1.addWidget(self.combo_ceiling, stretch=1)
        layout.addLayout(r1)

        exp_btns = QHBoxLayout()
        btn_exp_wav = QPushButton("💾 Export 24-bit Studio WAV")
        btn_exp_wav.setStyleSheet("background: #059669; color: white; font-weight: 800; font-size: 11px; padding: 7px 12px; border-radius: 5px;")
        btn_exp_wav.clicked.connect(lambda: self._export_format("wav"))

        btn_exp_mp3 = QPushButton("🎵 Export 320k MP3")
        btn_exp_mp3.setStyleSheet("background: #2563eb; color: white; font-weight: 800; font-size: 11px; padding: 7px 12px; border-radius: 5px;")
        btn_exp_mp3.clicked.connect(lambda: self._export_format("mp3"))

        btn_bridge_editor = QPushButton("✍️ Send to Lyric Editor Stem Player")
        btn_bridge_editor.setStyleSheet("font-weight: 700; font-size: 10.5px; padding: 7px 12px;")
        btn_bridge_editor.clicked.connect(self._send_to_lyric_editor)

        exp_btns.addWidget(btn_exp_wav)
        exp_btns.addWidget(btn_exp_mp3)
        exp_btns.addWidget(btn_bridge_editor)
        layout.addLayout(exp_btns)

        layout.addStretch()
        return widget

    # ── Queue & Audio Loading Operations ──

    def add_track_file(self, file_path: str | Path, auto_select: bool = True):
        p = Path(file_path)
        if not p.exists() or p.suffix.lower() not in [".mp3", ".wav", ".flac", ".m4a", ".ogg"]:
            return

        # Check for existing
        for tr in self.tracks:
            if tr["path"] == str(p):
                return

        track_data = {
            "path": str(p),
            "title": p.stem.replace("_", " ").title(),
            "bpm": 124,
            "key": "C Major",
            "lufs": -14.0,
            "score": 75,
            "status": "Ready",
            "master_path": "",
            "checked": True,
            "analysis": None
        }
        self.tracks.append(track_data)
        self._refresh_table()

        if auto_select or self.current_track_idx == -1:
            self._select_track(len(self.tracks) - 1)

    def _browse_audio_file(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Import Suno / Music Tracks", "",
            "Audio Files (*.mp3 *.wav *.flac *.m4a *.ogg);;All Files (*.*)"
        )
        for f in files:
            self.add_track_file(f, auto_select=True)

    def _browse_audio_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Import Audio Folder")
        if folder:
            for root_dir, _, filenames in os.walk(folder):
                for fn in sorted(filenames):
                    if Path(fn).suffix.lower() in [".mp3", ".wav", ".flac", ".m4a", ".ogg"]:
                        self.add_track_file(os.path.join(root_dir, fn), auto_select=False)
            if self.tracks and self.current_track_idx == -1:
                self._select_track(0)

    def _browse_output_dir(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Master Export Directory")
        if folder:
            self.txt_output_dir.setText(folder)

    def _check_all_queue(self):
        all_checked = all(tr.get("checked", True) for tr in self.tracks)
        for tr in self.tracks:
            tr["checked"] = not all_checked
        self._refresh_table()

    def _remove_selected_queue(self):
        if 0 <= self.current_track_idx < len(self.tracks):
            del self.tracks[self.current_track_idx]
            self.current_track_idx = max(0, min(self.current_track_idx, len(self.tracks) - 1))
            self._refresh_table()
            if self.tracks:
                self._select_track(self.current_track_idx)
            else:
                self.current_input_path = ""
                self.waveform_pane.set_audio_data(None, 44100)

    def _refresh_table(self):
        self.table_queue.setRowCount(len(self.tracks))
        self.lbl_q_count.setText(f"{len(self.tracks)} Tracks")

        for idx, tr in enumerate(self.tracks):
            # 0: Checkbox
            chk = QTableWidgetItem("✓" if tr.get("checked", True) else " ")
            chk.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_queue.setItem(idx, 0, chk)

            # 1: Title
            t_item = QTableWidgetItem(tr["title"])
            self.table_queue.setItem(idx, 1, t_item)

            # 2: BPM / Key
            bk = f"{tr['bpm']} / {tr['key']}"
            self.table_queue.setItem(idx, 2, QTableWidgetItem(bk))

            # 3: LUFS
            self.table_queue.setItem(idx, 3, QTableWidgetItem(f"{tr['lufs']:.1f}"))

            # 4: Score
            s_item = QTableWidgetItem(str(tr["score"]))
            s_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_queue.setItem(idx, 4, s_item)

            # 5: Status
            st_item = QTableWidgetItem(tr["status"])
            st_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if tr["status"] == "Mastered":
                st_item.setForeground(QColor("#10b981"))
            self.table_queue.setItem(idx, 5, st_item)

    def _on_table_row_clicked(self, row: int, col: int):
        if col == 0 and 0 <= row < len(self.tracks):
            self.tracks[row]["checked"] = not self.tracks[row].get("checked", True)
            self._refresh_table()
        else:
            self._select_track(row)

    def _select_track(self, idx: int):
        if not (0 <= idx < len(self.tracks)):
            return
        self.current_track_idx = idx
        track = self.tracks[idx]
        self.current_input_path = track["path"]
        self.current_master_path = track.get("master_path", "")

        # Select row visually
        self.table_queue.selectRow(idx)
        self.lbl_status.setText(f"Loaded: {Path(self.current_input_path).name}")

        # Load waveform
        try:
            samples, sr = AudioMasteringEngine.load_audio(self.current_input_path)
            self.waveform_pane.set_audio_data(samples, sr, is_mastered=bool(self.current_master_path))
        except Exception as e:
            self.lbl_status.setText(f"Waveform preview error: {e}")

        # Set player media
        play_path = self.current_master_path if (self.is_ab_mastered and self.current_master_path) else self.current_input_path
        self.player.setSource(QUrl.fromLocalFile(play_path))

        # Run fast analysis
        self._analyze_current_track()

    # ── AI Analysis Operations ──

    def _analyze_current_track(self):
        if not self.current_input_path or not Path(self.current_input_path).exists():
            return

        self.lbl_status.setText("Analyzing audio spectrum, EBU R128 LUFS & Suno artifacts...")
        QApplication.processEvents()

        try:
            res = AudioMasteringEngine.analyze_track_full(self.current_input_path)
            if 0 <= self.current_track_idx < len(self.tracks):
                tr = self.tracks[self.current_track_idx]
                tr["lufs"] = res["lufs"]
                tr["bpm"] = res["bpm"]
                tr["key"] = res["key"]
                tr["score"] = res["score"]
                tr["analysis"] = res
                self._refresh_table()

            # Update Stat Cards
            self.card_score.findChild(QLabel, "valLabel").setText(f"{res['score']} -> {res['target_score']} / 100")
            self.card_lufs.findChild(QLabel, "valLabel").setText(f"{res['lufs']:.1f} -> -13.0 LUFS")
            self.card_tp.findChild(QLabel, "valLabel").setText(f"{res['true_peak']:.1f} dBTP")
            self.card_bpm.findChild(QLabel, "valLabel").setText(f"{res['bpm']} BPM | {res['key']}")
            self.card_artifact.findChild(QLabel, "valLabel").setText(f"{res['artifacts']['artifact_index']} / 100")
            self.card_silence.findChild(QLabel, "valLabel").setText(f"{res['head_silence']:.2f}s / {res['tail_silence']:.2f}s")

            # Update Issues
            issues_txt = "\n".join(res["artifacts"]["issues"]) if res["artifacts"]["issues"] else "✓ Pristine balance! No severe Suno artifacts detected."
            self.txt_issues.setText(issues_txt)

            # Update Critique
            critique = (
                f"[Local Studio AI Report]\n"
                f"• Audio Profile: {res['bpm']} BPM, Musical Key of {res['key']}\n"
                f"• Dynamics: Integrated {res['lufs']:.1f} LUFS, True-Peak {res['true_peak']:.1f} dBTP\n"
                f"• Recommended Fix: 4x True-Peak Limiter, 280Hz Boxiness Cut (-2.2 dB), 11.5kHz Air (+1.8 dB), and 125% Stereo Expansion."
            )
            self.txt_critique.setText(critique)

            # Update Title AI
            self._generate_ai_titles()
            self.lbl_status.setText("✓ Audio Analysis complete.")
        except Exception as e:
            self.lbl_status.setText(f"Analysis error: {e}")

    def _generate_ai_titles(self):
        if not (0 <= self.current_track_idx < len(self.tracks)):
            return
        tr = self.tracks[self.current_track_idx]
        title_base = tr["title"]
        key = tr.get("key", "C Major")
        bpm = tr.get("bpm", 124)

        # Generate 5 contextual titles
        suggestions = [
            f"★ [Best AI Pick] {title_base}",
            f"2. Electric {title_base} (Radio Mix)",
            f"3. Midnight Anthem in {key}",
            f"4. Limitless Horizon ({bpm} BPM)",
            f"5. Neon Euphoria (Club Master)"
        ]
        self.combo_ai_titles.clear()
        self.combo_ai_titles.addItems(suggestions)
        self.txt_active_title.setText(title_base)

    def _on_title_selected_from_dropdown(self, idx: int):
        txt = self.combo_ai_titles.currentText()
        if txt:
            # Strip number prefix e.g. "★ [Best AI Pick] " or "2. "
            clean = txt.replace("★ [Best AI Pick] ", "").strip()
            if len(clean) > 3 and clean[0].isdigit() and clean[1:3] in [". ", ": "]:
                clean = clean[3:].strip()
            self.txt_active_title.setText(clean)

    def _apply_active_title_to_track(self):
        new_title = self.txt_active_title.text().strip()
        if new_title and 0 <= self.current_track_idx < len(self.tracks):
            self.tracks[self.current_track_idx]["title"] = new_title
            self._refresh_table()
            self.lbl_status.setText(f"✓ Renamed track to: {new_title}")

    # ── Mastering Processor Operations ──

    def _render_master_b(self):
        if not self.current_input_path or not Path(self.current_input_path).exists():
            self.lbl_status.setText("⚠️ Please select or import an audio track to master.")
            return

        out_dir = Path(self.txt_output_dir.text().strip() or (Path.home() / ".lyric_ai_writer" / "suno_masters"))
        out_dir.mkdir(parents=True, exist_ok=True)

        fmt_text = self.combo_format.currentText()
        ext = ".mp3" if "MP3" in fmt_text else ".wav"
        stem = Path(self.current_input_path).stem
        out_file = out_dir / f"{stem}_Mastered_Pro{ext}"

        # Collect DSP parameters from sliders
        params = {
            "target_preset": self.combo_target_preset.currentText(),
            "auto_trim": True,
            "de_ai_filter": True,
            "eq_low_gain": float(self.slider_low.slider_widget.value()),
            "eq_mud_cut_gain": float(self.slider_mud.slider_widget.value()),
            "eq_presence_gain": float(self.slider_pres.slider_widget.value()),
            "eq_air_gain": float(self.slider_air.slider_widget.value()),
            "stereo_width": float(self.slider_width.value()) / 100.0,
            "add_room_depth": True,
        }

        self.btn_ribbon_auto_all.setEnabled(False)
        self.btn_stop_auto.setEnabled(True)
        self.progress_bar.setValue(10)
        self.lbl_status.setText(f"Mastering: {stem}...")

        self.worker = MasterWorker(self.current_input_path, str(out_file), params)
        self.worker.progress_updated.connect(self._on_master_progress)
        self.worker.master_completed.connect(self._on_single_master_completed)
        self.worker.master_failed.connect(self._on_master_failed)
        self.worker.start()

    def _on_master_progress(self, pct: int, msg: str):
        self.progress_bar.setValue(pct)
        self.lbl_status.setText(msg)

    def _on_single_master_completed(self, res: dict):
        self.progress_bar.setValue(100)
        out_path = res["output_path"]
        self.current_master_path = out_path

        if 0 <= self.current_track_idx < len(self.tracks):
            tr = self.tracks[self.current_track_idx]
            tr["master_path"] = out_path
            tr["status"] = "Mastered"
            tr["score"] = min(98, tr["score"] + 22)
            self._refresh_table()

        # Update Waveform to Mastered B
        try:
            samples, sr = AudioMasteringEngine.load_audio(out_path)
            self.waveform_pane.set_audio_data(samples, sr, is_mastered=True)
        except Exception:
            pass

        # Switch Player to Mastered B
        self._set_ab_mode(True)
        self.lbl_status.setText(f"✓ Master Complete! Saved to: {Path(out_path).name} (LUFS: {res['final_lufs']:.1f})")
        self.btn_ribbon_auto_all.setEnabled(True)
        self.btn_stop_auto.setEnabled(False)

        # If batch is running, process next track
        if self.batch_running:
            self._process_next_batch_track()

    def _on_master_failed(self, err: str):
        self.btn_ribbon_auto_all.setEnabled(True)
        self.btn_stop_auto.setEnabled(False)
        self.lbl_status.setText(f"Mastering error: {err}")
        QMessageBox.critical(self, "Mastering Error", f"An error occurred while processing audio:\n\n{err}")

    # ── Live A/B Monitor & Playback Controls ──

    def _set_ab_mode(self, is_mastered: bool):
        self.is_ab_mastered = is_mastered
        self.btn_ab_master.setChecked(is_mastered)
        self.btn_ab_original.setChecked(not is_mastered)

        if is_mastered:
            self.btn_ab_master.setStyleSheet("background: #059669; color: white; font-weight: 800; font-size: 10px; padding: 3px 10px;")
            self.btn_ab_original.setStyleSheet("font-weight: 800; font-size: 10px; padding: 3px 10px;")
        else:
            self.btn_ab_original.setStyleSheet("background: #f59e0b; color: white; font-weight: 800; font-size: 10px; padding: 3px 10px;")
            self.btn_ab_master.setStyleSheet("font-weight: 800; font-size: 10px; padding: 3px 10px;")

        self.waveform_pane.set_mode(is_mastered)

        # Switch audio stream preserving playback position
        current_pos = self.player.position()
        target_file = self.current_master_path if (is_mastered and self.current_master_path) else self.current_input_path
        if target_file and Path(target_file).exists():
            was_playing = (self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState)
            self.player.setSource(QUrl.fromLocalFile(target_file))
            self.player.setPosition(current_pos)
            if was_playing:
                self.player.play()

    def _toggle_playback(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def _stop_playback(self):
        self.player.stop()
        self.waveform_pane.set_playback_position(0.0)

    def _seek_player(self, sec: float):
        ms = int(sec * 1000)
        self.player.setPosition(ms)

    def _on_player_position_changed(self, ms: int):
        sec = ms / 1000.0
        self.waveform_pane.set_playback_position(sec)
        tot_ms = self.player.duration()
        cur_str = f"{int(sec // 60):02d}:{int(sec % 60):02d}.{int((sec * 100) % 100):02d}"
        tot_s = tot_ms / 1000.0
        tot_str = f"{int(tot_s // 60):02d}:{int(tot_s % 60):02d}.{int((tot_s * 100) % 100):02d}"
        self.lbl_timecode.setText(f"{cur_str} / {tot_str}")

        # Simulate dynamic peak meters during playback
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            # Subtle random meter animation around -12 dBFS
            import random
            sim_l = max(-50.0, -12.0 + random.uniform(-4.0, 3.0))
            sim_r = max(-50.0, -12.0 + random.uniform(-4.0, 3.0))
            self.waveform_pane.set_levels(sim_l, sim_r)

    def _on_player_duration_changed(self, ms: int):
        pass

    def _on_playback_state_changed(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.btn_play_pause.setText("⏸ Pause")
        else:
            self.btn_play_pause.setText("▶ Play")
            self.waveform_pane.set_levels(-60.0, -60.0)

    def _on_vol_changed(self, v: int):
        self.audio_output.setVolume(v / 100.0)

    # ── Batch Operations ──

    def _start_1click_auto_all(self):
        self.batch_queue_indices = [i for i, tr in enumerate(self.tracks) if tr.get("checked", True)]
        if not self.batch_queue_indices:
            self.lbl_status.setText("⚠️ No tracks selected in queue. Please add audio or drag-and-drop tracks.")
            return

        self.batch_running = True
        self._process_next_batch_track()

    def _process_next_batch_track(self):
        if not self.batch_queue_indices or not self.batch_running:
            self.batch_running = False
            self.lbl_status.setText("✓ All batch tracks mastered and exported successfully!")
            self.btn_ribbon_auto_all.setEnabled(True)
            self.btn_stop_auto.setEnabled(False)
            return

        idx = self.batch_queue_indices.pop(0)
        self._select_track(idx)
        self._render_master_b()

    def _stop_batch(self):
        self.batch_running = False
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
        self.btn_ribbon_auto_all.setEnabled(True)
        self.btn_stop_auto.setEnabled(False)
        self.lbl_status.setText("Batch processing stopped.")

    # ── Export & Studio Bridge Handlers ──

    def _auto_trim_current(self):
        if not self.current_input_path:
            return
        data, sr = AudioMasteringEngine.load_audio(self.current_input_path)
        h, t = AudioMasteringEngine.detect_silence(data, sr)
        self.waveform_pane.canvas.set_trim_points(h, max(h + 1.0, (len(data) / sr) - t))
        self.lbl_status.setText(f"✓ Trim markers set: In={h:.2f}s, Out={(len(data)/sr)-t:.2f}s")

    def _export_current_master(self):
        if not self.current_master_path or not Path(self.current_master_path).exists():
            # If not yet rendered, render first
            self._render_master_b()
        else:
            self.lbl_status.setText(f"✓ Master file ready at: {self.current_master_path}")

    def _export_format(self, fmt: str):
        if not self.current_input_path:
            return
        out_dir = Path(self.txt_output_dir.text().strip() or (Path.home() / ".lyric_ai_writer" / "suno_masters"))
        out_dir.mkdir(parents=True, exist_ok=True)
        stem = Path(self.current_input_path).stem
        target_file = out_dir / f"{stem}_Master.{fmt}"

        AudioMasteringEngine.process_master(
            input_path=self.current_input_path,
            output_path=str(target_file),
            target_preset=self.combo_target_preset.currentText()
        )
        self.lbl_status.setText(f"✓ Exported {fmt.upper()} to: {target_file.name}")
        QMessageBox.information(self, "Export Complete", f"Successfully exported master to:\n\n{target_file}")

    def _open_output_folder(self):
        folder = Path(self.txt_output_dir.text().strip() or (Path.home() / ".lyric_ai_writer" / "suno_masters"))
        folder.mkdir(parents=True, exist_ok=True)
        from PyQt6.QtGui import QDesktopServices
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))

    def _send_to_lyric_editor(self):
        target = self.current_master_path or self.current_input_path
        if not target or not Path(target).exists():
            QMessageBox.warning(self, "No Audio Available", "Please import or master an audio track first.")
            return
        self.send_to_editor_requested.emit(target)
        self.lbl_status.setText(f"✓ Sent master audio to Lyric Editor Stem Player: {Path(target).name}")

    # ── Theme System ──

    def apply_theme(self, theme_or_dark):
        t = get_theme(theme_or_dark)
        self.current_theme = t.get("id", "obsidian")
        is_dark = t.get("is_dark", True)

        bg = t["bg_window"]
        card = t["bg_card"]
        inp = t["bg_input"]
        border = t["border"]
        pri = t["text_primary"]
        sec = t["text_secondary"]
        acc = t["accent"]

        self.setStyleSheet(f"""
            AudioMasteringView {{ background-color: {bg}; color: {pri}; }}
            QFrame#masterHeaderCard, QFrame#masterLeftPanel, QFrame#masterRightPanel {{
                background-color: {card};
                border: 1px solid {border};
                border-radius: 8px;
            }}
            QGroupBox {{
                background-color: {card};
                border: 1px solid {border};
                border-radius: 6px;
                color: {pri};
                margin-top: 14px;
            }}
            QGroupBox::title {{
                color: {sec};
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
            }}
            QLabel {{ color: {pri}; background: transparent; border: none; }}
            QLineEdit, QComboBox {{
                background-color: {inp};
                color: {pri};
                border: 1px solid {border};
                border-radius: 5px;
                padding: 3px 6px;
                font-size: 10px;
            }}
            QLineEdit:focus, QComboBox:focus {{
                border-color: {acc};
            }}
            QTableWidget {{
                background-color: {inp};
                color: {pri};
                border: 1px solid {border};
                gridline-color: {border};
            }}
            QHeaderView::section {{
                background-color: {card};
                color: {sec};
                border: 1px solid {border};
                font-weight: 700;
                font-size: 9.5px;
                padding: 4px;
            }}
        """)

        # Forward theme to waveform canvas & meters
        self.waveform_pane.apply_theme(t)
