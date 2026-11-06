# -*- coding: utf-8 -*-
"""
Studio Song Inspector Dialog (Popup Modal / Floating Workbench for Batch Pro).
Provides a dedicated, distraction-free popup window when inspecting or editing any track
from the Batch Pro grid, freeing up 100% of the screen height for the multi-song cards.
"""

import re
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFrame, QApplication, QWidget, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor
from app.gemini_client import DeepenLyricWorker
from app.ui.styles import get_theme


class StudioSongInspectorDialog(QDialog):
    """
    World-class DAW-style Track Inspector Dialog for Batch Pro.
    Features:
    - Side-by-side Suno Style Prompt Box & Full Monospace Lyrics Workbench
    - Live compact character counter (no stretched boxes)
    - 1-Click Suno Metatag Inserts & Quick Style Descriptors
    - Crossover Hook Swapper, Suno v6 Audio Cue Injector, Deepen Meaning
    - Previous / Next Track navigation across the batch
    - Pixel-perfect Dark & Light Theme styling
    """
    song_updated = pyqtSignal(dict)
    open_editor_requested = pyqtSignal(dict)
    open_visual_requested = pyqtSignal(dict)
    crossover_requested = pyqtSignal(dict)

    def __init__(self, song_data: dict, all_songs: list = None, is_dark: bool = True, parent=None):
        super().__init__(parent)
        self.song_data = dict(song_data)
        self.all_songs = all_songs or [self.song_data]
        self.current_index = self._find_song_index(self.song_data.get("id"))
        self.is_dark = is_dark
        self.style_limit = 200

        self.setWindowTitle(f"🎵 Studio Track Inspector — {self.song_data.get('title', 'Track')}")
        self.resize(920, 600)
        self.setMinimumSize(820, 520)

        self._init_ui()
        self._apply_theme(self.is_dark)
        self._load_song_data(self.song_data)

    def _find_song_index(self, song_id) -> int:
        for idx, s in enumerate(self.all_songs):
            if s.get("id") == song_id:
                return idx
        return 0

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 12, 14, 12)
        main_layout.setSpacing(10)

        # ══════════════════════════════════════════════════════════════════
        # ── ROW 1: HEADER (Index + Flag + Title + Roles + Quality + Close) ──
        # ══════════════════════════════════════════════════════════════════
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        h_layout = QHBoxLayout(header_frame)
        h_layout.setContentsMargins(10, 8, 10, 8)
        h_layout.setSpacing(8)

        # Index Badge
        self.lbl_idx = QLabel("01")
        self.lbl_idx.setStyleSheet("""
            font-family: 'Cascadia Code', 'Consolas', monospace;
            font-size: 11px;
            font-weight: 800;
            background-color: #1a2238;
            color: #93c5fd;
            border: 1px solid #3b82f6;
            border-radius: 4px;
            padding: 2px 6px;
        """)
        h_layout.addWidget(self.lbl_idx)

        # Language Badge
        self.lbl_lang = QLabel("🇰🇭")
        self.lbl_lang.setStyleSheet("font-size: 14px;")
        h_layout.addWidget(self.lbl_lang)

        # Title & Metadata Stack
        meta_stack = QVBoxLayout()
        meta_stack.setSpacing(2)

        self.lbl_title = QLabel("Song Title")
        self.lbl_title.setStyleSheet("font-size: 14px; font-weight: 800; color: #ffffff;")
        meta_stack.addWidget(self.lbl_title)

        meta_sub_row = QHBoxLayout()
        meta_sub_row.setSpacing(6)

        self.lbl_meta = QLabel("Genre • BPM • Key • Meter")
        self.lbl_meta.setStyleSheet("font-size: 10px; font-weight: 700; color: #38bdf8;")
        meta_sub_row.addWidget(self.lbl_meta)

        self.lbl_quality = QLabel("🎯 96% Match • Rhyme: 95%")
        self.lbl_quality.setStyleSheet("""
            background-color: #064e3b;
            color: #6ee7b7;
            border: 1px solid #059669;
            border-radius: 3px;
            padding: 1px 5px;
            font-size: 9px;
            font-weight: 800;
            font-family: 'Cascadia Code', monospace;
        """)
        meta_sub_row.addWidget(self.lbl_quality)

        self.lbl_role = QLabel("💿 Lead Single")
        self.lbl_role.setStyleSheet("""
            background-color: #311042;
            color: #f0abfc;
            border: 1px solid #a855f7;
            border-radius: 3px;
            padding: 1px 5px;
            font-size: 9px;
            font-weight: 700;
        """)
        meta_sub_row.addWidget(self.lbl_role)

        self.lbl_human_badge = QLabel("👤 96% Human")
        self.lbl_human_badge.setToolTip("Human Authenticity, Vocal Breath & Sensory Realism Rating")
        self.lbl_human_badge.setStyleSheet("""
            background-color: #064e3b;
            color: #6ee7b7;
            border: 1px solid #059669;
            border-radius: 3px;
            padding: 1px 6px;
            font-size: 9px;
            font-weight: 800;
            font-family: 'Cascadia Code', monospace;
        """)
        meta_sub_row.addWidget(self.lbl_human_badge)
        meta_sub_row.addStretch()

        meta_stack.addLayout(meta_sub_row)
        h_layout.addLayout(meta_stack, stretch=1)

        # Copy Suno Bundle Primary Action
        self.btn_copy_bundle = QPushButton("⚡ Copy Suno Bundle")
        self.btn_copy_bundle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_copy_bundle.setToolTip("Copy Title + Style Prompt + Lyrics to Clipboard in one click")
        self.btn_copy_bundle.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4f46e5, stop:1 #7c3aed);
                color: #ffffff;
                font-weight: 800;
                font-size: 11px;
                border: 1px solid #818cf8;
                border-radius: 6px;
                padding: 6px 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366f1, stop:1 #8b5cf6);
            }
        """)
        self.btn_copy_bundle.clicked.connect(self._copy_bundle)
        h_layout.addWidget(self.btn_copy_bundle)

        # Close X Button
        self.btn_close_x = QPushButton("✕")
        self.btn_close_x.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close_x.setFixedSize(26, 26)
        self.btn_close_x.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #94a3b8;
                font-size: 14px;
                font-weight: 800;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #ef4444;
                color: #ffffff;
            }
        """)
        self.btn_close_x.clicked.connect(self.accept)
        h_layout.addWidget(self.btn_close_x)

        main_layout.addWidget(header_frame)

        # ══════════════════════════════════════════════════════════════════
        # ── ROW 2: STUDIO ACTION BAR (Pills for quick tools) ──
        # ══════════════════════════════════════════════════════════════════
        action_bar = QHBoxLayout()
        action_bar.setSpacing(6)

        self.btn_copy_title = QPushButton("📋 Title")
        self.btn_copy_title.setToolTip("Copy Song Title")
        self.btn_copy_title.clicked.connect(self._copy_title)
        action_bar.addWidget(self.btn_copy_title)

        self.btn_copy_style = QPushButton("📋 Style")
        self.btn_copy_style.setToolTip("Copy Style Prompt")
        self.btn_copy_style.clicked.connect(self._copy_style)
        action_bar.addWidget(self.btn_copy_style)

        self.btn_copy_lyrics = QPushButton("📋 Lyrics")
        self.btn_copy_lyrics.setToolTip("Copy Lyrics")
        self.btn_copy_lyrics.clicked.connect(self._copy_lyrics)
        action_bar.addWidget(self.btn_copy_lyrics)

        # Inject Suno v6 Cues
        self.btn_inject_v6 = QPushButton("⚡ v6 Cues")
        self.btn_inject_v6.setToolTip("Inject Suno v6 cues ([Tempo], [Key], [Instrumental Solo], [Drop], [Fade Out]) into lyrics")
        self.btn_inject_v6.setStyleSheet("""
            QPushButton {
                background-color: #312e81;
                color: #c084fc;
                font-weight: 700;
                border: 1px solid #6366f1;
                border-radius: 5px;
                padding: 4px 10px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #4338ca;
                color: #ffffff;
            }
        """)
        self.btn_inject_v6.clicked.connect(self._inject_v6)
        action_bar.addWidget(self.btn_inject_v6)

        # Crossover Hook Swapper
        self.btn_crossover = QPushButton("🌐 Crossover Hook")
        self.btn_crossover.setToolTip("Transform Chorus into Bilingual Crossover Hook (Khmer ➔ English / English ➔ Khmer)")
        self.btn_crossover.setStyleSheet("""
            QPushButton {
                background-color: #064e3b;
                color: #6ee7b7;
                font-weight: 700;
                border: 1px solid #10b981;
                border-radius: 5px;
                padding: 4px 10px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #059669;
                color: #ffffff;
            }
        """)
        self.btn_crossover.clicked.connect(self._swap_crossover)
        action_bar.addWidget(self.btn_crossover)

        # Deepen Meaning
        self.btn_deepen = QPushButton("💎 Deepen")
        self.btn_deepen.setToolTip("Deepen Meaning with Berklee sensory imagery & revelation")
        self.btn_deepen.setStyleSheet("""
            QPushButton {
                background-color: #3b0764;
                color: #e9d5ff;
                font-weight: 700;
                border: 1px solid #7c3aed;
                border-radius: 5px;
                padding: 4px 10px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #581c87;
                color: #ffffff;
            }
        """)
        self.btn_deepen.clicked.connect(self._deepen_meaning)
        action_bar.addWidget(self.btn_deepen)

        # 3 Style Takes Mutation Menu
        self.btn_mutate = QPushButton("🎨 3 Takes")
        self.btn_mutate.setToolTip("Explore 3 alternate production style variations")
        self.btn_mutate.setStyleSheet("""
            QPushButton {
                background-color: #0c4a6e;
                color: #7dd3fc;
                font-weight: 700;
                border: 1px solid #0284c7;
                border-radius: 5px;
                padding: 4px 10px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #0369a1;
                color: #ffffff;
            }
        """)
        self.btn_mutate.clicked.connect(self._open_style_mutator)
        action_bar.addWidget(self.btn_mutate)

        # 👤 Humanize & Approve (Making Music Like Human Masterpiece)
        self.btn_humanize_approve = QPushButton("👤 Humanize & Approve")
        self.btn_humanize_approve.setToolTip("Elevate into 100% Human Masterpiece: inject realistic breath pauses, sensory realism, vulnerable bridge, and live pocket groove")
        self.btn_humanize_approve.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #0284c7);
                color: #ffffff;
                font-weight: 800;
                border: 1px solid #10b981;
                border-radius: 5px;
                padding: 4px 12px;
                font-size: 10px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 #38bdf8);
            }
        """)
        self.btn_humanize_approve.clicked.connect(self._humanize_and_approve)
        action_bar.addWidget(self.btn_humanize_approve)

        action_bar.addStretch()

        # Open in Main Workbench Editor
        self.btn_open_editor = QPushButton("📝 Workbench")
        self.btn_open_editor.setToolTip("Send this song into the main Lyric Editor workbench")
        self.btn_open_editor.setStyleSheet("""
            QPushButton {
                background-color: #0284c7;
                color: #ffffff;
                font-weight: 800;
                border: 1px solid #38bdf8;
                border-radius: 5px;
                padding: 4px 11px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #0369a1;
            }
        """)
        self.btn_open_editor.clicked.connect(self._open_in_editor)
        action_bar.addWidget(self.btn_open_editor)

        # Open in Visual Arranger
        self.btn_open_visual = QPushButton("🎨 Arranger")
        self.btn_open_visual.setToolTip("Open in Visual Arranger (DAW Timeline & Chords)")
        self.btn_open_visual.setStyleSheet("""
            QPushButton {
                background-color: #5b21b6;
                color: #ffffff;
                font-weight: 800;
                border: 1px solid #a78bfa;
                border-radius: 5px;
                padding: 4px 11px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #4c1d95;
            }
        """)
        self.btn_open_visual.clicked.connect(self._open_in_visual)
        action_bar.addWidget(self.btn_open_visual)

        main_layout.addLayout(action_bar)

        # ══════════════════════════════════════════════════════════════════
        # ── ROW 3: SPLIT CONTENT (STYLE BOX LEFT • LYRICS WORKBENCH RIGHT) ──
        # ══════════════════════════════════════════════════════════════════
        body_split = QHBoxLayout()
        body_split.setSpacing(10)

        # ── LEFT: Style Prompt Workbench ──
        style_box_frame = QFrame()
        style_box_frame.setObjectName("styleBoxFrame")
        style_layout = QVBoxLayout(style_box_frame)
        style_layout.setContentsMargins(10, 8, 10, 8)
        style_layout.setSpacing(6)

        style_head = QHBoxLayout()
        self.lbl_style_head = QLabel("STYLE PROMPT (សម្រាប់ SUNO STYLE BOX):")
        self.lbl_style_head.setStyleSheet("font-size: 10.5px; font-weight: 800; color: #38bdf8;")
        style_head.addWidget(self.lbl_style_head)
        style_head.addStretch()

        # Compact Inline Character Counter Badge (NO giant stretched box!)
        self.lbl_style_chars = QLabel("0 / 200 chars")
        self.lbl_style_chars.setFixedHeight(20)
        self.lbl_style_chars.setStyleSheet("""
            color: #38bdf8;
            font-size: 9.5px;
            font-weight: 800;
            background: #0c2d48;
            padding: 1px 6px;
            border-radius: 4px;
            border: 1px solid #0284c7;
            font-family: 'Cascadia Code', monospace;
        """)
        style_head.addWidget(self.lbl_style_chars)
        style_layout.addLayout(style_head)

        self.txt_style = QTextEdit()
        self.txt_style.setPlaceholderText("Enter comma-separated Suno v3.5/v4/v6 descriptors...")
        self.txt_style.setStyleSheet("""
            background: #0b0f1f;
            border: 1px solid #1c2642;
            border-radius: 6px;
            font-size: 11px;
            line-height: 1.35;
            color: #38bdf8;
            padding: 6px;
        """)
        self.txt_style.textChanged.connect(self._on_style_edited)
        style_layout.addWidget(self.txt_style, stretch=1)

        # Quick Descriptor Injection Pills
        desc_lbl = QLabel("QUICK DESCRIPTORS:")
        desc_lbl.setStyleSheet("font-size: 8.5px; font-weight: 800; color: #64748b; letter-spacing: 0.5px;")
        style_layout.addWidget(desc_lbl)

        quick_desc_row = QHBoxLayout()
        quick_desc_row.setSpacing(4)
        for tag in ["+ Live Pocket", "+ Tape Saturation", "+ Room Bleed", "+ Vocal Breath", "+ Rhodes Mark I", "+ Upright Bass"]:
            b = QPushButton(tag)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setFixedHeight(22)
            b.setStyleSheet("""
                QPushButton {
                    background-color: #141a2e;
                    color: #7dd3fc;
                    border: 1px solid #233052;
                    border-radius: 4px;
                    padding: 1px 4px;
                    font-size: 9px;
                    font-weight: 700;
                }
                QPushButton:hover {
                    background-color: #0284c7;
                    color: #ffffff;
                }
            """)
            b.clicked.connect(lambda _, t=tag[2:]: self._append_style_tag(t))
            quick_desc_row.addWidget(b)
        style_layout.addLayout(quick_desc_row)

        body_split.addWidget(style_box_frame, stretch=1)

        # ── RIGHT: Lyrics & Structure Workbench ──
        lyrics_frame = QFrame()
        lyrics_frame.setObjectName("lyricsFrame")
        lyrics_layout = QVBoxLayout(lyrics_frame)
        lyrics_layout.setContentsMargins(10, 8, 10, 8)
        lyrics_layout.setSpacing(6)

        lyrics_head = QHBoxLayout()
        self.lbl_lyrics_head = QLabel("LYRICS & SECTION METATAGS:")
        self.lbl_lyrics_head.setStyleSheet("font-size: 10.5px; font-weight: 800; color: #c084fc;")
        lyrics_head.addWidget(self.lbl_lyrics_head)
        lyrics_head.addStretch()

        # Metatag Insert Pills Row
        for tag in ["[Verse]", "[Chorus]", "[Breath]", "[Soft Sigh]", "[Voice Break]", "[Bridge Epiphany]", "[Outro]"]:
            pill = QPushButton(tag)
            pill.setCursor(Qt.CursorShape.PointingHandCursor)
            pill.setFixedHeight(21)
            pill.setStyleSheet("""
                QPushButton {
                    background-color: #1e1b4b;
                    color: #c084fc;
                    border: 1px solid #4338ca;
                    border-radius: 4px;
                    font-size: 9px;
                    padding: 1px 5px;
                    font-weight: 700;
                }
                QPushButton:hover {
                    background-color: #312e81;
                    color: #ffffff;
                    border-color: #818cf8;
                }
            """)
            pill.clicked.connect(lambda _, t=tag: self._insert_metatag(t))
            lyrics_head.addWidget(pill)

        lyrics_layout.addLayout(lyrics_head)

        self.txt_lyrics = QTextEdit()
        self.txt_lyrics.setStyleSheet("""
            background: #070913;
            border: 1px solid #181f33;
            border-radius: 6px;
            font-size: 11.5px;
            font-family: 'Cascadia Code', 'Consolas', monospace;
            color: #f8fafc;
            line-height: 1.4;
            padding: 8px;
        """)
        self.txt_lyrics.textChanged.connect(self._on_lyrics_edited)
        lyrics_layout.addWidget(self.txt_lyrics, stretch=1)

        body_split.addWidget(lyrics_frame, stretch=2)
        main_layout.addLayout(body_split, stretch=1)

        # ══════════════════════════════════════════════════════════════════
        # ── ROW 4: FOOTER (Prev/Next Track Navigation + Close Button) ──
        # ══════════════════════════════════════════════════════════════════
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(4, 2, 4, 2)
        footer_layout.setSpacing(8)

        self.btn_prev = QPushButton("◀ Previous Track")
        self.btn_prev.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_prev.setFixedHeight(28)
        self.btn_prev.setStyleSheet("""
            QPushButton {
                background-color: #161c32;
                color: #cbd5e1;
                border: 1px solid #283354;
                font-size: 10px;
                font-weight: 700;
                padding: 4px 12px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #232c4d;
                color: #ffffff;
            }
        """)
        self.btn_prev.clicked.connect(self._prev_track)
        footer_layout.addWidget(self.btn_prev)

        self.lbl_nav_status = QLabel("Track 1 of 20")
        self.lbl_nav_status.setStyleSheet("font-size: 11px; font-weight: 700; color: #94a3b8;")
        footer_layout.addWidget(self.lbl_nav_status)

        self.btn_next = QPushButton("Next Track ▶")
        self.btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_next.setFixedHeight(28)
        self.btn_next.setStyleSheet("""
            QPushButton {
                background-color: #161c32;
                color: #cbd5e1;
                border: 1px solid #283354;
                font-size: 10px;
                font-weight: 700;
                padding: 4px 12px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #232c4d;
                color: #ffffff;
            }
        """)
        self.btn_next.clicked.connect(self._next_track)
        footer_layout.addWidget(self.btn_next)

        footer_layout.addStretch()

        self.btn_done = QPushButton("✓ Done / Close")
        self.btn_done.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_done.setFixedHeight(28)
        self.btn_done.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: #ffffff;
                font-weight: 800;
                font-size: 11px;
                border: 1px solid #059669;
                border-radius: 5px;
                padding: 4px 16px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        self.btn_done.clicked.connect(self.accept)
        footer_layout.addWidget(self.btn_done)

        main_layout.addLayout(footer_layout)

    def _load_song_data(self, song: dict):
        self.song_data = song
        self.current_index = self._find_song_index(song.get("id"))

        # Update window title
        t_str = song.get("title", "Untitled Track")
        self.setWindowTitle(f"🎵 Studio Track Inspector — {t_str}")

        # Update Header
        raw_idx = song.get("id", 1)
        try:
            numeric_idx = int(str(raw_idx).replace("TRK-", "").replace("Track-", "").strip())
            idx_str = f"{numeric_idx:02d}"
        except Exception:
            idx_str = str(raw_idx)[:4]
        self.lbl_idx.setText(idx_str)

        # Language flag
        lang = song.get("language", "")
        lyrics = song.get("lyrics", "")
        is_bi = "Bilingual" in lang or (any('\u1780' <= c <= '\u17ff' for c in lyrics) and any('a' <= c.lower() <= 'z' for c in lyrics))
        is_kh = "Khmer" in lang or any('\u1780' <= c <= '\u17ff' for c in t_str + lyrics)
        if is_bi:
            self.lbl_lang.setText("🇰🇭🇬🇧")
        elif is_kh:
            self.lbl_lang.setText("🇰🇭")
        else:
            self.lbl_lang.setText("🇬🇧")

        self.lbl_title.setText(t_str)

        genre = song.get("genre", "Custom Genre")
        bpm = song.get("bpm", "120 BPM")
        key = song.get("key", "C")
        meter = song.get("meter", "")
        meter_str = f"  •  {meter}" if meter else ""
        self.lbl_meta.setText(f"{genre}  •  {bpm}  •  Key: {key}{meter_str}")

        q_hit = song.get("quality_score", 96)
        q_rhyme = song.get("rhyme_score", 94)
        self.lbl_quality.setText(f"🎯 {q_hit}% Match • Rhyme: {q_rhyme}%")

        role = song.get("album_role", "")
        if role:
            role_short = role.replace("💿 Track ", "T").replace("Track ", "T")
            if ":" in role_short:
                role_short = "💿 " + role_short.split(":", 1)[1].strip()
            self.lbl_role.setText(role_short[:18])
            self.lbl_role.setVisible(True)
        else:
            self.lbl_role.setVisible(False)

        if hasattr(self, "lbl_human_badge"):
            h_score = song.get("human_score", 95)
            if song.get("human_certified"):
                self.lbl_human_badge.setText("👤 100% Human Certified")
                self.lbl_human_badge.setStyleSheet("background-color: #064e3b; color: #34d399; border: 1px solid #10b981; border-radius: 3px; padding: 1px 6px; font-size: 9px; font-weight: 800; font-family: 'Cascadia Code', monospace;")
            else:
                self.lbl_human_badge.setText(f"👤 {h_score}% Human")
                self.lbl_human_badge.setStyleSheet("background-color: #064e3b; color: #6ee7b7; border: 1px solid #059669; border-radius: 3px; padding: 1px 6px; font-size: 9px; font-weight: 800; font-family: 'Cascadia Code', monospace;")

        # Update Content
        self.txt_style.blockSignals(True)
        self.txt_lyrics.blockSignals(True)
        self.txt_style.setPlainText(song.get("style_prompt", ""))
        self.txt_lyrics.setPlainText(song.get("lyrics", ""))
        self.txt_style.blockSignals(False)
        self.txt_lyrics.blockSignals(False)

        self._update_char_counter()

        # Update Navigation Footer
        total = len(self.all_songs)
        self.lbl_nav_status.setText(f"Track {self.current_index + 1} of {total}")
        self.btn_prev.setEnabled(self.current_index > 0)
        self.btn_next.setEnabled(self.current_index < total - 1)

    def _update_char_counter(self):
        txt = self.txt_style.toPlainText().strip()
        count = len(txt)
        self.lbl_style_chars.setText(f"{count} / {self.style_limit} chars")
        if count > self.style_limit:
            self.lbl_style_chars.setStyleSheet("color: #ef4444; font-size: 9.5px; font-weight: 800; background: #450a0a; padding: 1px 6px; border-radius: 4px; border: 1px solid #b91c1c; font-family: 'Cascadia Code', monospace;")
        elif count > self.style_limit - 20:
            self.lbl_style_chars.setStyleSheet("color: #f59e0b; font-size: 9.5px; font-weight: 800; background: #451a03; padding: 1px 6px; border-radius: 4px; border: 1px solid #d97706; font-family: 'Cascadia Code', monospace;")
        else:
            self.lbl_style_chars.setStyleSheet("color: #38bdf8; font-size: 9.5px; font-weight: 800; background: #0c2d48; padding: 1px 6px; border-radius: 4px; border: 1px solid #0284c7; font-family: 'Cascadia Code', monospace;")

    def _on_style_edited(self):
        txt = self.txt_style.toPlainText()
        self.song_data["style_prompt"] = txt
        self._update_char_counter()
        self.song_updated.emit(self.song_data)

    def _on_lyrics_edited(self):
        txt = self.txt_lyrics.toPlainText()
        self.song_data["lyrics"] = txt
        self.song_updated.emit(self.song_data)

    def _append_style_tag(self, tag: str):
        curr = self.txt_style.toPlainText().strip()
        if curr and not curr.endswith(","):
            curr += ","
        new_style = f"{curr} {tag}".strip()
        self.txt_style.setPlainText(new_style[:self.style_limit])

    def _insert_metatag(self, tag: str):
        cursor = self.txt_lyrics.textCursor()
        cursor.insertText(f"\n{tag}\n")
        self.txt_lyrics.setTextCursor(cursor)
        self.txt_lyrics.setFocus()

    def _copy_bundle(self):
        bundle = f"""Title: {self.song_data.get('title', '')}
Genre: {self.song_data.get('genre', '')} ({self.song_data.get('bpm', '')}, Key: {self.song_data.get('key', '')})

[STYLE OF MUSIC]
{self.txt_style.toPlainText().strip()}

[LYRICS]
{self.txt_lyrics.toPlainText().strip()}
"""
        QApplication.clipboard().setText(bundle.strip())
        self._flash_btn(self.btn_copy_bundle, "✓ Copied All!")

    def _copy_title(self):
        QApplication.clipboard().setText(self.song_data.get("title", ""))
        self._flash_btn(self.btn_copy_title, "Copied!")

    def _copy_style(self):
        QApplication.clipboard().setText(self.txt_style.toPlainText().strip())
        self._flash_btn(self.btn_copy_style, "Copied!")

    def _copy_lyrics(self):
        QApplication.clipboard().setText(self.txt_lyrics.toPlainText().strip())
        self._flash_btn(self.btn_copy_lyrics, "Copied!")

    def _inject_v6(self):
        from app.ui.batch_generator_view import inject_suno_v6_cues
        bpm = self.song_data.get("bpm", "120 BPM")
        key = self.song_data.get("key", "C")
        genre = self.song_data.get("genre", "Pop")
        lyrics = self.txt_lyrics.toPlainText()
        enriched = inject_suno_v6_cues(lyrics, bpm, key, genre)
        self.txt_lyrics.setPlainText(enriched)
        self._flash_btn(self.btn_inject_v6, "✓ Injected!")

    def _swap_crossover(self):
        self.crossover_requested.emit(self.song_data)
        # Reload updated song data
        self._load_song_data(self.song_data)
        self._flash_btn(self.btn_crossover, "✓ Swapped!")

    def _deepen_meaning(self):
        self.btn_deepen.setEnabled(False)
        self.btn_deepen.setText("💎 Deepening...")

        title = self.song_data.get("title", "")
        genre = self.song_data.get("genre", "")
        lyrics = self.txt_lyrics.toPlainText()

        self.deepen_worker = DeepenLyricWorker(lyrics, title, genre)
        self.deepen_worker.result_ready.connect(self._on_deepen_finished)
        self.deepen_worker.error.connect(self._on_deepen_error)
        self.deepen_worker.start()

    def _on_deepen_finished(self, new_lyrics: str):
        self.btn_deepen.setEnabled(True)
        self.btn_deepen.setText("💎 Deepen")
        self.txt_lyrics.setPlainText(new_lyrics)
        self._flash_btn(self.btn_deepen, "✓ Deepened!")

    def _on_deepen_error(self, err_msg: str):
        self.btn_deepen.setEnabled(True)
        self.btn_deepen.setText("💎 Deepen")

    def _open_style_mutator(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #0f1426;
                color: #f1f5f9;
                border: 1px solid #283354;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 14px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 600;
            }
            QMenu::item:selected {
                background-color: #3b82f6;
                color: #ffffff;
            }
        """)

        mutations = [
            ("Acoustic Unplugged Take", "acoustic fingerstyle, unplugged, Martin guitar, upright bass, warm intimate vocals"),
            ("80s Synthwave Night Take", "80s synthwave, analog Prophet-5 synths, LinnDrum, neon atmosphere, gated snare"),
            ("Khmer 60s Garage Rock Take", "Khmer 60s garage rock, Sinn Sisamouth tape saturation, Farfisa organ, fuzz guitar"),
            ("Modern Heritage Trap Take", "Khmer trap drill, 808 sub slide, sampled Chapei riff, rapid flow, stadium drop")
        ]

        for label, style_str in mutations:
            action = menu.addAction(f"🎲 {label}")
            action.triggered.connect(lambda _, s=style_str, l=label: self._apply_mutation(s, l))

        menu.exec(self.btn_mutate.mapToGlobal(self.btn_mutate.rect().bottomLeft()))

    def _apply_mutation(self, style_str: str, label: str):
        self.txt_style.setPlainText(style_str[:self.style_limit])
        self._flash_btn(self.btn_mutate, "✓ Applied!")

    def _open_in_editor(self):
        self.open_editor_requested.emit(self.song_data)
        self.accept()

    def _open_in_visual(self):
        self.open_visual_requested.emit(self.song_data)
        self.accept()

    def _prev_track(self):
        if self.current_index > 0:
            self.current_index -= 1
            self._load_song_data(self.all_songs[self.current_index])

    def _next_track(self):
        if self.current_index < len(self.all_songs) - 1:
            self.current_index += 1
            self._load_song_data(self.all_songs[self.current_index])

    def _flash_btn(self, btn: QPushButton, msg: str):
        orig = btn.text()
        btn.setText(msg)
        QTimer.singleShot(1200, lambda: btn.setText(orig))

    def _humanize_and_approve(self):
        self.btn_humanize_approve.setEnabled(False)
        self.btn_humanize_approve.setText("⏳ Humanizing...")
        from app.gemini_client import HumanizeApproveWorker
        self.humanizer_worker = HumanizeApproveWorker(self.song_data, parent=self)
        self.humanizer_worker.finished.connect(self._on_humanize_finished)
        self.humanizer_worker.error.connect(self._on_humanize_error)
        self.humanizer_worker.start()

    def _on_humanize_finished(self, res: dict):
        self.btn_humanize_approve.setEnabled(True)
        self.btn_humanize_approve.setText("✅ Human Approved!")
        self.song_data.update(res)
        self._load_song_data(self.song_data)
        self.song_updated.emit(self.song_data)
        QTimer.singleShot(2500, lambda: self.btn_humanize_approve.setText("👤 Humanize & Approve") if hasattr(self, "btn_humanize_approve") else None)

    def _on_humanize_error(self, err_msg: str):
        self.btn_humanize_approve.setEnabled(True)
        self.btn_humanize_approve.setText("👤 Humanize & Approve")

    def _apply_theme(self, theme_or_dark):
        t = get_theme(theme_or_dark)
        self.theme = t
        self.theme_key = t.get("id", "obsidian")
        is_dark = t.get("is_dark", True)
        self.is_dark = is_dark

        if is_dark:
            self.setStyleSheet(f"""
                QDialog {{
                    background-color: {t['bg_window']};
                    color: {t['text_primary']};
                }}
                QFrame#headerFrame {{
                    background-color: {t['bg_card']};
                    border: 1px solid {t['border']};
                    border-radius: 8px;
                }}
                QFrame#styleBoxFrame, QFrame#lyricsFrame {{
                    background-color: {t['bg_card']};
                    border: 1px solid {t['border']};
                    border-radius: 8px;
                }}
            """)
            btn_action_style = f"""
                QPushButton {{
                    background-color: {t['bg_card_alt']};
                    color: {t['text_secondary']};
                    border: 1px solid {t['border']};
                    font-size: 10px;
                    font-weight: 700;
                    padding: 4px 10px;
                    border-radius: 5px;
                }}
                QPushButton:hover {{
                    background-color: {t['border']};
                    color: #ffffff;
                    border-color: {t['border_accent']};
                }}
            """
            for b in [self.btn_copy_title, self.btn_copy_style, self.btn_copy_lyrics]:
                b.setStyleSheet(btn_action_style)
            if hasattr(self, "btn_deepen"):
                self.btn_deepen.setStyleSheet(f"background-color: {t['subtle_pill_bg']}; color: {t['text_accent']}; border: 1px solid {t['border_accent']}; border-radius: 5px; font-weight: 700; font-size: 10px; padding: 4px 10px;")
            if hasattr(self, "btn_open_editor"):
                self.btn_open_editor.setStyleSheet(f"background: {t['accent_gradient']}; color: #ffffff; border: 1px solid {t['border_accent']}; border-radius: 5px; font-weight: 800; font-size: 10.5px; padding: 5px 12px;")
        else:
            self.setStyleSheet("""
                QDialog {
                    background-color: #f8fafc;
                    color: #0f172a;
                }
                QFrame#headerFrame {
                    background-color: #ffffff;
                    border: 1px solid #cbd5e1;
                    border-radius: 8px;
                }
                QFrame#styleBoxFrame, QFrame#lyricsFrame {
                    background-color: #ffffff;
                    border: 1px solid #cbd5e1;
                    border-radius: 8px;
                }
            """)
            self.lbl_title.setStyleSheet("font-size: 14px; font-weight: 800; color: #0f172a;")
            self.txt_style.setStyleSheet("background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 6px; font-size: 11px; color: #1d4ed8; padding: 6px;")
            self.txt_lyrics.setStyleSheet("background: #ffffff; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 11.5px; font-family: 'Cascadia Code', monospace; color: #0f172a; padding: 8px;")
            btn_action_style = """
                QPushButton {
                    background-color: #ffffff;
                    color: #0f172a;
                    border: 1px solid #cbd5e1;
                    font-size: 10px;
                    font-weight: 700;
                    padding: 4px 10px;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #f1f5f9;
                    color: #0f172a;
                    border-color: #94a3b8;
                }
            """
            for b in [self.btn_copy_title, self.btn_copy_style, self.btn_copy_lyrics]:
                b.setStyleSheet(btn_action_style)
            if hasattr(self, "btn_deepen"):
                self.btn_deepen.setStyleSheet("background-color: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; border-radius: 5px; font-weight: 700; font-size: 10px; padding: 4px 10px;")
            if hasattr(self, "btn_open_editor"):
                self.btn_open_editor.setStyleSheet(f"background: {t['accent_gradient']}; color: #ffffff; border: 1px solid {t['border_accent']}; border-radius: 5px; font-weight: 800; font-size: 10.5px; padding: 5px 12px;")
