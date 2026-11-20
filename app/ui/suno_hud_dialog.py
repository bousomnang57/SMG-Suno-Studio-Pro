"""
Floating Suno Quick-Paste Companion HUD.
Stays cleanly on top of your logged-in Chrome/Edge Suno window so creating single songs
or 20-track Batch Studio Pro albums takes 1-click per field — zero account risk,
zero unofficial cookie bots, works with every Suno version (v3.5 / v4 / v4.5 / v6).
"""

from __future__ import annotations

import re
from typing import Callable, Dict, List, Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QPlainTextEdit, QFrame, QApplication
)
from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtGui import QDesktopServices, QIcon

from app.config import config_manager, SUNO_PLANS, get_asset_path
from app.ui.styles import get_theme


class SunoCompanionHUD(QDialog):
    """Compact, always-on-top Quick-Paste Companion Dock for https://suno.com/create."""

    def __init__(
        self,
        tracks: List[Dict],
        start_index: int = 0,
        theme_key: str = "obsidian",
        on_track_done: Optional[Callable[[Dict], None]] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.tracks: List[Dict] = tracks or [{
            "title": "Untitled Song",
            "style_prompt": "",
            "lyrics": "",
            "negative_prompt": "",
        }]
        self.current_index = max(0, min(start_index, len(self.tracks) - 1))
        self.theme_key = theme_key
        self.on_track_done = on_track_done
        self._pinned_on_top = True

        self.setWindowTitle("🚀 Suno Quick-Paste Companion HUD")
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowMinimizeButtonHint
        )
        self.resize(420, 500)
        self.setMinimumSize(360, 420)

        logo_path = get_asset_path("logo.png")
        if logo_path.exists():
            self.setWindowIcon(QIcon(str(logo_path)))

        self._init_ui()
        self.apply_theme(theme_key)
        self._load_current_track()

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(8)

        # ── 1. Top Header: Title + Pin On Top + Account/Credit Badge ──
        hdr = QHBoxLayout()
        hdr.setSpacing(6)

        self.lbl_title = QLabel("🚀 Suno Companion HUD")
        self.lbl_title.setStyleSheet("font-size: 13px; font-weight: 800;")
        hdr.addWidget(self.lbl_title)
        hdr.addStretch(1)

        self.btn_pin = QPushButton("📌 On Top")
        self.btn_pin.setCheckable(True)
        self.btn_pin.setChecked(True)
        self.btn_pin.setFixedHeight(24)
        self.btn_pin.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_pin.setToolTip("Keep this HUD floating above your browser while pasting into Suno")
        self.btn_pin.toggled.connect(self._toggle_on_top)
        hdr.addWidget(self.btn_pin)

        root.addLayout(hdr)

        # Account & Plan Info Strip
        self.account_bar = QFrame()
        self.account_bar.setObjectName("hudAccountBar")
        ab_layout = QHBoxLayout(self.account_bar)
        ab_layout.setContentsMargins(8, 5, 8, 5)
        ab_layout.setSpacing(6)

        self.lbl_plan_credits = QLabel("")
        self.lbl_plan_credits.setStyleSheet("font-size: 10.5px; font-weight: 700;")
        ab_layout.addWidget(self.lbl_plan_credits, stretch=1)

        self.lbl_rights = QLabel("")
        self.lbl_rights.setStyleSheet("font-size: 9.5px; font-weight: 800; padding: 2px 6px; border-radius: 4px;")
        ab_layout.addWidget(self.lbl_rights)

        root.addWidget(self.account_bar)

        # ── 2. Queue Navigator (Visible for Batch Multi-Song Queues) ──
        self.queue_frame = QFrame()
        self.queue_frame.setObjectName("hudQueueFrame")
        q_layout = QHBoxLayout(self.queue_frame)
        q_layout.setContentsMargins(6, 4, 6, 4)
        q_layout.setSpacing(6)

        self.btn_prev = QPushButton("◀ Prev")
        self.btn_prev.setFixedHeight(24)
        self.btn_prev.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_prev.clicked.connect(self._prev_track)
        q_layout.addWidget(self.btn_prev)

        self.lbl_queue_pos = QLabel("Track 1 / 1")
        self.lbl_queue_pos.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_queue_pos.setStyleSheet("font-size: 11px; font-weight: 800;")
        q_layout.addWidget(self.lbl_queue_pos, stretch=1)

        self.btn_next = QPushButton("Next ▶")
        self.btn_next.setFixedHeight(24)
        self.btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_next.clicked.connect(self._next_track)
        q_layout.addWidget(self.btn_next)

        root.addWidget(self.queue_frame)

        # ── 3. Step 1: Song Title ──
        row_t = QHBoxLayout()
        row_t.setSpacing(6)
        self.txt_title = QLineEdit()
        self.txt_title.setReadOnly(True)
        self.txt_title.setPlaceholderText("Song Title")
        row_t.addWidget(self.txt_title, stretch=1)

        self.btn_copy_title = QPushButton("1. 📋 Title")
        self.btn_copy_title.setFixedWidth(96)
        self.btn_copy_title.setFixedHeight(28)
        self.btn_copy_title.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_copy_title.clicked.connect(self._copy_title)
        row_t.addWidget(self.btn_copy_title)
        root.addLayout(row_t)

        # ── 4. Step 2: Style of Music Prompt + Live Char Gauge ──
        s_hdr = QHBoxLayout()
        self.lbl_style_hdr = QLabel("Style of Music (Paste into Suno Style box):")
        self.lbl_style_hdr.setStyleSheet("font-size: 10px; font-weight: 700;")
        s_hdr.addWidget(self.lbl_style_hdr)
        s_hdr.addStretch(1)
        self.lbl_style_chars = QLabel("0 / 200")
        self.lbl_style_chars.setStyleSheet("font-size: 10px; font-weight: 800;")
        s_hdr.addWidget(self.lbl_style_chars)
        root.addLayout(s_hdr)

        row_s = QHBoxLayout()
        row_s.setSpacing(6)
        self.txt_style = QPlainTextEdit()
        self.txt_style.setReadOnly(True)
        self.txt_style.setFixedHeight(58)
        row_s.addWidget(self.txt_style, stretch=1)

        self.btn_copy_style = QPushButton("2. 🎨 Style")
        self.btn_copy_style.setFixedWidth(96)
        self.btn_copy_style.setFixedHeight(58)
        self.btn_copy_style.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_copy_style.clicked.connect(self._copy_style)
        row_s.addWidget(self.btn_copy_style)
        root.addLayout(row_s)

        # ── 5. Step 3: Lyrics Preview + Copy Button ──
        l_hdr = QHBoxLayout()
        self.lbl_lyrics_hdr = QLabel("Lyrics (Paste into Suno Custom Lyrics box):")
        self.lbl_lyrics_hdr.setStyleSheet("font-size: 10px; font-weight: 700;")
        l_hdr.addWidget(self.lbl_lyrics_hdr)
        l_hdr.addStretch(1)
        self.lbl_lyrics_meta = QLabel("0 lines")
        self.lbl_lyrics_meta.setStyleSheet("font-size: 10px; font-weight: 700;")
        l_hdr.addWidget(self.lbl_lyrics_meta)
        root.addLayout(l_hdr)

        self.txt_lyrics = QPlainTextEdit()
        self.txt_lyrics.setReadOnly(True)
        root.addWidget(self.txt_lyrics, stretch=1)

        copy_row = QHBoxLayout()
        copy_row.setSpacing(6)

        self.btn_copy_lyrics = QPushButton("3. ✍️ Copy Full Lyrics")
        self.btn_copy_lyrics.setFixedHeight(32)
        self.btn_copy_lyrics.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_copy_lyrics.clicked.connect(self._copy_lyrics)
        copy_row.addWidget(self.btn_copy_lyrics, stretch=2)

        self.btn_copy_neg = QPushButton("4. 🚫 Exclude")
        self.btn_copy_neg.setFixedHeight(32)
        self.btn_copy_neg.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_copy_neg.setToolTip("Copy Negative / Exclude Styles into Suno Exclude field")
        self.btn_copy_neg.clicked.connect(self._copy_negative)
        copy_row.addWidget(self.btn_copy_neg, stretch=1)
        root.addLayout(copy_row)

        # ── 6. Primary Suno Browser Launch + Mark Created (-10 cr) ──
        act_row = QHBoxLayout()
        act_row.setSpacing(6)

        self.btn_open_suno = QPushButton("🌐 Open suno.com/create")
        self.btn_open_suno.setFixedHeight(34)
        self.btn_open_suno.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open_suno.setToolTip("Open your logged-in Suno Create page in your default browser")
        self.btn_open_suno.clicked.connect(self._open_suno_create)
        act_row.addWidget(self.btn_open_suno, stretch=1)

        self.btn_mark_done = QPushButton("✅ Created (-10 cr) ➔ Next")
        self.btn_mark_done.setFixedHeight(34)
        self.btn_mark_done.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mark_done.setToolTip("Mark this song as created in Suno, deduct 10 estimated credits, and move to next track")
        self.btn_mark_done.clicked.connect(self._mark_created_and_next)
        act_row.addWidget(self.btn_mark_done, stretch=1)

        root.addLayout(act_row)

        self.lbl_status = QLabel("Tip: In Suno, turn on 'Custom' mode, then click 1 ➔ 2 ➔ 3 above!")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setStyleSheet("font-size: 9.5px; font-weight: 600;")
        root.addWidget(self.lbl_status)

    def _get_engine_char_limit(self) -> int:
        eng = config_manager.get("suno_engine", "Suno v4 / v3.5 (200 chars)")
        m = re.search(r"(\d{3})", str(eng))
        return int(m.group(1)) if m else 200

    def _refresh_account_strip(self):
        plan_name = config_manager.get("suno_plan", "Pro (2,500 cr/mo — Commercial)")
        plan_info = SUNO_PLANS.get(plan_name, {"commercial": True, "badge": "Pro"})
        credits_left = int(config_manager.get("suno_credits_remaining", 2500))
        handle = config_manager.get("suno_account_handle", "").strip()
        short_plan = plan_name.split("(")[0].strip()
        prefix = f"{handle} • " if handle else ""
        self.lbl_plan_credits.setText(f"🎵 {prefix}{short_plan} • ~{credits_left:,} cr left")

        is_dark = get_theme(self.theme_key).get("is_dark", True)
        if plan_info.get("commercial", True):
            self.lbl_rights.setText("✓ Commercial")
            self.lbl_rights.setStyleSheet(
                "font-size: 9.5px; font-weight: 800; padding: 2px 6px; border-radius: 4px; "
                + ("background: #064e3b; color: #34d399; border: 1px solid #059669;" if is_dark else "background: #dcfce7; color: #047857; border: 1px solid #86efac;")
            )
        else:
            self.lbl_rights.setText("⚠ Personal Only")
            self.lbl_rights.setStyleSheet(
                "font-size: 9.5px; font-weight: 800; padding: 2px 6px; border-radius: 4px; "
                + ("background: #451a03; color: #fbbf24; border: 1px solid #d97706;" if is_dark else "background: #fef3c7; color: #b45309; border: 1px solid #f59e0b;")
            )

    def _load_current_track(self):
        self._refresh_account_strip()
        track = self.tracks[self.current_index]
        title = str(track.get("title") or "Untitled Song").strip()
        style = str(track.get("style_prompt") or "").strip()
        lyrics = str(track.get("lyrics") or "").strip()
        neg = str(track.get("negative_prompt") or "").strip()
        is_done = bool(track.get("suno_done", False) or str(track.get("status", "")).lower() == "done")

        self.txt_title.setText(title)
        self.txt_style.setPlainText(style)
        self.txt_lyrics.setPlainText(lyrics)

        limit = self._get_engine_char_limit()
        self.lbl_style_chars.setText(f"{len(style)} / {limit} chars")
        if len(style) > limit:
            self.lbl_style_chars.setStyleSheet("font-size: 10px; font-weight: 800; color: #ef4444;")
        else:
            self.lbl_style_chars.setStyleSheet("font-size: 10px; font-weight: 800; color: #10b981;")

        line_cnt = len([ln for ln in lyrics.splitlines() if ln.strip()])
        self.lbl_lyrics_meta.setText(f"{line_cnt} lines • {'✅ Created' if is_done else '⏳ Pending'}")

        self.btn_copy_neg.setEnabled(bool(neg))
        self.btn_copy_neg.setToolTip(f"Exclude: {neg}" if neg else "No negative/exclude tags set for this track")

        total = len(self.tracks)
        self.queue_frame.setVisible(total > 1)
        if total > 1:
            done_cnt = sum(1 for tr in self.tracks if tr.get("suno_done") or str(tr.get("status", "")).lower() == "done")
            self.lbl_queue_pos.setText(f"Track {self.current_index + 1} / {total}  •  {done_cnt}/{total} Done")
            self.btn_prev.setEnabled(self.current_index > 0)
            self.btn_next.setEnabled(self.current_index < total - 1)
            self.btn_mark_done.setText("✅ Created (-10 cr) ➔ Next" if self.current_index < total - 1 else "✅ Mark Final Created (-10 cr)")
        else:
            self.btn_mark_done.setText("✅ Mark Created (-10 cr)")

    def update_tracks(self, tracks: List[Dict], start_index: int = 0, on_track_done: Optional[Callable[[Dict], None]] = None):
        self.tracks = tracks or self.tracks
        self.current_index = max(0, min(start_index, len(self.tracks) - 1))
        if on_track_done is not None:
            self.on_track_done = on_track_done
        self._load_current_track()

    def _toggle_on_top(self, checked: bool):
        self._pinned_on_top = checked
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, checked)
        self.btn_pin.setText("📌 On Top" if checked else "📌 Unpinned")
        self.show()

    def _flash_btn(self, btn: QPushButton, orig_text: str, copied_text: str = "✓ Copied!"):
        btn.setText(copied_text)
        QTimer.singleShot(1200, lambda: btn.setText(orig_text))

    def _copy_title(self):
        txt = self.txt_title.text().strip()
        if txt:
            QApplication.clipboard().setText(txt)
            self._flash_btn(self.btn_copy_title, "1. 📋 Title")
            self.lbl_status.setText(f"✓ Copied Title: {txt[:36]}")

    def _copy_style(self):
        txt = self.txt_style.toPlainText().strip()
        if txt:
            QApplication.clipboard().setText(txt)
            self._flash_btn(self.btn_copy_style, "2. 🎨 Style")
            self.lbl_status.setText(f"✓ Copied Style Prompt ({len(txt)} chars) — paste into Suno!")

    def _copy_lyrics(self):
        txt = self.txt_lyrics.toPlainText().strip()
        if txt:
            QApplication.clipboard().setText(txt)
            self._flash_btn(self.btn_copy_lyrics, "3. ✍️ Copy Full Lyrics")
            self.lbl_status.setText("✓ Copied Full Lyrics — click Create in Suno!")

    def _copy_negative(self):
        neg = str(self.tracks[self.current_index].get("negative_prompt") or "").strip()
        if neg:
            QApplication.clipboard().setText(neg)
            self._flash_btn(self.btn_copy_neg, "4. 🚫 Exclude")
            self.lbl_status.setText("✓ Copied Exclude / Negative styles!")

    def _open_suno_create(self):
        url = config_manager.get("suno_create_url", "https://suno.com/create") or "https://suno.com/create"
        QDesktopServices.openUrl(QUrl(url))
        self.lbl_status.setText("🌐 Opened suno.com/create in your logged-in browser!")

    def _mark_created_and_next(self):
        track = self.tracks[self.current_index]
        track["suno_done"] = True
        track["status"] = "Done"
        remaining = config_manager.consume_suno_credits(10)
        if callable(self.on_track_done):
            try:
                self.on_track_done(track)
            except Exception:
                pass
        if self.current_index < len(self.tracks) - 1:
            self.current_index += 1
        self._load_current_track()
        self.lbl_status.setText(f"✅ Marked Created! Est. credits remaining: ~{remaining:,}")

    def _prev_track(self):
        if self.current_index > 0:
            self.current_index -= 1
            self._load_current_track()

    def _next_track(self):
        if self.current_index < len(self.tracks) - 1:
            self.current_index += 1
            self._load_current_track()

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
        acc_grad = t["accent_gradient"]

        self.setStyleSheet(f"""
            QDialog {{ background-color: {bg}; color: {pri}; }}
            QFrame#hudAccountBar, QFrame#hudQueueFrame {{
                background-color: {card};
                border: 1px solid {border};
                border-radius: 7px;
            }}
            QLabel {{ color: {pri}; background: transparent; border: none; }}
            QLineEdit, QPlainTextEdit {{
                background-color: {inp};
                color: {pri};
                border: 1px solid {border};
                border-radius: 6px;
                padding: 4px 6px;
                font-size: 10.5px;
            }}
        """)

        btn_sub = (
            f"background: {t['bg_btn']}; color: {pri}; border: 1px solid {border}; border-radius: 6px; font-weight: 700; font-size: 10.5px; padding: 3px 8px;"
            if is_dark else
            "background: #ffffff; color: #0f172a; border: 1px solid #cbd5e1; border-radius: 6px; font-weight: 700; font-size: 10.5px; padding: 3px 8px;"
        )
        for b in [self.btn_pin, self.btn_prev, self.btn_next, self.btn_copy_title, self.btn_copy_neg]:
            b.setStyleSheet(btn_sub)

        self.btn_copy_style.setStyleSheet(
            f"background: {t['subtle_pill_bg']}; color: {t['text_accent']}; border: 1px solid {t['border_accent']}; border-radius: 6px; font-weight: 800; font-size: 10.5px;"
            if is_dark else
            "background: #f5f3ff; color: #6d28d9; border: 1px solid #c4b5fd; border-radius: 6px; font-weight: 800; font-size: 10.5px;"
        )
        self.btn_copy_lyrics.setStyleSheet(
            f"background: {acc_grad}; color: #ffffff; border: 1px solid {t['border_accent']}; border-radius: 6px; font-weight: 800; font-size: 11px;"
        )
        self.btn_open_suno.setStyleSheet(
            "background: #1e3a8a; color: #dbeafe; border: 1px solid #3b82f6; border-radius: 6px; font-weight: 800; font-size: 10.5px;"
            if is_dark else
            "background: #eff6ff; color: #1d4ed8; border: 1px solid #93c5fd; border-radius: 6px; font-weight: 800; font-size: 10.5px;"
        )
        self.btn_mark_done.setStyleSheet(
            "background: #065f46; color: #ecfdf5; border: 1px solid #10b981; border-radius: 6px; font-weight: 800; font-size: 10.5px;"
            if is_dark else
            "background: #16a34a; color: #ffffff; border: 1px solid #15803d; border-radius: 6px; font-weight: 800; font-size: 10.5px;"
        )
        self.lbl_style_hdr.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {sec};")
        self.lbl_lyrics_hdr.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {sec};")
        self.lbl_status.setStyleSheet(f"font-size: 9.5px; font-weight: 600; color: {acc};")
        self._refresh_account_strip()
