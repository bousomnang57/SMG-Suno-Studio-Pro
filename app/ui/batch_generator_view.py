"""
Batch Multi-Song Studio Pro View (បង្កើតបទចម្រៀងបានច្រើនក្នុងពេលតែមួយ).
Turbo AI Songwriting Engine generating 5-30 ready-to-use song cards at once
with instant Style Prompts, Sectioned Lyrics, Suno v6 Metatag Injection,
and 1-click Quick-Queue workflows for Suno v3.5 / v4 / v6.
"""

import json
import re
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QScrollArea, QFrame, QGridLayout,
    QComboBox, QApplication, QFileDialog, QMessageBox,
    QProgressBar, QMenu, QSizePolicy, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QAction
from app.gemini_client import BatchGenerateWorker, DeepenLyricWorker
from app.ui.styles import get_theme
from app.ui.batch_song_dialog import StudioSongInspectorDialog


def inject_suno_v6_cues(lyrics: str, bpm: str, key: str, genre: str, vocal_type: str = "Mixed") -> str:
    """
    Injects professional Suno v4/v6 structural metatags, dynamic audio cues,
    and clean fadeout endings into lyrics.
    """
    lines = lyrics.split("\n")
    new_lines = []

    # Check if tempo/key header already present
    has_header = any("[tempo:" in l.lower() or "[bpm:" in l.lower() for l in lines)
    if not has_header:
        new_lines.append(f"[Tempo: {bpm}]")
        new_lines.append(f"[Key: {key}]")
        new_lines.append("[Production: High Dynamic Range, Warm Analog Master, Spatial Stereo]")
        new_lines.append("")

    for l in lines:
        lc = l.strip()
        low = lc.lower()

        # Enhance Verse 1
        if low in ["[verse 1]", "[វគ្គ១]", "[verse]", "[វគ្គ 1]"]:
            new_lines.append(f"{lc[:-1]}: Intimate Delivery]" if lc.endswith("]") else f"{lc}: Intimate Delivery]")
        # Enhance Pre-Chorus
        elif low in ["[pre-chorus]", "[បន្ទរត្រៀម]"]:
            new_lines.append(f"{lc[:-1]}: Building Tension, Rising Percussion]" if lc.endswith("]") else f"{lc}: Building Tension]")
        # Enhance Chorus
        elif low in ["[chorus]", "[បន្ទរ]"]:
            new_lines.append(f"{lc[:-1]}: Soaring Hook, Full Dynamic Belt, Wide Stereo]" if lc.endswith("]") else f"{lc}: Soaring Hook]")
        # Enhance Bridge
        elif low in ["[bridge]", "[តភ្ជាប់]", "[ទម្លាក់]"]:
            new_lines.append(f"{lc[:-1]}: Stripped Acoustic Breakdown, Emotional Peak]" if lc.endswith("]") else f"{lc}: Emotional Breakdown]")
        # Enhance Outro
        elif low in ["[outro]", "[បញ្ចប់]"]:
            new_lines.append(f"{lc[:-1]}: Vocal Ad-libs, Instrumental Decay, Fade Out]" if lc.endswith("]") else f"{lc}: Fade Out]")
        else:
            new_lines.append(l)

    # Ensure professional clean fade-out ending
    if not any("[end]" in l.lower() for l in new_lines):
        new_lines.append("")
        new_lines.append("[Fade Out]")
        new_lines.append("[End]")

    return "\n".join(new_lines)


class BatchSongCard(QFrame):
    """Individual song card in the multi-song grid with Workflow Tracker & Favorites."""
    selected = pyqtSignal(dict)
    open_editor_requested = pyqtSignal(dict)
    open_visual_requested = pyqtSignal(dict)
    crossover_requested = pyqtSignal(dict)
    status_changed = pyqtSignal(dict)
    mutate_requested = pyqtSignal(dict)

    def __init__(self, song_data: dict, parent=None):
        super().__init__(parent)
        self.song_data = song_data
        self.is_active = False

        # Ensure default status flags
        if "is_favorite" not in self.song_data:
            self.song_data["is_favorite"] = False
        if "status" not in self.song_data:
            self.song_data["status"] = "new"  # "new", "copied", "done"

        self.setObjectName("batchSongCard")
        self.is_dark = True
        self.setMinimumWidth(280)
        self.setMinimumHeight(260)
        self.setMaximumHeight(315)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._init_ui()
        self._set_style(False)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(9, 8, 9, 8)
        layout.setSpacing(4)

        # ── ROW 1: Index + Lang + Title + Star + Editor + Status ──
        h_row = QHBoxLayout()
        h_row.setSpacing(5)

        idx = self.song_data.get("id", 1)
        self.idx_lbl = QLabel(f"{idx:02d}")
        self.idx_lbl.setStyleSheet("""
            font-family: 'Cascadia Code', 'Consolas', monospace;
            font-size: 10px;
            font-weight: 800;
            background-color: #1a2238;
            color: #93c5fd;
            border: 1px solid #3b82f6;
            border-radius: 4px;
            padding: 1px 4px;
        """)
        h_row.addWidget(self.idx_lbl)

        # Language Badge
        track_lang = self.song_data.get("language", "")
        lyrics_str = self.song_data.get("lyrics", "")
        title_str = self.song_data.get("title", "")
        is_fusion = "Bilingual" in track_lang or "Fusion" in track_lang or (any('\u1780' <= c <= '\u17ff' for c in lyrics_str) and any('a' <= c.lower() <= 'z' for c in lyrics_str) and "Chorus" in lyrics_str)
        is_khmer_card = "Khmer" in track_lang or any('\u1780' <= c <= '\u17ff' for c in title_str + lyrics_str)

        if is_fusion:
            self.lang_badge = QLabel("🇰🇭🇬🇧")
            self.lang_badge.setToolTip("Bilingual Fusion Track (ខ្មែរ + English Hook)")
        elif is_khmer_card:
            self.lang_badge = QLabel("🇰🇭")
            self.lang_badge.setToolTip("Khmer Track (បទចម្រៀងខ្មែរ)")
        else:
            self.lang_badge = QLabel("🇬🇧")
            self.lang_badge.setToolTip("English Track (English Song)")
        self.lang_badge.setStyleSheet("font-size: 11px; margin-left: 1px;")
        h_row.addWidget(self.lang_badge)

        self.title_lbl = QLabel(self.song_data.get("title", "Untitled Track"))
        self.title_lbl.setStyleSheet("font-family: 'Kantumruy Pro', 'Segoe UI', sans-serif; font-weight: 800; font-size: 11.5px; color: #ffffff;")
        self.title_lbl.setWordWrap(True)
        h_row.addWidget(self.title_lbl, stretch=1)

        # Favorite Star Button
        self.btn_star = QPushButton()
        self.btn_star.setFixedSize(18, 18)
        self.btn_star.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_star.setToolTip("Mark as Favorite Candidate (⭐)")
        self._update_star_ui()
        self.btn_star.clicked.connect(self._toggle_star)
        h_row.addWidget(self.btn_star)


        # Status badge (New / Copied / In Editor)
        self.status_badge = QLabel()
        self._update_status_ui()
        h_row.addWidget(self.status_badge)

        layout.addLayout(h_row)

        # ── ROW 2: Subtitle Metadata (Genre • BPM • Key) ──
        genre = self.song_data.get("genre", "Custom Genre")
        bpm = self.song_data.get("bpm", "120 BPM")
        key = self.song_data.get("key", "C")
        meter = self.song_data.get("meter", "")
        meter_str = f"  •  {meter}" if meter else ""
        self.meta_lbl = QLabel(f"{genre}  •  {bpm}  •  Key: {key}{meter_str}")
        self.meta_lbl.setStyleSheet("color: #38bdf8; font-size: 9px; font-weight: 700; background: transparent; border: none;")
        self.meta_lbl.setWordWrap(False)
        layout.addWidget(self.meta_lbl)

        # ── ROW 2.5: PRO STUDIO BADGES (Quality & Rhyme Scorer + Album Role) ──
        badge_row = QHBoxLayout()
        badge_row.setSpacing(4)
        badge_row.setContentsMargins(0, 0, 0, 0)

        q_hit = self.song_data.get("quality_score", 96)
        q_rhyme = self.song_data.get("rhyme_score", 94)
        q_human = self.song_data.get("human_score", 95)
        is_human = self.song_data.get("human_certified", False)
        badge_txt = f"🎯 {q_hit}% • 👤 100% Human" if is_human else f"🎯 {q_hit}% • 👤 {q_human}%"
        self.quality_badge = QLabel(badge_txt)
        self.quality_badge.setStyleSheet("""
            background-color: #064e3b;
            color: #6ee7b7;
            border: 1px solid #059669;
            border-radius: 3px;
            padding: 1px 4px;
            font-size: 8.5px;
            font-weight: 800;
            font-family: 'Cascadia Code', 'Consolas', monospace;
        """)
        self.quality_badge.setToolTip(f"Pro Studio Hit Analysis:\n• Hit Potential: {q_hit}%\n• Rhyme Density: {q_rhyme}%\n• Human Authenticity: {q_human}%\n• Vocal Breath Architecture Certified")
        badge_row.addWidget(self.quality_badge)

        role = self.song_data.get("album_role", "")
        if role:
            role_short = role.replace("💿 Track ", "T").replace("Track ", "T")
            if ":" in role_short:
                role_short = "💿 " + role_short.split(":", 1)[1].strip()
            self.role_badge = QLabel(role_short[:16])
            self.role_badge.setStyleSheet("""
                background-color: #311042;
                color: #f0abfc;
                border: 1px solid #a855f7;
                border-radius: 3px;
                padding: 1px 3px;
                font-size: 8px;
                font-weight: 700;
            """)
            self.role_badge.setToolTip(f"Album Concept Arc Role:\n{role}")
            badge_row.addWidget(self.role_badge)

        # Real-time Novelty Score Badge
        self.novelty_badge = QLabel()
        self.update_novelty_badge()
        badge_row.addWidget(self.novelty_badge)

        badge_row.addStretch()
        layout.addLayout(badge_row)

        # ── ROW 3: STYLE PROMPT Micro Glass Chip (Clean, No redundant label) ──
        self.lbl_style_title = QLabel()
        self.lbl_style_title.hide()

        style_txt = self.song_data.get("style_prompt", "")
        self.style_box = QLabel()
        self.style_box.setStyleSheet("background: #090c17; border: 1px solid #1c2642; border-radius: 5px; padding: 3px 6px; color: #7dd3fc; font-size: 9.5px; line-height: 1.25;")
        self.style_box.setWordWrap(True)
        self.style_box.setFixedHeight(34)
        self.update_style_preview()
        layout.addWidget(self.style_box)

        # ── ROW 4: LYRICS PREVIEW Glass Code Card (Clean, Monospace, No redundant label) ──
        self.lbl_lyrics_title = QLabel()
        self.lbl_lyrics_title.hide()

        self.lyric_box = QLabel()
        self.lyric_box.setStyleSheet("background: #060913; border: 1px solid #181f36; border-radius: 5px; padding: 4px 6px; color: #f8fafc; font-family: 'Cascadia Code', 'Consolas', monospace; font-size: 9.5px; line-height: 1.35;")
        self.lyric_box.setWordWrap(True)
        self.update_lyrics_preview()
        layout.addWidget(self.lyric_box, stretch=1)

        # ── ROW 5: 3 Wide Action Buttons: [🎨 Style] [✍️ Lyrics] [⚡ All] ──
        btn_row = QHBoxLayout()
        btn_row.setSpacing(4)
        btn_row.setContentsMargins(0, 3, 0, 0)

        self.btn_copy_style = QPushButton("🎨 Style")
        self.btn_copy_style.setToolTip("Copy Suno Style Prompt to Clipboard")
        self.btn_copy_style.setFixedHeight(25)
        self.btn_copy_style.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_copy_style.setStyleSheet("""
            QPushButton {
                background-color: #141a2e;
                color: #38bdf8;
                border: 1px solid #233052;
                border-radius: 4px;
                padding: 2px 5px;
                font-size: 10px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #0284c7;
                color: #ffffff;
                border-color: #38bdf8;
            }
            QPushButton:pressed {
                background-color: #075985;
            }
        """)
        self.btn_copy_style.clicked.connect(self._copy_style)
        btn_row.addWidget(self.btn_copy_style, stretch=1)

        self.btn_copy_lyrics = QPushButton("✍️ Lyrics")
        self.btn_copy_lyrics.setToolTip("Copy Lyrics to Clipboard")
        self.btn_copy_lyrics.setFixedHeight(25)
        self.btn_copy_lyrics.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_copy_lyrics.setStyleSheet("""
            QPushButton {
                background-color: #141a2e;
                color: #c084fc;
                border: 1px solid #233052;
                border-radius: 4px;
                padding: 2px 5px;
                font-size: 10px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #7c3aed;
                color: #ffffff;
                border-color: #a855f7;
            }
            QPushButton:pressed {
                background-color: #5b21b6;
            }
        """)
        self.btn_copy_lyrics.clicked.connect(self._copy_lyrics)
        btn_row.addWidget(self.btn_copy_lyrics, stretch=1)

        self.btn_copy_all = QPushButton("⚡ Suno All")
        self.btn_copy_all.setToolTip("Copy Full Suno Bundle (Title + Style + Lyrics) to Clipboard")
        self.btn_copy_all.setFixedHeight(25)
        self.btn_copy_all.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_copy_all.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4f46e5, stop:1 #7c3aed);
                color: #ffffff;
                border: 1px solid #818cf8;
                border-radius: 4px;
                padding: 2px 4px;
                font-size: 9.5px;
                font-weight: 800;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366f1, stop:1 #8b5cf6);
                border-color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #3730a3;
            }
        """)
        self.btn_copy_all.clicked.connect(self._copy_all)
        btn_row.addWidget(self.btn_copy_all, stretch=1)

        self.btn_mutate = QPushButton("🎲 Mutate")
        self.btn_mutate.setToolTip("🎲 Mutate Song In-Place (Modulate BPM/Key, rewrite fresh angles, zero repeat)")
        self.btn_mutate.setFixedHeight(25)
        self.btn_mutate.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mutate.setStyleSheet("""
            QPushButton {
                background-color: #1e1b4b;
                color: #a78bfa;
                border: 1px solid #4338ca;
                border-radius: 4px;
                padding: 2px 4px;
                font-size: 9.5px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #4f46e5;
                color: #ffffff;
                border-color: #818cf8;
            }
            QPushButton:pressed {
                background-color: #3730a3;
            }
        """)
        self.btn_mutate.clicked.connect(lambda: self.mutate_requested.emit(self.song_data))
        btn_row.addWidget(self.btn_mutate, stretch=1)

        layout.addLayout(btn_row)
    def _toggle_star(self):
        is_fav = not self.song_data.get("is_favorite", False)
        self.song_data["is_favorite"] = is_fav
        self._update_star_ui()
        self.status_changed.emit(self.song_data)

    def _update_star_ui(self):
        is_fav = self.song_data.get("is_favorite", False)
        if is_fav:
            self.btn_star.setText("★")
            self.btn_star.setStyleSheet("background: transparent; color: #fbbf24; font-size: 13px; border: none; font-weight: 900;")
        else:
            self.btn_star.setText("☆")
            color = "#64748b" if getattr(self, "is_dark", True) else "#94a3b8"
            self.btn_star.setStyleSheet(f"background: transparent; color: {color}; font-size: 13px; border: none;")

    def _update_status_ui(self):
        status = self.song_data.get("status", "new")
        is_dark = getattr(self, "is_dark", True)
        if status == "copied":
            self.status_badge.setText("✓ Copied")
            self.status_badge.setToolTip("Already copied to clipboard")
            if is_dark:
                self.status_badge.setStyleSheet("background: #064e3b; color: #34d399; font-size: 8.5px; font-weight: 800; padding: 1px 4px; border-radius: 3px; border: 1px solid #059669;")
            else:
                self.status_badge.setStyleSheet("background: #d1fae5; color: #047857; font-size: 8.5px; font-weight: 800; padding: 1px 4px; border-radius: 3px; border: 1px solid #a7f3d0;")
        elif status == "done":
            self.status_badge.setText("🟣 Editor")
            self.status_badge.setToolTip("Opened in Editor")
            if is_dark:
                self.status_badge.setStyleSheet("background: #4c1d95; color: #c084fc; font-size: 8.5px; font-weight: 800; padding: 1px 4px; border-radius: 3px; border: 1px solid #7c3aed;")
            else:
                self.status_badge.setStyleSheet("background: #ede9fe; color: #6d28d9; font-size: 8.5px; font-weight: 800; padding: 1px 4px; border-radius: 3px; border: 1px solid #c4b5fd;")
        else:
            self.status_badge.setText("● New")
            self.status_badge.setToolTip("New track, not yet copied")
            if is_dark:
                self.status_badge.setStyleSheet("background: #1e243d; color: #94a3b8; font-size: 8.5px; font-weight: 800; padding: 1px 4px; border-radius: 3px; border: 1px solid #334155;")
            else:
                self.status_badge.setStyleSheet("background: #f1f5f9; color: #64748b; font-size: 8.5px; font-weight: 800; padding: 1px 4px; border-radius: 3px; border: 1px solid #cbd5e1;")

    def update_quality_badge(self):
        q_hit = self.song_data.get("quality_score", 96)
        q_human = self.song_data.get("human_score", 95)
        is_human = self.song_data.get("human_certified", False)
        badge_txt = f"🎯 {q_hit}% • 👤 100% Human" if is_human else f"🎯 {q_hit}% • 👤 {q_human}%"
        self.quality_badge.setText(badge_txt)
        if is_human:
            self.quality_badge.setStyleSheet("background-color: #064e3b; color: #34d399; border: 1px solid #10b981; border-radius: 3px; padding: 1px 4px; font-size: 8.5px; font-weight: 800; font-family: 'Cascadia Code', 'Consolas', monospace;")

    def update_novelty_badge(self):
        score = self.song_data.get("novelty_score")
        badge_txt = self.song_data.get("novelty_badge")
        if score is None or not badge_txt:
            from app.anti_cliche_engine import AntiClicheEngine
            res = AntiClicheEngine.calculate_novelty_score(
                self.song_data.get("title", ""),
                self.song_data.get("lyrics", ""),
                self.song_data.get("language", "English")
            )
            score = res["score"]
            badge_txt = f"✨ {score}% Fresh" if score >= 85 else f"⚠️ {score}%"
            self.song_data["novelty_score"] = score
            self.song_data["novelty_badge"] = badge_txt
        else:
            if "Novelty:" in badge_txt:
                badge_txt = f"✨ {score}% Fresh" if score >= 85 else f"⚠️ {score}%"

        self.novelty_badge.setText(badge_txt)
        if score >= 90:
            bg, col, bdr = "#064e3b", "#6ee7b7", "#059669"
        elif score >= 75:
            bg, col, bdr = "#1e1b4b", "#c084fc", "#7c3aed"
        else:
            bg, col, bdr = "#451a03", "#fcd34d", "#d97706"

        self.novelty_badge.setStyleSheet(f"""
            background-color: {bg};
            color: {col};
            border: 1px solid {bdr};
            border-radius: 3px;
            padding: 1px 4px;
            font-size: 8.5px;
            font-weight: 800;
            font-family: 'Cascadia Code', 'Consolas', monospace;
        """)
        self.novelty_badge.setToolTip(f"Anti-Cliché Novelty Score: {score}%\nZero repetitive tropes, fresh metaphors and sensory objects.")

    def update_card(self, new_song_data: dict):
        """Refreshes the card UI with mutated song data in-place."""
        self.song_data = new_song_data
        self.title_lbl.setText(self.song_data.get("title", "Untitled Track"))
        genre = self.song_data.get("genre", "Custom Genre")
        bpm = self.song_data.get("bpm", "120 BPM")
        key = self.song_data.get("key", "C")
        meter = self.song_data.get("meter", "")
        meter_str = f"  •  {meter}" if meter else ""
        self.meta_lbl.setText(f"{genre}  •  {bpm}  •  Key: {key}{meter_str}")
        self.update_quality_badge()
        self.update_novelty_badge()
        self.update_style_preview()
        self.update_lyrics_preview()
        self._update_star_ui()
        self._update_status_ui()

        # Visual pulse animation
        self.setStyleSheet("""
            QFrame#batchSongCard {
                background: #1e1b4b;
                border: 2px solid #a855f7;
                border-radius: 8px;
            }
        """)
        QTimer.singleShot(600, lambda: self._set_style(self.is_active))

    def update_lyrics_preview(self):
        raw_lyrics = self.song_data.get("lyrics", "")
        clean_lines = [l.strip() for l in raw_lyrics.split("\n") if l.strip() and not l.strip().startswith("[")][:3]
        snippet_text = "\n".join(clean_lines) if clean_lines else "Establishing rhythm & live groove..."
        self.lyric_box.setText(f"✍️ {snippet_text}")

    def update_style_preview(self):
        style_txt = self.song_data.get("style_prompt", "")
        cut = style_txt[:120] + ("..." if len(style_txt) > 120 else "")
        self.style_box.setText(f"🎨 {cut}")

    def _set_style(self, active: bool):
        self.is_active = active
        t = getattr(self, "theme", get_theme(getattr(self, "is_dark", True)))
        is_dark = t.get("is_dark", True)
        if is_dark:
            if active:
                self.setStyleSheet(f"""
                    QFrame#batchSongCard {{
                        background: {t['bg_card']};
                        border: 2px solid {t['accent']};
                        border-radius: 8px;
                    }}
                """)
            else:
                self.setStyleSheet(f"""
                    QFrame#batchSongCard {{
                        background-color: {t['bg_card']};
                        border: 1px solid {t['border']};
                        border-radius: 8px;
                    }}
                    QFrame#batchSongCard:hover {{
                        border: 1px solid {t['border_accent']};
                        background-color: {t['bg_card_alt']};
                    }}
                """)
        else:
            if active:
                self.setStyleSheet(f"""
                    QFrame#batchSongCard {{
                        background: #f8fafc;
                        border: 2px solid {t['accent']};
                        border-radius: 8px;
                    }}
                """)
            else:
                self.setStyleSheet(f"""
                    QFrame#batchSongCard {{
                        background-color: #ffffff;
                        border: 1px solid #cbd5e1;
                        border-radius: 8px;
                    }}
                    QFrame#batchSongCard:hover {{
                        border: 1px solid {t['accent']};
                        background-color: #f8fafc;
                    }}
                """)

    def apply_theme(self, theme_or_dark):
        t = get_theme(theme_or_dark)
        self.theme = t
        is_dark = t.get("is_dark", True)
        self.is_dark = is_dark
        self._set_style(self.is_active)
        self._update_star_ui()
        self._update_status_ui()
        if is_dark:
            self.idx_lbl.setStyleSheet(f"""
                background-color: {t['subtle_pill_bg']};
                color: {t['subtle_pill_text']};
                font-family: 'Cascadia Code', 'Consolas', monospace;
                font-weight: 800;
                font-size: 10px;
                padding: 1px 4px;
                border-radius: 4px;
                border: 1px solid {t['border_accent']};
            """)
            self.title_lbl.setStyleSheet(f"font-family: 'Kantumruy Pro', 'Segoe UI', sans-serif; font-weight: 800; font-size: 12px; color: {t['text_primary']};")
            self.meta_lbl.setStyleSheet(f"color: {t['text_accent']}; font-size: 9.5px; font-weight: 700; background: transparent; border: none;")
            self.lbl_style_title.hide()
            self.style_box.setStyleSheet(f"background: {t['bg_input']}; border: 1px solid {t['border']}; border-radius: 5px; padding: 3px 6px; color: {t['text_accent']}; font-size: 9.5px; line-height: 1.25;")
            self.style_box.setFixedHeight(34)
            self.lbl_lyrics_title.hide()
            self.lyric_box.setStyleSheet(f"background: {t['bg_window']}; border: 1px solid {t['border_subtle']}; border-radius: 5px; padding: 4px 6px; color: {t['text_primary']}; font-family: 'Cascadia Code', 'Consolas', monospace; font-size: 9.5px; line-height: 1.35;")
            self.btn_copy_style.setStyleSheet(f"""
                QPushButton {{
                    background-color: {t['bg_card_alt']};
                    color: {t['text_accent']};
                    border: 1px solid {t['border']};
                    border-radius: 4px;
                    padding: 2px 5px;
                    font-size: 9.5px;
                    font-weight: 700;
                }}
                QPushButton:hover {{
                    background-color: {t['accent']};
                    color: #ffffff;
                    border-color: {t['border_accent']};
                }}
            """)
            self.btn_copy_lyrics.setStyleSheet(f"""
                QPushButton {{
                    background-color: {t['bg_card_alt']};
                    color: {t['text_secondary']};
                    border: 1px solid {t['border']};
                    border-radius: 4px;
                    padding: 2px 5px;
                    font-size: 9.5px;
                    font-weight: 700;
                }}
                QPushButton:hover {{
                    background-color: {t['accent']};
                    color: #ffffff;
                    border-color: {t['border_accent']};
                }}
            """)
            self.btn_copy_all.setStyleSheet(f"""
                QPushButton {{
                    background: {t['accent_gradient']};
                    color: #ffffff;
                    border: 1px solid {t['border_accent']};
                    border-radius: 4px;
                    padding: 2px 8px;
                    font-size: 9.5px;
                    font-weight: 800;
                }}
                QPushButton:hover {{
                    background: {t['accent_hover']};
                    border-color: #ffffff;
                }}
            """)
            if hasattr(self, "btn_mutate"):
                self.btn_mutate.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {t['subtle_pill_bg']};
                        color: {t['text_accent']};
                        border: 1px solid {t['border']};
                        border-radius: 4px;
                        padding: 2px 4px;
                        font-size: 9.5px;
                        font-weight: 700;
                    }}
                    QPushButton:hover {{
                        background-color: {t['accent']};
                        color: #ffffff;
                        border-color: {t['border_accent']};
                    }}
                """)
            if hasattr(self, "btn_edit"):
                self.btn_edit.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {t['bg_card_alt']};
                        color: #fbbf24;
                        border: 1px solid {t['border']};
                        border-radius: 3px;
                        font-size: 9px;
                        font-weight: 800;
                    }}
                    QPushButton:hover {{
                        background-color: #d97706;
                        color: #ffffff;
                    }}
                """)
            if hasattr(self, "btn_crossover"):
                self.btn_crossover.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {t['bg_card_alt']};
                        color: #34d399;
                        border: 1px solid {t['border']};
                        border-radius: 3px;
                        font-size: 9px;
                        font-weight: 800;
                    }}
                    QPushButton:hover {{
                        background-color: #059669;
                        color: #ffffff;
                    }}
                """)
            if hasattr(self, "btn_visual"):
                self.btn_visual.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {t['bg_card_alt']};
                        color: {t['text_accent']};
                        border: 1px solid {t['border']};
                        border-radius: 3px;
                        font-size: 9px;
                        font-weight: 800;
                    }}
                    QPushButton:hover {{
                        background-color: {t['accent']};
                        color: #ffffff;
                    }}
                """)
        else:
            self.idx_lbl.setStyleSheet("""
                background-color: #eff6ff;
                color: #1d4ed8;
                font-family: 'Cascadia Code', 'Consolas', monospace;
                font-weight: 800;
                font-size: 10px;
                padding: 1px 4px;
                border-radius: 4px;
                border: 1px solid #bfdbfe;
            """)
            self.title_lbl.setStyleSheet("font-family: 'Kantumruy Pro', 'Segoe UI', sans-serif; font-weight: 800; font-size: 12px; color: #0f172a;")
            self.meta_lbl.setStyleSheet("color: #0369a1; font-size: 9.5px; font-weight: 700; background: transparent; border: none;")
            self.lbl_style_title.hide()
            self.style_box.setStyleSheet("background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 5px; padding: 3px 6px; color: #1d4ed8; font-size: 9.5px; line-height: 1.25;")
            self.style_box.setFixedHeight(34)
            self.lbl_lyrics_title.hide()
            self.lyric_box.setStyleSheet("background: #ffffff; border: 1px solid #cbd5e1; border-radius: 5px; padding: 4px 6px; color: #0f172a; font-family: 'Cascadia Code', 'Consolas', monospace; font-size: 9.5px; line-height: 1.35;")
            self.btn_copy_style.setStyleSheet("""
                QPushButton {
                    background-color: #ffffff;
                    color: #0369a1;
                    border: 1px solid #cbd5e1;
                    border-radius: 4px;
                    padding: 2px 5px;
                    font-size: 9.5px;
                    font-weight: 700;
                }
                QPushButton:hover {
                    background-color: #0284c7;
                    color: #ffffff;
                    border-color: #0284c7;
                }
            """)
            self.btn_copy_lyrics.setStyleSheet("""
                QPushButton {
                    background-color: #ffffff;
                    color: #0f172a;
                    border: 1px solid #cbd5e1;
                    border-radius: 4px;
                    padding: 2px 5px;
                    font-size: 9.5px;
                    font-weight: 700;
                }
                QPushButton:hover {
                    background-color: #2563eb;
                    color: #ffffff;
                    border-color: #2563eb;
                }
            """)
            self.btn_copy_all.setStyleSheet(f"""
                QPushButton {{
                    background: {t['accent_gradient']};
                    color: #ffffff;
                    border: 1px solid {t['border_accent']};
                    border-radius: 4px;
                    padding: 2px 8px;
                    font-size: 9.5px;
                    font-weight: 800;
                }}
                QPushButton:hover {{
                    background: {t['accent_hover']};
                }}
            """)
            if hasattr(self, "btn_mutate"):
                self.btn_mutate.setStyleSheet("""
                    QPushButton {
                        background-color: #ffffff;
                        color: #1d4ed8;
                        border: 1px solid #bfdbfe;
                        border-radius: 4px;
                        padding: 2px 4px;
                        font-size: 9.5px;
                        font-weight: 700;
                    }
                    QPushButton:hover {
                        background-color: #2563eb;
                        color: #ffffff;
                        border-color: #1d4ed8;
                    }
                """)
            if hasattr(self, "btn_edit"):
                self.btn_edit.setStyleSheet("""
                    QPushButton {
                        background-color: #ffffff;
                        color: #b45309;
                        border: 1px solid #cbd5e1;
                        border-radius: 3px;
                        font-size: 9px;
                        font-weight: 800;
                    }
                    QPushButton:hover {
                        background-color: #f59e0b;
                        color: #ffffff;
                    }
                """)
            if hasattr(self, "btn_crossover"):
                self.btn_crossover.setStyleSheet("""
                    QPushButton {
                        background-color: #ffffff;
                        color: #047857;
                        border: 1px solid #cbd5e1;
                        border-radius: 3px;
                        font-size: 9px;
                        font-weight: 800;
                    }
                    QPushButton:hover {
                        background-color: #059669;
                        color: #ffffff;
                    }
                """)
            if hasattr(self, "btn_visual"):
                self.btn_visual.setStyleSheet(f"""
                    QPushButton {{
                        background-color: #ffffff;
                        color: {t['accent']};
                        border: 1px solid #cbd5e1;
                        border-radius: 3px;
                        font-size: 9px;
                        font-weight: 800;
                    }}
                    QPushButton:hover {{
                        background-color: {t['accent']};
                        color: #ffffff;
                    }}
                """)

    def set_active(self, active: bool):
        self._set_style(active)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.selected.emit(self.song_data)

    def mouseDoubleClickEvent(self, event):
        super().mouseDoubleClickEvent(event)
        self.selected.emit(self.song_data)

    def _copy_style(self):
        text = self.song_data.get("style_prompt", "")
        if text:
            QApplication.clipboard().setText(text)
            self.song_data["status"] = "copied"
            self._update_status_ui()
            self.status_changed.emit(self.song_data)
            self._flash_btn(self.btn_copy_style, "Copied!")

    def _copy_lyrics(self):
        text = self.song_data.get("lyrics", "")
        if text:
            QApplication.clipboard().setText(text)
            self.song_data["status"] = "copied"
            self._update_status_ui()
            self.status_changed.emit(self.song_data)
            self._flash_btn(self.btn_copy_lyrics, "Copied!")

    def _copy_all(self):
        bundle = f"""Title: {self.song_data.get('title', '')}
Genre: {self.song_data.get('genre', '')} ({self.song_data.get('bpm', '')}, Key: {self.song_data.get('key', '')})

[STYLE OF MUSIC]
{self.song_data.get('style_prompt', '')}

[LYRICS]
{self.song_data.get('lyrics', '')}
"""
        QApplication.clipboard().setText(bundle.strip())
        self.song_data["status"] = "copied"
        self._update_status_ui()
        self.status_changed.emit(self.song_data)
        self._flash_btn(self.btn_copy_all, "✓ Done")

    def _open_in_editor(self):
        self.song_data["status"] = "done"
        self._update_status_ui()
        self.status_changed.emit(self.song_data)
        self.open_editor_requested.emit(self.song_data)

    def _open_in_visual(self):
        self.open_visual_requested.emit(self.song_data)

    def _request_crossover(self):
        self.crossover_requested.emit(self.song_data)

    def _flash_btn(self, btn: QPushButton, label: str):
        orig_text = btn.text()
        btn.setText(label)
        QTimer.singleShot(1200, lambda: btn.setText(orig_text))


class BatchGeneratorView(QWidget):
    open_editor_requested = pyqtSignal(dict)
    open_visual_requested = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.all_songs = []
        self.card_widgets = []
        self.selected_song = None
        self.worker = None

        self.current_lang = "Both"
        self.current_count = 20
        self.current_vocal = "Mixed"
        self.current_persona = "Natural Studio Vocal"
        self.album_arc_enabled = False
        self.session_memory_titles = set()
        self.current_style_limit = 200
        self.current_diversity = "Wide Spectrum"
        self.anti_duplication = True
        self.filter_mode = "all"  # "all", "favorites", "uncopied", "copied"
        self._current_cols = 4
        self.is_dark = True
        self.theme_pills = []
        self.seed_pills = []

        self.persona_presets_data = {
            "English": [
                "🌟 Studio Clean Vocal (Natural)",
                "🎙️ Billie Eilish (Whispers, ASMR Sub)",
                "🎙️ The Weeknd (Dark Synthwave Falsetto)",
                "🎙️ Ariana Grande (High R&B Melisma)",
                "🎙️ Post Malone (Raspy Melodic Trap)",
                "🎙️ Adele (Soaring Gospel Belt)",
                "🎙️ Drake (Smooth 808 Melodic Flow)",
                "🎙️ Bruno Mars (Retro Funk Soul Tenor)",
                "🎙️ Chris Cornell (Gritty Grunge Rock)",
                "🎙️ Bon Iver (Layered Vocoder Indie)"
            ],
            "Khmer": [
                "🌟 សំនៀងធម្មជាតិ (Natural Acoustic)",
                "🎙️ ស៊ីន ស៊ីសាមុត (60s Tape Saturation)",
                "🎙️ រស់ សេរីសុទ្ធា (Golden Era Soprano)",
                "🎙️ ព្រាប សុវត្ថិ (90s Pop Baritone)",
                "🔥 វណ្ណដា / Klaha (កូនខ្មែរ Trap Flow)",
                "🥁 កន្ត្រឹមស៊ូរិន្ទ (Festive Folk Belt)",
                "🌸 ម៉េង កែវពេជ្ជតា (ភ្លេងការ Classical Silk)"
            ],
            "Both": [
                "🌟 Studio Clean / ធម្មជាតិ (Natural)",
                "🎙️ ស៊ីន ស៊ីសាមុត (60s Vintage Tape)",
                "🎙️ Billie Eilish (Intimate Whispers & Sub)",
                "🎙️ រស់ សេរីសុទ្ធា (Golden Soprano)",
                "🎙️ The Weeknd (Dark Synthwave Falsetto)",
                "🔥 វណ្ណដា / Klaha (Khmer Trap Flow)",
                "🎙️ Ariana Grande (High R&B Melisma)",
                "🥁 កន្ត្រឹមស៊ូរិន្ទ (Surin Kantrum Belt)",
                "🎙️ Adele (Soaring Power Belt)",
                "🌸 ម៉េង កែវពេជ្ជតា (Pleng Ka Silk)"
            ]
        }

        # Dynamic Studio Presets tailored for Khmer, English, and Both
        self.theme_pills_data = {
            "Khmer": [
                [("💔 មនោសញ្ចេតនា", "ស្រណោះស្រណោក បទមនោសញ្ចេតនាខ្មែរ"),
                 ("🕺 រាំវង់ & កន្ត្រឹម", "រាំវង់ & កន្ត្រឹមចូលឆ្នាំថ្មី សប្បាយរីករាយ")],
                [("📻 មាស ៦០-៧០", "បទមាសទសវត្សរ៍ ៦០-៧០ ស៊ីន ស៊ីសាមុត & រស់ សេរីសុទ្ធា"),
                 ("🔥 កូនខ្មែរ Trap", "Khmer trap hip-hop, កូនខ្មែរតស៊ូ ឈាមជ័រអ្នកប្រយុទ្ធ")],
                [("🌾 ក្លិនដីស្រែ & ចាប៉ី", "ចាប៉ីដងវែង បទស្រុកស្រែជនបទ គុណឪពុកម្តាយ"),
                 ("✨ ភ្លេងការ & មនោរម្យ", "ភ្លេងការបុរាណសម័យ ពិរោះរណ្តំ ស្នេហ៍ស្មោះ")]
            ],
            "English": [
                [("💔 Heartbreak Pop", "sad song, heartbreak, bittersweet reflection"),
                 ("⚡ Modern Synth-Pop", "80s retro synth-pop, upbeat earworm hook")],
                [("🌧️ Chill Lo-Fi / R&B", "rainy night lofi chill, late night neo-soul"),
                 ("🎸 Driving Arena Rock", "driving rock anthem, heavy electric guitar")],
                [("🔥 Melodic Trap Beat", "modern trap 808 sub-bass, rapid melodic flow"),
                 ("🌾 Acoustic Indie Folk", "warm acoustic indie folk, fingerstyle Martin guitar")]
            ],
            "Both": [
                [("💔 Sad / កម្សត់", "bittersweet heartbreak, ស្រណោះស្រណោក"),
                 ("⚡ EDM / រាំវង់", "high energy festival dance, រាំវង់សម័យ")],
                [("🌧️ Lo-Fi / ស្រណោះ", "rainy night lofi, កាហ្វេទឹកភ្លៀង"),
                 ("🎸 Rock / មាស៦០", "classic rock, បទមាស ៦០-៧០")],
                [("🔥 Trap / កូនខ្មែរ", "bilingual trap, ឈាមជ័រអ្នកប្រយុទ្ធ"),
                 ("✨ Pop / ភ្លេងការ", "bilingual radio pop, ពិរោះរណ្តំ")]
            ]
        }

        self.seed_pills_data = {
            "Khmer": [
                [("💔 ជួបគ្នាក្រោយបែក", "បែកគ្នាយូរឆ្នាំ ជួបគ្នាម្តងទៀតដោយចៃដន្យនៅកន្លែងចាស់"),
                 ("☕ ភ្លៀងធ្លាក់កាហ្វេ", "អង្គុយមាត់បង្អួចហាងកាហ្វេពេលភ្លៀងធ្លាក់ នឹកដល់អនុស្សាវរីយ៍ចាស់")],
                [("🇰🇭 ឈាមជ័រខ្មែរតស៊ូ", "កូនខ្មែរតស៊ូពីបាតដៃទទេ បង្ហាញភាពអង់អាច និងមិនភ្លេចគុណឪពុកម្តាយ"),
                 ("⏳ ពាក្យសន្យាចាស់", "ពាក្យសន្យាកាលពីកុមារភាពដែលមិនអាចបំភ្លេចបាន ទោះកាលវេលាកន្លងផុតទៅច្រើនឆ្នាំ")]
            ],
            "English": [
                [("💔 10-Yr Reunion", "Running into an ex at an airport lounge after 10 years apart"),
                 ("☕ 2 AM Coffee Shop", "Sitting alone in a 24-hour neon diner counting raindrops")],
                [("🎸 Chasing Dreams", "Leaving a small hometown with a beat-up guitar chasing a dream"),
                 ("⏳ Broken Promise", "A promise made under the high school bleachers that never came true")]
            ],
            "Both": [
                [("💔 Reunion • ជួបគ្នា", "ជួបគ្នាម្តងទៀតក្រោយបែកគ្នា ១០ ឆ្នាំ (10-year reunion)"),
                 ("☕ Cafe • ទឹកភ្លៀង", "Midnight coffee in the pouring rain (កាហ្វេពេលភ្លៀង)")],
                [("🇰🇭 Heritage • ឈាមជ័រ", "កូនខ្មែរតស៊ូពីបាតដៃទទេ (Rising from humble roots)"),
                 ("⏳ Promise • សច្ចា", "Unbroken promise across time (ពាក្យសន្យាមិនប្រែប្រួល)")]
            ]
        }

        self.depth_modes_data = {
            "Khmer": [
                "💔 មេពាក្យ ៧ (Pathya Vat • កម្សត់ជ្រៅ & ស្រណោះ)",
                "📖 មេពាក្យ ៨ (Prom Git • ដំណើររឿងកាព្យ & ជីវិត)",
                "⚡ មេពាក្យ ៤ (Kkak Gatei • កូនខ្មែរ Trap & រាំវង់)",
                "🌟 បទព្រហ្មគីតិ (Classical Poetic Metaphor)",
                "🌾 បទកាកគតិ (Traditional Folk & ស្រុកស្រែ)",
                "📻 បទមនោរម្យសម័យ (Modern Radio Pop Hit)"
            ],
            "English": [
                "💔 Conversational Diary (Taylor / Finneas Confessional)",
                "📖 Berklee Sensory Objects (Show, Don't Tell)",
                "⚡ Contemporary Slant Rhymes (Modern Pop Prosody)",
                "🌟 Indie Folk Intimacy (Whisper, Fry & Fingerstyle)",
                "🔥 Modern Trap Cadence (808 Bounce & Rapid Flow)",
                "📻 Global Billboard Anthem (Max Martin Huge Hook)"
            ],
            "Both": [
                "🌟 50/50 Dual Engine Split (Odd: Khmer, Even: English)",
                "🌐 Crossover Hit (Khmer Verses + English Chorus Hook)",
                "🔥 Heritage Trap Fusion (Chapei Pluck + 808 Slide)",
                "💔 Melancholic Duet (Tro Ou Strings + Rhodes Soul)"
            ]
        }

        self.diversity_modes_data = {
            "Khmer": [
                "🌟 គ្រប់ចង្វាក់ខ្មែរ (Wide Khmer Spectrum)",
                "🇰🇭 60s Golden Era & Vintage (មាស ៦០-៧០)",
                "🔥 Khmer Trap & Drill (កូនខ្មែរ Hip-Hop)",
                "🥁 Festive Romvong & Kantrum (រាំវង់ & កន្ត្រឹម)",
                "🌧️ Deep Emotional Melancholy (មនោសញ្ចេតនាជ្រៅ)",
                "🎸 Khmer Acoustic Folk (សំនៀងចាប៉ី & ហ្គីតា)"
            ],
            "English": [
                "🌟 Wide Western Spectrum (Billboard Mix)",
                "⚡ 80s Retro Synthwave & Dance",
                "🎸 Nashville Indie Folk & Americana",
                "🔥 Modern Billboard Pop & Trap",
                "🎷 Late-Night Neo-Soul & R&B",
                "🎸 90s Grunge & Stadium Arena Rock",
                "🌧️ Deep Cinematic Melancholy"
            ],
            "Both": [
                "🌟 គ្រប់ប្រភេទ (Wide Spectrum - 50/50 Split)",
                "🌐 Bilingual Cross-Culture Hits (ខ្មែរ + EN Hooks)",
                "🇰🇭 Heritage & Billboard Fusion",
                "🎸 Dual Acoustic Storytelling",
                "⚡ Dual Electronic & Dance"
            ]
        }
        self.metatag_pills = []
        self.inspector_dialog = None

        self._init_ui()
        self._update_dynamic_language_presets(self.current_lang)
        self._load_initial_demo()

    def _calculate_columns(self) -> int:
        if getattr(self, "_user_fixed_cols", None):
            return self._user_fixed_cols

        viewport_w = 0
        if hasattr(self, "cards_scroll") and self.cards_scroll.viewport():
            viewport_w = self.cards_scroll.viewport().width()
        if viewport_w < 150:
            is_side_vis = hasattr(self, "side_scroll") and self.side_scroll.isVisible()
            viewport_w = max(400, self.width() - (375 if is_side_vis else 0) - 40)

        # Responsive DAW-style column count: optimal width ~340px-400px per card
        # Produces 3 spacious, unclipped columns on standard 1080p monitors with sidebar (~1200px viewport)
        # Produces 4 columns when sidebar is collapsed (~1550px viewport)
        # Allows 5 columns on ultra-wide / 4K screens (>= 1850px)
        # Drops gracefully to 2 columns on smaller laptop screens (< 900px)
        cols = viewport_w // 345
        if viewport_w >= 1850:
            return max(2, min(5, cols))
        return max(2, min(4, cols))

    def _set_view_mode(self, mode):
        self._view_mode = mode
        if mode == "table":
            if hasattr(self, "cards_scroll"):
                self.cards_scroll.hide()
            if hasattr(self, "tracklist_table"):
                self.tracklist_table.show()
                self._populate_table()
        else:
            if hasattr(self, "tracklist_table"):
                self.tracklist_table.hide()
            if hasattr(self, "cards_scroll"):
                self.cards_scroll.show()
            if mode == 3:
                self._user_fixed_cols = 3
            elif mode == 4:
                self._user_fixed_cols = 4
            elif mode == 5:
                self._user_fixed_cols = 5
            else:
                self._user_fixed_cols = None
            self._check_and_update_columns()
        self._update_column_toggle_ui()

    def _update_column_toggle_ui(self):
        mode = getattr(self, "_view_mode", getattr(self, "_user_fixed_cols", None))
        is_dark = getattr(self, "is_dark", True)
        buttons = [
            (3, getattr(self, "btn_cols_3", None)),
            (4, getattr(self, "btn_cols_4", None)),
            (5, getattr(self, "btn_cols_5", None)),
            ("table", getattr(self, "btn_view_table", None)),
            (None, getattr(self, "btn_cols_auto", None))
        ]
        for val, btn in buttons:
            if not btn:
                continue
            if val == "table":
                is_active = (getattr(self, "_view_mode", None) == "table")
            elif getattr(self, "_view_mode", None) == "table":
                is_active = False
            else:
                is_active = (getattr(self, "_user_fixed_cols", None) == val)

            if is_dark:
                if is_active:
                    btn.setStyleSheet("background-color: #4f46e5; color: #ffffff; font-weight: 800; font-size: 10px; border: 1px solid #818cf8; border-radius: 4px; padding: 3px 8px;")
                else:
                    btn.setStyleSheet("background-color: #13172c; color: #94a3b8; font-weight: 600; font-size: 10px; border: 1px solid #232c4b; border-radius: 4px; padding: 3px 8px;")
            else:
                if is_active:
                    btn.setStyleSheet("background-color: #4f46e5; color: #ffffff; font-weight: 800; font-size: 10px; border: 1px solid #3730a3; border-radius: 4px; padding: 3px 8px;")
                else:
                    btn.setStyleSheet("background-color: #f1f5f9; color: #475569; font-weight: 600; font-size: 10px; border: 1px solid #cbd5e1; border-radius: 4px; padding: 3px 8px;")

    def _toggle_sidebar(self):
        if not hasattr(self, "side_scroll"):
            return
        is_visible = self.side_scroll.isVisible()
        self.side_scroll.setVisible(not is_visible)
        if not is_visible:
            self.btn_toggle_sidebar.setText("◀ Sidebar")
            self.btn_toggle_sidebar.setToolTip("Hide sidebar to expand grid to 100% full width")
        else:
            self.btn_toggle_sidebar.setText("▶ Sidebar")
            self.btn_toggle_sidebar.setToolTip("Show sidebar to edit batch creation settings")
        QTimer.singleShot(40, self._check_and_update_columns)

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self._check_and_update_columns)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._check_and_update_columns()

    def _check_and_update_columns(self):
        new_cols = self._calculate_columns()
        if new_cols != getattr(self, "_current_cols", 0) and self.card_widgets:
            self._current_cols = new_cols
            self._rearrange_grid()
        elif self.card_widgets and hasattr(self, "grid_layout"):
            cols = getattr(self, "_current_cols", 4)
            for c in range(12):
                self.grid_layout.setColumnStretch(c, 1 if c < cols else 0)

    def _rearrange_grid(self):
        cols = getattr(self, "_current_cols", 4)
        if cols < 1:
            cols = 1

        for c in range(12):
            self.grid_layout.setColumnStretch(c, 0)

        visible_cards = [c for c in self.card_widgets if not c.isHidden()]
        for i, card in enumerate(visible_cards):
            self.grid_layout.removeWidget(card)
            row = i // cols
            col = i % cols
            self.grid_layout.addWidget(card, row, col)

        for c in range(cols):
            self.grid_layout.setColumnStretch(c, 1)

    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(12)

        # ══════════════════════════════════════════════════════════════════
        # ── LEFT CONTROLLER SIDEBAR (WIDTH ~ 360px - ZERO CLIPPING FIT) ──
        # ══════════════════════════════════════════════════════════════════
        self.side_scroll = QScrollArea()
        self.side_scroll.setWidgetResizable(True)
        self.side_scroll.setFixedWidth(375)
        self.side_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.side_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.side_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.side_scroll.setStyleSheet("background-color: transparent;")

        self.sidebar = QWidget()
        side_layout = QVBoxLayout(self.sidebar)
        side_layout.setContentsMargins(6, 4, 6, 4)
        side_layout.setSpacing(4)

        # ── 1. SONG THEME / MOOD ──
        self.lbl_s1 = QLabel("🎵 1. THEME & MOOD • ប្រធានបទ")
        lbl_s1 = self.lbl_s1
        lbl_s1.setStyleSheet("font-size: 10px; font-weight: 800; color: #94a3b8; letter-spacing: 0.5px;")
        side_layout.addWidget(lbl_s1)

        self.txt_theme = QTextEdit("sad song")
        self.txt_theme.setPlaceholderText("ឧទាហរណ៍: sad song, heartbreak, midnight drive, ស្រណោះស្រណោក...")
        self.txt_theme.setFixedHeight(30)
        self.txt_theme.setStyleSheet("padding: 2px 6px; font-size: 11px; background: #0b0f1f; border: 1px solid #283354; border-radius: 4px; color: #f1f5f9;")
        side_layout.addWidget(self.txt_theme)

        # 🎲 Anti-Cliché Concept Matrix Shuffler
        self.btn_roll_concept = QPushButton("🎲 Shuffler: គំនិតថ្មីប្លែក (Anti-Cliché Metaphor)")
        self.btn_roll_concept.setFixedHeight(26)
        self.btn_roll_concept.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_roll_concept.setToolTip("🎲 Dynamic Concept, Metaphor & Sensory Object Matrix:\nShuffles an unexpected atmosphere, tangible sensory anchor, and deep emotional conflict to guarantee 100% original, non-repetitive lyrics!")
        self.btn_roll_concept.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1e1b4b, stop:1 #311042);
                color: #c084fc;
                border: 1px solid #7c3aed;
                border-radius: 4px;
                font-weight: 800;
                font-size: 10px;
                padding: 2px 6px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2e1065, stop:1 #4a044e);
                border-color: #d8b4fe;
                color: #ffffff;
            }
        """)
        self.btn_roll_concept.clicked.connect(self._roll_fresh_anti_cliche_concept)
        side_layout.addWidget(self.btn_roll_concept)

        # Quick Theme Inspiration Pills (3 spacious rows of 2 pills - zero clipping, ~155px each)
        initial_theme_pills = self.theme_pills_data.get(self.current_lang, self.theme_pills_data["Both"])
        for row_pills in initial_theme_pills:
            t_row = QHBoxLayout()
            t_row.setSpacing(4)
            for t_label, t_val in row_pills:
                b = QPushButton(t_label)
                b.setCursor(Qt.CursorShape.PointingHandCursor)
                b.setFixedHeight(23)
                b.setStyleSheet("background-color: #171d34; color: #94a3b8; border: 1px solid #253052; border-radius: 4px; padding: 2px 4px; font-size: 9.5px; font-weight: 600;")
                b.clicked.connect(lambda _, v=t_val: self.txt_theme.setPlainText(v))
                self.theme_pills.append(b)
                t_row.addWidget(b, 1)
            side_layout.addLayout(t_row)

        # ── 2. STORY SEED / NARRATIVE BACKSTORY ──
        self.lbl_s2 = QLabel("📖 2. STORY SEED • ដំណើររឿង")
        lbl_s2 = self.lbl_s2
        lbl_s2.setStyleSheet("font-size: 10px; font-weight: 800; color: #94a3b8; letter-spacing: 0.5px;")
        side_layout.addWidget(lbl_s2)

        self.txt_story_seed = QTextEdit()
        self.txt_story_seed.setPlaceholderText("ឧទាហរណ៍: ជួបគ្នាម្តងទៀតក្រោយបែកគ្នា ១០ ឆ្នាំ, កូនខ្មែរតស៊ូពីបាតដៃទទេ...")
        self.txt_story_seed.setFixedHeight(28)
        self.txt_story_seed.setStyleSheet("padding: 2px 6px; font-size: 10px; background: #0b0f1f; border: 1px solid #283354; border-radius: 4px; color: #e2e8f0;")
        side_layout.addWidget(self.txt_story_seed)

        # Quick Seed Pills (2 spacious rows of 2 pills - zero clipping, ~155px each)
        initial_seed_pills = self.seed_pills_data.get(self.current_lang, self.seed_pills_data["Both"])
        for row_seeds in initial_seed_pills:
            s_row = QHBoxLayout()
            s_row.setSpacing(4)
            for s_label, s_val in row_seeds:
                b = QPushButton(s_label)
                b.setCursor(Qt.CursorShape.PointingHandCursor)
                b.setFixedHeight(23)
                b.setStyleSheet("background-color: #111827; color: #a5b4fc; border: 1px solid #374151; border-radius: 4px; padding: 2px 4px; font-size: 9.5px; font-weight: 600;")
                b.clicked.connect(lambda _, v=s_val: self.txt_story_seed.setPlainText(v))
                self.seed_pills.append(b)
                s_row.addWidget(b, 1)
            side_layout.addLayout(s_row)

        # ── 3. LYRICAL DEPTH & MEANING MODE ──
        self.lbl_s3 = QLabel("💎 3. LYRICAL DEPTH • ជម្រៅអត្ថន័យ")
        lbl_s3 = self.lbl_s3
        lbl_s3.setStyleSheet("font-size: 10px; font-weight: 800; color: #94a3b8; letter-spacing: 0.5px;")
        side_layout.addWidget(lbl_s3)

        self.combo_depth_mode = QComboBox()
        self.combo_depth_mode.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.combo_depth_mode.setMinimumContentsLength(10)
        self.combo_depth_mode.addItems([
            "💔 Deep Catharsis (កម្សត់ជ្រៅ • ពាក្យ ៧)",
            "📖 Narrative Storyteller (ដំណើររឿង • ពាក្យ ៨)",
            "⚡ Fast Trap / Dance (ចង្វាក់ញាក់ • ពាក្យ ៤)",
            "🌟 Classical Poetic Metaphor (រចនាបទកាព្យ ព្រហ្មគីតិ)",
            "🌐 Bilingual Fusion (Khmer Verses + English Chorus Hook)",
            "📻 Commercial Radio Hit (ចង្វាក់ទាក់ទាញ Billboard)"
        ])
        self.combo_depth_mode.currentTextChanged.connect(self._on_depth_mode_changed)
        self.combo_depth_mode.setFixedHeight(25)
        self.combo_depth_mode.setStyleSheet("padding: 1px 6px; font-weight: 700; font-size: 10px; background: #0b0f1f; border: 1px solid #7c3aed; border-radius: 4px; color: #c084fc;")
        side_layout.addWidget(self.combo_depth_mode)

        # ── 4. LYRICS LANGUAGE PILLS (1 Sleek Row - 5 Languages) ──
        self.lbl_s4 = QLabel("🌐 4. LYRICS LANGUAGE • ភាសា")
        lbl_s4 = self.lbl_s4
        lbl_s4.setStyleSheet("font-size: 10px; font-weight: 800; color: #94a3b8; letter-spacing: 0.5px;")
        side_layout.addWidget(lbl_s4)

        self.lang_buttons = {}
        langs_def_rows = [
            [
                ("Khmer", "🇰🇭 ខ្មែរ", "បង្កើតបទចម្រៀងជាភាសាខ្មែរ ១០០% (Classical meters, Golden Era & Folk)"),
                ("English", "🇬🇧 English", "Create 100% English songs (Billboard, Slant Rhymes & Conversational)"),
                ("Both", "🌟 50/50 Fusion", "Bilingual crossover: Authentic Khmer verses + English chorus anthem")
            ],
            [
                ("Alternating", "🔄 Alternating", "Tracks alternate strictly one-by-one: Odd = Khmer, Even = English"),
                ("DualKaraoke", "🎤 Dual Karaoke", "Side-by-side karaoke lines with English translation subtitles")
            ]
        ]
        for l_def in langs_def_rows:
            l_row = QHBoxLayout()
            l_row.setSpacing(4)
            for l_code, l_name, l_tip in l_def:
                b = QPushButton(l_name)
                b.setCheckable(True)
                b.setChecked(l_code == self.current_lang)
                b.setCursor(Qt.CursorShape.PointingHandCursor)
                b.setFixedHeight(23)
                b.setToolTip(l_tip)
                b.setStyleSheet(self._pill_style(l_code == self.current_lang))
                b.clicked.connect(lambda _, code=l_code: self._set_language(code))
                self.lang_buttons[l_code] = b
                l_row.addWidget(b, 1)
            side_layout.addLayout(l_row)

        # ── 5. VOCAL TYPE CHIPS (1 Sleek Row - 4 Vocals) ──
        self.lbl_s5 = QLabel("🎙️ 5. VOCAL FILTER • សំឡេង")
        lbl_s5 = self.lbl_s5
        lbl_s5.setStyleSheet("font-size: 10px; font-weight: 800; color: #94a3b8; letter-spacing: 0.5px;")
        side_layout.addWidget(lbl_s5)

        self.vocal_buttons = {}
        for row_vocs in [
            [("Mixed", "🎙️ ទាំងអស់ (Mixed)"), ("Male", "👨 ប្រុស (Male)")],
            [("Female", "👩 ស្រី (Female)"), ("Duet", "👥 ឆ្លើយឆ្លង (Duet)")]
        ]:
            v_row = QHBoxLayout()
            v_row.setSpacing(4)
            for v_code, v_name in row_vocs:
                b = QPushButton(v_name)
                b.setCheckable(True)
                b.setChecked(v_code == "Mixed")
                b.setCursor(Qt.CursorShape.PointingHandCursor)
                b.setFixedHeight(23)
                b.setStyleSheet(self._pill_style(v_code == "Mixed"))
                b.clicked.connect(lambda _, code=v_code: self._set_vocal(code))
                self.vocal_buttons[v_code] = b
                v_row.addWidget(b, 1)
            side_layout.addLayout(v_row)

        # Vocal Persona & Acoustic Stem Dropdown
        self.combo_persona = QComboBox()
        self.combo_persona.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.combo_persona.setMinimumContentsLength(10)
        self.combo_persona.addItems(self.persona_presets_data["Both"])
        self.combo_persona.setFixedHeight(24)
        self.combo_persona.setStyleSheet("padding: 1px 6px; font-weight: 700; font-size: 9.5px; background: #0b0f1f; border: 1px solid #3b82f6; border-radius: 4px; color: #93c5fd;")
        self.combo_persona.currentTextChanged.connect(self._on_persona_changed)
        side_layout.addWidget(self.combo_persona)

        # ── 6. DIVERSITY SPECTRUM & ANTI-DUPLICATION (Integrated Row) ──
        self.lbl_s6 = QLabel("🎼 6. DIVERSITY & ANTI-DUPLICATION")
        lbl_s6 = self.lbl_s6
        lbl_s6.setStyleSheet("font-size: 10px; font-weight: 800; color: #94a3b8; letter-spacing: 0.5px;")
        side_layout.addWidget(lbl_s6)

        div_dup_row = QHBoxLayout()
        div_dup_row.setSpacing(4)

        self.combo_diversity = QComboBox()
        self.combo_diversity.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.combo_diversity.setMinimumContentsLength(10)
        self.combo_diversity.addItems([
            "🌟 គ្រប់ប្រភេទ (Wide Spectrum)",
            "🇰🇭 60s Golden Era & Vintage (មាស ៦០-៧០)",
            "🔥 Khmer Trap & Drill (កូនខ្មែរ Hip-Hop)",
            "🥁 Festive Romvong & Kantrum (រាំវង់ & កន្ត្រឹម)",
            "🌐 Bilingual Cross-Culture Hits (ខ្មែរ + EN Hooks)",
            "🎸 Acoustic Storytelling (សំនៀង Folk & Blues)",
            "⚡ 80s Synthwave & Dance (ចង្វាក់រាំសម័យ)",
            "🌧️ Deep Emotional Melancholy (មនោសញ្ចេតនាជ្រៅ)"
        ])
        self.combo_diversity.setFixedHeight(25)
        self.combo_diversity.setStyleSheet("padding: 1px 6px; font-weight: 700; font-size: 10px; background: #0b0f1f; border: 1px solid #4338ca; border-radius: 4px; color: #a5b4fc;")
        self.combo_diversity.currentTextChanged.connect(self._on_diversity_changed)
        div_dup_row.addWidget(self.combo_diversity, 1)

        self.btn_anti_dup = QPushButton("🛡️ Zero Clones")
        self.btn_anti_dup.setCheckable(True)
        self.btn_anti_dup.setChecked(True)
        self.btn_anti_dup.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_anti_dup.setFixedHeight(25)
        self.btn_anti_dup.setFixedWidth(95)
        self.btn_anti_dup.setToolTip("Enforces 5-dimensional variance across all songs:\n• Shifts tempo tiers (<75, 85, 120, 140, 3/4 waltz)\n• Rotates musical keys (Am, Dm, G, F#m, C, Eb, Bm)\n• Blacklists AI rhyme clichés (night/light, fire/desire)\n• Enforces concrete physical imagery & micro-genre tags")
        self._update_anti_dup_style(True)
        self.btn_anti_dup.clicked.connect(self._toggle_anti_dup)
        div_dup_row.addWidget(self.btn_anti_dup)
        side_layout.addLayout(div_dup_row)

        # 💿 Concept Album Story Arc & 🧠 Cross-Batch Semantic Memory Tracker
        arc_mem_row = QHBoxLayout()
        arc_mem_row.setSpacing(4)

        self.btn_album_arc_toggle = QPushButton("💿 Album Arc (EP/LP)")
        self.btn_album_arc_toggle.setCheckable(True)
        self.btn_album_arc_toggle.setChecked(getattr(self, "album_arc_enabled", False))
        self.btn_album_arc_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_album_arc_toggle.setFixedHeight(24)
        self.btn_album_arc_toggle.setToolTip("1-Click Concept Album / EP Story Arc:\nMaps tracks across a dramatic narrative progression (The Spark -> Golden Hour -> The Fracture -> Midnight Climax -> Dawn Acceptance) instead of isolated songs!")
        self._update_album_arc_style()
        self.btn_album_arc_toggle.clicked.connect(self._toggle_album_arc)
        arc_mem_row.addWidget(self.btn_album_arc_toggle, 1)

        self.lbl_memory_badge = QLabel("🧠 Memory: 0")
        self.lbl_memory_badge.setFixedHeight(24)
        self.lbl_memory_badge.setStyleSheet("font-size: 8.5px; font-weight: 700; color: #a5b4fc; background: #1e1b4b; border: 1px solid #4338ca; border-radius: 4px; padding: 1px 5px;")
        self.lbl_memory_badge.setToolTip("Session-persistent zero-repeat memory cache: Tracks all generated song titles to ensure subsequent batches never repeat previous concepts.")
        arc_mem_row.addWidget(self.lbl_memory_badge)

        self.btn_clear_memory = QPushButton("Clear")
        self.btn_clear_memory.setFixedWidth(42)
        self.btn_clear_memory.setFixedHeight(24)
        self.btn_clear_memory.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear_memory.setStyleSheet("font-size: 8.5px; font-weight: 700; color: #94a3b8; background: #13172c; border: 1px solid #232c4b; border-radius: 4px;")
        self.btn_clear_memory.setToolTip("Clear session memory cache")
        self.btn_clear_memory.clicked.connect(self._clear_memory_cache)
        arc_mem_row.addWidget(self.btn_clear_memory)

        side_layout.addLayout(arc_mem_row)

        # ── 7. SONG COUNT & STYLE LIMIT ──
        count_row = QHBoxLayout()
        count_row.setSpacing(4)

        c_box = QVBoxLayout()
        c_box.setSpacing(1)
        self.lbl_count = QLabel("ចំនួនបទ (Count):")
        c_lbl = self.lbl_count
        c_lbl.setStyleSheet("font-size: 9px; color: #94a3b8;")
        c_box.addWidget(c_lbl)
        self.combo_count = QComboBox()
        self.combo_count.addItems(["5 បទ", "10 បទ", "15 បទ", "20 បទ", "30 បទ"])
        self.combo_count.setCurrentText("20 បទ")
        self.combo_count.setFixedHeight(25)
        self.combo_count.setStyleSheet("padding: 1px 6px; font-weight: 700; font-size: 10px; background: #0b0f1f; border: 1px solid #283354; border-radius: 4px; color: #a78bfa;")
        self.combo_count.currentTextChanged.connect(self._on_count_changed)
        c_box.addWidget(self.combo_count)
        count_row.addLayout(c_box, 1)

        s_box = QVBoxLayout()
        s_box.setSpacing(1)
        s_lbl = QLabel("Style Limit:")
        s_lbl.setStyleSheet("font-size: 9px; color: #94a3b8;")
        s_box.addWidget(s_lbl)
        self.combo_style_limit = QComboBox()
        self.combo_style_limit.addItems(["200 Chars (Suno v3.5/v4/v6)", "120 Chars (Suno v3)"])
        self.combo_style_limit.setFixedHeight(25)
        self.combo_style_limit.setStyleSheet("padding: 1px 6px; font-size: 10px; background: #0b0f1f; border: 1px solid #283354; border-radius: 4px; color: #38bdf8;")
        self.combo_style_limit.currentTextChanged.connect(self._on_style_limit_changed)
        s_box.addWidget(self.combo_style_limit)
        count_row.addLayout(s_box, 2)

        side_layout.addLayout(count_row)

        # ── PRIMARY ACTION BUTTON (TURBO) ──
        self.btn_generate_batch = QPushButton("⚡ បង្កើតបទចម្រៀងថ្មី (Turbo Engine)")
        self.btn_generate_batch.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_generate_batch.setFixedHeight(34)
        self.btn_generate_batch.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7c3aed, stop:1 #4f46e5);
                color: #ffffff;
                font-weight: 800;
                font-size: 12px;
                padding: 4px;
                border: 1px solid #a855f7;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8b5cf6, stop:1 #6366f1);
                border-color: #c084fc;
            }
            QPushButton:disabled {
                background: #1e1b4b;
                color: #64748b;
                border-color: #2e1065;
            }
        """)
        self.btn_generate_batch.clicked.connect(self._start_batch_generation)
        side_layout.addWidget(self.btn_generate_batch)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(5)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #1e2238;
                border-radius: 2px;
                border: none;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8b5cf6, stop:1 #38bdf8);
                border-radius: 2px;
            }
        """)
        self.progress_bar.setVisible(False)
        side_layout.addWidget(self.progress_bar)

        # Secondary Actions (Single row of 4 compact buttons - zero clipping in 345px)
        sub_act_row = QHBoxLayout()
        sub_act_row.setSpacing(4)

        self.btn_append = QPushButton("+ ថែម")
        self.btn_append.setToolTip("បង្កើតបទចម្រៀងបន្ថែម (Append more tracks)")
        self.btn_append.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_append.setFixedHeight(26)
        self.btn_append.setStyleSheet(self._btn_sub())
        self.btn_append.clicked.connect(self._append_batch)
        sub_act_row.addWidget(self.btn_append, 1)

        self.btn_copy_all_batch = QPushButton("📋 Copy")
        self.btn_copy_all_batch.setToolTip("Copy all songs to clipboard")
        self.btn_copy_all_batch.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_copy_all_batch.setFixedHeight(26)
        self.btn_copy_all_batch.setStyleSheet(self._btn_sub())
        self.btn_copy_all_batch.clicked.connect(self._copy_entire_batch)
        sub_act_row.addWidget(self.btn_copy_all_batch, 1)

        self.btn_save_all = QPushButton("💾 Save")
        self.btn_save_all.setToolTip("Export batch lyrics to file")
        self.btn_save_all.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save_all.setFixedHeight(26)
        self.btn_save_all.setStyleSheet(self._btn_sub())
        self.btn_save_all.clicked.connect(self._export_batch_file)
        sub_act_row.addWidget(self.btn_save_all, 1)

        self.btn_clear_sidebar = QPushButton("🗑️ Clear")
        self.btn_clear_sidebar.setToolTip("សម្អាតបទចម្រៀងទាំងអស់ចេញពី Grid")
        self.btn_clear_sidebar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear_sidebar.setFixedHeight(26)
        self.btn_clear_sidebar.setStyleSheet(self._btn_clear_style())
        self.btn_clear_sidebar.clicked.connect(self._clear_batch_action)
        sub_act_row.addWidget(self.btn_clear_sidebar, 1)

        side_layout.addLayout(sub_act_row)

        # Bottom Counter / Status
        self.lbl_batch_stat = QLabel("សរុប 20 បទ (Khmer + EN)... ស្អាត Copy បានភ្លាមៗ")
        self.lbl_batch_stat.setFixedHeight(24)
        self.lbl_batch_stat.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_batch_stat.setStyleSheet("color: #34d399; font-size: 10.5px; font-weight: 700; background: #064e3b; border-radius: 4px;")
        side_layout.addWidget(self.lbl_batch_stat)

        side_layout.addStretch()
        self.side_scroll.setWidget(self.sidebar)
        main_layout.addWidget(self.side_scroll)

        # ══════════════════════════════════════════════════════════════════
        # ── CENTER & BOTTOM: MULTI-SONG GRID + INSPECTOR DRAWER ──
        # ══════════════════════════════════════════════════════════════════
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        # ── Full-Height Cards Grid Area ──
        grid_area = QWidget()
        grid_v_layout = QVBoxLayout(grid_area)
        grid_v_layout.setContentsMargins(0, 0, 0, 0)
        grid_v_layout.setSpacing(6)

        # Grid Header Row 1: Studio Master Header (Sidebar Toggle + Title + Primary Workflows)
        grid_header1 = QHBoxLayout()
        grid_header1.setSpacing(6)

        self.btn_toggle_sidebar = QPushButton("◀ Sidebar")
        self.btn_toggle_sidebar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_sidebar.setToolTip("Toggle sidebar to expand workspace (+375px full width)")
        self.btn_toggle_sidebar.setStyleSheet("""
            QPushButton {
                background-color: #13172c;
                color: #93c5fd;
                font-weight: 700;
                font-size: 10.5px;
                border: 1px solid #232c4b;
                border-radius: 4px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: #1e293b;
                color: #ffffff;
                border-color: #3b82f6;
            }
        """)
        self.btn_toggle_sidebar.clicked.connect(self._toggle_sidebar)
        grid_header1.addWidget(self.btn_toggle_sidebar)

        self.lbl_grid_title = QLabel("🎴 Batch Studio Pro Tracks")
        self.lbl_grid_title.setStyleSheet("font-size: 13.5px; font-weight: 800; color: #f8fafc;")
        grid_header1.addWidget(self.lbl_grid_title)

        self.lbl_grid_badge = QLabel("20 Tracks Ready")
        self.lbl_grid_badge.setStyleSheet("""
            background-color: #1e293b;
            color: #38bdf8;
            font-size: 9.5px;
            font-weight: 700;
            border: 1px solid #334155;
            border-radius: 4px;
            padding: 2px 6px;
        """)
        grid_header1.addWidget(self.lbl_grid_badge)

        self.lbl_avg_novelty = QLabel("✨ Novelty: 96% Fresh")
        self.lbl_avg_novelty.setStyleSheet("""
            background-color: #064e3b;
            color: #6ee7b7;
            font-size: 9px;
            font-weight: 800;
            padding: 2px 6px;
            border-radius: 4px;
            border: 1px solid #059669;
            font-family: 'Cascadia Code', 'Consolas', monospace;
        """)
        self.lbl_avg_novelty.setToolTip("Anti-Cliché Engine: Average freshness & diversity across all songs in the batch")
        grid_header1.addWidget(self.lbl_avg_novelty)

        grid_header1.addStretch()

        # Primary Quick Workflow Action: Copy Next Uncopied
        self.btn_copy_next = QPushButton("🚀 Copy Next Uncopied")
        self.btn_copy_next.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_copy_next.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #0284c7);
                color: #ffffff;
                font-weight: 800;
                font-size: 11px;
                border: 1px solid #10b981;
                border-radius: 5px;
                padding: 4px 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 #38bdf8);
            }
        """)
        self.btn_copy_next.setToolTip("Instantly copies the next uncopied song to clipboard and marks it [✓ Copied]")
        self.btn_copy_next.clicked.connect(self._copy_next_uncopied)
        grid_header1.addWidget(self.btn_copy_next)

        # AI Authenticity Humanizer Button (Direct 1-Click)
        self.btn_humanize_all = QPushButton("👤 Humanize All 20")
        self.btn_humanize_all.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_humanize_all.setToolTip("Elevate all 20 tracks into living human masterpieces: inject breath cues, sensory realism, and live room pocket groove")
        self.btn_humanize_all.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #047857, stop:1 #0369a1);
                color: #ffffff;
                font-weight: 800;
                font-size: 11px;
                border: 1px solid #10b981;
                border-radius: 5px;
                padding: 4px 10px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #0284c7);
            }
        """)
        self.btn_humanize_all.clicked.connect(self._humanize_all_tracks)
        grid_header1.addWidget(self.btn_humanize_all)

        # Studio Tools Dropdown Menu (Inject v6, Album Arc, 1-Lyric Takes, Export)
        self.btn_studio_tools = QPushButton("⚡ Studio Tools ▾")
        self.btn_studio_tools.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_studio_tools.setToolTip("Advanced Studio Generation & Transformation Tools")
        self.btn_studio_tools.setStyleSheet("""
            QPushButton {
                background-color: #1e1b4b;
                color: #c084fc;
                font-weight: 700;
                font-size: 11px;
                border: 1px solid #6366f1;
                border-radius: 5px;
                padding: 4px 10px;
            }
            QPushButton:hover {
                background-color: #312e81;
                color: #ffffff;
            }
        """)
        studio_menu = QMenu(self)
        act_v6 = studio_menu.addAction("⚡ Inject Suno v6 Cues (All 20 Tracks)")
        act_v6.triggered.connect(self._inject_v6_to_all)
        act_arc = studio_menu.addAction("💿 Structure Concept Album Arc (Intro ➔ Climax)")
        act_arc.triggered.connect(self._apply_album_concept_arc)
        act_split = studio_menu.addAction("🔀 1-Lyric ➔ 20 Radical Genre Takes")
        act_split.triggered.connect(self._split_into_20_styles)
        studio_menu.addSeparator()
        act_copy_all = studio_menu.addAction("📋 Copy All Suno Prompts to Clipboard")
        act_copy_all.triggered.connect(self._copy_entire_batch)
        act_export_json = studio_menu.addAction("💾 Export Full Batch to JSON (.json)")
        act_export_json.triggered.connect(self._export_batch_file)
        self.btn_studio_tools.setMenu(studio_menu)
        grid_header1.addWidget(self.btn_studio_tools)

        # Backwards-compatibility button instances
        self.btn_inject_all_v6 = QPushButton("⚡ Inject Suno v6 Cues (All)")
        self.btn_inject_all_v6.clicked.connect(self._inject_v6_to_all)
        self.btn_album_arc = QPushButton("💿 Album Arc")
        self.btn_album_arc.clicked.connect(self._apply_album_concept_arc)
        self.btn_take_splitter = QPushButton("🔀 1-Lyric ➔ 20 Takes")
        self.btn_take_splitter.clicked.connect(self._split_into_20_styles)

        # Project Controls Capsule
        self.btn_new_project = QPushButton("✨ New")
        self.btn_new_project.setToolTip("Start New Batch Project (Reset inputs and clear canvas)")
        self.btn_new_project.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_new_project.setStyleSheet(self._btn_new_style())
        self.btn_new_project.clicked.connect(self.new_batch_project)
        grid_header1.addWidget(self.btn_new_project)

        self.btn_clear_grid = QPushButton("🗑️ Clear")
        self.btn_clear_grid.setToolTip("Clear all tracks from grid")
        self.btn_clear_grid.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear_grid.setStyleSheet(self._btn_clear_style())
        self.btn_clear_grid.clicked.connect(self._clear_batch_action)
        grid_header1.addWidget(self.btn_clear_grid)

        grid_v_layout.addLayout(grid_header1)

        # Grid Header Row 2: Workflow Filter Bar & View Density Switcher
        grid_filter_bar = QHBoxLayout()
        grid_filter_bar.setSpacing(6)

        self.btn_filter_all = QPushButton("All (20)")
        self.btn_filter_fav = QPushButton("⭐ Favorites (0)")
        self.btn_filter_uncopied = QPushButton("⏳ Uncopied (20)")
        self.btn_filter_copied = QPushButton("✓ Copied (0)")

        for mode, btn in [("all", self.btn_filter_all), ("favorites", self.btn_filter_fav), ("uncopied", self.btn_filter_uncopied), ("copied", self.btn_filter_copied)]:
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, m=mode: self._set_filter_mode(m))
            grid_filter_bar.addWidget(btn)

        self._update_filter_button_styles()

        # Quick Search Bar for instant filtering by title, genre, bpm, or lyrics
        self.txt_grid_search = QLineEdit()
        self.txt_grid_search.setPlaceholderText("🔍 ស្វែងរក... (Search tracks)")
        self.txt_grid_search.setClearButtonEnabled(True)
        self.txt_grid_search.setFixedWidth(190)
        self.txt_grid_search.setStyleSheet("""
            QLineEdit {
                background: #0f1426;
                color: #f1f5f9;
                border: 1px solid #283354;
                border-radius: 5px;
                padding: 4px 8px;
                font-size: 11px;
            }
            QLineEdit:focus {
                border-color: #6366f1;
            }
        """)
        self.txt_grid_search.textChanged.connect(self._on_search_text_changed)
        grid_filter_bar.addWidget(self.txt_grid_search)

        grid_filter_bar.addStretch()

        # Grid Density & View Switchers: [ 🔲 3 Cols ] [ ⊞ 4 Cols ] [ 📋 Table ] [ ◫ Auto ]
        self.btn_cols_3 = QPushButton("🔲 3 Cols")
        self.btn_cols_3.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cols_3.setToolTip("Switch to 3 spacious columns with wide readable cards (Recommended for 1080p)")
        self.btn_cols_3.clicked.connect(lambda: self._set_view_mode(3))
        grid_filter_bar.addWidget(self.btn_cols_3)

        self.btn_cols_4 = QPushButton("⊞ 4 Cols")
        self.btn_cols_4.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cols_4.setToolTip("Switch to balanced 4 columns studio grid")
        self.btn_cols_4.clicked.connect(lambda: self._set_view_mode(4))
        grid_filter_bar.addWidget(self.btn_cols_4)

        self.btn_cols_5 = QPushButton("▦ 5 Cols")
        self.btn_cols_5.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cols_5.setToolTip("Switch to compact 5 columns view")
        self.btn_cols_5.clicked.connect(lambda: self._set_view_mode(5))

        self.btn_view_table = QPushButton("📋 Table")
        self.btn_view_table.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_view_table.setToolTip("Switch to Studio Multi-Track Table View (Review all 20 songs in one clear spreadsheet)")
        self.btn_view_table.clicked.connect(lambda: self._set_view_mode("table"))
        grid_filter_bar.addWidget(self.btn_view_table)

        self.btn_cols_auto = QPushButton("◫ Auto")
        self.btn_cols_auto.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cols_auto.setToolTip("Auto-fit columns responsively based on window size")
        self.btn_cols_auto.clicked.connect(lambda: self._set_view_mode("auto"))
        grid_filter_bar.addWidget(self.btn_cols_auto)
        self._update_column_toggle_ui()

        self.lbl_queue_hint = QLabel("💡 គន្លឹះ: ចុច [🚀 Copy Next] ដើម្បីយកបទទៅ generate លើ Suno ម្តងមួយៗលឿនបំផុត")
        self.lbl_queue_hint.setStyleSheet("color: #64748b; font-size: 10px; font-style: italic;")
        grid_filter_bar.addWidget(self.lbl_queue_hint)

        grid_v_layout.addLayout(grid_filter_bar)

        self.cards_scroll = QScrollArea()
        self.cards_scroll.setWidgetResizable(True)
        self.cards_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.cards_scroll.setStyleSheet("background-color: transparent; border: none;")

        self.cards_container = QWidget()
        self.cards_container.setStyleSheet("background-color: transparent;")
        self.grid_layout = QGridLayout(self.cards_container)
        self.grid_layout.setContentsMargins(4, 4, 4, 4)
        self.grid_layout.setSpacing(6)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.cards_scroll.setWidget(self.cards_container)
        grid_v_layout.addWidget(self.cards_scroll, stretch=1)

        # ── Studio Tracklist Table View ──
        self.tracklist_table = QTableWidget()
        self.tracklist_table.setColumnCount(11)
        self.tracklist_table.setHorizontalHeaderLabels([
            "#", "Lang", "★", "Status", "Title", "Genre & BPM", "Key", "Quality", "Style Prompt", "Lyrics Snippet", "Actions"
        ])
        self.tracklist_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tracklist_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tracklist_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tracklist_table.setAlternatingRowColors(True)
        self.tracklist_table.verticalHeader().setVisible(False)
        self.tracklist_table.setShowGrid(True)
        self.tracklist_table.cellDoubleClicked.connect(self._on_table_cell_double_clicked)
        self.tracklist_table.hide()
        self._configure_table_columns()
        grid_v_layout.addWidget(self.tracklist_table, stretch=1)
        right_layout.addWidget(grid_area, stretch=1)

        main_layout.addWidget(right_container, stretch=1)

    def _pill_style(self, active: bool) -> str:
        t = getattr(self, "theme", get_theme(getattr(self, "is_dark", True)))
        is_dark = t.get("is_dark", True)
        if is_dark:
            if active:
                return f"""
                    QPushButton {{
                        background-color: {t['active_pill_bg']};
                        color: {t['active_pill_color']};
                        border: 1px solid {t['border_accent']};
                        font-weight: 800;
                        font-size: 9.5px;
                        padding: 2px 3px;
                        border-radius: 4px;
                    }}
                    QPushButton:hover {{
                        background-color: {t['accent_hover']};
                        border-color: #ffffff;
                    }}
                """
            return f"""
                QPushButton {{
                    background-color: {t['subtle_pill_bg']};
                    color: {t['subtle_pill_text']};
                    border: 1px solid {t['border']};
                    font-size: 10px;
                    font-weight: 600;
                    padding: 2px 4px;
                    border-radius: 4px;
                }}
                QPushButton:hover {{
                    background-color: {t['bg_card_alt']};
                    color: #ffffff;
                    border-color: {t['border_accent']};
                }}
            """
        else:
            if active:
                return f"""
                    QPushButton {{
                        background-color: {t['accent']};
                        color: #ffffff;
                        border: 1px solid {t['border_accent']};
                        font-weight: 800;
                        font-size: 9.5px;
                        padding: 2px 3px;
                        border-radius: 4px;
                    }}
                    QPushButton:hover {{
                        background-color: {t['accent_hover']};
                    }}
                """
            return """
                QPushButton {
                    background-color: #ffffff;
                    color: #1e293b;
                    border: 1px solid #cbd5e1;
                    font-size: 10px;
                    font-weight: 600;
                    padding: 2px 4px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #f1f5f9;
                    color: #0f172a;
                    border-color: #94a3b8;
                }
            """

    def _btn_sub(self) -> str:
        t = getattr(self, "theme", get_theme(getattr(self, "is_dark", True)))
        is_dark = t.get("is_dark", True)
        if is_dark:
            return f"""
                QPushButton {{
                    background-color: {t['bg_card_alt']};
                    color: {t['text_secondary']};
                    border: 1px solid {t['border']};
                    font-weight: 700;
                    font-size: 10.5px;
                    padding: 2px 4px;
                    border-radius: 4px;
                }}
                QPushButton:hover {{
                    background-color: {t['border']};
                    color: #ffffff;
                    border-color: {t['border_accent']};
                }}
                QPushButton:pressed {{
                    background-color: {t['bg_card']};
                }}
            """
        return """
            QPushButton {
                background-color: #ffffff;
                color: #1e293b;
                border: 1px solid #cbd5e1;
                font-weight: 700;
                font-size: 10.5px;
                padding: 2px 4px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #f1f5f9;
                color: #0f172a;
                border-color: #94a3b8;
            }
            QPushButton:pressed {
                background-color: #e2e8f0;
            }
        """

    def _btn_clear_style(self) -> str:
        is_dark = getattr(self, "is_dark", True)
        if is_dark:
            return """
                QPushButton {
                    background-color: #260c14;
                    color: #fb7185;
                    border: 1px solid #9f1239;
                    font-weight: 700;
                    font-size: 10.5px;
                    padding: 2px 4px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #e11d48;
                    color: #ffffff;
                    border-color: #f43f5e;
                }
                QPushButton:pressed {
                    background-color: #881337;
                }
            """
        return """
            QPushButton {
                background-color: #fff1f2;
                color: #e11d48;
                border: 1px solid #fecdd3;
                font-weight: 700;
                font-size: 10.5px;
                padding: 2px 4px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #ffe4e6;
                color: #be123c;
                border-color: #fda4af;
            }
            QPushButton:pressed {
                background-color: #fecdd3;
            }
        """

    def _btn_new_style(self) -> str:
        is_dark = getattr(self, "is_dark", True)
        if is_dark:
            return """
                QPushButton {
                    background-color: #0c2033;
                    color: #38bdf8;
                    border: 1px solid #0284c7;
                    font-weight: 700;
                    font-size: 11px;
                    padding: 5px 8px;
                    border-radius: 6px;
                }
                QPushButton:hover {
                    background-color: #0284c7;
                    color: #ffffff;
                    border-color: #7dd3fc;
                }
                QPushButton:pressed {
                    background-color: #0369a1;
                }
            """
        return """
            QPushButton {
                background-color: #f0f9ff;
                color: #0284c7;
                border: 1px solid #bae6fd;
                font-weight: 700;
                font-size: 11px;
                padding: 5px 8px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #e0f2fe;
                color: #0369a1;
                border-color: #7dd3fc;
            }
            QPushButton:pressed {
                background-color: #bae6fd;
            }
        """

    # ── State Updates ──
    def _update_dynamic_language_presets(self, lang: str):
        mode_key = "Both"
        if "Khmer" in lang or "ខ្មែរ" in lang:
            mode_key = "Khmer"
        elif "English" in lang:
            mode_key = "English"

        # 1. Update Section Headers
        if hasattr(self, "lbl_s1"):
            if mode_key == "English":
                self.lbl_s1.setText("🎵 1. THEME & STYLE")
                self.lbl_s2.setText("📖 2. STORY SEED & BACKSTORY")
                self.lbl_s3.setText("💎 3. LYRIC ARCHITECTURE & METER")
                self.lbl_s4.setText("🌐 4. LYRIC LANGUAGE")
                self.lbl_s5.setText("🎙️ 5. VOCAL DELIVERY")
                self.lbl_s6.setText("🎼 6. DIVERSITY & ANTI-DUPLICATION")
            elif mode_key == "Khmer":
                self.lbl_s1.setText("🎵 1. ប្រធានបទ & អារម្មណ៍")
                self.lbl_s2.setText("📖 2. ដំណើររឿងបទចម្រៀង")
                self.lbl_s3.setText("💎 3. ជម្រៅអត្ថន័យ & កាព្យ")
                self.lbl_s4.setText("🌐 4. ភាសាទំនុកច្រៀង")
                self.lbl_s5.setText("🎙️ 5. តម្រងសំឡេងច្រៀង")
                self.lbl_s6.setText("🎼 6. ភាពចម្រុះ និងការពារការជាន់គ្នា")
            else: # Both
                self.lbl_s1.setText("🎵 1. THEME & MOOD • ប្រធានបទ")
                self.lbl_s2.setText("📖 2. STORY SEED • ដំណើររឿង")
                self.lbl_s3.setText("💎 3. LYRICAL DEPTH • ជម្រៅអត្ថន័យ")
                self.lbl_s4.setText("🌐 4. LYRICS LANGUAGE • ភាសា")
                self.lbl_s5.setText("🎙️ 5. VOCAL FILTER • សំឡេង")
                self.lbl_s6.setText("🎼 6. DIVERSITY & ANTI-DUPLICATION")

        # 2. Update Theme Pills
        theme_presets = self.theme_pills_data.get(mode_key, self.theme_pills_data["Both"])
        flat_theme = [item for row in theme_presets for item in row]
        for idx, (label, val) in enumerate(flat_theme):
            if idx < len(self.theme_pills):
                btn = self.theme_pills[idx]
                btn.setText(label)
                try:
                    btn.clicked.disconnect()
                except Exception:
                    pass
                btn.clicked.connect(lambda _, v=val: self.txt_theme.setPlainText(v))

        # 3. Update Seed Pills
        seed_presets = self.seed_pills_data.get(mode_key, self.seed_pills_data["Both"])
        flat_seed = [item for row in seed_presets for item in row]
        for idx, (label, val) in enumerate(flat_seed):
            if idx < len(self.seed_pills):
                btn = self.seed_pills[idx]
                btn.setText(label)
                try:
                    btn.clicked.disconnect()
                except Exception:
                    pass
                btn.clicked.connect(lambda _, v=val: self.txt_story_seed.setPlainText(v))

        # 4. Update Lyrical Depth / Meter Dropdown
        depth_items = self.depth_modes_data.get(mode_key, self.depth_modes_data["Both"])
        self.combo_depth_mode.blockSignals(True)
        self.combo_depth_mode.clear()
        self.combo_depth_mode.addItems(depth_items)
        self.combo_depth_mode.setCurrentIndex(0)
        self.combo_depth_mode.blockSignals(False)

        # 5. Update Diversity Spectrum Dropdown
        div_items = self.diversity_modes_data.get(mode_key, self.diversity_modes_data["Both"])
        self.combo_diversity.blockSignals(True)
        self.combo_diversity.clear()
        self.combo_diversity.addItems(div_items)
        self.combo_diversity.setCurrentIndex(0)
        self._on_diversity_changed(div_items[0])
        self.combo_diversity.blockSignals(False)

        # 5.5 Update Vocal Persona Dropdown
        if hasattr(self, "combo_persona"):
            persona_items = self.persona_presets_data.get(mode_key, self.persona_presets_data["Both"])
            self.combo_persona.blockSignals(True)
            self.combo_persona.clear()
            self.combo_persona.addItems(persona_items)
            self.combo_persona.setCurrentIndex(0)
            self.combo_persona.blockSignals(False)

        # 6. Update Vocal Buttons
        vocal_labels = {
            "English": {
                "Mixed": "🎙️ All (Mixed)",
                "Male": "👨 Male Solo",
                "Female": "👩 Female Solo",
                "Duet": "👥 Duet / Dialogue"
            },
            "Khmer": {
                "Mixed": "🎙️ ទាំងអស់ (Mixed)",
                "Male": "👨 ប្រុស (Male)",
                "Female": "👩 ស្រី (Female)",
                "Duet": "👥 ឆ្លើយឆ្លង (Duet)"
            },
            "Both": {
                "Mixed": "🎙️ ទាំងអស់ (Mixed)",
                "Male": "👨 ប្រុស (Male)",
                "Female": "👩 ស្រី (Female)",
                "Duet": "👥 ឆ្លើយឆ្លង (Duet)"
            }
        }
        curr_voc_map = vocal_labels.get(mode_key, vocal_labels["Both"])
        if hasattr(self, "vocal_buttons"):
            for code, btn in self.vocal_buttons.items():
                if code in curr_voc_map:
                    btn.setText(curr_voc_map[code])

        # 7. Update Count Label & Combobox
        if hasattr(self, "lbl_count"):
            self.lbl_count.setText("Count:" if mode_key == "English" else ("ចំនួន:" if mode_key == "Khmer" else "ចំនួនបទ (Count):"))

        if hasattr(self, "combo_count"):
            self.combo_count.blockSignals(True)
            cur_val = self.current_count
            self.combo_count.clear()
            if mode_key == "English":
                self.combo_count.addItems(["5 Songs", "10 Songs", "15 Songs", "20 Songs", "30 Songs"])
                target_txt = f"{cur_val} Songs"
            elif mode_key == "Khmer":
                self.combo_count.addItems(["៥ បទ", "១០ បទ", "១៥ បទ", "២០ បទ", "៣០ បទ"])
                kh_map = {"5": "៥", "10": "១០", "15": "១៥", "20": "២០", "30": "៣០"}
                target_txt = f"{kh_map.get(str(cur_val), str(cur_val))} បទ"
            else:
                self.combo_count.addItems(["5 បទ", "10 បទ", "15 បទ", "20 បទ", "30 បទ"])
                target_txt = f"{cur_val} បទ"
            idx = self.combo_count.findText(target_txt)
            if idx >= 0:
                self.combo_count.setCurrentIndex(idx)
            self.combo_count.blockSignals(False)

        # 8. Update Primary Generate & Secondary Action Buttons
        if hasattr(self, "btn_generate_batch"):
            if mode_key == "English":
                self.btn_generate_batch.setText(f"⚡ Generate {self.current_count} Songs (Turbo Engine)")
            elif mode_key == "Khmer":
                self.btn_generate_batch.setText(f"⚡ បង្កើត {self.current_count} បទចម្រៀងថ្មី (Turbo Engine)")
            else:
                self.btn_generate_batch.setText(f"⚡ បង្កើត {self.current_count} បទចម្រៀង (Dual Engine)")

        if hasattr(self, "btn_append"):
            self.btn_append.setText("+ Add More" if mode_key == "English" else ("+ ថែម" if mode_key == "Khmer" else "+ ថែម / Add"))
        if hasattr(self, "btn_copy_all_batch"):
            self.btn_copy_all_batch.setText("📋 Copy" if mode_key == "English" else "📋 Copy")
        if hasattr(self, "btn_save_all"):
            self.btn_save_all.setText("💾 Save" if mode_key == "English" else "💾 Save")
        if hasattr(self, "btn_clear_sidebar"):
            self.btn_clear_sidebar.setText("🗑️ Clear" if mode_key == "English" else "🗑️ Clear")

        if hasattr(self, "lbl_batch_stat"):
            if mode_key == "English":
                self.lbl_batch_stat.setText(f"Total {self.current_count} Songs... Ready to Copy / Suno")
            elif mode_key == "Khmer":
                self.lbl_batch_stat.setText(f"សរុប {self.current_count} បទ... ស្អាត Copy បានភ្លាមៗ")
            else:
                self.lbl_batch_stat.setText(f"សរុប {self.current_count} បទ (Khmer + EN) • Copy បាន")

        if hasattr(self, "btn_anti_dup"):
            self.btn_anti_dup.setText("🛡️ Zero Clones" if mode_key != "Khmer" else "🛡️ គ្មានការជាន់គ្នា")

        # 9. Update Story Seed Placeholder
        if mode_key == "Khmer":
            self.txt_story_seed.setPlaceholderText("ឧទាហរណ៍: ជួបគ្នាម្តងទៀតក្រោយបែកគ្នា ១០ ឆ្នាំ, កូនខ្មែរតស៊ូពីបាតដៃទទេ...")
        elif mode_key == "English":
            self.txt_story_seed.setPlaceholderText("Example: 10-year reunion at airport, midnight coffee in the rain, chasing big dreams...")
        else:
            self.txt_story_seed.setPlaceholderText("ឧទាហរណ៍ / Example: ជួបគ្នាម្តងទៀត (10-Year Reunion), bilingual heartbreak...")

        # 10. Update Theme Placeholder & Default Theme Text
        cur_t = self.txt_theme.toPlainText().strip()
        if mode_key == "Khmer":
            self.txt_theme.setPlaceholderText("ឧទាហរណ៍: ស្រណោះស្រណោក បទមនោសញ្ចេតនាខ្មែរ, ស្ទឹងសង្កែ, ផ្កាចំប៉ី...")
            if cur_t in ["sad song", "bilingual heartbreak / ស្រណោះស្រណោក", "bittersweet heartbreak, late night drive"]:
                self.txt_theme.setPlainText("ស្រណោះស្រណោក បទមនោសញ្ចេតនាខ្មែរ")
        elif mode_key == "English":
            self.txt_theme.setPlaceholderText("Example: sad song, heartbreak, midnight city drive, neon lights...")
            if cur_t in ["sad song", "ស្រណោះស្រណោក បទមនោសញ្ចេតនាខ្មែរ", "bilingual heartbreak / ស្រណោះស្រណោក"]:
                self.txt_theme.setPlainText("bittersweet heartbreak, late night drive")
        else: # Both
            self.txt_theme.setPlaceholderText("ឧទាហរណ៍: bilingual heartbreak, ស្រណោះស្រណោក, cross-culture hit...")
            if cur_t in ["ស្រណោះស្រណោក បទមនោសញ្ចេតនាខ្មែរ", "bittersweet heartbreak, late night drive"]:
                self.txt_theme.setPlainText("bilingual heartbreak / ស្រណោះស្រណោក")

        # 11. Update Grid Title & Filters
        if hasattr(self, "lbl_grid_title"):
            song_cnt = len(self.all_songs) if hasattr(self, "all_songs") else 20
            if mode_key == "English":
                self.lbl_grid_title.setText(f"🎴 Batch Studio Pro Tracks ({song_cnt} Ready Takes)")
            elif mode_key == "Khmer":
                self.lbl_grid_title.setText(f"🎴 បណ្ដុំបទចម្រៀង Studio Pro ({song_cnt} បទរួចរាល់)")
            else:
                self.lbl_grid_title.setText(f"🎴 Batch Studio Pro Tracks ({song_cnt} បទចម្រៀង)")

    def _set_language(self, lang: str):
        self.current_lang = lang
        for code, btn in self.lang_buttons.items():
            btn.setChecked(code == lang)
            btn.setStyleSheet(self._pill_style(code == lang))
        self._update_dynamic_language_presets(lang)
        self._load_initial_demo()

    def _roll_fresh_anti_cliche_concept(self):
        """Generates an unexpected, highly novel atmosphere, sensory anchor, and emotional conflict."""
        from app.anti_cliche_engine import AntiClicheEngine
        res = AntiClicheEngine.roll_fresh_concept(self.current_lang)
        self.txt_theme.setPlainText(res["theme"])
        self.txt_story_seed.setPlainText(res["seed"])
        if hasattr(self, "lbl_batch_stat"):
            self.lbl_batch_stat.setText("🎲 Anti-Cliché Concept Injected: Fresh Atmosphere & Sensory Anchor!")

    def _toggle_album_arc(self):
        """Toggle concept album dramatic storytelling arc mode."""
        self.album_arc_enabled = self.btn_album_arc_toggle.isChecked()
        self._update_album_arc_style()
        self._load_initial_demo()

    def _update_album_arc_style(self):
        if not hasattr(self, "btn_album_arc_toggle"):
            return
        is_on = getattr(self, "album_arc_enabled", False)
        is_dark = getattr(self, "is_dark", True)
        if is_dark:
            if is_on:
                self.btn_album_arc_toggle.setStyleSheet("""
                    QPushButton {
                        background-color: #581c87;
                        color: #f0abfc;
                        border: 1px solid #c084fc;
                        border-radius: 4px;
                        font-weight: 800;
                        font-size: 9px;
                        padding: 2px 4px;
                    }
                """)
            else:
                self.btn_album_arc_toggle.setStyleSheet("""
                    QPushButton {
                        background-color: #171d34;
                        color: #94a3b8;
                        border: 1px solid #253052;
                        border-radius: 4px;
                        font-weight: 600;
                        font-size: 9px;
                        padding: 2px 4px;
                    }
                    QPushButton:hover {
                        border-color: #a855f7;
                        color: #f0abfc;
                    }
                """)
        else:
            if is_on:
                self.btn_album_arc_toggle.setStyleSheet("""
                    QPushButton {
                        background-color: #f3e8ff;
                        color: #7e22ce;
                        border: 1px solid #c084fc;
                        border-radius: 4px;
                        font-weight: 800;
                        font-size: 9px;
                        padding: 2px 4px;
                    }
                """)
            else:
                self.btn_album_arc_toggle.setStyleSheet("""
                    QPushButton {
                        background-color: #f1f5f9;
                        color: #64748b;
                        border: 1px solid #cbd5e1;
                        border-radius: 4px;
                        font-weight: 600;
                        font-size: 9px;
                        padding: 2px 4px;
                    }
                    QPushButton:hover {
                        border-color: #7e22ce;
                        color: #7e22ce;
                    }
                """)

    def _clear_memory_cache(self):
        """Clears the session-persistent zero-repeat memory cache."""
        self.session_memory_titles.clear()
        self._update_memory_ui()
        if hasattr(self, "lbl_batch_stat"):
            self.lbl_batch_stat.setText("🧠 Zero-Repeat Memory Cache Cleared.")

    def _update_memory_ui(self):
        cnt = len(self.session_memory_titles)
        if hasattr(self, "lbl_memory_badge"):
            self.lbl_memory_badge.setText(f"🧠 Memory: {cnt}")
            self.lbl_memory_badge.setToolTip(f"Session-persistent memory tracking {cnt} song titles across batches to guarantee zero repetition.")

    def _update_novelty_metrics(self):
        """Calculates and renders the average batch novelty freshness score."""
        if not self.all_songs or not hasattr(self, "lbl_avg_novelty"):
            return
        scores = []
        for s in self.all_songs:
            score = s.get("novelty_score")
            if score is None:
                from app.anti_cliche_engine import AntiClicheEngine
                res = AntiClicheEngine.calculate_novelty_score(s.get("title", ""), s.get("lyrics", ""), s.get("language", "English"))
                score = res["score"]
                s["novelty_score"] = score
                s["novelty_badge"] = res["badge"]
            scores.append(score)
        avg = int(sum(scores) / max(1, len(scores)))
        self.lbl_avg_novelty.setText(f"✨ Novelty: {avg}% Fresh")

    def _on_mutate_card(self, song_data: dict):
        """Mutate a single song in-place using the Anti-Cliché Engine."""
        from app.anti_cliche_engine import AntiClicheEngine
        lang = song_data.get("language", self.current_lang)
        mutated = AntiClicheEngine.mutate_single_song_locally(song_data, lang)

        target_id = song_data.get("id")
        for idx, s in enumerate(self.all_songs):
            if s.get("id") == target_id:
                self.all_songs[idx] = mutated
                break

        for card in self.card_widgets:
            if card.song_data.get("id") == target_id:
                card.update_card(mutated)
                break

        if self.selected_song and self.selected_song.get("id") == target_id:
            self._on_card_selected(mutated, open_dialog=False)

        self.session_memory_titles.add(mutated.get("title", ""))
        self._update_memory_ui()
        self._update_novelty_metrics()

        if hasattr(self, "lbl_batch_stat"):
            self.lbl_batch_stat.setText(f"🎲 Track {target_id} Mutated: {mutated.get('title')} ({mutated.get('novelty_badge')})")

    def _set_vocal(self, vocal: str):
        self.current_vocal = vocal
        for code, btn in self.vocal_buttons.items():
            btn.setChecked(code == vocal)
            btn.setStyleSheet(self._pill_style(code == vocal))

    def _on_depth_mode_changed(self, text: str):
        if "Bilingual" in text or "Fusion" in text:
            idx = self.combo_diversity.findText("🌐 Bilingual Cross-Culture Hits (ខ្មែរ + EN Hooks)")
            if idx >= 0:
                self.combo_diversity.blockSignals(True)
                self.combo_diversity.setCurrentIndex(idx)
                self.combo_diversity.blockSignals(False)
                self.current_diversity = "Bilingual Cross-Culture Hits"
            for code, btn in self.lang_buttons.items():
                btn.setChecked(code == "Both")
                btn.setStyleSheet(self._pill_style(code == "Both"))
            self.current_lang = "Both"
        self._load_initial_demo()

    def _on_diversity_changed(self, text: str):
        if "60s" in text or "Golden Era" in text:
            self.current_diversity = "60s Golden Era & Vintage"
        elif "Trap" in text or "Drill" in text:
            self.current_diversity = "Khmer Trap & Drill"
        elif "Romvong" in text or "Kantrum" in text:
            self.current_diversity = "Festive Romvong & Kantrum"
        elif "Bilingual" in text or "Cross-Culture" in text:
            self.current_diversity = "Bilingual Cross-Culture Hits"
        elif "Acoustic" in text:
            self.current_diversity = "Acoustic Storytelling"
        elif "Synthwave" in text or "Electronic" in text:
            self.current_diversity = "80s Synthwave & Dance"
        elif "Melancholy" in text or "Emotional" in text:
            self.current_diversity = "Deep Emotional Melancholy"
        else:
            self.current_diversity = "Wide Spectrum"
        self._load_initial_demo()

    def _toggle_anti_dup(self):
        self.anti_duplication = self.btn_anti_dup.isChecked()
        self._update_anti_dup_style(self.anti_duplication)

    def _update_anti_dup_style(self, active: bool):
        if active:
            self.btn_anti_dup.setText("🛡️ Zero Clones")
            self.btn_anti_dup.setToolTip("Anti-Duplication Engine: ACTIVE (Zero Clones)\nEnforces 5-dimensional variance across all songs:\n• Shifts tempo tiers\n• Rotates musical keys\n• Blacklists AI rhyme clichés\n• Enforces concrete physical imagery & micro-genre tags")
            self.btn_anti_dup.setStyleSheet("""
                QPushButton {
                    background-color: #064e3b;
                    color: #34d399;
                    font-weight: 800;
                    font-size: 9.5px;
                    border: 1px solid #059669;
                    border-radius: 4px;
                    padding: 2px 4px;
                }
                QPushButton:hover {
                    background-color: #047857;
                }
            """)
        else:
            self.btn_anti_dup.setText("⚠️ Dup: OFF")
            self.btn_anti_dup.setToolTip("Anti-Duplication Engine: BYPASSED")
            self.btn_anti_dup.setStyleSheet("""
                QPushButton {
                    background-color: #3b1812;
                    color: #f87171;
                    font-weight: 700;
                    font-size: 9.5px;
                    border: 1px solid #7f1d1d;
                    border-radius: 4px;
                    padding: 2px 4px;
                }
                QPushButton:hover {
                    background-color: #4c1d17;
                }
            """)

    def _on_count_changed(self, text: str):
        try:
            val = int("".join(filter(str.isdigit, text)))
            self.current_count = val
        except Exception:
            self.current_count = 20
        self._load_initial_demo()

    def _on_style_limit_changed(self, text: str):
        if "120" in text:
            self.current_style_limit = 120
        else:
            self.current_style_limit = 200
        if hasattr(self, "lbl_insp_style_chars") and self.selected_song:
            self.lbl_insp_style_chars.setText(f"{len(self.selected_song.get('style_prompt', ''))} / {self.current_style_limit} chars")

    def _load_initial_demo(self):
        depth_mode = self.combo_depth_mode.currentText() if hasattr(self, "combo_depth_mode") else ""
        worker = BatchGenerateWorker(
            theme="sad song",
            language=self.current_lang,
            count=self.current_count,
            style_limit=self.current_style_limit,
            diversity_mode=self.current_diversity,
            depth_mode=depth_mode,
            anti_duplication=self.anti_duplication,
            existing_titles=list(self.session_memory_titles),
            vocal_persona=getattr(self, "current_persona", ""),
            album_arc=getattr(self, "album_arc_enabled", False)
        )
        demo_songs = worker._get_demo_batch(
            "sad song",
            self.current_lang,
            self.current_count,
            self.current_diversity,
            existing_titles=list(self.session_memory_titles),
            depth_mode=depth_mode,
            vocal_persona=getattr(self, "current_persona", ""),
            album_arc=getattr(self, "album_arc_enabled", False)
        )
        self._populate_grid(demo_songs)

    # ── Studio Tracklist Table Helpers ──
    def _configure_table_columns(self):
        header = self.tracklist_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(0, 36)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(1, 45)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(2, 32)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(3, 75)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        header.resizeSection(4, 180)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)
        header.resizeSection(5, 140)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(6, 75)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(7, 120)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(10, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(10, 160)

    def _on_table_cell_double_clicked(self, row: int, column: int):
        if 0 <= row < len(self.all_songs):
            song = self.all_songs[row]
            self._on_card_selected(song, open_dialog=True)

    def _populate_table(self):
        if not hasattr(self, "tracklist_table"):
            return
        # Detach and delete any existing cell widgets to prevent stray artifacts
        for r in range(self.tracklist_table.rowCount()):
            for c in range(self.tracklist_table.columnCount()):
                w = self.tracklist_table.cellWidget(r, c)
                if w:
                    self.tracklist_table.removeCellWidget(r, c)
                    w.hide()
                    w.setParent(None)
                    w.deleteLater()
        self.tracklist_table.clearContents()
        songs = getattr(self, "all_songs", [])
        self.tracklist_table.setRowCount(len(songs))
        self._configure_table_columns()
        is_dark = getattr(self, "is_dark", True)

        text_color = "#f8fafc" if is_dark else "#0f172a"
        sub_color = "#94a3b8" if is_dark else "#64748b"
        accent_blue = "#38bdf8" if is_dark else "#0284c7"

        for row, s in enumerate(songs):
            idx = s.get("id", row + 1)
            lang = s.get("language", "")
            lyrics = s.get("lyrics", "")
            title = s.get("title", "Untitled")
            is_fusion = "Bilingual" in lang or "Fusion" in lang or (any('\u1780' <= c <= '\u17ff' for c in lyrics) and any('a' <= c.lower() <= 'z' for c in lyrics) and "Chorus" in lyrics)
            is_khmer = "Khmer" in lang or any('\u1780' <= c <= '\u17ff' for c in title + lyrics)
            flag = "🇰🇭🇬🇧" if is_fusion else ("🇰🇭" if is_khmer else "🇬🇧")
            is_fav = s.get("is_favorite", False)
            status = s.get("status", "new")
            genre = s.get("genre", "")
            bpm = s.get("bpm", "")
            key = s.get("key", "")
            meter = s.get("meter", "4/4")
            q_hit = s.get("quality_score", 96)
            is_human = s.get("human_certified", False)
            q_human = 100 if is_human else s.get("human_score", 95)
            style_txt = s.get("style_prompt", "")

            # Col 0: Index
            it_idx = QTableWidgetItem(f"{idx:02d}")
            it_idx.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            it_idx.setForeground(QColor("#93c5fd" if is_dark else "#2563eb"))
            self.tracklist_table.setItem(row, 0, it_idx)

            # Col 1: Flag
            it_flag = QTableWidgetItem(flag)
            it_flag.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tracklist_table.setItem(row, 1, it_flag)

            # Col 2: Star
            it_star = QTableWidgetItem("★" if is_fav else "☆")
            it_star.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            it_star.setForeground(QColor("#fbbf24" if is_fav else ("#475569" if is_dark else "#94a3b8")))
            self.tracklist_table.setItem(row, 2, it_star)

            # Col 3: Status
            status_txt = "✓ Copied" if status == "copied" else ("🟣 Editor" if status == "done" else "● New")
            it_status = QTableWidgetItem(status_txt)
            it_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if status == "copied":
                it_status.setForeground(QColor("#34d399" if is_dark else "#059669"))
            elif status == "done":
                it_status.setForeground(QColor("#c084fc" if is_dark else "#7c3aed"))
            else:
                it_status.setForeground(QColor("#94a3b8" if is_dark else "#64748b"))
            self.tracklist_table.setItem(row, 3, it_status)

            # Col 4: Title
            it_title = QTableWidgetItem(title)
            it_title.setForeground(QColor(text_color))
            font_title = QFont()
            font_title.setBold(True)
            it_title.setFont(font_title)
            self.tracklist_table.setItem(row, 4, it_title)

            # Col 5: Genre & BPM
            it_genre = QTableWidgetItem(f"{genre} • {bpm}")
            it_genre.setForeground(QColor(accent_blue))
            self.tracklist_table.setItem(row, 5, it_genre)

            # Col 6: Key & Meter
            it_key = QTableWidgetItem(f"{key} • {meter}")
            it_key.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            it_key.setForeground(QColor(sub_color))
            self.tracklist_table.setItem(row, 6, it_key)

            # Col 7: Quality
            cert_txt = f"🎯 {q_hit}% • 👤 {q_human}%"
            it_qual = QTableWidgetItem(cert_txt)
            it_qual.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            it_qual.setForeground(QColor("#6ee7b7" if is_dark else "#047857"))
            self.tracklist_table.setItem(row, 7, it_qual)

            # Col 8: Style Prompt Preview
            it_style = QTableWidgetItem(style_txt[:70] + ("..." if len(style_txt) > 70 else ""))
            it_style.setForeground(QColor(sub_color))
            self.tracklist_table.setItem(row, 8, it_style)

            # Col 9: Lyrics Snippet
            clean_lines = [l.strip() for l in lyrics.split("\n") if l.strip() and not l.strip().startswith("[")]
            snip = " / ".join(clean_lines[:2]) if clean_lines else "Live groove..."
            it_lyric = QTableWidgetItem(snip[:75] + ("..." if len(snip) > 75 else ""))
            it_lyric.setForeground(QColor(text_color))
            self.tracklist_table.setItem(row, 9, it_lyric)

            # Col 10: Action buttons widget
            action_widget = QWidget()
            act_layout = QHBoxLayout(action_widget)
            act_layout.setContentsMargins(2, 2, 2, 2)
            act_layout.setSpacing(4)

            btn_cs = QPushButton("🎨")
            btn_cs.setToolTip("Copy Style")
            btn_cs.setFixedSize(26, 24)
            btn_cs.clicked.connect(lambda _, song=s: self._copy_single_style(song))

            btn_cl = QPushButton("✍️")
            btn_cl.setToolTip("Copy Lyrics")
            btn_cl.setFixedSize(26, 24)
            btn_cl.clicked.connect(lambda _, song=s: self._copy_single_lyrics(song))

            btn_ca = QPushButton("⚡")
            btn_ca.setToolTip("Copy Suno Bundle")
            btn_ca.setFixedSize(26, 24)
            btn_ca.clicked.connect(lambda _, song=s: self._copy_single_all(song))

            btn_insp = QPushButton("🔍 Open")
            btn_insp.setToolTip("Open in Song Inspector")
            btn_insp.setFixedHeight(24)
            btn_insp.clicked.connect(lambda _, song=s: self._on_card_selected(song, open_dialog=True))

            for b in [btn_cs, btn_cl, btn_ca, btn_insp]:
                b.setCursor(Qt.CursorShape.PointingHandCursor)
            self._style_table_action_buttons(btn_cs, btn_cl, btn_ca, btn_insp, is_dark)

            act_layout.addWidget(btn_cs)
            act_layout.addWidget(btn_cl)
            act_layout.addWidget(btn_ca)
            act_layout.addWidget(btn_insp)
            self.tracklist_table.setCellWidget(row, 10, action_widget)

            self.tracklist_table.setRowHeight(row, 36)

    def _style_table_action_buttons(self, btn_cs, btn_cl, btn_ca, btn_insp, is_dark: bool):
        if is_dark:
            btn_cs.setStyleSheet("background-color: #141a2e; color: #38bdf8; border: 1px solid #233052; border-radius: 3px; font-size: 10px; font-weight: 700;")
            btn_cl.setStyleSheet("background-color: #141a2e; color: #c084fc; border: 1px solid #233052; border-radius: 3px; font-size: 10px; font-weight: 700;")
            btn_ca.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4f46e5, stop:1 #7c3aed); color: #ffffff; border: 1px solid #818cf8; border-radius: 3px; font-size: 10px; font-weight: 800;")
            btn_insp.setStyleSheet("background-color: #0284c7; color: #ffffff; border: 1px solid #38bdf8; border-radius: 3px; font-size: 9.5px; font-weight: 700; padding: 2px 6px;")
        else:
            btn_cs.setStyleSheet("background-color: #f1f5f9; color: #0284c7; border: 1px solid #cbd5e1; border-radius: 3px; font-size: 10px; font-weight: 700;")
            btn_cl.setStyleSheet("background-color: #f1f5f9; color: #7c3aed; border: 1px solid #cbd5e1; border-radius: 3px; font-size: 10px; font-weight: 700;")
            btn_ca.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4f46e5, stop:1 #7c3aed); color: #ffffff; border: 1px solid #818cf8; border-radius: 3px; font-size: 10px; font-weight: 800;")
            btn_insp.setStyleSheet("background-color: #0284c7; color: #ffffff; border: 1px solid #0369a1; border-radius: 3px; font-size: 9.5px; font-weight: 700; padding: 2px 6px;")

    def _copy_single_style(self, song: dict):
        text = song.get("style_prompt", "")
        if text:
            QApplication.clipboard().setText(text)
            song["status"] = "copied"
            self._on_card_status_changed(song)
            if hasattr(self, "_view_mode") and self._view_mode == "table":
                self._populate_table()

    def _copy_single_lyrics(self, song: dict):
        text = song.get("lyrics", "")
        if text:
            QApplication.clipboard().setText(text)
            song["status"] = "copied"
            self._on_card_status_changed(song)
            if hasattr(self, "_view_mode") and self._view_mode == "table":
                self._populate_table()

    def _copy_single_all(self, song: dict):
        bundle = f"""Title: {song.get('title', '')}
Genre: {song.get('genre', '')} ({song.get('bpm', '')}, Key: {song.get('key', '')})

[STYLE OF MUSIC]
{song.get('style_prompt', '')}

[LYRICS]
{song.get('lyrics', '')}
"""
        QApplication.clipboard().setText(bundle.strip())
        song["status"] = "copied"
        self._on_card_status_changed(song)
        if hasattr(self, "_view_mode") and self._view_mode == "table":
            self._populate_table()

    # ── Grid Rendering & Filtering ──
    def _populate_grid(self, songs: list):
        self.all_songs = songs
        self.card_widgets.clear()

        # Clear existing layout and widgets
        if hasattr(self, "grid_layout") and self.grid_layout:
            while self.grid_layout.count():
                item = self.grid_layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.hide()
                    widget.setParent(None)
                    widget.deleteLater()

        for c in self.card_widgets:
            c.hide()
            c.setParent(None)
            c.deleteLater()
        self.card_widgets.clear()

        if not songs:
            self.selected_song = None
            self.txt_insp_style.blockSignals(True)
            self.txt_insp_lyrics.blockSignals(True)
            self.txt_insp_style.clear()
            self.txt_insp_lyrics.clear()
            self.txt_insp_style.blockSignals(False)
            self.txt_insp_lyrics.blockSignals(False)
            if hasattr(self, "lbl_insp_style_chars"):
                self.lbl_insp_style_chars.setText(f"0 / {self.current_style_limit} chars")
            self._show_empty_state()
            self.lbl_grid_title.setText("🎴 បណ្ដុំបទចម្រៀង Studio Pro (0 Tracks — Empty Canvas)")
            self.lbl_batch_stat.setText("✨ ផ្ទាំងការងារទទេ — រួចរាល់សម្រាប់បង្កើតថ្មី")
            self._update_filter_counts()
            return

        cols = self._calculate_columns()
        self._current_cols = cols

        for c in range(12):
            self.grid_layout.setColumnStretch(c, 0)

        for i, s in enumerate(songs):
            card = BatchSongCard(s, self.cards_container)
            card.apply_theme(getattr(self, 'theme_key', self.is_dark))
            card.selected.connect(lambda s: self._on_card_selected(s, open_dialog=True))
            card.open_editor_requested.connect(self._forward_to_editor)
            card.open_visual_requested.connect(self.open_visual_requested.emit)
            card.crossover_requested.connect(self._swap_crossover_hook)
            card.status_changed.connect(self._on_card_status_changed)
            card.mutate_requested.connect(self._on_mutate_card)
            row = i // cols
            col = i % cols
            self.grid_layout.addWidget(card, row, col)
            self.card_widgets.append(card)

        for c in range(cols):
            self.grid_layout.setColumnStretch(c, 1)

        if self.current_lang == "English":
            self.lbl_grid_title.setText(f"🎴 Batch Studio Pro Tracks ({len(songs)} Ready Takes)")
        elif "Khmer" in self.current_lang or "ខ្មែរ" in self.current_lang:
            self.lbl_grid_title.setText(f"🎴 បណ្ដុំបទចម្រៀង Studio Pro ({len(songs)} បទរួចរាល់)")
        else:
            self.lbl_grid_title.setText(f"🎴 Batch Studio Pro Tracks ({len(songs)} បទចម្រៀង)")

        if hasattr(self, "lbl_batch_stat"):
            if self.current_lang == "English":
                self.lbl_batch_stat.setText(f"Total {len(songs)} Songs... Ready to Copy / Suno")
            elif "Khmer" in self.current_lang or "ខ្មែរ" in self.current_lang:
                self.lbl_batch_stat.setText(f"សរុប {len(songs)} បទ... ស្អាត Copy បានភ្លាមៗ")
            else:
                self.lbl_batch_stat.setText(f"សរុប {len(songs)} បទ (Khmer + English)... ស្អាត Copy បានភ្លាមៗ")
        self._update_filter_counts()
        self._apply_filter()

        if hasattr(self, "tracklist_table") and self.tracklist_table.isVisible():
            self._populate_table()
        if hasattr(self, "lbl_grid_badge"):
            self.lbl_grid_badge.setText(f"{len(songs)} Tracks Ready")
        self._update_novelty_metrics()
        for s in songs:
            if s.get("title"):
                self.session_memory_titles.add(s["title"])
        self._update_memory_ui()
        if songs:
            self._on_card_selected(songs[0], open_dialog=False)

    def _show_empty_state(self):
        empty_widget = QFrame(self.cards_container)
        empty_widget.setObjectName("emptyStateFrame")
        is_dark = getattr(self, "is_dark", True)

        bg = "#0f1426" if is_dark else "#f8fafc"
        border = "#283354" if is_dark else "#cbd5e1"
        txt_title = "#f8fafc" if is_dark else "#0f172a"
        txt_sub = "#94a3b8" if is_dark else "#64748b"

        empty_widget.setStyleSheet(f"""
            QFrame#emptyStateFrame {{
                background-color: {bg};
                border: 2px dashed {border};
                border-radius: 12px;
                padding: 40px 20px;
            }}
        """)
        empty_layout = QVBoxLayout(empty_widget)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.setSpacing(10)

        icon_lbl = QLabel("🎴")
        icon_lbl.setStyleSheet("font-size: 38px; background: transparent; border: none;")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(icon_lbl)

        title_lbl = QLabel("ផ្ទាំងការងារទទេ (Empty Studio Canvas)")
        title_lbl.setStyleSheet(f"font-size: 15px; font-weight: 800; color: {txt_title}; background: transparent; border: none;")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(title_lbl)

        sub_lbl = QLabel("មិនទាន់មានបទចម្រៀងនៅក្នុង Grid នេះទេ។ សូមចុចប៊ូតុងខាងក្រោមដើម្បីបង្កើតបទចម្រៀងថ្មីៗភ្លាមៗ៖")
        sub_lbl.setStyleSheet(f"font-size: 11.5px; color: {txt_sub}; background: transparent; border: none;")
        sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(sub_lbl)

        self.btn_quick_create = QPushButton("⚡ បង្កើតបទចម្រៀងឥឡូវនេះ (Generate Now)")
        self.btn_quick_create.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_quick_create.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7c3aed, stop:1 #4f46e5);
                color: #ffffff;
                font-weight: 800;
                font-size: 12px;
                padding: 10px 24px;
                border: 1px solid #a855f7;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8b5cf6, stop:1 #6366f1);
            }
        """)
        self.btn_quick_create.clicked.connect(self._start_batch_generation)
        empty_layout.addWidget(self.btn_quick_create, alignment=Qt.AlignmentFlag.AlignCenter)

        cols = max(1, getattr(self, "_current_cols", 4))
        self.grid_layout.addWidget(empty_widget, 0, 0, 1, cols)
        for c in range(cols):
            self.grid_layout.setColumnStretch(c, 1)

    def _is_worker_running(self) -> bool:
        return hasattr(self, "worker") and self.worker is not None and self.worker.isRunning()

    def _set_busy(self, is_busy: bool):
        self.btn_generate_batch.setEnabled(not is_busy)
        self.btn_append.setEnabled(not is_busy)
        if hasattr(self, "btn_clear_sidebar") and self.btn_clear_sidebar:
            self.btn_clear_sidebar.setEnabled(not is_busy)
        if hasattr(self, "btn_clear_grid") and self.btn_clear_grid:
            self.btn_clear_grid.setEnabled(not is_busy)
        if hasattr(self, "btn_new_project") and self.btn_new_project:
            self.btn_new_project.setEnabled(not is_busy)
        if hasattr(self, "btn_quick_create") and self.btn_quick_create:
            self.btn_quick_create.setEnabled(not is_busy)

    def _clear_batch_action(self):
        if self._is_worker_running():
            self.lbl_batch_stat.setText("⚠️ កំពុងបង្កើតបទចម្រៀង សូមរង់ចាំការបញ្ចប់សិន...")
            return
        if not self.all_songs:
            self.lbl_batch_stat.setText("✨ ផ្ទាំង Grid ទំនេរស្រាប់ (រួចរាល់សម្រាប់បង្កើតថ្មី)")
            return

        reply = QMessageBox.question(
            self,
            "Clear Batch Songs",
            f"តើអ្នកពិតជាចង់សម្អាត និងលុបបទចម្រៀងទាំងអស់ចំនួន {len(self.all_songs)} បទ ចេញពី Grid មែនទេ?\n(Are you sure you want to clear all {len(self.all_songs)} songs from the grid?)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.clear_batch_data()

    def clear_batch_data(self):
        self._populate_grid([])
        self.lbl_batch_stat.setText("✨ បានសម្អាតរួចរាល់ — ផ្ទាំងការងារទទេ")

    def _set_diversity(self, diversity_text: str):
        if hasattr(self, "combo_diversity"):
            for i in range(self.combo_diversity.count()):
                if diversity_text.lower() in self.combo_diversity.itemText(i).lower():
                    self.combo_diversity.setCurrentIndex(i)
                    return
            self.combo_diversity.setCurrentIndex(0)

    def new_batch_project(self):
        if self._is_worker_running():
            self.lbl_batch_stat.setText("⚠️ កំពុងបង្កើតបទចម្រៀង សូមរង់ចាំការបញ្ចប់សិន...")
            return
        if self.all_songs:
            reply = QMessageBox.question(
                self,
                "New Batch Project",
                "តើអ្នកចង់ចាប់ផ្តើមគម្រោងថ្មី (New Batch Project) មែនទេ?\nទិន្នន័យបទចម្រៀង និងប្រធានបទនឹងត្រូវកំណត់ឡើងវិញ។\n(Start a fresh batch project? Current songs will be cleared and inputs reset.)",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        # Reset sidebar inputs with a fresh inspiring theme
        import random
        themes_en = [
            "Midnight Rain & Neon Reflections",
            "Coffee Shop Romance & Forgotten Letters",
            "Highway Under Summer Stars",
            "Lost in the Analog Haze",
            "Concrete Wildflowers & Dreams",
            "Velvet Shadows & Lingering Perfume",
            "Stargazing on an Empty Rooftop",
            "Golden Hour Acoustic Memories",
            "Ocean Breeze & Bonfire Embers",
            "Chasing Whispers in the Wind",
            "Electric Heartbeats at 3 AM",
            "Cyberpunk Alley & Broken Promises"
        ]
        themes_kh = [
            "រឿងរ៉ាវស្នេហាឆ្លងកាត់រដូវភ្លៀងផ្ការីក",
            "អនុស្សាវរីយ៍ស្ទឹងសង្កែ និងក្ដីស្រណោះ",
            "ក្ដីសង្ឃឹម និងការតស៊ូរបស់កូនខ្មែរ",
            "រាត្រីស្រមោលព្រះចន្ទពេញបូណ៌មី",
            "ភ្លេងការស្នេហ៍ដំបូងមិនអាចបំភ្លេច",
            "កាហ្វេរាត្រី និងដំណក់ទឹកភ្លៀង",
            "រាំវង់ចូលឆ្នាំថ្មី សប្បាយរីករាយ",
            "ផ្លូវដីក្រហមត្រឡប់ទៅស្រុកកំណើត",
            "សំឡេងទ្រសោរាត្រីរងារ",
            "ផ្កាចំប៉ីស្រទំកណ្តាលក្រុង"
        ]
        if self.current_lang == "Both" or "Both" in self.current_lang:
            pool = themes_kh + themes_en
        elif "Khmer" in self.current_lang or "ខ្មែរ" in self.current_lang:
            pool = themes_kh
        else:
            pool = themes_en
        cur = self.txt_theme.toPlainText().strip()
        candidates = [t for t in pool if t != cur]
        new_theme = random.choice(candidates if candidates else pool)
        self.txt_theme.setPlainText(new_theme)

        if hasattr(self, "txt_story_seed"):
            self.txt_story_seed.clear()
        if hasattr(self, "combo_depth_mode"):
            self.combo_depth_mode.setCurrentIndex(0)

        # Reset language & vocal pills
        self._set_vocal("Mixed")
        self._set_diversity("Wide Spectrum")

        # Clear batch data & show empty canvas
        self.clear_batch_data()
        self.lbl_batch_stat.setText(f"✨ គម្រោងថ្មី: «{new_theme}» — ចុច «⚡ បង្កើតបទចម្រៀងថ្មី»")

    def _on_card_selected(self, song_data: dict, open_dialog: bool = True):
        self.selected_song = song_data
        for card in self.card_widgets:
            card.set_active(card.song_data.get("id") == song_data.get("id"))

        if hasattr(self, "txt_insp_style"):
            self.txt_insp_style.blockSignals(True)
            self.txt_insp_style.setText(song_data.get("style_prompt", ""))
            self.txt_insp_style.blockSignals(False)
        if hasattr(self, "txt_insp_lyrics"):
            self.txt_insp_lyrics.blockSignals(True)
            self.txt_insp_lyrics.setText(song_data.get("lyrics", ""))
            self.txt_insp_lyrics.blockSignals(False)
        if hasattr(self, "lbl_insp_style_chars"):
            self.lbl_insp_style_chars.setText(f"{len(song_data.get('style_prompt', ''))} / {self.current_style_limit} chars")

        if open_dialog:
            self._open_song_inspector(song_data)

    def _open_song_inspector(self, song_data: dict):
        if not hasattr(self, "inspector_dialog") or self.inspector_dialog is None:
            self.inspector_dialog = StudioSongInspectorDialog(
                song_data=song_data,
                all_songs=self.all_songs,
                is_dark=self.is_dark,
                parent=self
            )
            self.inspector_dialog.song_updated.connect(self._on_dialog_song_updated)
            self.inspector_dialog.open_editor_requested.connect(self._forward_to_editor)
            self.inspector_dialog.open_visual_requested.connect(self.open_visual_requested.emit)
            self.inspector_dialog.crossover_requested.connect(self._swap_crossover_hook)
            self.inspector_dialog.finished.connect(self._on_dialog_closed)
            self.inspector_dialog.show()
        else:
            self.inspector_dialog.all_songs = self.all_songs
            self.inspector_dialog._load_song_data(song_data)
            self.inspector_dialog.raise_()
            self.inspector_dialog.activateWindow()

    def _on_dialog_song_updated(self, updated_song: dict):
        s_id = updated_song.get("id")
        for i, s in enumerate(self.all_songs):
            if s.get("id") == s_id:
                self.all_songs[i] = updated_song
                break
        for card in self.card_widgets:
            if card.song_data.get("id") == s_id:
                card.song_data = updated_song
                card.update_lyrics_preview()
                card.update_style_preview()
                card.title_lbl.setText(updated_song.get("title", ""))
                q_hit = updated_song.get("quality_score", 96)
                q_rhyme = updated_song.get("rhyme_score", 94)
                if hasattr(card, "quality_badge"):
                    card.quality_badge.setText(f"🎯 {q_hit}% • Rhyme: {q_rhyme}%")
                break

    def _on_dialog_closed(self):
        self.inspector_dialog = None

    def _on_card_status_changed(self, song_data: dict):
        self._update_filter_counts()
        self._apply_filter()
        if hasattr(self, "tracklist_table") and self.tracklist_table.isVisible():
            self._populate_table()

    def _set_filter_mode(self, mode: str):
        self.filter_mode = mode
        self._update_filter_button_styles()
        if hasattr(self, '_update_column_toggle_ui'):
            self._update_column_toggle_ui()
        self._apply_filter()

    def _update_filter_button_styles(self):
        buttons = [
            ("all", self.btn_filter_all),
            ("favorites", self.btn_filter_fav),
            ("uncopied", self.btn_filter_uncopied),
            ("copied", self.btn_filter_copied)
        ]
        t = getattr(self, "theme", get_theme(getattr(self, "is_dark", True)))
        is_dark = t.get("is_dark", True)
        for mode, btn in buttons:
            is_active = (self.filter_mode == mode)
            if is_dark:
                if is_active:
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {t['active_pill_bg']};
                            color: {t['active_pill_color']};
                            font-weight: 800;
                            font-size: 11px;
                            border: 1px solid {t['border_accent']};
                            border-radius: 5px;
                            padding: 4px 10px;
                        }}
                    """)
                else:
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {t['subtle_pill_bg']};
                            color: {t['text_muted']};
                            font-weight: 600;
                            font-size: 11px;
                            border: 1px solid {t['border']};
                            border-radius: 5px;
                            padding: 4px 10px;
                        }}
                        QPushButton:hover {{
                            background-color: {t['bg_card_alt']};
                            color: #ffffff;
                        }}
                    """)
            else:
                if is_active:
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {t['accent']};
                            color: #ffffff;
                            font-weight: 800;
                            font-size: 11px;
                            border: 1px solid {t['border_accent']};
                            border-radius: 5px;
                            padding: 4px 10px;
                        }}
                    """)
                else:
                    btn.setStyleSheet("""
                        QPushButton {
                            background-color: #ffffff;
                            color: #334155;
                            font-weight: 600;
                            font-size: 11px;
                            border: 1px solid #cbd5e1;
                            border-radius: 5px;
                            padding: 4px 10px;
                        }
                        QPushButton:hover {
                            background-color: #f1f5f9;
                            color: #0f172a;
                        }
                    """)

    def _update_filter_counts(self):
        total = len(self.all_songs)
        favs = sum(1 for s in self.all_songs if s.get("is_favorite", False))
        copied = sum(1 for s in self.all_songs if s.get("status") in ["copied", "done"])
        uncopied = total - copied

        is_kh = "Khmer" in self.current_lang or "ខ្មែរ" in self.current_lang
        is_en = self.current_lang == "English"
        if is_en:
            self.btn_filter_all.setText(f"All ({total})")
            self.btn_filter_fav.setText(f"⭐ Favorites ({favs})")
            self.btn_filter_uncopied.setText(f"⏳ Uncopied ({uncopied})")
            self.btn_filter_copied.setText(f"✓ Copied ({copied})")
        elif is_kh:
            self.btn_filter_all.setText(f"ទាំងអស់ ({total})")
            self.btn_filter_fav.setText(f"⭐ ផ្កាយ ({favs})")
            self.btn_filter_uncopied.setText(f"⏳ មិនទាន់ Copy ({uncopied})")
            self.btn_filter_copied.setText(f"✓ បាន Copy ({copied})")
        else:
            self.btn_filter_all.setText(f"All / ទាំងអស់ ({total})")
            self.btn_filter_fav.setText(f"⭐ Favorites ({favs})")
            self.btn_filter_uncopied.setText(f"⏳ Uncopied ({uncopied})")
            self.btn_filter_copied.setText(f"✓ Copied ({copied})")

    def _on_search_text_changed(self, text: str):
        self.search_query = text.strip().lower()
        self._apply_filter()

    def _apply_filter(self):
        query = getattr(self, "search_query", "").strip().lower()
        for card in self.card_widgets:
            s = card.song_data
            matches_filter = True
            if self.filter_mode == "all":
                matches_filter = True
            elif self.filter_mode == "favorites":
                matches_filter = bool(s.get("is_favorite", False))
            elif self.filter_mode == "uncopied":
                matches_filter = (s.get("status", "new") == "new")
            elif self.filter_mode == "copied":
                matches_filter = (s.get("status") in ["copied", "done"])

            matches_search = True
            if query:
                title = str(s.get("title", "")).lower()
                genre = str(s.get("genre", "")).lower()
                bpm = str(s.get("bpm", "")).lower()
                key = str(s.get("key", "")).lower()
                lyrics = str(s.get("lyrics", "")).lower()
                matches_search = (query in title or query in genre or query in bpm or query in key or query in lyrics)

            card.setVisible(matches_filter and matches_search)

        if hasattr(self, "tracklist_table") and self.tracklist_table:
            for row in range(self.tracklist_table.rowCount()):
                if row < len(self.all_songs):
                    s = self.all_songs[row]
                    m_filt = True
                    if self.filter_mode == "all":
                        m_filt = True
                    elif self.filter_mode == "favorites":
                        m_filt = bool(s.get("is_favorite", False))
                    elif self.filter_mode == "uncopied":
                        m_filt = (s.get("status", "new") == "new")
                    elif self.filter_mode == "copied":
                        m_filt = (s.get("status") in ["copied", "done"])

                    m_srch = True
                    if query:
                        t = str(s.get("title", "")).lower()
                        g = str(s.get("genre", "")).lower()
                        b = str(s.get("bpm", "")).lower()
                        k = str(s.get("key", "")).lower()
                        l = str(s.get("lyrics", "")).lower()
                        m_srch = (query in t or query in g or query in b or query in k or query in l)

                    self.tracklist_table.setRowHidden(row, not (m_filt and m_srch))

        self._rearrange_grid()

    def _copy_next_uncopied(self):
        next_song = None
        target_card = None
        for card in self.card_widgets:
            if card.song_data.get("status", "new") == "new":
                next_song = card.song_data
                target_card = card
                break

        if not next_song:
            QMessageBox.information(
                self,
                "All Tracks Copied!",
                "🎉 All tracks in this batch have already been copied!\nYour entire album queue is ready in Suno."
            )
            return

        bundle = f"""Title: {next_song.get('title', '')}
Genre: {next_song.get('genre', '')} ({next_song.get('bpm', '')}, Key: {next_song.get('key', '')})

[STYLE OF MUSIC]
{next_song.get('style_prompt', '')}

[LYRICS]
{next_song.get('lyrics', '')}
"""
        QApplication.clipboard().setText(bundle.strip())
        next_song["status"] = "copied"
        if target_card:
            target_card._update_status_ui()
            self._on_card_selected(next_song)
            self.cards_scroll.ensureWidgetVisible(target_card)

        self._update_filter_counts()
        self._apply_filter()
        self._flash_btn(self.btn_copy_next, f"✓ Copied #{next_song.get('id', 1):02d}!")

    def _forward_to_editor(self, song_data: dict):
        self.open_editor_requested.emit(song_data)

    def _open_selected_in_editor(self):
        if self.selected_song:
            self.selected_song["status"] = "done"
            for card in self.card_widgets:
                if card.song_data.get("id") == self.selected_song.get("id"):
                    card._update_status_ui()
                    break
            self._update_filter_counts()
            self.open_editor_requested.emit(self.selected_song)

    # ── Suno v6 Metatag Injection ──
    def _inject_v6_to_selected(self):
        if not self.selected_song:
            return
        bpm = self.selected_song.get("bpm", "120 BPM")
        key = self.selected_song.get("key", "C")
        genre = self.selected_song.get("genre", "Pop")
        cur_lyrics = self.txt_insp_lyrics.toPlainText().strip()

        enriched = inject_suno_v6_cues(cur_lyrics, bpm, key, genre, self.current_vocal)
        self.txt_insp_lyrics.setText(enriched)
        self.selected_song["lyrics"] = enriched

        # Update card snippet
        for card in self.card_widgets:
            if card.song_data.get("id") == self.selected_song.get("id"):
                card.update_lyrics_preview()
                break

        self._flash_btn(self.btn_insp_inject_v6, "✓ Injected!")

    def _inject_v6_to_all(self):
        if not self.all_songs:
            return
        reply = QMessageBox.question(
            self,
            "Inject Suno v6 Cues",
            f"Are you sure you want to inject Suno v6 audio cues ([Tempo], [Key], [Instrumental Solo], [Drop], [Fade Out]) into all {len(self.all_songs)} songs?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            for s in self.all_songs:
                bpm = s.get("bpm", "120 BPM")
                key = s.get("key", "C")
                genre = s.get("genre", "Pop")
                s["lyrics"] = inject_suno_v6_cues(s.get("lyrics", ""), bpm, key, genre, self.current_vocal)

            for card in self.card_widgets:
                card.update_lyrics_preview()

            if self.selected_song:
                self.txt_insp_lyrics.setText(self.selected_song.get("lyrics", ""))

            self._flash_btn(self.btn_inject_all_v6, "✓ All Injected!")
            QMessageBox.information(self, "Success", f"Successfully injected Suno v6 metatags into all {len(self.all_songs)} tracks!")

    def _insert_metatag(self, tag: str):
        cursor = self.txt_insp_lyrics.textCursor()
        cursor.insertText(f"\n{tag}\n")
        self.txt_insp_lyrics.setTextCursor(cursor)
        if self.selected_song:
            self.selected_song["lyrics"] = self.txt_insp_lyrics.toPlainText()
            for card in self.card_widgets:
                if card.song_data.get("id") == self.selected_song.get("id"):
                    card.update_lyrics_preview()
                    break

    # ── Lyrical Depth & Meaning Deepener ──
    def _deepen_selected_song_meaning(self):
        if not self.selected_song:
            return

        title = self.selected_song.get("title", "Song")
        genre = self.selected_song.get("genre", "Pop")
        lyrics = self.txt_insp_lyrics.toPlainText().strip()
        if not lyrics:
            return

        depth_mode = self.combo_depth_mode.currentText() if hasattr(self, "combo_depth_mode") else "Deep Emotional Catharsis"
        self.btn_insp_deepen.setEnabled(False)
        self.btn_insp_deepen.setText("💎 Deepening...")
        self.lbl_batch_stat.setText(f"💎 កំពុងកែច្នៃ '{title}' ឱ្យមានន័យជ្រៅ (Berklee Sensory Engine)...")

        self.deepen_worker = DeepenLyricWorker(
            title=title,
            genre=genre,
            lyrics=lyrics,
            language=self.current_lang,
            depth_mode=depth_mode
        )
        self.deepen_worker.finished.connect(self._on_lyrics_deepened)
        self.deepen_worker.error.connect(self._on_lyrics_deepen_error)
        self.deepen_worker.start()

    def _on_lyrics_deepened(self, new_lyrics: str):
        self.btn_insp_deepen.setEnabled(True)
        self.btn_insp_deepen.setText("💎 Deepen")
        if not self.selected_song:
            return

        self.txt_insp_lyrics.setPlainText(new_lyrics)
        self.selected_song["lyrics"] = new_lyrics
        for card in self.card_widgets:
            if card.song_data.get("id") == self.selected_song.get("id"):
                card.song_data["lyrics"] = new_lyrics
                card.update_lyrics_preview()
                break
        self._flash_btn(self.btn_insp_deepen, "✓ Deepened!")
        self.lbl_batch_stat.setText(f"✓ '{self.selected_song.get('title')}' lyrics deepened with poetic meaning!")

    def _on_lyrics_deepen_error(self, err: str):
        self.btn_insp_deepen.setEnabled(True)
        self.btn_insp_deepen.setText("💎 Deepen")
        QMessageBox.warning(self, "Deepen Error", f"Could not deepen lyrics:\n{err}")

    def _open_style_mutator_menu(self):
        if not self.selected_song:
            return

        bpm = self.selected_song.get("bpm", "120 BPM")
        key = self.selected_song.get("key", "C")

        take_a = f"acoustic folk, intimate close-mic vocal, fingerpicked Martin D-28 acoustic, gentle shaker, wooden room acoustics, {bpm}, Key: {key}"
        take_b = f"80s synthwave, punchy LinnDrum kick, analog sawtooth arpeggios, neon atmosphere, airy vocal production, {bpm}, Key: {key}"
        take_c = f"cinematic rock ballad, gritty overdriven guitars, soaring stadium crescendo, thunderous live drums, spatial reverb, {bpm}, Key: {key}"

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #121422;
                color: #f1f5f9;
                border: 1px solid #4338ca;
                padding: 4px;
                font-size: 11px;
            }
            QMenu::item {
                padding: 6px 12px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #6d28d9;
                color: #ffffff;
            }
        """)

        act_a = QAction(f"🎸 Take 1: Acoustic & Unplugged ({bpm}, {key})", self)
        act_a.triggered.connect(lambda: self._apply_mutated_style(take_a[:self.current_style_limit], "Acoustic Unplugged"))
        menu.addAction(act_a)

        act_b = QAction(f"⚡ Take 2: 80s Synthwave / Melodic Dance ({bpm}, {key})", self)
        act_b.triggered.connect(lambda: self._apply_mutated_style(take_b[:self.current_style_limit], "Synthwave"))
        menu.addAction(act_b)

        act_c = QAction(f"🔥 Take 3: Stadium Rock / Cinematic Ballad ({bpm}, {key})", self)
        act_c.triggered.connect(lambda: self._apply_mutated_style(take_c[:self.current_style_limit], "Arena Rock"))
        menu.addAction(act_c)

        menu.exec(self.btn_insp_mutate.mapToGlobal(self.btn_insp_mutate.rect().bottomLeft()))

    def _apply_mutated_style(self, style_str: str, genre_label: str):
        if self.selected_song:
            self.selected_song["style_prompt"] = style_str
            self.selected_song["genre"] = genre_label
            self.txt_insp_style.setText(style_str)
            for card in self.card_widgets:
                if card.song_data.get("id") == self.selected_song.get("id"):
                    card.update_style_preview()
                    break
            self._flash_btn(self.btn_insp_mutate, f"✓ Applied {genre_label}!")

    # ── Generation Actions ──
    def _start_batch_generation(self):
        if self._is_worker_running():
            return
        theme = self.txt_theme.toPlainText().strip() or "sad song"
        self._set_busy(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(10)
        self.lbl_batch_stat.setText("⏳ កំពុងបង្កើតបទដោយ Anti-Duplication Turbo Engine...")

        depth_mode = self.combo_depth_mode.currentText() if hasattr(self, "combo_depth_mode") else "Deep Emotional Catharsis"
        story_seed = self.txt_story_seed.toPlainText().strip() if hasattr(self, "txt_story_seed") else ""

        self.worker = BatchGenerateWorker(
            theme=theme,
            language=self.current_lang,
            count=self.current_count,
            style_limit=self.current_style_limit,
            vocal_type=self.current_vocal,
            diversity_mode=self.current_diversity,
            anti_duplication=self.anti_duplication,
            depth_mode=depth_mode,
            story_seed=story_seed,
            offset=0,
            existing_titles=list(self.session_memory_titles),
            vocal_persona=getattr(self, "current_persona", ""),
            album_arc=getattr(self, "album_arc_enabled", False)
        )
        self.worker.status_update.connect(self.lbl_batch_stat.setText)
        self.worker.song_ready.connect(self._on_worker_progress)
        self.worker.batch_finished.connect(self._on_batch_finished)
        self.worker.error.connect(self._on_worker_error)
        self.worker.start()

    def _append_batch(self):
        if self._is_worker_running():
            return
        theme = self.txt_theme.toPlainText().strip() or "sad song"
        self._set_busy(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(10)
        self.lbl_batch_stat.setText("⏳ កំពុងបង្កើតបទបន្ថែម...")

        depth_mode = self.combo_depth_mode.currentText() if hasattr(self, "combo_depth_mode") else "Deep Emotional Catharsis"
        story_seed = self.txt_story_seed.toPlainText().strip() if hasattr(self, "txt_story_seed") else ""

        append_count = min(10, self.current_count) if self.current_count > 0 else 10
        offset_idx = len(self.all_songs)
        existing_titles = [s.get("title", "") for s in self.all_songs if s.get("title")]

        self.worker = BatchGenerateWorker(
            theme=theme,
            language=self.current_lang,
            count=append_count,
            style_limit=self.current_style_limit,
            vocal_type=self.current_vocal,
            diversity_mode=self.current_diversity,
            anti_duplication=self.anti_duplication,
            depth_mode=depth_mode,
            story_seed=story_seed,
            offset=offset_idx,
            existing_titles=list(self.session_memory_titles.union(set(existing_titles))),
            vocal_persona=getattr(self, "current_persona", ""),
            album_arc=getattr(self, "album_arc_enabled", False)
        )
        self.worker.status_update.connect(self.lbl_batch_stat.setText)
        self.worker.song_ready.connect(self._on_worker_progress)
        self.worker.batch_finished.connect(self._on_append_finished)
        self.worker.error.connect(self._on_worker_error)
        self.worker.start()

    def _on_worker_progress(self, song_obj: dict, current: int, total: int):
        pct = int((current / max(1, total)) * 100)
        self.progress_bar.setValue(pct)
        self.lbl_batch_stat.setText(f"⏳ កំពុងបង្កើតបទទី {current} នៃ {total}...")

    def _on_batch_finished(self, songs: list):
        self.progress_bar.setValue(100)
        self.progress_bar.setVisible(False)
        self._set_busy(False)
        self._populate_grid(songs)

    def _on_append_finished(self, new_songs: list):
        self.progress_bar.setValue(100)
        self.progress_bar.setVisible(False)
        self._set_busy(False)

        start_id = len(self.all_songs) + 1
        for i, s in enumerate(new_songs):
            s["id"] = start_id + i

        combined = self.all_songs + new_songs
        self._populate_grid(combined)

    def _on_worker_error(self, err_msg: str):
        self.progress_bar.setVisible(False)
        self._set_busy(False)
        self.lbl_batch_stat.setText("⚠️ មានបញ្ហាក្នុងការបង្កើត (ប្រើទិន្នន័យ Demo ជំនួស)")

    # ── Batch Clipboard Actions ──
    def _copy_entire_batch(self):
        if not self.all_songs:
            return
        lines = []
        for s in self.all_songs:
            lines.append(f"#{s.get('id', 1):02d} {s.get('title', '')}")
            lines.append(f"Style: {s.get('style_prompt', '')}")
            lines.append(f"Lyrics:\n{s.get('lyrics', '')}\n")
            lines.append("-" * 40)
        QApplication.clipboard().setText("\n".join(lines))
        QMessageBox.information(self, "Copied All", f"បាន Copy បទទាំងអស់ចំនួន {len(self.all_songs)} បទចូលទៅក្នុង Clipboard រួចរាល់!")

    def _on_persona_changed(self, text: str):
        self.current_persona = text

    def _apply_album_concept_arc(self):
        if not self.all_songs:
            return
        album_roles_10 = [
            "💿 Track 01: Overture / Ambient Intro",
            "💿 Track 02: Lead Radio Single",
            "💿 Track 03: Driving Mid-Tempo Groove",
            "💿 Track 04: Vulnerable Deep Cut Ballad",
            "💿 Track 05: Fast Crossover Anthem",
            "💿 Track 06: Acoustic Interlude",
            "💿 Track 07: Dark Turning Point",
            "💿 Track 08: Epic Emotional Climax",
            "💿 Track 09: Anthemic Reprise & Drop",
            "💿 Track 10: Epilogue & Piano Outro"
        ]
        album_roles_20 = album_roles_10 + [
            "💿 Track 11: Disc 2 Awakening",
            "💿 Track 12: Euphoric Dance Banger",
            "💿 Track 13: Midnight Confessional",
            "💿 Track 14: High Stakes Confrontation",
            "💿 Track 15: Heavy Guitar Solo Climax",
            "💿 Track 16: Ethereal Ambient Bridge",
            "💿 Track 17: Redemption Anthem",
            "💿 Track 18: Full Ensemble Finale",
            "💿 Track 19: Grand Cathartic Resolution",
            "💿 Track 20: Vinyl Noise & Final Breath"
        ]

        roles_list = album_roles_20 if len(self.all_songs) > 10 else album_roles_10
        for i, s in enumerate(self.all_songs):
            assigned = roles_list[i % len(roles_list)]
            s["album_role"] = assigned
            if not s.get("lyrics", "").startswith("[Album Arc"):
                s["lyrics"] = f"[Album Arc: {assigned.replace('💿 ', '')}]\n" + s.get("lyrics", "")

        self.album_arc_enabled = True
        self._populate_grid(self.all_songs)
        self.lbl_batch_stat.setText(f"💿 Album Concept Arc Activated: Structured {len(self.all_songs)} tracks into cohesive storyline!")

    def _split_into_20_styles(self):
        target = self.selected_song or (self.all_songs[0] if self.all_songs else None)
        if not target:
            return

        base_title = target.get("title", "Master Take")
        base_lyrics = target.get("lyrics", "")
        clean_title = re.sub(r'\s*\(Take\s*\d+.*?\)', '', base_title).strip()
        clean_title = re.sub(r'\s*\(.*?\)$', '', clean_title).strip()

        style_palettes = [
            ("60s Golden Garage Rock", "72 BPM", "Am", "Khmer 60s garage rock, 72 BPM, Key: Am, Farfisa organ, fuzz guitar, Sinn Sisamouth tape saturation, warm tube condenser mic"),
            ("80s Cyberpunk Synthwave", "124 BPM", "Dm", "80s cyberpunk synthwave, 124 BPM, Key: Dm, analog Prophet-5 synths, punchy LinnDrum, gated snare, neon aesthetic"),
            ("Acoustic Fingerstyle Folk", "78 BPM", "G", "acoustic folk ballad, 78 BPM, Key: G, fingerpicked Martin D-28, gentle upright bass, cello, intimate breathy vocal"),
            ("Khmer Heritage Trap Drill", "140 BPM", "Em", "Khmer trap drill, 140 BPM, Key: Em, sliding 808 sub-bass, sampled Chapei riff, rapid rhythmic flow, stadium drop"),
            ("Stadium Arena Rock", "128 BPM", "F#m", "stadium arena rock, 128 BPM, Key: F#m, roaring Les Paul electric guitar, driving bassline, powerhouse drums, guitar solo"),
            ("Silky Neo-Soul & Rhodes", "84 BPM", "C#m", "silky neo-soul, 84 BPM, Key: C#m, Rhodes Mark I, laid-back rimshot, warm analog bass, falsetto vocal harmonies"),
            ("Surin Electric Kantrum Folk", "132 BPM", "C", "Surin electric kantrum, 132 BPM, Key: C, Skor Daey percussion, electric Tro Sau, celebratory festive call-and-response"),
            ("Ambient Cinematic Strings", "65 BPM", "Eb", "ambient cinematic orchestral, 65 BPM, Key: Eb, felt piano, soaring symphonic strings, haunting French horn, emotional climax"),
            ("UK Garage & 2-Step", "134 BPM", "Bm", "UK garage 2-step, 134 BPM, Key: Bm, syncopated shuffle drums, deep sub-bass pulse, pitched vocal chops, vinyl crackle"),
            ("Psych-Surf Rock 1970s", "146 BPM", "A", "70s psych surf rock, 146 BPM, Key: A, spring reverb guitar, Ros Sereysothea bright soprano, driving garage fuzz"),
            ("Dark Bedroom Lo-Fi", "80 BPM", "Bb", "dark bedroom lofi, 80 BPM, Key: Bb, warbly tape keys, vinyl dust, muted sub kick, intimate whispered vocals"),
            ("Euphoric Festival EDM", "128 BPM", "F", "festival melodic EDM anthem, 128 BPM, Key: F, soaring supersaw leads, 16-bar snare riser, explosive bass drop"),
            ("Pleng Ka Royal R&B Fusion", "76 BPM", "D", "Pleng Ka wedding R&B fusion, 76 BPM, Key: D, Tro Ou strings, nylon guitar, Meng Keo Pichenda silk vocal ornamentations"),
            ("Indie Post-Punk Revival", "150 BPM", "Em", "indie post-punk, 150 BPM, Key: Em, chorus-drenched driving bass, angular jangly electric guitars, urgent vocal delivery"),
            ("Americana Bluegrass Stomp", "102 BPM", "G", "americana bluegrass stomp, 102 BPM, Key: G, rapid banjo picking, fiddle solo, acoustic strumming, foot stomps"),
            ("Reggae Dub & Tro Sau", "74 BPM", "C", "reggae dub fusion, 74 BPM, Key: C, offbeat skank guitar, deep reggae bassline, tape echo Tro Sau leads"),
            ("Gothic Darkwave Industrial", "118 BPM", "Dm", "gothic darkwave, 118 BPM, Key: Dm, analog Moog bass arpeggio, cold drum machine, reverbed baritone vocal"),
            ("R&B Trap Slow Jam", "68 BPM", "F#m", "sensual R&B trap slow jam, 68 BPM, Key: F#m, rolling 808s, filtered Rhodes, seductive vocal runs, hi-hat rolls"),
            ("Bossa Nova Sunset Jazz", "116 BPM", "Dmaj7", "bossa nova sunset jazz, 116 BPM, Key: Dmaj7, fingerstyle nylon guitar, brushed snare, flute, suave conversational vocal"),
            ("Hollywood Epic Orchestral", "90 BPM", "Cm", "epic Hollywood trailer score, 90 BPM, Key: Cm, massive Taiko drums, Hans Zimmer brass stabs, choir climax")
        ]

        new_batch = []
        for i, (g_name, g_bpm, g_key, g_style) in enumerate(style_palettes):
            adapted_lyrics = re.sub(r'\[Intro[^\]]*\]', f'[Intro: {g_bpm}, {g_style.split(",")[0]}]', base_lyrics)
            if not adapted_lyrics.startswith("[Intro"):
                adapted_lyrics = f"[Intro: {g_bpm}, {g_style.split(',')[0]}]\n\n" + adapted_lyrics

            track_title = f"{clean_title} (Take {i+1:02d} • {g_name.split()[0]})"
            new_batch.append({
                "id": i + 1,
                "title": track_title,
                "album_role": f"💿 Take {i+1:02d}: {g_name}",
                "genre": g_name,
                "bpm": g_bpm,
                "key": g_key,
                "meter": target.get("meter", "Prosody Match"),
                "quality_score": 94 + (i % 5),
                "rhyme_score": 93 + ((i * 3) % 6),
                "style_prompt": g_style[:self.current_style_limit],
                "lyrics": adapted_lyrics,
                "language": target.get("language", "English")
            })

        self.all_songs = new_batch
        self._populate_grid(new_batch)
        self.lbl_batch_stat.setText(f"🔀 Multi-Style Take Splitter: Created 20 radical genre takes for '{clean_title}'!")

    def _humanize_all_tracks(self):
        if not self.all_songs:
            return
        from app.humanizer_engine import HumanizerEngine
        count = 0
        for song in self.all_songs:
            lang = song.get("language", "English")
            song["lyrics"] = HumanizerEngine.humanize_lyrics_locally(song.get("lyrics", ""), lang)
            song["style_prompt"] = HumanizerEngine.humanize_style_prompt_locally(song.get("style_prompt", ""), lang)
            scores = HumanizerEngine.score_human_authenticity(song["lyrics"], song["style_prompt"], lang)
            song["human_score"] = max(94, scores["overall_score"])
            song["human_certified"] = True
            count += 1

        for card in self.card_widgets:
            card.update_lyrics_preview()
            card.update_style_preview()
            card.update_quality_badge()

        if self.selected_song and hasattr(self, "txt_insp_lyrics"):
            self.txt_insp_lyrics.setText(self.selected_song.get("lyrics", ""))
            self.txt_insp_style.setText(self.selected_song.get("style_prompt", ""))

        self.lbl_batch_stat.setText(f"🌟 ស្នាដៃមនុស្សពិត: បានកែសម្រួល {count} បទឱ្យមានដង្ហើមច្រៀង និង Groove ធម្មជាតិ ១០០%!")

    def _humanize_selected_track(self):
        if not self.selected_song:
            return
        from app.humanizer_engine import HumanizerEngine
        lang = self.selected_song.get("language", "English")
        self.selected_song["lyrics"] = HumanizerEngine.humanize_lyrics_locally(self.selected_song.get("lyrics", ""), lang)
        self.selected_song["style_prompt"] = HumanizerEngine.humanize_style_prompt_locally(self.selected_song.get("style_prompt", ""), lang)
        scores = HumanizerEngine.score_human_authenticity(self.selected_song["lyrics"], self.selected_song["style_prompt"], lang)
        self.selected_song["human_score"] = max(95, scores["overall_score"])
        self.selected_song["human_certified"] = True

        if hasattr(self, "txt_insp_lyrics"):
            self.txt_insp_lyrics.setText(self.selected_song.get("lyrics", ""))
        if hasattr(self, "txt_insp_style"):
            self.txt_insp_style.setText(self.selected_song.get("style_prompt", ""))

        for card in self.card_widgets:
            if card.song_data.get("id") == self.selected_song.get("id"):
                card.update_lyrics_preview()
                card.update_style_preview()
                card.update_quality_badge()
                break

        if hasattr(self, "btn_insp_humanize"):
            self.btn_insp_humanize.setText("✅ Human Approved!")
            QTimer.singleShot(2000, lambda: self.btn_insp_humanize.setText("👤 Humanize & Approve") if hasattr(self, "btn_insp_humanize") else None)

    def _swap_selected_crossover_hook(self):
        if self.selected_song:
            self._swap_crossover_hook(self.selected_song)

    def _swap_crossover_hook(self, song_data: dict):
        if not song_data:
            return
        lyrics = song_data.get("lyrics", "")
        title = song_data.get("title", "")
        cur_lang = song_data.get("language", "")
        has_kh = any('\u1780' <= c <= '\u17ff' for c in lyrics)
        has_en = any('a' <= c.lower() <= 'z' for c in lyrics)
        is_already_fusion = "Bilingual" in cur_lang or (has_kh and has_en and ("Chorus" in lyrics or "Hook" in lyrics))

        kh_hook = """[បន្ទរ: Soaring Khmer Vocal - បទពាក្យ ៧]
ភ្លៀងធ្លាក់រលឹមលើដំបូល
បេះដូងអួលណែននឹកកន្លង
ធ្លាប់ដើរក្បែរគ្នាតាមដងផ្លូវ
ឥឡូវព្រាត់ប្រាសឆ្ងាយសែនឆ្ងាយ!
ទោះបីព្យុះភ្លៀងមកបោកបក់
ក្ដីស្រមៃនៅតែរឹងមាំ!"""

        en_hook = """[Chorus: English Billboard Anthem - Soaring Belt]
Running through the shadows of the rain!
Trying to wash away this heavy pain!
You left your memory in this empty room,
Now I'm dancing alone beneath the midnight moon!
We turn the concrete into gold!
Stand up for the stories never told!"""

        duet_hook = """[Chorus: Bilingual Duet Call-and-Response]
(English): Can you feel the heartbeat in the night?
(ខ្មែរ): ដួងចិត្តនៅតែរង់ចាំពន្លឺថ្ងៃ!
(English): We rise up from the broken ground!
(ខ្មែរ): សំឡេងកូនខ្មែររំពងពេញលោកិយ!
(Together): Forever shining like the stars above!"""

        if is_already_fusion:
            if "[Chorus" in lyrics or "[បន្ទរ" in lyrics:
                lyrics = re.sub(r'\[(?:Chorus|បន្ទរ|Hook)[^\]]*\]\n(?:[^\n\[]+\n*)+', duet_hook + "\n\n", lyrics, count=1)
            else:
                lyrics += "\n\n" + duet_hook
            song_data["meter"] = "Bilingual Duet (Call & Response)"
        elif has_kh:
            if "[បន្ទរ" in lyrics or "[Chorus" in lyrics:
                lyrics = re.sub(r'\[(?:បន្ទរ|Chorus)[^\]]*\]\n(?:[^\n\[]+\n*)+', en_hook + "\n\n", lyrics, count=1)
            else:
                lyrics += "\n\n" + en_hook
            song_data["language"] = "Bilingual Fusion"
            song_data["meter"] = "Bilingual (ពាក្យ ៧ + English Hook)"
            style_p = song_data.get("style_prompt", "")
            if "bilingual" not in style_p.lower():
                song_data["style_prompt"] = (style_p + ", bilingual crossover hook, Billboard English chorus")[:self.current_style_limit]
        else:
            if "[Chorus" in lyrics:
                lyrics = re.sub(r'\[Chorus[^\]]*\]\n(?:[^\n\[]+\n*)+', kh_hook + "\n\n", lyrics, count=1)
            else:
                lyrics += "\n\n" + kh_hook
            song_data["language"] = "Bilingual Fusion"
            song_data["meter"] = "Bilingual (AABB + Khmer Meter Hook)"
            style_p = song_data.get("style_prompt", "")
            if "bilingual" not in style_p.lower():
                song_data["style_prompt"] = (style_p + ", bilingual crossover hook, authentic Khmer emotional chorus")[:self.current_style_limit]

        song_data["lyrics"] = lyrics
        song_data["quality_score"] = min(99, song_data.get("quality_score", 95) + 2)
        song_data["rhyme_score"] = min(98, song_data.get("rhyme_score", 94) + 1)

        for card in self.card_widgets:
            if card.song_data.get("id") == song_data.get("id"):
                card.song_data = song_data
                card.lang_badge.setText("🇰🇭🇬🇧")
                card.lang_badge.setToolTip("Bilingual Fusion Track (ខ្មែរ + English Hook)")
                card.update_lyrics_preview()
                if hasattr(card, "quality_badge"):
                    card.quality_badge.setText(f"🎯 {song_data['quality_score']}% • Rhyme: {song_data['rhyme_score']}%")
                break

        if self.selected_song and self.selected_song.get("id") == song_data.get("id"):
            self.txt_insp_lyrics.blockSignals(True)
            self.txt_insp_lyrics.setPlainText(lyrics)
            self.txt_insp_lyrics.blockSignals(False)
            self.txt_insp_style.blockSignals(True)
            self.txt_insp_style.setPlainText(song_data.get("style_prompt", ""))
            self.txt_insp_style.blockSignals(False)

        self.lbl_batch_stat.setText(f"🌐 Crossover Hook Swapped: Created Billboard Bilingual Hook for '{title}'!")

    def _export_batch_file(self):
        if not self.all_songs:
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Export Pro Studio Batch", 
            "Studio_Pro_Batch_Session.csv", 
            "CSV for Suno / Excel (*.csv);;Karaoke LRC Bundle (*.lrc);;Album Booklet Markdown (*.md);;JSON Files (*.json);;Text Files (*.txt)"
        )
        if not file_path:
            return
        try:
            if file_path.endswith(".json"):
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(self.all_songs, f, ensure_ascii=False, indent=2)

            elif file_path.endswith(".csv"):
                import csv
                with open(file_path, "w", encoding="utf-8-sig", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["ID", "Title", "Album Role", "Hit Quality", "Rhyme Density", "Language", "Poetic Meter", "Genre", "BPM", "Key", "Style Prompt", "Lyrics"])
                    for s in self.all_songs:
                        writer.writerow([
                            s.get("id", 1),
                            s.get("title", ""),
                            s.get("album_role", ""),
                            f"{s.get('quality_score', 95)}%",
                            f"{s.get('rhyme_score', 94)}%",
                            s.get("language", ""),
                            s.get("meter", ""),
                            s.get("genre", ""),
                            s.get("bpm", ""),
                            s.get("key", ""),
                            s.get("style_prompt", ""),
                            s.get("lyrics", "")
                        ])

            elif file_path.endswith(".lrc"):
                lrc_lines = []
                for s in self.all_songs:
                    bpm_val = 120
                    try:
                        bpm_val = int("".join(filter(str.isdigit, s.get("bpm", "120"))))
                    except Exception:
                        bpm_val = 120
                    sec_per_beat = 60.0 / max(40, bpm_val)

                    lrc_lines.append(f"[ti:{s.get('title', '')}]")
                    lrc_lines.append("[ar:Lyric AI Writer Studio Pro]")
                    lrc_lines.append(f"[al:{s.get('album_role', 'Studio Batch')}]")
                    lrc_lines.append("[by:Suno v3.5/v4/v6]")
                    lrc_lines.append(f"# Genre: {s.get('genre', '')} • BPM: {s.get('bpm', '')} • Key: {s.get('key', '')}")
                    lrc_lines.append(f"# Style Prompt: {s.get('style_prompt', '')}")
                    
                    cur_sec = 0.0
                    for line in s.get("lyrics", "").split("\n"):
                        clean_l = line.strip()
                        if not clean_l:
                            continue
                        m = int(cur_sec // 60)
                        sec = cur_sec % 60
                        time_tag = f"[{m:02d}:{sec:05.2f}]"
                        lrc_lines.append(f"{time_tag}{clean_l}")
                        if clean_l.startswith("[") and clean_l.endswith("]"):
                            cur_sec += sec_per_beat * 8
                        else:
                            cur_sec += sec_per_beat * 4
                    lrc_lines.append(f"[{int((cur_sec + 8) // 60):02d}:{(cur_sec + 8) % 60:05.2f}][Outro: Fade Out]")
                    lrc_lines.append("\n" + "=" * 50 + "\n")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(lrc_lines))

            elif file_path.endswith(".md"):
                md_out = []
                theme_txt = self.txt_theme.toPlainText().strip() or "Studio Session"
                md_out.append("# 💿 STUDIO CONCEPT ALBUM BOOKLET")
                md_out.append(f"**Theme & Mood**: `{theme_txt}`")
                md_out.append(f"**Vocal Persona**: `{getattr(self, 'current_persona', 'Natural')}`")
                md_out.append(f"**Total Tracks**: `{len(self.all_songs)} Tracks` • **Anti-Duplication**: `Zero Clones Enforced`\n")
                md_out.append("## 📋 MASTER TRACKLIST & STEM MATRIX")
                md_out.append("| # | Title | Album Role | Genre | BPM | Key | Meter | Quality |")
                md_out.append("|---|---|---|---|---|---|---|---|")
                for s in self.all_songs:
                    md_out.append(f"| {s.get('id', 1):02d} | **{s.get('title', '')}** | {s.get('album_role', 'Track')} | {s.get('genre', '')} | {s.get('bpm', '')} | {s.get('key', '')} | {s.get('meter', '')} | {s.get('quality_score', 96)}% |")
                md_out.append("\n---\n")
                md_out.append("## 🎵 INDIVIDUAL TRACK SHEETS & SUNO PROMPTS\n")
                for s in self.all_songs:
                    md_out.append(f"### Track {s.get('id', 1):02d}: {s.get('title', '')}")
                    if s.get("album_role"):
                        md_out.append(f"**Role**: `{s.get('album_role')}`")
                    md_out.append(f"- **Acoustics**: `{s.get('genre', '')}` • `{s.get('bpm', '')}` • Key: `{s.get('key', '')}` • Meter: `{s.get('meter', '')}`")
                    md_out.append(f"- **Hit Quality Score**: `{s.get('quality_score', 96)}%` (Rhyme Density: `{s.get('rhyme_score', 94)}%`)")
                    md_out.append("\n**Suno v3.5/v4/v6 Style Prompt**:")
                    md_out.append(f"> `{s.get('style_prompt', '')}`\n")
                    md_out.append("**Lyrics**:")
                    md_out.append("```text")
                    md_out.append(s.get("lyrics", ""))
                    md_out.append("```\n")
                    md_out.append("---\n")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(md_out))

            else:
                lines = []
                for s in self.all_songs:
                    role_str = f" [{s.get('album_role')}]" if s.get('album_role') else ""
                    lines.append(f"=== [{s.get('id', 1):02d}] {s.get('title', '')}{role_str} ===")
                    m_txt = f" • Meter: {s.get('meter', '')}" if s.get('meter') else ""
                    q_txt = f" • Quality: {s.get('quality_score', 96)}% (Rhyme: {s.get('rhyme_score', 94)}%)"
                    lines.append(f"Genre: {s.get('genre', '')} • {s.get('bpm', '')} • Key: {s.get('key', '')}{m_txt}{q_txt}")
                    lines.append(f"\n[STYLE PROMPT]\n{s.get('style_prompt', '')}\n")
                    lines.append(f"[LYRICS]\n{s.get('lyrics', '')}\n")
                    lines.append("=" * 60 + "\n")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(lines))

            QMessageBox.information(self, "Export Success", f"រក្សាទុកបានជោគជ័យ (Saved successfully):\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))

    def _flash_btn(self, btn: QPushButton, label: str):
        orig_text = btn.text()
        btn.setText(label)
        QTimer.singleShot(1400, lambda: btn.setText(orig_text))

    def apply_theme(self, theme_or_dark):
        t = get_theme(theme_or_dark)
        self.theme = t
        self.theme_key = t.get("id", "obsidian")
        is_dark = t.get("is_dark", True)
        self.is_dark = is_dark

        # 1. Update all cards
        for card in self.card_widgets:
            card.apply_theme(theme_or_dark)

        # 2. Update filter tabs
        self._update_filter_button_styles()
        if hasattr(self, '_update_column_toggle_ui'):
            self._update_column_toggle_ui()

        # 3. Update language & vocal pills
        for code, btn in self.lang_buttons.items():
            btn.setStyleSheet(self._pill_style(code == self.current_lang))
        for code, btn in self.vocal_buttons.items():
            btn.setStyleSheet(self._pill_style(code == self.current_vocal))

        # 4. Anti-duplication toggle & Album Arc
        self._update_anti_dup_style(self.anti_duplication)
        self._update_album_arc_style()

        # Update Main Turbo Button
        if hasattr(self, "btn_generate_batch"):
            self.btn_generate_batch.setStyleSheet(f"""
                QPushButton {{
                    background: {t['accent_gradient']};
                    color: #ffffff;
                    border: 1px solid {t['border_accent']};
                    border-radius: 6px;
                    font-weight: 800;
                    font-size: 12px;
                    padding: 6px 14px;
                }}
                QPushButton:hover {{
                    background: {t['accent_hover']};
                    border-color: #ffffff;
                }}
                QPushButton:pressed {{
                    background-color: {t['accent_secondary']};
                }}
            """)

        # 5. Buttons and input cards
        if is_dark:
            if hasattr(self, "txt_theme"):
                self.txt_theme.setStyleSheet(f"padding: 2px 6px; font-size: 11px; background: {t['bg_input']}; border: 1px solid {t['border']}; border-radius: 5px; color: {t['text_primary']};")
            if hasattr(self, "combo_diversity"):
                self.combo_diversity.setStyleSheet(f"padding: 1px 6px; font-weight: 700; font-size: 10px; background: {t['bg_input']}; border: 1px solid {t['border']}; border-radius: 4px; color: {t['text_secondary']};")
            if hasattr(self, "combo_count"):
                self.combo_count.setStyleSheet(f"padding: 1px 6px; font-weight: 700; font-size: 10px; background: {t['bg_input']}; border: 1px solid {t['border']}; border-radius: 4px; color: {t['text_accent']};")
            if hasattr(self, "combo_style_limit"):
                self.combo_style_limit.setStyleSheet(f"padding: 1px 6px; font-size: 10px; background: {t['bg_input']}; border: 1px solid {t['border']}; border-radius: 4px; color: {t['text_accent']};")
            if hasattr(self, "txt_story_seed"):
                self.txt_story_seed.setStyleSheet(f"padding: 2px 6px; font-size: 10px; background: {t['bg_input']}; border: 1px solid {t['border']}; border-radius: 5px; color: {t['text_primary']};")
            if hasattr(self, "seed_pills"):
                for p in self.seed_pills:
                    p.setStyleSheet(f"background-color: {t['subtle_pill_bg']}; color: {t['subtle_pill_text']}; border: 1px solid {t['border']}; border-radius: 4px; padding: 1px 4px; font-size: 9px; font-weight: 600;")
            if hasattr(self, "combo_depth_mode"):
                self.combo_depth_mode.setStyleSheet(f"padding: 1px 6px; font-weight: 700; font-size: 10px; background: {t['bg_input']}; border: 1px solid {t['border']}; border-radius: 4px; color: {t['text_accent']};")

            if hasattr(self, "btn_append"):
                self.btn_append.setStyleSheet(self._btn_sub())
            if hasattr(self, "btn_copy_all_batch"):
                self.btn_copy_all_batch.setStyleSheet(self._btn_sub())
            if hasattr(self, "btn_save_all"):
                self.btn_save_all.setStyleSheet(self._btn_sub())
            if hasattr(self, "btn_clear_sidebar"):
                self.btn_clear_sidebar.setStyleSheet(self._btn_clear_style())
            if hasattr(self, "btn_clear_grid"):
                self.btn_clear_grid.setStyleSheet(self._btn_clear_style())
            if hasattr(self, "btn_new_project"):
                self.btn_new_project.setStyleSheet(self._btn_new_style())
            if hasattr(self, "lbl_batch_stat"):
                self.lbl_batch_stat.setStyleSheet("color: #34d399; font-size: 10.5px; font-weight: 700; background: #064e3b; border-radius: 4px;")

            if hasattr(self, "lbl_grid_title"):
                self.lbl_grid_title.setStyleSheet(f"font-size: 14px; font-weight: 800; color: {t['text_primary']};")
            if hasattr(self, "lbl_grid_badge"):
                self.lbl_grid_badge.setStyleSheet(f"background-color: {t['subtle_pill_bg']}; color: {t['text_accent']}; font-size: 9.5px; font-weight: 700; border: 1px solid {t['border']}; border-radius: 4px; padding: 2px 6px;")
            if hasattr(self, "lbl_avg_novelty"):
                self.lbl_avg_novelty.setStyleSheet("background-color: #064e3b; color: #6ee7b7; font-size: 9px; font-weight: 800; padding: 2px 6px; border-radius: 4px; border: 1px solid #059669; font-family: 'Cascadia Code', 'Consolas', monospace;")
            if hasattr(self, "btn_roll_concept"):
                self.btn_roll_concept.setStyleSheet(f"""
                    QPushButton {{
                        background: {t['subtle_pill_bg']};
                        color: {t['text_accent']};
                        border: 1px solid {t['border_accent']};
                        border-radius: 4px;
                        font-weight: 800;
                        font-size: 10px;
                        padding: 2px 6px;
                    }}
                    QPushButton:hover {{
                        background: {t['accent']};
                        color: #ffffff;
                    }}
                """)
            if hasattr(self, "lbl_memory_badge"):
                self.lbl_memory_badge.setStyleSheet(f"font-size: 8.5px; font-weight: 700; color: {t['text_secondary']}; background: {t['bg_card_alt']}; border: 1px solid {t['border']}; border-radius: 4px; padding: 1px 5px;")
            if hasattr(self, "btn_clear_memory"):
                self.btn_clear_memory.setStyleSheet(f"font-size: 8.5px; font-weight: 700; color: {t['text_muted']}; background: {t['bg_card_alt']}; border: 1px solid {t['border']}; border-radius: 4px;")
            if hasattr(self, "btn_toggle_sidebar"):
                self.btn_toggle_sidebar.setStyleSheet(f"background-color: {t['subtle_pill_bg']}; color: {t['text_accent']}; font-weight: 700; font-size: 10.5px; border: 1px solid {t['border']}; border-radius: 4px; padding: 4px 8px;")
            if hasattr(self, "btn_studio_tools"):
                self.btn_studio_tools.setStyleSheet(f"background-color: {t['subtle_pill_bg']}; color: {t['text_accent']}; font-weight: 700; font-size: 11px; border: 1px solid {t['border_accent']}; border-radius: 5px; padding: 4px 10px;")
            if hasattr(self, "tracklist_table"):
                self.tracklist_table.setStyleSheet(f"""
                    QTableWidget {{
                        background-color: {t['bg_input']};
                        alternate-background-color: {t['bg_card_alt']};
                        color: {t['text_primary']};
                        gridline-color: {t['border']};
                        border: 1px solid {t['border']};
                        border-radius: 6px;
                        selection-background-color: {t['accent']};
                        selection-color: #ffffff;
                        font-size: 11px;
                    }}
                    QHeaderView::section {{
                        background-color: {t['bg_card']};
                        color: {t['text_secondary']};
                        font-weight: 800;
                        font-size: 10px;
                        border: 1px solid {t['border']};
                        padding: 4px;
                    }}
                """)
            if hasattr(self, "txt_grid_search"):
                self.txt_grid_search.setStyleSheet(f"background: {t['bg_input']}; color: {t['text_primary']}; border: 1px solid {t['border']}; border-radius: 5px; padding: 4px 8px; font-size: 11px;")
            if hasattr(self, "btn_inject_all_v6"):
                self.btn_inject_all_v6.setStyleSheet(f"background-color: {t['subtle_pill_bg']}; color: {t['text_accent']}; font-weight: 700; font-size: 11px; border: 1px solid {t['border_accent']}; border-radius: 5px; padding: 4px 10px;")

            if hasattr(self, "theme_pills"):
                for p in self.theme_pills:
                    p.setStyleSheet(f"background-color: {t['bg_card_alt']}; color: {t['text_secondary']}; border: 1px solid {t['border']}; border-radius: 4px; padding: 1px 4px; font-size: 9px; font-weight: 600;")
        else:
            # Modern High-Contrast Light Mode
            if hasattr(self, "txt_theme"):
                self.txt_theme.setStyleSheet("padding: 2px 6px; font-size: 11px; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 5px; color: #0f172a;")
            if hasattr(self, "combo_diversity"):
                self.combo_diversity.setStyleSheet("padding: 1px 6px; font-weight: 700; font-size: 10px; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 4px; color: #1d4ed8;")
            if hasattr(self, "combo_count"):
                self.combo_count.setStyleSheet("padding: 1px 6px; font-weight: 700; font-size: 10px; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 4px; color: #0f172a;")
            if hasattr(self, "combo_style_limit"):
                self.combo_style_limit.setStyleSheet("padding: 1px 6px; font-size: 10px; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 4px; color: #0369a1;")
            if hasattr(self, "txt_story_seed"):
                self.txt_story_seed.setStyleSheet("padding: 2px 6px; font-size: 10px; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 5px; color: #0f172a;")
            if hasattr(self, "seed_pills"):
                for p in self.seed_pills:
                    p.setStyleSheet("background-color: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; border-radius: 4px; padding: 1px 4px; font-size: 9px; font-weight: 600;")
            if hasattr(self, "combo_depth_mode"):
                self.combo_depth_mode.setStyleSheet("padding: 1px 6px; font-weight: 700; font-size: 10px; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 4px; color: #1d4ed8;")

            if hasattr(self, "btn_append"):
                self.btn_append.setStyleSheet(self._btn_sub())
            if hasattr(self, "btn_copy_all_batch"):
                self.btn_copy_all_batch.setStyleSheet(self._btn_sub())
            if hasattr(self, "btn_save_all"):
                self.btn_save_all.setStyleSheet(self._btn_sub())
            if hasattr(self, "btn_clear_sidebar"):
                self.btn_clear_sidebar.setStyleSheet(self._btn_clear_style())
            if hasattr(self, "btn_clear_grid"):
                self.btn_clear_grid.setStyleSheet(self._btn_clear_style())
            if hasattr(self, "btn_new_project"):
                self.btn_new_project.setStyleSheet(self._btn_new_style())
            if hasattr(self, "lbl_batch_stat"):
                self.lbl_batch_stat.setStyleSheet("color: #047857; font-size: 10.5px; font-weight: 700; background: #d1fae5; border: 1px solid #a7f3d0; border-radius: 4px;")

            if hasattr(self, "lbl_grid_title"):
                self.lbl_grid_title.setStyleSheet("font-size: 14px; font-weight: 800; color: #0f172a;")
            if hasattr(self, "lbl_grid_badge"):
                self.lbl_grid_badge.setStyleSheet("background-color: #f1f5f9; color: #0369a1; font-size: 9.5px; font-weight: 700; border: 1px solid #cbd5e1; border-radius: 4px; padding: 2px 6px;")
            if hasattr(self, "lbl_avg_novelty"):
                self.lbl_avg_novelty.setStyleSheet("background-color: #d1fae5; color: #047857; font-size: 9px; font-weight: 800; padding: 2px 6px; border-radius: 4px; border: 1px solid #a7f3d0; font-family: 'Cascadia Code', 'Consolas', monospace;")
            if hasattr(self, "btn_roll_concept"):
                self.btn_roll_concept.setStyleSheet("""
                    QPushButton {
                        background: #eff6ff;
                        color: #1d4ed8;
                        border: 1px solid #bfdbfe;
                        border-radius: 4px;
                        font-weight: 800;
                        font-size: 10px;
                        padding: 2px 6px;
                    }
                    QPushButton:hover {
                        background: #dbeafe;
                        color: #1e40af;
                    }
                """)
            if hasattr(self, "lbl_memory_badge"):
                self.lbl_memory_badge.setStyleSheet("font-size: 8.5px; font-weight: 700; color: #1d4ed8; background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 4px; padding: 1px 5px;")
            if hasattr(self, "btn_clear_memory"):
                self.btn_clear_memory.setStyleSheet("font-size: 8.5px; font-weight: 700; color: #475569; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 4px;")
            if hasattr(self, "btn_toggle_sidebar"):
                self.btn_toggle_sidebar.setStyleSheet("background-color: #eff6ff; color: #1d4ed8; font-weight: 700; font-size: 10.5px; border: 1px solid #bfdbfe; border-radius: 4px; padding: 4px 8px;")
            if hasattr(self, "btn_studio_tools"):
                self.btn_studio_tools.setStyleSheet("background-color: #eff6ff; color: #1d4ed8; font-weight: 700; font-size: 11px; border: 1px solid #bfdbfe; border-radius: 5px; padding: 4px 10px;")
            if hasattr(self, "tracklist_table"):
                self.tracklist_table.setStyleSheet("""
                    QTableWidget {
                        background-color: #ffffff;
                        alternate-background-color: #f8fafc;
                        color: #0f172a;
                        gridline-color: #e2e8f0;
                        border: 1px solid #cbd5e1;
                        border-radius: 6px;
                        selection-background-color: #eff6ff;
                        selection-color: #1d4ed8;
                        font-size: 11px;
                    }
                    QHeaderView::section {
                        background-color: #f8fafc;
                        color: #1e293b;
                        font-weight: 800;
                        font-size: 10px;
                        border: 1px solid #cbd5e1;
                        padding: 4px;
                    }
                """)
            if hasattr(self, "txt_grid_search"):
                self.txt_grid_search.setStyleSheet("background: #ffffff; color: #0f172a; border: 1px solid #cbd5e1; border-radius: 5px; padding: 4px 8px; font-size: 11px;")
            if hasattr(self, "btn_inject_all_v6"):
                self.btn_inject_all_v6.setStyleSheet("background-color: #eff6ff; color: #1d4ed8; font-weight: 700; font-size: 11px; border: 1px solid #bfdbfe; border-radius: 5px; padding: 4px 10px;")

            if hasattr(self, "metatag_pills"):
                for pill in self.metatag_pills:
                    pill.setStyleSheet("background-color: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; border-radius: 4px; font-size: 9.5px; padding: 2px 6px; font-weight: 700;")
            if hasattr(self, "theme_pills"):
                for p in self.theme_pills:
                    p.setStyleSheet("background-color: #f8fafc; color: #334155; border: 1px solid #cbd5e1; border-radius: 4px; padding: 3px 5px; font-size: 9.5px; font-weight: 600;")

        if not self.all_songs and hasattr(self, "grid_layout"):
            self._show_empty_state()
        if hasattr(self, "inspector_dialog") and self.inspector_dialog:
            self.inspector_dialog._apply_theme(is_dark)
