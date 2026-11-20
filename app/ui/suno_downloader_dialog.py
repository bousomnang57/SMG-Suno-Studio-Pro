"""
Suno Music Link Downloader Dialog:
Interactive UI to paste any Suno song link, inspect metadata & lyrics,
select format (MP3, MP4, PNG, Full Pack), download with live progress,
and audition instantly in the Lyric Editor Workbench.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QProgressBar, QFrame, QTextEdit, QFileDialog, QApplication,
    QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QUrl, QTimer
from PyQt6.QtGui import QIcon, QDesktopServices, QPixmap

from app.suno_downloader import SunoLinkParser, SunoDownloadWorker
from app.ui.styles import get_theme


class SunoLinkDownloadDialog(QDialog):
    """Dialog to download Suno music by pasting a link."""

    load_into_editor_requested = pyqtSignal(str)  # audio_path
    import_lyrics_requested = pyqtSignal(str, str)  # title, lyrics

    def __init__(self, parent=None, theme_key: str = "obsidian", initial_url: str = ""):
        super().__init__(parent)
        self.theme_key = theme_key
        self.download_worker: Optional[SunoDownloadWorker] = None
        self.last_downloaded_path: str = ""
        self.current_metadata: Dict = {}

        self.setWindowTitle("📥 Suno Music Downloader by Link")
        self.setFixedSize(540, 520)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        self._init_ui()
        self.apply_theme(theme_key)

        # Set initial link or inspect clipboard
        if initial_url:
            self.txt_url.setText(initial_url)
            QTimer.singleShot(150, self._inspect_link)
        else:
            self._auto_paste_clipboard()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        # Title / Subtitle
        header_row = QHBoxLayout()
        header_row.setSpacing(8)
        lbl_icon = QLabel("📥")
        lbl_icon.setStyleSheet("font-size: 24px;")
        header_row.addWidget(lbl_icon)

        title_col = QVBoxLayout()
        title_col.setSpacing(1)
        self.lbl_head_title = QLabel("Download Suno Music by Link")
        self.lbl_head_title.setStyleSheet("font-size: 14.5px; font-weight: 800;")
        title_col.addWidget(self.lbl_head_title)

        self.lbl_head_sub = QLabel("Paste any Suno song URL (suno.com/song/...), short link, or CDN link")
        self.lbl_head_sub.setStyleSheet("font-size: 10.5px; color: #94a3b8;")
        title_col.addWidget(self.lbl_head_sub)
        header_row.addLayout(title_col)
        header_row.addStretch(1)
        layout.addLayout(header_row)

        # Link Input Box
        input_row = QHBoxLayout()
        input_row.setSpacing(6)
        self.txt_url = QLineEdit()
        self.txt_url.setPlaceholderText("https://suno.com/song/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")
        self.txt_url.setFixedHeight(32)
        self.txt_url.textChanged.connect(self._on_url_text_changed)
        self.txt_url.returnPressed.connect(self._start_download)
        input_row.addWidget(self.txt_url, stretch=1)

        self.btn_paste = QPushButton("📋 Paste")
        self.btn_paste.setFixedHeight(32)
        self.btn_paste.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_paste.setToolTip("Paste link from clipboard")
        self.btn_paste.clicked.connect(self._paste_from_clipboard)
        input_row.addWidget(self.btn_paste)

        self.btn_inspect = QPushButton("🔍 Inspect")
        self.btn_inspect.setFixedHeight(32)
        self.btn_inspect.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_inspect.setToolTip("Fetch song title, style, and lyrics preview")
        self.btn_inspect.clicked.connect(self._inspect_link)
        input_row.addWidget(self.btn_inspect)
        layout.addLayout(input_row)

        # Track Metadata Preview Card
        self.preview_card = QFrame()
        self.preview_card.setObjectName("dlPreviewCard")
        pc_layout = QVBoxLayout(self.preview_card)
        pc_layout.setContentsMargins(10, 8, 10, 8)
        pc_layout.setSpacing(5)

        self.lbl_track_title = QLabel("🎵 Ready to inspect link")
        self.lbl_track_title.setStyleSheet("font-size: 12px; font-weight: 800;")
        pc_layout.addWidget(self.lbl_track_title)

        self.lbl_track_style = QLabel("Style / Tags: -")
        self.lbl_track_style.setStyleSheet("font-size: 10px; color: #38bdf8; font-weight: 600;")
        self.lbl_track_style.setWordWrap(True)
        pc_layout.addWidget(self.lbl_track_style)

        self.txt_lyrics_preview = QTextEdit()
        self.txt_lyrics_preview.setReadOnly(True)
        self.txt_lyrics_preview.setFixedHeight(85)
        self.txt_lyrics_preview.setPlaceholderText("Lyrics preview will appear here...")
        self.txt_lyrics_preview.setStyleSheet("font-size: 10px; font-family: 'Consolas', monospace;")
        pc_layout.addWidget(self.txt_lyrics_preview)

        layout.addWidget(self.preview_card)

        # Options Row: Format & Destination Folder
        opt_layout = QHBoxLayout()
        opt_layout.setSpacing(8)

        # Format Picker
        fmt_col = QVBoxLayout()
        fmt_col.setSpacing(2)
        fmt_col.addWidget(QLabel("Media Format:"))
        self.combo_format = QComboBox()
        self.combo_format.setFixedHeight(28)
        self.combo_format.addItem("🎵 MP3 Audio (Master Track)", "mp3")
        self.combo_format.addItem("🎬 MP4 Video (Visualizer)", "mp4")
        self.combo_format.addItem("🖼️ Cover Artwork (PNG)", "png")
        self.combo_format.addItem("📦 Full Pack (MP3 + Cover + Lyrics .txt)", "pack")
        fmt_col.addWidget(self.combo_format)
        opt_layout.addLayout(fmt_col, stretch=1)

        # Destination Folder
        dest_col = QVBoxLayout()
        dest_col.setSpacing(2)
        dest_col.addWidget(QLabel("Save Folder:"))
        dest_row = QHBoxLayout()
        dest_row.setSpacing(4)
        self.txt_dest = QLineEdit(str(SunoDownloadWorker.default_download_dir()))
        self.txt_dest.setFixedHeight(28)
        self.txt_dest.setReadOnly(True)
        dest_row.addWidget(self.txt_dest, stretch=1)

        self.btn_browse = QPushButton("📁")
        self.btn_browse.setFixedSize(30, 28)
        self.btn_browse.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_browse.setToolTip("Select destination folder")
        self.btn_browse.clicked.connect(self._browse_dest_folder)
        dest_row.addWidget(self.btn_browse)
        dest_col.addLayout(dest_row)
        opt_layout.addLayout(dest_col, stretch=1)

        layout.addLayout(opt_layout)

        # Progress Section
        self.lbl_status = QLabel("Enter a link and click 'Download Now'")
        self.lbl_status.setStyleSheet("font-size: 10px; font-weight: 600; color: #94a3b8;")
        layout.addWidget(self.lbl_status)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(12)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # Action Buttons (Download / Cancel)
        btn_action_row = QHBoxLayout()
        btn_action_row.setSpacing(6)

        self.btn_download = QPushButton("⬇️ Download Now")
        self.btn_download.setObjectName("primaryGenerateButton")
        self.btn_download.setFixedHeight(34)
        self.btn_download.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_download.clicked.connect(self._start_download)
        btn_action_row.addWidget(self.btn_download, stretch=2)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setFixedHeight(34)
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.clicked.connect(self._on_cancel)
        btn_action_row.addWidget(self.btn_cancel, stretch=1)
        layout.addLayout(btn_action_row)

        # Post-Download Action Deck (Initially Hidden)
        self.post_frame = QFrame()
        self.post_frame.setObjectName("dlPostFrame")
        pf_layout = QHBoxLayout(self.post_frame)
        pf_layout.setContentsMargins(6, 4, 6, 4)
        pf_layout.setSpacing(5)

        self.btn_audition = QPushButton("🎧 Audition in Editor")
        self.btn_audition.setFixedHeight(27)
        self.btn_audition.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_audition.setToolTip("Mount downloaded audio directly into Lyric Editor Stem Player")
        self.btn_audition.clicked.connect(self._audition_in_editor)
        pf_layout.addWidget(self.btn_audition)

        self.btn_import_lyrics = QPushButton("📝 Import Lyrics")
        self.btn_import_lyrics.setFixedHeight(27)
        self.btn_import_lyrics.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_import_lyrics.setToolTip("Import song title and lyrics into Lyric Editor Workbench")
        self.btn_import_lyrics.clicked.connect(self._import_lyrics)
        pf_layout.addWidget(self.btn_import_lyrics)

        self.btn_open_file = QPushButton("📁 Show in Explorer")
        self.btn_open_file.setFixedHeight(27)
        self.btn_open_file.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open_file.clicked.connect(self._reveal_file)
        pf_layout.addWidget(self.btn_open_file)

        self.post_frame.hide()
        layout.addWidget(self.post_frame)

    # ── Clipboard & Link Inspection ──
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
        self.post_frame.hide()
        if not text.strip():
            self.lbl_status.setText("Enter a Suno link and click 'Download Now'")
            self.lbl_track_title.setText("🎵 Ready to inspect link")
            self.lbl_track_style.setText("Style / Tags: -")
            self.txt_lyrics_preview.clear()

    def _inspect_link(self):
        raw = self.txt_url.text().strip()
        if not raw:
            return
        self.lbl_status.setText("🔍 Inspecting song metadata from Suno...")
        meta = SunoLinkParser.fetch_metadata(raw)
        self.current_metadata = meta

        title = meta.get("title") or "Suno Track"
        self.lbl_track_title.setText(f"🎵 {title}")
        style = meta.get("style") or "Auto-detected"
        self.lbl_track_style.setText(f"Style / Tags: {style}")

        lyrics = meta.get("lyrics", "").strip()
        if lyrics:
            self.txt_lyrics_preview.setPlainText(lyrics)
            self.btn_import_lyrics.setEnabled(True)
        else:
            self.txt_lyrics_preview.setPlainText("(No lyrics metadata embedded in track page)")
            self.btn_import_lyrics.setEnabled(False)

        uuid = meta.get("uuid")
        if uuid:
            self.lbl_status.setText(f"✓ Verified Suno Track ID: {uuid[:8]}... Ready to download")
        else:
            self.lbl_status.setText("✓ Ready to download media link")

    def _browse_dest_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Save Directory", self.txt_dest.text())
        if folder:
            self.txt_dest.setText(folder)

    # ── Download Execution ──
    def _start_download(self):
        raw = self.txt_url.text().strip()
        if not raw:
            QMessageBox.warning(self, "Missing Link", "Please enter or paste a valid Suno song link.")
            return

        fmt = self.combo_format.currentData()
        dest_dir = self.txt_dest.text().strip()

        self.btn_download.setEnabled(False)
        self.btn_inspect.setEnabled(False)
        self.btn_paste.setEnabled(False)
        self.progress_bar.show()
        self.progress_bar.setValue(0)
        self.post_frame.hide()
        self.lbl_status.setText("⬇️ Connecting to Suno CDN...")

        self.download_worker = SunoDownloadWorker(
            input_url_or_uuid=raw,
            media_format=fmt,
            custom_destination_dir=dest_dir,
            parent=self,
        )
        self.download_worker.progress.connect(self._on_download_progress)
        self.download_worker.status_message.connect(self._on_status_message)
        self.download_worker.finished.connect(self._on_download_finished)
        self.download_worker.start()

    def _on_download_progress(self, percent: int, current_b: int, total_b: int, speed_kbps: float):
        self.progress_bar.setValue(percent)
        mb_cur = current_b / (1024 * 1024)
        mb_tot = total_b / (1024 * 1024) if total_b > 0 else 0
        speed_txt = f"{speed_kbps / 1024:.1f} MB/s" if speed_kbps >= 1000 else f"{speed_kbps:.0f} KB/s"
        if total_b > 0:
            self.lbl_status.setText(f"⬇️ Downloading: {percent}% ({mb_cur:.1f} / {mb_tot:.1f} MB) • {speed_txt}")
        else:
            self.lbl_status.setText(f"⬇️ Downloading: {mb_cur:.1f} MB • {speed_txt}")

    def _on_status_message(self, msg: str):
        self.lbl_status.setText(msg)

    def _on_download_finished(self, success: bool, file_path: str, metadata: Dict, err: str):
        self.btn_download.setEnabled(True)
        self.btn_inspect.setEnabled(True)
        self.btn_paste.setEnabled(True)

        if success and file_path and Path(file_path).exists():
            self.last_downloaded_path = file_path
            self.current_metadata = metadata
            p = Path(file_path)
            self.lbl_status.setText(f"✅ Downloaded successfully: {p.name}")
            self.progress_bar.setValue(100)
            self.post_frame.show()

            # Enable/disable audio auditioning based on extension
            is_audio = p.suffix.lower() in [".mp3", ".wav", ".m4a", ".ogg"]
            self.btn_audition.setEnabled(is_audio)
        else:
            self.progress_bar.hide()
            self.lbl_status.setText(f"⚠️ Error: {err}")
            QMessageBox.critical(self, "Download Error", f"Failed to download Suno music:\n\n{err}")

    def _on_cancel(self):
        if self.download_worker and self.download_worker.isRunning():
            self.download_worker.cancel()
            self.download_worker.wait(1200)
        self.reject()

    # ── Post-Download Actions ──
    def _audition_in_editor(self):
        if self.last_downloaded_path and Path(self.last_downloaded_path).exists():
            self.load_into_editor_requested.emit(self.last_downloaded_path)
            self.accept()

    def _import_lyrics(self):
        lyrics = self.current_metadata.get("lyrics", "").strip() or self.txt_lyrics_preview.toPlainText().strip()
        title = self.current_metadata.get("title", "").strip() or "Suno Song"
        if lyrics:
            self.import_lyrics_requested.emit(title, lyrics)
            self.accept()
        else:
            QMessageBox.information(self, "No Lyrics", "No lyrics were found embedded in this Suno track.")

    def _reveal_file(self):
        if self.last_downloaded_path and Path(self.last_downloaded_path).exists():
            p = Path(self.last_downloaded_path)
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(p.parent)))

    # ── 5-Theme Styling ──
    def apply_theme(self, theme_or_dark):
        t = get_theme(theme_or_dark)
        self.theme_key = t.get("id", "obsidian")
        is_dark = t.get("is_dark", True)

        bg = t["bg_window"]
        card = t["bg_card"]
        inp = t["bg_input"]
        border = t["border"]
        pri = t["text_primary"]
        sec = t["text_secondary"]
        acc = t["accent"]
        acc_sec = t["accent_secondary"]
        acc_grad = t["accent_gradient"]

        self.setStyleSheet(f"""
            QDialog {{ background-color: {bg}; color: {pri}; }}
            QFrame#dlPreviewCard, QFrame#dlPostFrame {{
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
                border-radius: 6px;
            }}
            QProgressBar::chunk {{
                background: {acc_grad};
                border-radius: 5px;
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
                font-size: 12px;
                font-weight: 800;
            }}
        """)
