"""
Suno Downloader Studio Dialog:
Inspired by UseSuno (usesuno.com/tools/downloader).
Download any public Suno song or Hook as MP3, Lossless Studio WAV, Original audio stream,
MP4 video, or HD cover art. Decryption, audio decoding, and format conversion complete 100% locally.
Supports Single Track / Hook mode, Bulk Downloader (up to 20 links), and Suno Playlist / Album extraction.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QProgressBar, QFrame, QTextEdit, QFileDialog, QApplication,
    QMessageBox, QTabWidget, QWidget, QSplitter, QTableWidget, QTableWidgetItem,
    QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal, QUrl, QTimer
from PyQt6.QtGui import QIcon, QDesktopServices, QPixmap
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

from app.suno_downloader import SunoLinkParser, SunoDownloadWorker, SunoBulkDownloadWorker, SunoAudioConverter
from app.ui.styles import get_theme


class SunoLinkDownloadDialog(QDialog):
    """Studio Suno Downloader dialog matching usesuno.com/tools/downloader feature set."""

    load_into_editor_requested = pyqtSignal(str)  # audio_path
    import_lyrics_requested = pyqtSignal(str, str)  # title, lyrics
    send_to_visual_requested = pyqtSignal(dict)  # formula/tags

    def __init__(self, parent=None, theme_key: str = "obsidian", initial_url: str = ""):
        super().__init__(parent)
        self.theme_key = theme_key
        self.download_worker: Optional[SunoDownloadWorker] = None
        self.bulk_worker: Optional[SunoBulkDownloadWorker] = None
        self.last_downloaded_path: str = ""
        self.current_metadata: Dict = {}

        # Audio preview player for auditioning stream before/after download
        self.preview_player = QMediaPlayer()
        self.preview_audio_output = QAudioOutput()
        self.preview_player.setAudioOutput(self.preview_audio_output)
        self.preview_player.playbackStateChanged.connect(self._on_preview_state_changed)

        self.setWindowTitle("📥 Suno Music Downloader — MP3, WAV, Original Audio, Video & Art")
        self.resize(720, 640)
        self.setMinimumSize(660, 560)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        self._init_ui()
        self.apply_theme(theme_key)

        if initial_url:
            self.txt_url.setText(initial_url)
            QTimer.singleShot(150, self._inspect_link)
        else:
            self._auto_paste_clipboard()

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(10)

        # ── 1. Top Header (UseSuno Brand styling) ──
        header_row = QHBoxLayout()
        header_row.setSpacing(10)

        lbl_logo = QLabel("🎵")
        lbl_logo.setStyleSheet("font-size: 26px;")
        header_row.addWidget(lbl_logo)

        h_col = QVBoxLayout()
        h_col.setSpacing(1)
        self.lbl_head_title = QLabel("Suno Downloader Studio — MP3, Lossless WAV & MP4")
        self.lbl_head_title.setStyleSheet("font-size: 15px; font-weight: 800;")
        h_col.addWidget(self.lbl_head_title)

        self.lbl_head_sub = QLabel("Download any public Suno song or Hook as MP3, WAV, original audio, MP4 video or cover art. 100% local conversion.")
        self.lbl_head_sub.setStyleSheet("font-size: 10.5px; color: #94a3b8;")
        h_col.addWidget(self.lbl_head_sub)
        header_row.addLayout(h_col)
        header_row.addStretch(1)

        # Destination Folder Pill
        dest_pill = QHBoxLayout()
        dest_pill.setSpacing(4)
        self.lbl_dest_display = QLabel("📂 ~/.lyric_ai_writer/suno_downloads/")
        self.lbl_dest_display.setStyleSheet("font-size: 9.5px; color: #94a3b8; font-family: monospace;")
        dest_pill.addWidget(self.lbl_dest_display)

        self.btn_change_dest = QPushButton("📁")
        self.btn_change_dest.setFixedSize(26, 24)
        self.btn_change_dest.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_change_dest.setToolTip("Change save directory")
        self.btn_change_dest.clicked.connect(self._browse_dest_folder)
        dest_pill.addWidget(self.btn_change_dest)
        header_row.addLayout(dest_pill)

        root.addLayout(header_row)

        # ── 2. Mode Tabs (Single Song / Hook vs Bulk / Playlist) ──
        self.tabs = QTabWidget()
        self.tabs.setObjectName("sunoDlTabs")

        # Tab 1: Single Song / Hook Downloader
        self.tab_single = QWidget()
        self._init_single_tab(self.tab_single)
        self.tabs.addTab(self.tab_single, "🎵 Single Song / Hook")

        # Tab 2: Bulk / Batch Downloader (Up to 20 links)
        self.tab_bulk = QWidget()
        self._init_bulk_tab(self.tab_bulk)
        self.tabs.addTab(self.tab_bulk, "📑 Bulk Downloader (Up to 20 Links)")

        root.addWidget(self.tabs, stretch=1)

        # ── 3. Bottom Global Status & Close ──
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(8)

        self.lbl_status = QLabel("Paste any Suno song/hook link and select format to download")
        self.lbl_status.setStyleSheet("font-size: 10.5px; font-weight: 600; color: #94a3b8;")
        bottom_row.addWidget(self.lbl_status, stretch=1)

        self.btn_open_folder = QPushButton("📂 Open Folder")
        self.btn_open_folder.setFixedHeight(28)
        self.btn_open_folder.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open_folder.clicked.connect(self._open_downloads_folder)
        bottom_row.addWidget(self.btn_open_folder)

        self.btn_close = QPushButton("Close")
        self.btn_close.setFixedHeight(28)
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.clicked.connect(self._on_close)
        bottom_row.addWidget(self.btn_close)

        root.addLayout(bottom_row)

    # ── Single Song / Hook Tab UI ──
    def _init_single_tab(self, parent: QWidget):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Input Row
        input_row = QHBoxLayout()
        input_row.setSpacing(6)
        self.txt_url = QLineEdit()
        self.txt_url.setPlaceholderText("Paste Suno song or hook link (e.g. suno.com/song/..., suno.com/hook/..., or CDN)...")
        self.txt_url.setFixedHeight(34)
        self.txt_url.textChanged.connect(self._on_url_text_changed)
        self.txt_url.returnPressed.connect(lambda: self._trigger_download("mp3"))
        input_row.addWidget(self.txt_url, stretch=1)

        self.btn_paste = QPushButton("📋 Paste")
        self.btn_paste.setFixedHeight(34)
        self.btn_paste.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_paste.clicked.connect(self._paste_from_clipboard)
        input_row.addWidget(self.btn_paste)

        self.btn_inspect = QPushButton("🔍 Inspect")
        self.btn_inspect.setFixedHeight(34)
        self.btn_inspect.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_inspect.clicked.connect(self._inspect_link)
        input_row.addWidget(self.btn_inspect)
        layout.addLayout(input_row)

        # ── Responsive Song Card (Inspired by UseSuno card design) ──
        self.card_frame = QFrame()
        self.card_frame.setObjectName("sunoSongCard")
        cf_layout = QVBoxLayout(self.card_frame)
        cf_layout.setContentsMargins(12, 10, 12, 10)
        cf_layout.setSpacing(8)

        card_top = QHBoxLayout()
        card_top.setSpacing(12)

        # Artwork / Play Audition Box
        self.art_box = QFrame()
        self.art_box.setFixedSize(88, 88)
        self.art_box.setStyleSheet("background: #0f172a; border-radius: 8px; border: 1px solid #334155;")
        art_layout = QVBoxLayout(self.art_box)
        art_layout.setContentsMargins(0, 0, 0, 0)
        art_layout.setSpacing(0)

        self.lbl_art = QLabel("🎵")
        self.lbl_art.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_art.setStyleSheet("font-size: 32px;")
        art_layout.addWidget(self.lbl_art, stretch=1)

        self.btn_audition_stream = QPushButton("▶ Audition")
        self.btn_audition_stream.setFixedHeight(20)
        self.btn_audition_stream.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_audition_stream.setStyleSheet("font-size: 9px; font-weight: 700; background: rgba(0,0,0,0.7); color: #38bdf8; border: none; border-bottom-left-radius: 8px; border-bottom-right-radius: 8px;")
        self.btn_audition_stream.clicked.connect(self._toggle_stream_preview)
        art_layout.addWidget(self.btn_audition_stream)
        card_top.addWidget(self.art_box)

        # Track Info Column
        meta_col = QVBoxLayout()
        meta_col.setSpacing(3)

        title_row = QHBoxLayout()
        title_row.setSpacing(6)
        self.lbl_title = QLabel("Ready to inspect Suno track or hook")
        self.lbl_title.setStyleSheet("font-size: 13.5px; font-weight: 800;")
        title_row.addWidget(self.lbl_title, stretch=1)

        self.badge_type = QLabel("🎵 Song")
        self.badge_type.setStyleSheet("font-size: 9.5px; font-weight: 800; padding: 2px 6px; border-radius: 4px; background: #1e293b; color: #38bdf8;")
        title_row.addWidget(self.badge_type)
        meta_col.addLayout(title_row)

        self.lbl_artist = QLabel("Artist: - • Engine: Suno v4 • Duration: 0:00")
        self.lbl_artist.setStyleSheet("font-size: 10px; color: #94a3b8; font-weight: 600;")
        meta_col.addWidget(self.lbl_artist)

        self.lbl_style = QLabel("Style / Mood: -")
        self.lbl_style.setStyleSheet("font-size: 10px; color: #a855f7; font-weight: 600;")
        self.lbl_style.setWordWrap(True)
        meta_col.addWidget(self.lbl_style)

        card_top.addLayout(meta_col, stretch=1)
        cf_layout.addLayout(card_top)

        # Lyrics & Prompt Box
        self.txt_lyrics = QTextEdit()
        self.txt_lyrics.setReadOnly(True)
        self.txt_lyrics.setFixedHeight(80)
        self.txt_lyrics.setPlaceholderText("Lyrics or prompt will appear here once inspected...")
        self.txt_lyrics.setStyleSheet("font-size: 10px; font-family: 'Consolas', monospace;")
        cf_layout.addWidget(self.txt_lyrics)

        layout.addWidget(self.card_frame)

        # ── 1-Click Format Chips (Inspired by UseSuno download format options) ──
        chips_frame = QFrame()
        chips_frame.setObjectName("sunoChipsFrame")
        cp_layout = QVBoxLayout(chips_frame)
        cp_layout.setContentsMargins(8, 8, 8, 8)
        cp_layout.setSpacing(6)

        lbl_chips_head = QLabel("⚡ 1-Click Fast Download Options (Decryption & Conversion In-App):")
        lbl_chips_head.setStyleSheet("font-size: 10.5px; font-weight: 700; color: #38bdf8;")
        cp_layout.addWidget(lbl_chips_head)

        grid = QHBoxLayout()
        grid.setSpacing(6)

        self.btn_dl_mp3 = QPushButton("🎵 MP3 (320k)")
        self.btn_dl_mp3.setToolTip("Download high-quality master MP3 audio")
        self.btn_dl_mp3.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_dl_mp3.clicked.connect(lambda: self._trigger_download("mp3"))
        grid.addWidget(self.btn_dl_mp3)

        self.btn_dl_wav = QPushButton("🎚️ Lossless WAV")
        self.btn_dl_wav.setToolTip("Convert locally to pristine uncompressed PCM Studio WAV (for DAWs)")
        self.btn_dl_wav.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_dl_wav.clicked.connect(lambda: self._trigger_download("wav"))
        grid.addWidget(self.btn_dl_wav)

        self.btn_dl_orig = QPushButton("🔊 Original Stream")
        self.btn_dl_orig.setToolTip("Download untouched raw stream direct from Suno CDN")
        self.btn_dl_orig.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_dl_orig.clicked.connect(lambda: self._trigger_download("original"))
        grid.addWidget(self.btn_dl_orig)

        self.btn_dl_video = QPushButton("🎬 MP4 Video")
        self.btn_dl_video.setToolTip("Download Suno visualizer music video")
        self.btn_dl_video.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_dl_video.clicked.connect(lambda: self._trigger_download("mp4"))
        grid.addWidget(self.btn_dl_video)

        self.btn_dl_art = QPushButton("🖼️ Cover Art")
        self.btn_dl_art.setToolTip("Download full-resolution HD album cover artwork")
        self.btn_dl_art.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_dl_art.clicked.connect(lambda: self._trigger_download("png"))
        grid.addWidget(self.btn_dl_art)

        self.btn_dl_lyrics = QPushButton("📝 Lyrics .txt")
        self.btn_dl_lyrics.setToolTip("Export song lyrics with style metadata")
        self.btn_dl_lyrics.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_dl_lyrics.clicked.connect(lambda: self._trigger_download("lyrics"))
        grid.addWidget(self.btn_dl_lyrics)

        self.btn_dl_pack = QPushButton("📦 Full Pack (ZIP)")
        self.btn_dl_pack.setObjectName("accentButton")
        self.btn_dl_pack.setToolTip("Download complete production pack: MP3 + WAV + Cover Art + Lyrics")
        self.btn_dl_pack.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_dl_pack.clicked.connect(lambda: self._trigger_download("pack"))
        grid.addWidget(self.btn_dl_pack)

        cp_layout.addLayout(grid)
        layout.addWidget(chips_frame)

        # Progress bar
        self.progress_single = QProgressBar()
        self.progress_single.setFixedHeight(10)
        self.progress_single.setRange(0, 100)
        self.progress_single.setValue(0)
        self.progress_single.setTextVisible(False)
        self.progress_single.hide()
        layout.addWidget(self.progress_single)

        # Post-Download Integration Card
        self.single_post_frame = QFrame()
        self.single_post_frame.setObjectName("dlPostFrame")
        spf_layout = QHBoxLayout(self.single_post_frame)
        spf_layout.setContentsMargins(6, 4, 6, 4)
        spf_layout.setSpacing(6)

        self.btn_audition_editor = QPushButton("🎧 Audition in Lyric Editor")
        self.btn_audition_editor.setFixedHeight(27)
        self.btn_audition_editor.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_audition_editor.setToolTip("Load directly into Lyric Editor Workbench stem player")
        self.btn_audition_editor.clicked.connect(self._audition_in_editor)
        spf_layout.addWidget(self.btn_audition_editor)

        self.btn_import_lyrics = QPushButton("📝 Import Lyrics to Studio")
        self.btn_import_lyrics.setFixedHeight(27)
        self.btn_import_lyrics.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_import_lyrics.clicked.connect(self._import_lyrics)
        spf_layout.addWidget(self.btn_import_lyrics)

        self.btn_send_visual = QPushButton("🎨 Send to Visual Arranger")
        self.btn_send_visual.setFixedHeight(27)
        self.btn_send_visual.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_send_visual.clicked.connect(self._send_to_visual)
        spf_layout.addWidget(self.btn_send_visual)

        self.btn_reveal_single = QPushButton("📁 Show File")
        self.btn_reveal_single.setFixedHeight(27)
        self.btn_reveal_single.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_reveal_single.clicked.connect(self._reveal_last_file)
        spf_layout.addWidget(self.btn_reveal_single)

        self.single_post_frame.hide()
        layout.addWidget(self.single_post_frame)
        layout.addStretch(1)

    # ── Bulk / Playlist Tab UI ──
    def _init_bulk_tab(self, parent: QWidget):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        lbl_bulk_hint = QLabel("Paste up to 20 Suno song/hook links (one per line) or a Suno playlist/album URL:")
        lbl_bulk_hint.setStyleSheet("font-size: 11px; font-weight: 600; color: #94a3b8;")
        layout.addWidget(lbl_bulk_hint)

        self.txt_bulk_input = QTextEdit()
        self.txt_bulk_input.setFixedHeight(95)
        self.txt_bulk_input.setPlaceholderText(
            "https://suno.com/song/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx\n"
            "https://suno.com/hook/yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy\n"
            "https://suno.com/playlist/zzzzzzzz-zzzz-zzzz-zzzz-zzzzzzzzzzzz"
        )
        self.txt_bulk_input.setStyleSheet("font-size: 10px; font-family: monospace;")
        layout.addWidget(self.txt_bulk_input)

        b_ctrl = QHBoxLayout()
        b_ctrl.setSpacing(6)

        self.btn_paste_bulk = QPushButton("📋 Paste Clipboard")
        self.btn_paste_bulk.setFixedHeight(28)
        self.btn_paste_bulk.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_paste_bulk.clicked.connect(self._paste_into_bulk)
        b_ctrl.addWidget(self.btn_paste_bulk)

        self.btn_parse_bulk = QPushButton("🔍 Parse Links / Playlist")
        self.btn_parse_bulk.setFixedHeight(28)
        self.btn_parse_bulk.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_parse_bulk.clicked.connect(self._parse_bulk_links)
        b_ctrl.addWidget(self.btn_parse_bulk)

        b_ctrl.addStretch(1)

        b_ctrl.addWidget(QLabel("Format:"))
        self.combo_bulk_fmt = QComboBox()
        self.combo_bulk_fmt.setFixedHeight(28)
        self.combo_bulk_fmt.addItem("🎵 MP3 Audio", "mp3")
        self.combo_bulk_fmt.addItem("🎚️ Lossless Studio WAV", "wav")
        self.combo_bulk_fmt.addItem("🔊 Original Stream", "original")
        self.combo_bulk_fmt.addItem("🎬 MP4 Video", "mp4")
        self.combo_bulk_fmt.addItem("🖼️ Cover Artwork", "png")
        self.combo_bulk_fmt.addItem("📦 Full Bundle (ZIP)", "pack")
        b_ctrl.addWidget(self.combo_bulk_fmt)

        self.btn_start_bulk = QPushButton("⬇️ Download All Queue")
        self.btn_start_bulk.setObjectName("primaryGenerateButton")
        self.btn_start_bulk.setFixedHeight(30)
        self.btn_start_bulk.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_start_bulk.clicked.connect(self._start_bulk_download)
        b_ctrl.addWidget(self.btn_start_bulk)

        layout.addLayout(b_ctrl)

        # Queue Table
        self.tbl_bulk = QTableWidget(0, 4)
        self.tbl_bulk.setHorizontalHeaderLabels(["#", "Track / Link", "Status", "Progress"])
        self.tbl_bulk.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tbl_bulk.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_bulk.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_bulk.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.tbl_bulk.setColumnWidth(3, 110)
        self.tbl_bulk.setStyleSheet("font-size: 10px;")
        layout.addWidget(self.tbl_bulk, stretch=1)

        self.progress_bulk = QProgressBar()
        self.progress_bulk.setFixedHeight(8)
        self.progress_bulk.setRange(0, 100)
        self.progress_bulk.setValue(0)
        self.progress_bulk.setTextVisible(False)
        self.progress_bulk.hide()
        layout.addWidget(self.progress_bulk)

    # ── Single Link Actions ──
    def _auto_paste_clipboard(self):
        clip = QApplication.clipboard().text().strip()
        if clip and ("suno.com" in clip or "suno.ai" in clip or SunoLinkParser.extract_uuid(clip)):
            self.txt_url.setText(clip)
            QTimer.singleShot(100, self._inspect_link)

    def _paste_from_clipboard(self):
        clip = QApplication.clipboard().text().strip()
        if clip:
            self.txt_url.setText(clip)
            self._inspect_link()

    def _on_url_text_changed(self, text: str):
        self.single_post_frame.hide()
        if not text.strip():
            self.lbl_title.setText("Ready to inspect Suno track or hook")
            self.lbl_artist.setText("Artist: - • Duration: 0:00")
            self.lbl_style.setText("Style / Mood: -")
            self.txt_lyrics.clear()

    def _inspect_link(self):
        raw = self.txt_url.text().strip()
        if not raw:
            return
        self.lbl_status.setText("🔍 Inspecting track metadata from Suno...")
        meta = SunoLinkParser.fetch_metadata(raw)
        self.current_metadata = meta

        title = meta.get("title") or "Suno Track"
        self.lbl_title.setText(f"🎵 {title}")
        self.badge_type.setText(f"🪝 {meta.get('track_type', 'Song')}" if meta.get("track_type") == "Hook" else "🎵 Song")
        artist = meta.get("artist") or "Suno AI"
        dur = meta.get("duration_str") or "0:00"
        engine = meta.get("model_version", "v4")
        self.lbl_artist.setText(f"Artist: {artist} • Engine: Suno {engine} • Duration: {dur}")

        style = meta.get("style") or "Auto-detected"
        self.lbl_style.setText(f"Style / Mood: {style}")

        lyrics = meta.get("lyrics", "").strip()
        if lyrics:
            self.txt_lyrics.setPlainText(lyrics)
            self.btn_import_lyrics.setEnabled(True)
        else:
            self.txt_lyrics.setPlainText("(No lyrics metadata embedded in track)")
            self.btn_import_lyrics.setEnabled(False)

        uuid = meta.get("uuid")
        if uuid:
            self.lbl_status.setText(f"✓ Verified Suno ID: {uuid[:8]}... Select format below to download")
        else:
            self.lbl_status.setText("✓ Ready to download media link")

    def _toggle_stream_preview(self):
        from PyQt6.QtMultimedia import QMediaPlayer
        if self.preview_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.preview_player.pause()
            self.btn_audition_stream.setText("▶ Audition")
        else:
            url = self.current_metadata.get("audio_url")
            if not url and self.current_metadata.get("uuid"):
                url = f"https://cdn1.suno.ai/{self.current_metadata['uuid']}.mp3"
            if url:
                self.preview_player.setSource(QUrl(url))
                self.preview_player.play()
                self.btn_audition_stream.setText("⏸ Pause")
            else:
                QMessageBox.information(self, "Audition", "Please inspect a valid Suno track link first.")

    def _on_preview_state_changed(self, state):
        from PyQt6.QtMultimedia import QMediaPlayer
        if state != QMediaPlayer.PlaybackState.PlayingState:
            self.btn_audition_stream.setText("▶ Audition")

    def _trigger_download(self, fmt: str):
        raw = self.txt_url.text().strip()
        if not raw:
            QMessageBox.warning(self, "Missing Link", "Please enter or paste a valid Suno song link.")
            return

        dest_dir = self._current_dest_dir()

        self._set_chips_enabled(False)
        self.progress_single.show()
        self.progress_single.setValue(0)
        self.single_post_frame.hide()
        self.lbl_status.setText(f"⬇️ Downloading {fmt.upper()} from Suno CDN...")

        self.download_worker = SunoDownloadWorker(
            input_url_or_uuid=raw,
            media_format=fmt,
            custom_destination_dir=dest_dir,
            parent=self,
        )
        self.download_worker.progress.connect(self._on_single_progress)
        self.download_worker.status_message.connect(self.lbl_status.setText)
        self.download_worker.finished.connect(self._on_single_finished)
        self.download_worker.start()

    def _set_chips_enabled(self, enabled: bool):
        for btn in [
            self.btn_dl_mp3, self.btn_dl_wav, self.btn_dl_orig,
            self.btn_dl_video, self.btn_dl_art, self.btn_dl_lyrics, self.btn_dl_pack
        ]:
            btn.setEnabled(enabled)

    def _on_single_progress(self, percent: int, cur_b: int, tot_b: int, speed_kbps: float):
        self.progress_single.setValue(percent)
        mb_cur = cur_b / (1024 * 1024)
        mb_tot = tot_b / (1024 * 1024) if tot_b > 0 else 0
        spd_txt = f"{speed_kbps / 1024:.1f} MB/s" if speed_kbps >= 1000 else f"{speed_kbps:.0f} KB/s"
        if tot_b > 0:
            self.lbl_status.setText(f"⬇️ Downloading: {percent}% ({mb_cur:.1f} / {mb_tot:.1f} MB) • {spd_txt}")
        else:
            self.lbl_status.setText(f"⬇️ Downloading: {mb_cur:.1f} MB • {spd_txt}")

    def _on_single_finished(self, success: bool, file_path: str, metadata: Dict, err: str):
        self._set_chips_enabled(True)
        if success and file_path and Path(file_path).exists():
            self.last_downloaded_path = file_path
            self.current_metadata = metadata
            p = Path(file_path)
            self.lbl_status.setText(f"✅ Ready: {p.name}")
            self.progress_single.setValue(100)
            self.single_post_frame.show()

            is_audio = p.suffix.lower() in [".mp3", ".wav", ".m4a", ".ogg"]
            self.btn_audition_editor.setEnabled(is_audio)
        else:
            self.progress_single.hide()
            self.lbl_status.setText(f"⚠️ Error: {err}")
            QMessageBox.critical(self, "Download Error", f"Failed to download Suno media:\n\n{err}")

    # ── Bulk / Playlist Tab Actions ──
    def _paste_into_bulk(self):
        clip = QApplication.clipboard().text().strip()
        if clip:
            self.txt_bulk_input.append(clip)
            self._parse_bulk_links()

    def _parse_bulk_links(self):
        text = self.txt_bulk_input.toPlainText().strip()
        if not text:
            return

        urls = []
        if "/playlist/" in text:
            self.lbl_status.setText("🔍 Resolving Suno Playlist tracks...")
            tracks = SunoLinkParser.fetch_playlist_tracks(text)
            urls = [f"https://suno.com/song/{t['uuid']}" for t in tracks if t.get("uuid")]
        else:
            uids = SunoLinkParser.extract_all_uuids(text, max_limit=20)
            urls = [f"https://suno.com/song/{u}" for u in uids]

        self.tbl_bulk.setRowCount(len(urls))
        for row, u in enumerate(urls):
            self.tbl_bulk.setItem(row, 0, QTableWidgetItem(f"{row + 1:02d}"))
            self.tbl_bulk.setItem(row, 1, QTableWidgetItem(u))
            self.tbl_bulk.setItem(row, 2, QTableWidgetItem("Queued"))
            self.tbl_bulk.setItem(row, 3, QTableWidgetItem("0%"))

        self.lbl_status.setText(f"✓ Found {len(urls)} Suno tracks in queue. Click 'Download All Queue' to begin.")

    def _start_bulk_download(self):
        row_count = self.tbl_bulk.rowCount()
        if row_count == 0:
            self._parse_bulk_links()
            row_count = self.tbl_bulk.rowCount()

        if row_count == 0:
            QMessageBox.warning(self, "No Links", "Please paste at least one Suno song link or playlist.")
            return

        urls = [self.tbl_bulk.item(r, 1).text().strip() for r in range(row_count)]
        fmt = self.combo_bulk_fmt.currentData()
        dest_dir = self._current_dest_dir()

        self.btn_start_bulk.setEnabled(False)
        self.progress_bulk.show()
        self.progress_bulk.setValue(0)

        self.bulk_worker = SunoBulkDownloadWorker(
            urls=urls,
            media_format=fmt,
            destination_dir=dest_dir,
            parent=self,
        )

        def _on_track_start(idx, tot, url):
            row = idx - 1
            if row < self.tbl_bulk.rowCount():
                self.tbl_bulk.setItem(row, 2, QTableWidgetItem("Downloading..."))

        def _on_track_prog(idx, tot, pct, spd):
            row = idx - 1
            if row < self.tbl_bulk.rowCount():
                self.tbl_bulk.setItem(row, 3, QTableWidgetItem(f"{pct}%"))
            total_pct = int(((idx - 1 + (pct / 100.0)) / tot) * 100)
            self.progress_bulk.setValue(total_pct)

        def _on_track_done(idx, ok, path, meta, err):
            row = idx - 1
            if row < self.tbl_bulk.rowCount():
                st = "✓ Done" if ok else f"⚠️ {err[:15]}"
                self.tbl_bulk.setItem(row, 2, QTableWidgetItem(st))
                self.tbl_bulk.setItem(row, 3, QTableWidgetItem("100%" if ok else "Fail"))
                if meta.get("title") and row < self.tbl_bulk.rowCount():
                    self.tbl_bulk.setItem(row, 1, QTableWidgetItem(f"🎵 {meta['title']}"))

        def _on_bulk_finish(succ, fail, paths):
            self.btn_start_bulk.setEnabled(True)
            self.progress_bulk.setValue(100)
            self.lbl_status.setText(f"🎉 Bulk Download Completed: {succ} successful, {fail} failed.")
            QMessageBox.information(
                self, "Bulk Download Complete",
                f"Successfully downloaded {succ} Suno tracks into:\n{dest_dir}"
            )

        self.bulk_worker.track_started.connect(_on_track_start)
        self.bulk_worker.track_progress.connect(_on_track_prog)
        self.bulk_worker.track_finished.connect(_on_track_done)
        self.bulk_worker.batch_finished.connect(_on_bulk_finish)
        self.bulk_worker.start()

    # ── Post-Download Studio Integration ──
    def _audition_in_editor(self):
        if self.last_downloaded_path and Path(self.last_downloaded_path).exists():
            self.preview_player.stop()
            self.load_into_editor_requested.emit(self.last_downloaded_path)
            self.accept()

    def _import_lyrics(self):
        lyrics = self.current_metadata.get("lyrics", "").strip() or self.txt_lyrics.toPlainText().strip()
        title = self.current_metadata.get("title", "").strip() or "Suno Song"
        if lyrics:
            self.import_lyrics_requested.emit(title, lyrics)
            self.accept()
        else:
            QMessageBox.information(self, "No Lyrics", "No lyrics metadata was found embedded in this track.")

    def _send_to_visual(self):
        style = self.current_metadata.get("style", "")
        lyrics = self.current_metadata.get("lyrics", "")
        title = self.current_metadata.get("title", "")
        self.send_to_visual_requested.emit({
            "title": title,
            "style_prompt": style,
            "lyrics": lyrics,
        })
        self.accept()

    def _reveal_last_file(self):
        if self.last_downloaded_path and Path(self.last_downloaded_path).exists():
            p = Path(self.last_downloaded_path)
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(p.parent)))

    def _open_downloads_folder(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(self._current_dest_dir()))

    def _browse_dest_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Save Directory", self._current_dest_dir())
        if folder:
            self.lbl_dest_display.setText(f"📂 {folder[:32]}...")
            self.lbl_dest_display.setToolTip(folder)
            self._custom_dir = folder

    def _current_dest_dir(self) -> str:
        return getattr(self, "_custom_dir", str(SunoDownloadWorker.default_download_dir()))

    def _on_close(self):
        self.preview_player.stop()
        if self.download_worker and self.download_worker.isRunning():
            self.download_worker.cancel()
            self.download_worker.wait(800)
        if self.bulk_worker and self.bulk_worker.isRunning():
            self.bulk_worker.cancel()
            self.bulk_worker.wait(800)
        self.reject()

    # ── 5-Theme Styling ──
    def apply_theme(self, theme_or_dark):
        t = get_theme(theme_or_dark)
        self.theme_key = t.get("id", "obsidian")
        is_dark = t.get("is_dark", True)

        bg = t["bg_window"]
        card = t["bg_card"]
        inp = t["bg_input"]
        border = t["border"]
        border_sub = t["border_subtle"]
        pri = t["text_primary"]
        sec = t["text_secondary"]
        acc = t["accent"]
        acc_sec = t["accent_secondary"]
        acc_grad = t["accent_gradient"]

        self.setStyleSheet(f"""
            QDialog {{ background-color: {bg}; color: {pri}; }}
            QTabWidget::pane {{
                border: 1px solid {border};
                background: {bg};
                border-radius: 8px;
            }}
            QTabBar::tab {{
                background: {t['bg_btn'] if is_dark else '#f1f5f9'};
                color: {sec};
                padding: 6px 14px;
                font-size: 11px;
                font-weight: 700;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background: {card};
                color: {pri};
                border-bottom: 2px solid {acc};
            }}
            QFrame#sunoSongCard, QFrame#sunoChipsFrame, QFrame#dlPostFrame {{
                background-color: {card};
                border: 1px solid {border};
                border-radius: 8px;
            }}
            QLabel {{ color: {pri}; background: transparent; }}
            QLineEdit, QTextEdit, QComboBox {{
                background-color: {inp};
                color: {pri};
                border: 1px solid {border};
                border-radius: 6px;
                padding: 4px 8px;
            }}
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
                border: 1px solid {acc};
            }}
            QProgressBar {{
                background-color: {inp};
                border: 1px solid {border};
                border-radius: 5px;
            }}
            QProgressBar::chunk {{
                background: {acc_grad};
                border-radius: 4px;
            }}
            QPushButton {{
                background-color: {t['bg_btn'] if is_dark else '#ffffff'};
                color: {pri};
                border: 1px solid {border};
                border-radius: 6px;
                font-weight: 700;
                font-size: 11px;
                padding: 4px 10px;
            }}
            QPushButton:hover {{
                background-color: {t['bg_btn_hover'] if is_dark else '#f1f5f9'};
                border-color: {acc};
            }}
            QPushButton#primaryGenerateButton {{
                background: {acc_grad};
                color: #ffffff;
                border: 1px solid {acc_sec};
                font-size: 11px;
                font-weight: 800;
            }}
            QPushButton#accentButton {{
                background-color: {t['subtle_pill_bg']};
                color: {t['text_accent']};
                border: 1px solid {t['border_accent']};
                font-weight: 800;
            }}
            QTableWidget {{
                background-color: {card};
                color: {pri};
                gridline-color: {border_sub};
                border: 1px solid {border};
                border-radius: 6px;
            }}
            QHeaderView::section {{
                background-color: {inp};
                color: {sec};
                font-weight: 700;
                padding: 3px;
                border: 1px solid {border};
            }}
        """)
