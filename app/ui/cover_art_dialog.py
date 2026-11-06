"""
AI Album Cover & YouTube Thumbnail Generator Dialog.
Live interactive preview, style presets, typography customization,
and 1-click export for Spotify/Suno 1:1 and YouTube 16:9 covers.
"""

import os
import tempfile
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QLineEdit, QGroupBox, QFileDialog,
    QMessageBox, QFrame, QRadioButton, QButtonGroup, QScrollArea,
    QTabWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage
from PIL import Image
from app.cover_art_generator import CoverArtGenerator, STYLE_PRESETS


class CoverArtDialog(QDialog):
    cover_generated = pyqtSignal(str) # Path to saved cover image

    def __init__(self, parent=None, is_dark: bool = True, title: str = "Untitled Track", artist: str = "Lyric AI Writer", lyrics: str = ""):
        super().__init__(parent)
        self.is_dark = is_dark
        self.song_title = title
        self.artist_name = artist
        self.lyrics = lyrics
        self.current_image: Optional[Image.Image] = None
        self.temp_cover_path: Optional[str] = None

        self.setWindowTitle(f"🖼️ AI Album Cover & YouTube Thumbnail Generator — {self.song_title}")
        self.resize(920, 720)
        self.setMinimumSize(840, 640)

        self._init_ui()
        self.apply_theme(self.is_dark)
        self._generate_cover()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(14)

        # Header Title
        header_row = QHBoxLayout()
        title_box = QVBoxLayout()
        self.lbl_title = QLabel("🖼️ AI Album Cover & YouTube Thumbnail Generator")
        self.lbl_title.setStyleSheet("font-size: 18px; font-weight: 800;")
        self.lbl_subtitle = QLabel("Generate high-res 1:1 Spotify/Suno album covers and 16:9 YouTube MV thumbnails.")
        self.lbl_subtitle.setStyleSheet("font-size: 12px; color: #64748b;")
        title_box.addWidget(self.lbl_title)
        title_box.addWidget(self.lbl_subtitle)
        header_row.addLayout(title_box)
        header_row.addStretch()
        main_layout.addLayout(header_row)

        # Main Split: Left Controls, Right Live Preview
        content_row = QHBoxLayout()
        content_row.setSpacing(16)

        # Left Column: Configuration Controls
        left_box = QVBoxLayout()
        left_box.setSpacing(12)

        # 1. Format & Aspect Ratio
        format_group = QGroupBox("📐 Aspect Ratio & Platform")
        f_layout = QVBoxLayout(format_group)
        f_layout.setContentsMargins(10, 10, 10, 10)
        f_layout.setSpacing(6)
        self.ratio_group = QButtonGroup(self)
        self.radio_sq = QRadioButton("1:1 Square (Spotify / Suno / Apple Music)")
        self.radio_sq.setChecked(True)
        self.radio_yt = QRadioButton("16:9 Landscape (YouTube MV / TikTok / Video)")
        self.ratio_group.addButton(self.radio_sq, 0)
        self.ratio_group.addButton(self.radio_yt, 1)
        self.radio_sq.toggled.connect(self._generate_cover)
        self.radio_yt.toggled.connect(self._generate_cover)
        f_layout.addWidget(self.radio_sq)
        f_layout.addWidget(self.radio_yt)
        left_box.addWidget(format_group)

        # 2. Visual Art Style
        style_group = QGroupBox("🎨 Visual Art Style Preset")
        s_layout = QVBoxLayout(style_group)
        s_layout.setContentsMargins(10, 10, 10, 10)
        self.combo_style = QComboBox()
        for k, v in STYLE_PRESETS.items():
            self.combo_style.addItem(v["name"], k)
        self.combo_style.currentIndexChanged.connect(self._generate_cover)
        s_layout.addWidget(self.combo_style)
        left_box.addWidget(style_group)

        # 3. Typography & Badges
        typo_group = QGroupBox("✍️ Typography & Studio Branding")
        t_layout = QVBoxLayout(typo_group)
        t_layout.setContentsMargins(10, 10, 10, 10)
        t_layout.setSpacing(8)

        lbl_t = QLabel("Song Title:")
        lbl_t.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748b;")
        self.txt_title = QLineEdit(self.song_title)
        self.txt_title.textChanged.connect(self._generate_cover)
        t_layout.addWidget(lbl_t)
        t_layout.addWidget(self.txt_title)

        lbl_a = QLabel("Artist / Producer:")
        lbl_a.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748b;")
        self.txt_artist = QLineEdit(self.artist_name)
        self.txt_artist.textChanged.connect(self._generate_cover)
        t_layout.addWidget(lbl_a)
        t_layout.addWidget(self.txt_artist)

        lbl_sub = QLabel("Subtitle / Category:")
        lbl_sub.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748b;")
        self.txt_sub = QLineEdit("ORIGINAL SOUNDTRACK")
        self.txt_sub.textChanged.connect(self._generate_cover)
        t_layout.addWidget(lbl_sub)
        t_layout.addWidget(self.txt_sub)

        lbl_b = QLabel("Studio Audio Badge:")
        lbl_b.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748b;")
        self.txt_badge = QLineEdit("STEREO · 96kHz / 24-bit")
        self.txt_badge.textChanged.connect(self._generate_cover)
        t_layout.addWidget(lbl_b)
        t_layout.addWidget(self.txt_badge)

        left_box.addWidget(typo_group)

        # 4. AI Prompt Builder Preview
        ai_group = QGroupBox("🤖 Imagen 3 / Gemini Visual Prompt")
        ai_layout = QVBoxLayout(ai_group)
        ai_layout.setContentsMargins(10, 10, 10, 10)
        ai_layout.setSpacing(6)
        self.lbl_ai_prompt = QLabel()
        self.lbl_ai_prompt.setStyleSheet("font-size: 10px; color: #94a3b8; font-style: italic;")
        self.lbl_ai_prompt.setWordWrap(True)
        self.btn_copy_prompt = QPushButton("📋 Copy AI Prompt")
        self.btn_copy_prompt.clicked.connect(self._copy_prompt)
        ai_layout.addWidget(self.lbl_ai_prompt)
        ai_layout.addWidget(self.btn_copy_prompt)
        left_box.addWidget(ai_group)

        content_row.addLayout(left_box, stretch=1)

        # Right Column: Live Cover Art Preview
        preview_group = QGroupBox("👁️ Live High-Res Cover Preview")
        p_layout = QVBoxLayout(preview_group)
        p_layout.setContentsMargins(12, 12, 12, 12)

        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("background-color: #0b0f19; border-radius: 8px; border: 1px solid #1e293b;")
        self.preview_label.setMinimumSize(420, 420)
        p_layout.addWidget(self.preview_label, stretch=1)

        content_row.addWidget(preview_group, stretch=1)
        main_layout.addLayout(content_row, stretch=1)

        # Bottom Bar: Export Actions
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(10)

        self.btn_export_png = QPushButton("💾 Export High-Res Image (.png)")
        self.btn_export_png.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_export_png.setFixedHeight(38)
        self.btn_export_png.setStyleSheet("background-color: #8b5cf6; color: white; font-weight: 700; border-radius: 6px; padding: 0 18px;")
        self.btn_export_png.clicked.connect(self._export_png)

        self.btn_save_project = QPushButton("📦 Save as Project Cover (Bundle in ZIP)")
        self.btn_save_project.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save_project.setFixedHeight(38)
        self.btn_save_project.setStyleSheet("background-color: #10b981; color: white; font-weight: 700; border-radius: 6px; padding: 0 18px;")
        self.btn_save_project.clicked.connect(self._save_to_project)

        self.btn_close = QPushButton("Close")
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.setFixedHeight(38)
        self.btn_close.setFixedWidth(80)
        self.btn_close.clicked.connect(self.accept)

        bottom_row.addWidget(self.btn_export_png)
        bottom_row.addWidget(self.btn_save_project)
        bottom_row.addStretch()
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
            QLineEdit, QComboBox {{
                background-color: {bg_col};
                color: {text_col};
                border: 1px solid {border_col};
                border-radius: 6px;
                padding: 5px 10px;
                font-size: 12px;
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

    def _generate_cover(self):
        title = self.txt_title.text().strip() or "Untitled"
        artist = self.txt_artist.text().strip() or "Lyric AI"
        subtitle = self.txt_sub.text().strip() or "ORIGINAL SOUNDTRACK"
        badge = self.txt_badge.text().strip() or "STEREO"
        style_key = self.combo_style.currentData() or "cyberpunk_neon"
        aspect = "16:9" if self.radio_yt.isChecked() else "1:1"

        # Generate PIL image
        self.current_image = CoverArtGenerator.generate_cover_art(
            title=title,
            artist=artist,
            style_key=style_key,
            aspect_ratio=aspect,
            subtitle=subtitle,
            badge=badge
        )

        # Update AI Prompt
        prompt = CoverArtGenerator.craft_ai_prompt(title, style_key, self.lyrics)
        self.lbl_ai_prompt.setText(prompt)

        # Save to temp file for display
        out_dir = Path(tempfile.gettempdir()) / "worldlyric_covers"
        out_dir.mkdir(parents=True, exist_ok=True)
        self.temp_cover_path = str(out_dir / f"cover_{abs(hash(title)) % 100000}.png")
        self.current_image.save(self.temp_cover_path)

        # Scale for preview viewport
        pixmap = QPixmap(self.temp_cover_path)
        if aspect == "16:9":
            scaled = pixmap.scaled(440, 247, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        else:
            scaled = pixmap.scaled(420, 420, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        self.preview_label.setPixmap(scaled)

    def _copy_prompt(self):
        from PyQt6.QtWidgets import QApplication
        prompt = self.lbl_ai_prompt.text()
        QApplication.clipboard().setText(prompt)
        QMessageBox.information(self, "Prompt Copied", "AI image generation prompt copied to clipboard!")

    def _export_png(self):
        if not self.current_image:
            return

        aspect_tag = "16x9" if self.radio_yt.isChecked() else "1x1"
        safe_title = "".join(c for c in self.txt_title.text() if c.isalnum() or c in (" ", "-", "_")).strip()
        default_name = f"{safe_title}_Album_Cover_{aspect_tag}.png"

        dest, _ = QFileDialog.getSaveFileName(
            self,
            "Export High-Res Album Cover",
            default_name,
            "PNG Images (*.png);;JPEG Images (*.jpg);;All Files (*.*)"
        )
        if dest:
            try:
                self.current_image.save(dest)
                QMessageBox.information(self, "Cover Exported", f"Saved high-res cover art to:\n{dest}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to save image: {e}")

    def _save_to_project(self):
        if not self.temp_cover_path or not os.path.exists(self.temp_cover_path):
            return
        self.cover_generated.emit(self.temp_cover_path)
        QMessageBox.information(self, "Cover Saved", "Album cover saved to active project!\nIt will be included automatically when exporting the Suno Production ZIP bundle.")
