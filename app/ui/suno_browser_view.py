"""
6th Studio Tab: Embedded Suno Browser & Auto-Fill Workstation (🌐 Suno).
Provides persistent multi-account login profiles, 1-click React-compatible Title/Style/Lyrics/Exclude
auto-fill into suno.com/create, Batch Studio Pro queue docking, pre-flight style limit trimming,
and automatic MP3/WAV download naming with 1-click Editor Stem Player auditioning.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Callable, Dict, List, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QPlainTextEdit, QFrame, QComboBox, QCheckBox,
    QSplitter, QGridLayout, QApplication
)
from PyQt6.QtCore import Qt, QUrl, QTimer, pyqtSignal
from PyQt6.QtGui import QDesktopServices

from app.config import config_manager, SUNO_PLANS
from app.ui.styles import get_theme


class SunoBrowserView(QWidget):
    """Embedded Suno AI Browser & 1-Click Auto-Fill Workstation."""

    load_audio_into_editor_requested = pyqtSignal(str)
    open_floating_hud_requested = pyqtSignal()
    pull_from_studio_requested = pyqtSignal()
    open_link_downloader_requested = pyqtSignal(str)  # initial_url
    import_lyrics_requested = pyqtSignal(str, str)  # title, lyrics

    def __init__(self, parent=None, theme_key: str = "obsidian"):
        super().__init__(parent)
        self.theme_key = theme_key
        self.tracks: List[Dict] = [{
            "title": "Untitled Song",
            "style_prompt": "",
            "lyrics": "",
            "negative_prompt": "",
        }]
        self.current_index: int = 0
        self.on_track_done: Optional[Callable[[Dict], None]] = None
        self.last_downloaded_audio_path: str = ""
        self._last_js_executed: str = ""
        self._zoom_factor: float = 1.0

        self.account_slots = [
            "Account 1 (Primary)",
            "Account 2 (Backup)",
            "Account 3 (Studio)",
        ]
        saved_slot = config_manager.get("suno_active_account_slot", "Account 1 (Primary)")
        self.current_account_slot = saved_slot if saved_slot in self.account_slots else self.account_slots[0]

        self.web_view = None
        self.web_profile = None
        self.web_page = None
        self._browser_initialized = False

        self._init_ui()
        self.apply_theme(theme_key)
        self._load_current_track()

    def _downloads_dir(self) -> Path:
        d = Path.home() / ".lyric_ai_writer" / "suno_downloads"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _profile_dir(self, slot_name: str) -> Path:
        slug = re.sub(r"[^a-z0-9]+", "_", slot_name.lower()).strip("_") or "account_1"
        p = Path.home() / ".lyric_ai_writer" / "suno_web_profiles" / slug
        p.mkdir(parents=True, exist_ok=True)
        return p

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(6, 4, 6, 6)
        root.setSpacing(5)

        # ── 1. Top Browser & Account Navigation Bar ──
        self.nav_bar = QFrame()
        self.nav_bar.setObjectName("sunoNavBar")
        self.nav_bar.setFixedHeight(36)
        nav = QHBoxLayout(self.nav_bar)
        nav.setContentsMargins(8, 3, 8, 3)
        nav.setSpacing(6)

        self.btn_toggle_dock = QPushButton("◀ Dock")
        self.btn_toggle_dock.setCheckable(True)
        self.btn_toggle_dock.setChecked(True)
        self.btn_toggle_dock.setFixedHeight(26)
        self.btn_toggle_dock.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_dock.setToolTip("Show / Hide Left Song & Queue Control Dock")
        self.btn_toggle_dock.clicked.connect(self._toggle_left_dock)
        nav.addWidget(self.btn_toggle_dock)

        self.lbl_acct = QLabel("👤")
        nav.addWidget(self.lbl_acct)

        self.combo_account = QComboBox()
        self.combo_account.addItems(self.account_slots)
        self.combo_account.setCurrentText(self.current_account_slot)
        self.combo_account.setFixedHeight(26)
        self.combo_account.setMinimumWidth(138)
        self.combo_account.setToolTip("Switch persistent Suno login profile (each slot keeps its own signed-in cookies)")
        self.combo_account.currentTextChanged.connect(self._on_account_slot_changed)
        nav.addWidget(self.combo_account)

        self.lbl_account_credits = QLabel("")
        self.lbl_account_credits.setStyleSheet("font-size: 10.5px; font-weight: 800; padding: 2px 7px; border-radius: 5px;")
        nav.addWidget(self.lbl_account_credits)

        self.btn_nav_create = QPushButton("🎵 Create")
        self.btn_nav_create.setFixedHeight(26)
        self.btn_nav_create.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_nav_create.setToolTip("Navigate to https://suno.com/create")
        self.btn_nav_create.clicked.connect(lambda: self.navigate_to("https://suno.com/create"))
        nav.addWidget(self.btn_nav_create)

        self.btn_nav_library = QPushButton("📚 Library")
        self.btn_nav_library.setFixedHeight(26)
        self.btn_nav_library.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_nav_library.setToolTip("Navigate to https://suno.com/me")
        self.btn_nav_library.clicked.connect(lambda: self.navigate_to("https://suno.com/me"))
        nav.addWidget(self.btn_nav_library)

        self.btn_nav_account = QPushButton("💳 Plan")
        self.btn_nav_account.setFixedHeight(26)
        self.btn_nav_account.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_nav_account.setToolTip("Navigate to https://suno.com/account")
        self.btn_nav_account.clicked.connect(lambda: self.navigate_to("https://suno.com/account"))
        nav.addWidget(self.btn_nav_account)

        self.btn_nav_reload = QPushButton("🔄")
        self.btn_nav_reload.setFixedSize(28, 26)
        self.btn_nav_reload.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_nav_reload.setToolTip("Reload current Suno page")
        self.btn_nav_reload.clicked.connect(self._reload_page)
        nav.addWidget(self.btn_nav_reload)

        self.txt_url = QLineEdit("https://suno.com/create")
        self.txt_url.setFixedHeight(26)
        self.txt_url.returnPressed.connect(lambda: self.navigate_to(self.txt_url.text().strip()))
        nav.addWidget(self.txt_url, stretch=1)

        self.btn_zoom_out = QPushButton("-")
        self.btn_zoom_out.setFixedSize(24, 26)
        self.btn_zoom_out.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_zoom_out.clicked.connect(lambda: self._adjust_zoom(-0.1))
        nav.addWidget(self.btn_zoom_out)

        self.lbl_zoom = QLabel("100%")
        self.lbl_zoom.setFixedWidth(36)
        self.lbl_zoom.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_zoom.setStyleSheet("font-size: 10px; font-weight: 700;")
        nav.addWidget(self.lbl_zoom)

        self.btn_zoom_in = QPushButton("+")
        self.btn_zoom_in.setFixedSize(24, 26)
        self.btn_zoom_in.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_zoom_in.clicked.connect(lambda: self._adjust_zoom(0.1))
        nav.addWidget(self.btn_zoom_in)

        self.btn_open_ext = QPushButton("↗ Browser")
        self.btn_open_ext.setFixedHeight(26)
        self.btn_open_ext.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open_ext.setToolTip("Open current Suno URL in your external default browser")
        self.btn_open_ext.clicked.connect(self._open_external_browser)
        nav.addWidget(self.btn_open_ext)

        self.btn_download_link = QPushButton("📥 Download by Link")
        self.btn_download_link.setFixedHeight(26)
        self.btn_download_link.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_download_link.setToolTip("Download Suno song by link (MP3, MP4 Video, Cover Art) [Ctrl+Shift+D]")
        self.btn_download_link.clicked.connect(lambda: self.open_link_downloader_requested.emit(self.txt_url.text() if "song/" in self.txt_url.text() else ""))
        nav.addWidget(self.btn_download_link)

        self.btn_float_hud = QPushButton("📌 Float HUD")
        self.btn_float_hud.setFixedHeight(26)
        self.btn_float_hud.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_float_hud.setToolTip("Pop out Always-On-Top Floating Quick-Paste HUD [Ctrl+U]")
        self.btn_float_hud.clicked.connect(self.open_floating_hud_requested.emit)
        nav.addWidget(self.btn_float_hud)

        root.addWidget(self.nav_bar)

        # ── 2. Split-Pane Workbench: Left Auto-Fill Dock | Right Embedded Suno Browser ──
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left Dock Card
        self.dock_card = QFrame()
        self.dock_card.setObjectName("sunoDockCard")
        self.dock_card.setMinimumWidth(275)
        self.dock_card.setMaximumWidth(390)
        d_layout = QVBoxLayout(self.dock_card)
        d_layout.setContentsMargins(10, 8, 10, 8)
        d_layout.setSpacing(6)

        # Source & Queue Header
        src_row = QHBoxLayout()
        src_row.setSpacing(4)
        self.lbl_source_mode = QLabel("🎵 Active Studio Song")
        self.lbl_source_mode.setStyleSheet("font-size: 11.5px; font-weight: 800;")
        src_row.addWidget(self.lbl_source_mode, stretch=1)

        self.btn_sync_from_studio = QPushButton("🔄 Sync Studio")
        self.btn_sync_from_studio.setFixedHeight(22)
        self.btn_sync_from_studio.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_sync_from_studio.setToolTip("Pull latest song or Batch Queue from Studio views")
        self.btn_sync_from_studio.clicked.connect(self.pull_from_studio_requested.emit)
        src_row.addWidget(self.btn_sync_from_studio)
        d_layout.addLayout(src_row)

        # Queue Navigation Bar
        self.queue_nav_frame = QFrame()
        self.queue_nav_frame.setObjectName("sunoQueueNavFrame")
        qn_layout = QHBoxLayout(self.queue_nav_frame)
        qn_layout.setContentsMargins(4, 3, 4, 3)
        qn_layout.setSpacing(4)

        self.btn_prev = QPushButton("◀ Prev")
        self.btn_prev.setFixedHeight(22)
        self.btn_prev.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_prev.clicked.connect(self._prev_track)
        qn_layout.addWidget(self.btn_prev)

        self.lbl_queue_pos = QLabel("Track 1 / 1")
        self.lbl_queue_pos.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_queue_pos.setStyleSheet("font-size: 10.5px; font-weight: 800;")
        qn_layout.addWidget(self.lbl_queue_pos, stretch=1)

        self.btn_next = QPushButton("Next ▶")
        self.btn_next.setFixedHeight(22)
        self.btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_next.clicked.connect(self._next_track)
        qn_layout.addWidget(self.btn_next)
        d_layout.addWidget(self.queue_nav_frame)

        # Primary 1-Click Auto-Fill All Button
        self.btn_autofill_all = QPushButton("⚡ Auto-Fill All to Suno (Title + Style + Lyrics)")
        self.btn_autofill_all.setFixedHeight(34)
        self.btn_autofill_all.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_autofill_all.setToolTip("Automatically switch Suno to Custom mode and inject Title, Style, Lyrics & Exclude tags")
        self.btn_autofill_all.clicked.connect(self.autofill_all_to_suno)
        d_layout.addWidget(self.btn_autofill_all)

        # Editable Title Field
        t_row = QHBoxLayout()
        t_row.setSpacing(4)
        t_row.addWidget(QLabel("Title:"))
        self.txt_title = QLineEdit()
        self.txt_title.setPlaceholderText("Song Title...")
        t_row.addWidget(self.txt_title, stretch=1)
        d_layout.addLayout(t_row)

        # Style Header + Auto-Fit Guard
        st_hdr = QHBoxLayout()
        st_hdr.setSpacing(4)
        self.lbl_style_tag = QLabel("Style of Music:")
        self.lbl_style_tag.setStyleSheet("font-size: 10px; font-weight: 700;")
        st_hdr.addWidget(self.lbl_style_tag)
        st_hdr.addStretch(1)

        self.chk_auto_fit_style = QCheckBox("✂️ Auto-Fit")
        self.chk_auto_fit_style.setChecked(True)
        self.chk_auto_fit_style.setToolTip("Automatically deduplicate & trim Style Prompt to your Suno engine character limit before injecting")
        st_hdr.addWidget(self.chk_auto_fit_style)

        self.lbl_style_chars = QLabel("0 / 200")
        self.lbl_style_chars.setStyleSheet("font-size: 10px; font-weight: 800;")
        st_hdr.addWidget(self.lbl_style_chars)
        d_layout.addLayout(st_hdr)

        self.txt_style = QPlainTextEdit()
        self.txt_style.setPlaceholderText("Suno style tags, genre, BPM, vocal delivery...")
        self.txt_style.setFixedHeight(54)
        self.txt_style.textChanged.connect(self._update_char_counts)
        d_layout.addWidget(self.txt_style)

        # Lyrics Header & Box
        ly_hdr = QHBoxLayout()
        self.lbl_lyrics_tag = QLabel("Custom Lyrics (with [Section] tags):")
        self.lbl_lyrics_tag.setStyleSheet("font-size: 10px; font-weight: 700;")
        ly_hdr.addWidget(self.lbl_lyrics_tag)
        ly_hdr.addStretch(1)
        self.lbl_lyrics_meta = QLabel("0 lines")
        self.lbl_lyrics_meta.setStyleSheet("font-size: 10px; font-weight: 700;")
        ly_hdr.addWidget(self.lbl_lyrics_meta)
        d_layout.addLayout(ly_hdr)

        self.txt_lyrics = QPlainTextEdit()
        self.txt_lyrics.setPlaceholderText("[Verse 1]\nLyrics here...")
        self.txt_lyrics.textChanged.connect(self._update_char_counts)
        d_layout.addWidget(self.txt_lyrics, stretch=1)

        # Negative / Exclude Styles
        self.txt_negative = QLineEdit()
        self.txt_negative.setPlaceholderText("Exclude styles (optional, e.g. noisy, harsh screaming)...")
        d_layout.addWidget(self.txt_negative)

        # 2x2 Individual Field Fill & Copy Grid
        grid = QGridLayout()
        grid.setSpacing(4)

        self.btn_fill_title = QPushButton("1. 📋 Title")
        self.btn_fill_title.setFixedHeight(26)
        self.btn_fill_title.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_fill_title.setToolTip("Inject Title into Suno & copy to clipboard")
        self.btn_fill_title.clicked.connect(lambda: self._inject_single_field("title"))
        grid.addWidget(self.btn_fill_title, 0, 0)

        self.btn_fill_style = QPushButton("2. 🎨 Style")
        self.btn_fill_style.setFixedHeight(26)
        self.btn_fill_style.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_fill_style.setToolTip("Inject Style Prompt into Suno & copy to clipboard")
        self.btn_fill_style.clicked.connect(lambda: self._inject_single_field("style"))
        grid.addWidget(self.btn_fill_style, 0, 1)

        self.btn_fill_lyrics = QPushButton("3. ✍️ Lyrics")
        self.btn_fill_lyrics.setFixedHeight(26)
        self.btn_fill_lyrics.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_fill_lyrics.setToolTip("Inject Lyrics into Suno & copy to clipboard")
        self.btn_fill_lyrics.clicked.connect(lambda: self._inject_single_field("lyrics"))
        grid.addWidget(self.btn_fill_lyrics, 1, 0)

        self.btn_fill_neg = QPushButton("4. 🚫 Exclude")
        self.btn_fill_neg.setFixedHeight(26)
        self.btn_fill_neg.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_fill_neg.setToolTip("Inject Exclude/Negative tags into Suno & copy to clipboard")
        self.btn_fill_neg.clicked.connect(lambda: self._inject_single_field("negative"))
        grid.addWidget(self.btn_fill_neg, 1, 1)

        d_layout.addLayout(grid)

        # Universal Focused Field Fallback
        self.btn_fill_focused = QPushButton("🎯 Paste Lyrics into Clicked Suno Box")
        self.btn_fill_focused.setFixedHeight(26)
        self.btn_fill_focused.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_fill_focused.setToolTip("Future-proof fallback: click any box inside the Suno web page, then click here to fill it directly")
        self.btn_fill_focused.clicked.connect(lambda: self._inject_single_field("focused"))
        d_layout.addWidget(self.btn_fill_focused)

        # Mark Created & Next Track
        self.btn_mark_done = QPushButton("✅ Mark Created (-10 cr) ➔ Next Track")
        self.btn_mark_done.setFixedHeight(30)
        self.btn_mark_done.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mark_done.clicked.connect(self._mark_created_and_next)
        d_layout.addWidget(self.btn_mark_done)

        # Smart Download Manager Bar
        self.download_frame = QFrame()
        self.download_frame.setObjectName("sunoDownloadFrame")
        dl_layout = QVBoxLayout(self.download_frame)
        dl_layout.setContentsMargins(6, 6, 6, 6)
        dl_layout.setSpacing(4)

        # Quick Link Downloader Row
        quick_dl_row = QHBoxLayout()
        quick_dl_row.setSpacing(3)
        self.txt_quick_dl = QLineEdit()
        self.txt_quick_dl.setFixedHeight(25)
        self.txt_quick_dl.setPlaceholderText("Paste Suno link (suno.com/song/...)...")
        self.txt_quick_dl.setToolTip("Paste any Suno song link to download MP3 immediately")
        self.txt_quick_dl.returnPressed.connect(self._on_quick_download_clicked)
        quick_dl_row.addWidget(self.txt_quick_dl, stretch=1)

        self.btn_paste_quick_dl = QPushButton("📋")
        self.btn_paste_quick_dl.setFixedSize(25, 25)
        self.btn_paste_quick_dl.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_paste_quick_dl.setToolTip("Paste link from clipboard")
        self.btn_paste_quick_dl.clicked.connect(self._paste_into_quick_dl)
        quick_dl_row.addWidget(self.btn_paste_quick_dl)

        self.btn_quick_dl = QPushButton("⬇️")
        self.btn_quick_dl.setFixedSize(28, 25)
        self.btn_quick_dl.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_quick_dl.setToolTip("Download MP3 from link")
        self.btn_quick_dl.clicked.connect(self._on_quick_download_clicked)
        quick_dl_row.addWidget(self.btn_quick_dl)

        self.btn_open_full_dl = QPushButton("🔍")
        self.btn_open_full_dl.setFixedSize(25, 25)
        self.btn_open_full_dl.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open_full_dl.setToolTip("Open full Suno Downloader dialog (MP4 video, artwork, lyrics preview)")
        self.btn_open_full_dl.clicked.connect(lambda: self.open_link_downloader_requested.emit(self.txt_quick_dl.text().strip()))
        quick_dl_row.addWidget(self.btn_open_full_dl)
        dl_layout.addLayout(quick_dl_row)

        self.lbl_download_status = QLabel("📥 Suno MP3/WAV downloads auto-save with song title")
        self.lbl_download_status.setWordWrap(True)
        self.lbl_download_status.setStyleSheet("font-size: 9.5px; font-weight: 600;")
        dl_layout.addWidget(self.lbl_download_status)

        dl_btns = QHBoxLayout()
        dl_btns.setSpacing(4)
        self.btn_open_dl_folder = QPushButton("📂 Downloads")
        self.btn_open_dl_folder.setFixedHeight(23)
        self.btn_open_dl_folder.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open_dl_folder.clicked.connect(self._open_downloads_folder)
        dl_btns.addWidget(self.btn_open_dl_folder)

        self.btn_load_dl_to_editor = QPushButton("🎧 Audition in Editor")
        self.btn_load_dl_to_editor.setFixedHeight(23)
        self.btn_load_dl_to_editor.setEnabled(False)
        self.btn_load_dl_to_editor.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_load_dl_to_editor.clicked.connect(self._send_last_download_to_editor)
        dl_btns.addWidget(self.btn_load_dl_to_editor)
        dl_layout.addLayout(dl_btns)

        d_layout.addWidget(self.download_frame)

        # Right Pane: Embedded Suno WebEngine Container
        self.browser_container = QFrame()
        self.browser_container.setObjectName("sunoBrowserContainer")
        self.browser_layout = QVBoxLayout(self.browser_container)
        self.browser_layout.setContentsMargins(0, 0, 0, 0)
        self.browser_layout.setSpacing(0)

        self.lbl_browser_placeholder = QLabel(
            "🌐 Embedded Suno AI Studio Browser\n\n"
            "Initializing persistent multi-account session for https://suno.com/create..."
        )
        self.lbl_browser_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_browser_placeholder.setStyleSheet("font-size: 13px; font-weight: 700; padding: 24px;")
        self.browser_layout.addWidget(self.lbl_browser_placeholder)

        self.splitter.addWidget(self.dock_card)
        self.splitter.addWidget(self.browser_container)
        self.splitter.setCollapsible(0, True)
        self.splitter.setCollapsible(1, False)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([315, 960])

        root.addWidget(self.splitter, stretch=1)

    # ── Browser Lifecycle & Persistent Multi-Account Profile Management ──
    def ensure_browser_initialized(self):
        """Lazily initialize QWebEngineView on first visit to keep application startup instantaneous."""
        if self._browser_initialized:
            return
        self._browser_initialized = True

        # In headless offscreen unit-test mode, use lightweight deterministic test surface
        if os.environ.get("QT_QPA_PLATFORM", "").lower() == "offscreen":
            self.lbl_browser_placeholder.setText(
                f"🌐 Embedded Suno Browser Ready ({self.current_account_slot})\n"
                f"URL: {self.txt_url.text()}"
            )
            return

        try:
            from PyQt6.QtWebEngineWidgets import QWebEngineView
            from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage, QWebEngineSettings

            self.lbl_browser_placeholder.hide()
            self.web_view = QWebEngineView(self.browser_container)
            self.browser_layout.addWidget(self.web_view, stretch=1)
            self._mount_account_profile(self.current_account_slot)
        except Exception as e:
            self._browser_initialized = False
            self.lbl_browser_placeholder.show()
            self.lbl_browser_placeholder.setText(
                f"⚠️ Embedded WebEngine unavailable ({e}).\n"
                "Click '↗ Browser' or '📌 Float HUD' above to use your system browser."
            )

    def _mount_account_profile(self, slot_name: str):
        """Attach a dedicated persistent QWebEngineProfile for the selected Suno account slot."""
        if os.environ.get("QT_QPA_PLATFORM", "").lower() == "offscreen" or self.web_view is None:
            return
        try:
            from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage, QWebEngineSettings

            p_dir = self._profile_dir(slot_name)
            storage_name = f"SMGSuno_{re.sub(r'[^a-zA-Z0-9]', '', slot_name)}"
            profile = QWebEngineProfile(storage_name, self)
            profile.setPersistentStoragePath(str(p_dir / "storage"))
            profile.setCachePath(str(p_dir / "cache"))
            profile.setPersistentCookiesPolicy(
                QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies
            )
            profile.downloadRequested.connect(self._on_download_requested)

            page = QWebEnginePage(profile, self.web_view)
            settings = page.settings()
            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)

            self.web_view.setPage(page)
            self.web_profile = profile
            self.web_page = page
            self.web_view.urlChanged.connect(lambda u: self.txt_url.setText(u.toString()))
            self.web_view.loadProgress.connect(
                lambda p: self.lbl_download_status.setText(f"🌐 Loading Suno website: {p}%")
                if p < 100 else self.lbl_download_status.setText(f"✅ Suno Ready • {slot_name} • 1-Click Auto-Fill Armed")
            )
            target_url = self.txt_url.text().strip() or "https://suno.com/create"
            self.web_view.setUrl(QUrl(target_url))
            self.web_view.setZoomFactor(self._zoom_factor)
        except Exception as e:
            self.lbl_download_status.setText(f"⚠️ Profile switch error: {e}")

    def _on_account_slot_changed(self, slot_name: str):
        if not slot_name:
            return
        self.current_account_slot = slot_name
        config_manager.set("suno_active_account_slot", slot_name)
        if self._browser_initialized:
            if os.environ.get("QT_QPA_PLATFORM", "").lower() == "offscreen":
                self.lbl_browser_placeholder.setText(
                    f"🌐 Embedded Suno Browser Ready ({self.current_account_slot})\n"
                    f"URL: {self.txt_url.text()}"
                )
            else:
                self._mount_account_profile(slot_name)
        self.lbl_download_status.setText(f"👤 Switched to persistent profile: {slot_name}")

    def navigate_to(self, url_str: str):
        if not url_str:
            return
        if not url_str.startswith("http"):
            url_str = "https://" + url_str
        self.txt_url.setText(url_str)
        self.ensure_browser_initialized()
        if self.web_view is not None:
            self.web_view.setUrl(QUrl(url_str))

    def _reload_page(self):
        if self.web_view is not None:
            self.web_view.reload()

    def _adjust_zoom(self, delta: float):
        self._zoom_factor = max(0.6, min(1.5, round(self._zoom_factor + delta, 2)))
        self.lbl_zoom.setText(f"{int(round(self._zoom_factor * 100))}%")
        if self.web_view is not None:
            self.web_view.setZoomFactor(self._zoom_factor)

    def _toggle_left_dock(self):
        visible = not self.dock_card.isVisible()
        self.dock_card.setVisible(visible)
        self.btn_toggle_dock.setChecked(visible)
        self.btn_toggle_dock.setText("◀ Dock" if visible else "▶ Dock")

    def _open_external_browser(self):
        url = self.txt_url.text().strip() or "https://suno.com/create"
        QDesktopServices.openUrl(QUrl(url))

    # ── Smart MP3 / WAV Download Manager ──
    def _on_download_requested(self, download_item):
        try:
            suggested = download_item.downloadFileName() or "suno_track.mp3"
            ext = Path(suggested).suffix or ".mp3"
            raw_title = self.txt_title.text().strip() or "Suno_Song"
            safe_title = re.sub(r"[^\w\s\-\u1780-\u17FF]", "", raw_title).strip().replace(" ", "_") or "Suno_Song"
            idx_prefix = f"{self.current_index + 1:02d}_" if len(self.tracks) > 1 else ""
            dest_dir = self._downloads_dir()
            dest_name = f"{idx_prefix}{safe_title}{ext}"
            dest_path = dest_dir / dest_name
            counter = 2
            while dest_path.exists():
                dest_path = dest_dir / f"{idx_prefix}{safe_title}_{counter}{ext}"
                counter += 1

            download_item.setDownloadDirectory(str(dest_dir))
            download_item.setDownloadFileName(dest_path.name)
            download_item.accept()

            self.last_downloaded_audio_path = str(dest_path)
            self.lbl_download_status.setText(f"⬇️ Downloading: {dest_path.name}...")
            download_item.isFinishedChanged.connect(lambda: self._on_download_finished(dest_path))
        except Exception as e:
            self.lbl_download_status.setText(f"⚠️ Download error: {e}")

    def _on_download_finished(self, dest_path: Path):
        if dest_path.exists():
            self.last_downloaded_audio_path = str(dest_path)
            self.btn_load_dl_to_editor.setEnabled(True)
            self.lbl_download_status.setText(f"✅ Saved: {dest_path.name}")

    def _open_downloads_folder(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self._downloads_dir())))

    def _send_last_download_to_editor(self):
        if self.last_downloaded_audio_path and Path(self.last_downloaded_audio_path).exists():
            self.load_audio_into_editor_requested.emit(self.last_downloaded_audio_path)

    def _paste_into_quick_dl(self):
        txt = QApplication.clipboard().text().strip()
        if txt:
            self.txt_quick_dl.setText(txt)

    def _on_quick_download_clicked(self):
        url = self.txt_quick_dl.text().strip()
        if not url:
            # Check clipboard for convenience
            clip = QApplication.clipboard().text().strip()
            if clip and ("suno.com" in clip or "suno.ai" in clip or SunoLinkParser.extract_uuid(clip)):
                url = clip
                self.txt_quick_dl.setText(url)
            else:
                self.open_link_downloader_requested.emit("")
                return

        from app.suno_downloader import SunoDownloadWorker
        self.lbl_download_status.setText("⬇️ Connecting to Suno CDN...")
        self.btn_quick_dl.setEnabled(False)

        worker = SunoDownloadWorker(input_url_or_uuid=url, media_format="mp3", parent=self)
        self._quick_dl_worker = worker

        def _on_prog(pct, cur, tot, spd):
            spd_txt = f"{spd / 1024:.1f} MB/s" if spd >= 1000 else f"{spd:.0f} KB/s"
            self.lbl_download_status.setText(f"⬇️ Downloading: {pct}% • {spd_txt}")

        def _on_done(ok, path, meta, err):
            self.btn_quick_dl.setEnabled(True)
            if ok and path:
                self.last_downloaded_audio_path = path
                p = Path(path)
                self.lbl_download_status.setText(f"✅ Saved: {p.name}")
                self.btn_load_dl_to_editor.setEnabled(True)
                self.txt_quick_dl.clear()
            else:
                self.lbl_download_status.setText(f"⚠️ Error: {err[:45]}")

        worker.progress.connect(_on_prog)
        worker.finished.connect(_on_done)
        worker.start()

    # ── Track & Batch Queue Sync ──
    def _get_engine_char_limit(self) -> int:
        eng = config_manager.get("suno_engine", "Suno v4 / v3.5 (200 chars)")
        m = re.search(r"(\d{3})", str(eng))
        return int(m.group(1)) if m else 200

    @staticmethod
    def _fit_style_to_limit(style_text: str, limit: int) -> str:
        seen = set()
        deduped = []
        for raw in style_text.split(","):
            tok = raw.strip()
            if not tok:
                continue
            k = tok.lower()
            if k not in seen:
                seen.add(k)
                deduped.append(tok)
        out = []
        for tok in deduped:
            cand = ", ".join(out + [tok])
            if len(cand) <= limit:
                out.append(tok)
            else:
                break
        return ", ".join(out) if out else style_text[:limit].rstrip(", ")

    def refresh_account_badge(self):
        prof = config_manager.get_suno_profile()
        short_plan = prof["plan"].split("(")[0].strip()
        rights = "✓ Commercial" if prof["commercial"] else "⚠ Personal"
        self.lbl_account_credits.setText(f"🎵 {short_plan} • ~{prof['credits_remaining']:,} cr • {rights}")

    def _update_char_counts(self):
        style = self.txt_style.toPlainText().strip()
        limit = self._get_engine_char_limit()
        self.lbl_style_chars.setText(f"{len(style)} / {limit}")
        self.lbl_style_chars.setStyleSheet(
            f"font-size: 10px; font-weight: 800; color: {'#ef4444' if len(style) > limit else '#10b981'};"
        )
        lyrics = self.txt_lyrics.toPlainText().strip()
        lines = len([l for l in lyrics.splitlines() if l.strip()])
        self.lbl_lyrics_meta.setText(f"{lines} lines")

    def _load_current_track(self):
        self.refresh_account_badge()
        track = self.tracks[self.current_index]
        title = str(track.get("title") or "Untitled Song").strip()
        style = str(track.get("style_prompt") or "").strip()
        lyrics = str(track.get("lyrics") or "").strip()
        neg = str(track.get("negative_prompt") or "").strip()

        self.txt_title.setText(title)
        self.txt_style.setPlainText(style)
        self.txt_lyrics.setPlainText(lyrics)
        self.txt_negative.setText(neg)
        self._update_char_counts()

        total = len(self.tracks)
        if total > 1:
            done_cnt = sum(1 for tr in self.tracks if tr.get("suno_done") or str(tr.get("status", "")).lower() == "done")
            self.lbl_source_mode.setText(f"⚡ Batch Queue ({total} Tracks)")
            self.lbl_queue_pos.setText(f"Track {self.current_index + 1} / {total} • {done_cnt} Done")
            self.queue_nav_frame.setVisible(True)
            self.btn_prev.setEnabled(self.current_index > 0)
            self.btn_next.setEnabled(self.current_index < total - 1)
        else:
            self.lbl_source_mode.setText("🎵 Active Studio Song")
            self.lbl_queue_pos.setText("Track 1 / 1")
            self.queue_nav_frame.setVisible(False)

    def update_tracks(
        self,
        tracks: List[Dict],
        start_index: int = 0,
        on_track_done: Optional[Callable[[Dict], None]] = None,
    ):
        if tracks:
            self.tracks = tracks
        self.current_index = max(0, min(start_index, len(self.tracks) - 1))
        if on_track_done is not None:
            self.on_track_done = on_track_done
        self._load_current_track()

    set_tracks = update_tracks

    def _prev_track(self):
        if self.current_index > 0:
            self.current_index -= 1
            self._load_current_track()

    def _next_track(self):
        if self.current_index < len(self.tracks) - 1:
            self.current_index += 1
            self._load_current_track()

    def _mark_created_and_next(self):
        track = self.tracks[self.current_index]
        track["suno_done"] = True
        track["status"] = "Done"
        rem = config_manager.consume_suno_credits(10)
        if callable(self.on_track_done):
            try:
                self.on_track_done(track)
            except Exception:
                pass
        if self.current_index < len(self.tracks) - 1:
            self.current_index += 1
        self._load_current_track()
        self.lbl_download_status.setText(f"✅ Marked Created! Est. Suno credits left: ~{rem:,}")

    # ── React-Compatible JavaScript Auto-Fill Engine ──
    def _build_autofill_js(
        self,
        title: Optional[str] = None,
        style: Optional[str] = None,
        lyrics: Optional[str] = None,
        negative: Optional[str] = None,
        mode: str = "all",
    ) -> str:
        if title is None:
            title = self.txt_title.text().strip()
        if style is None:
            style = self._prepared_style_text()
        if lyrics is None:
            lyrics = self.txt_lyrics.toPlainText().strip()
        if negative is None:
            negative = self.txt_negative.text().strip()

        payload = json.dumps({
            "title": title,
            "style": style,
            "lyrics": lyrics,
            "negative": negative,
            "mode": mode,
        }, ensure_ascii=False)

        return f"""
        (function() {{
            const data = {payload};
            function setReactValue(el, val) {{
                if (!el) return false;
                el.focus();
                const proto = el.tagName === 'TEXTAREA'
                    ? window.HTMLTextAreaElement.prototype
                    : window.HTMLInputElement.prototype;
                const desc = Object.getOwnPropertyDescriptor(proto, 'value');
                if (desc && desc.set) {{
                    desc.set.call(el, val);
                }} else {{
                    el.value = val;
                }}
                el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                return true;
            }}

            if (data.mode === 'focused') {{
                const active = document.activeElement;
                if (active && (active.tagName === 'TEXTAREA' || active.tagName === 'INPUT')) {{
                    return setReactValue(active, data.lyrics || data.style || data.title) ? 'focused_ok' : 'no_focus';
                }}
                return 'no_focus';
            }}

            // 1. Ensure Custom Mode toggle is active if present
            const switches = Array.from(document.querySelectorAll('button, label, input[type="checkbox"], [role="switch"]'));
            for (const sw of switches) {{
                const txt = (sw.innerText || sw.getAttribute('aria-label') || '').toLowerCase();
                if (txt === 'custom' || txt.includes('custom mode')) {{
                    const checked = sw.getAttribute('aria-checked') === 'true' || sw.checked === true;
                    if (!checked && typeof sw.click === 'function') {{
                        sw.click();
                    }}
                    break;
                }}
            }}

            const fields = Array.from(document.querySelectorAll('textarea, input[type="text"], input:not([type])'))
                .filter(el => el.offsetParent !== null);

            let lyricsEl = null, styleEl = null, titleEl = null, negEl = null;
            for (const el of fields) {{
                const hint = (
                    (el.placeholder || '') + ' ' +
                    (el.getAttribute('aria-label') || '') + ' ' +
                    (el.name || '') + ' ' +
                    (el.id || '')
                ).toLowerCase();

                if (!lyricsEl && el.tagName === 'TEXTAREA' && /lyric|write your own|enter your own|verse|song words/i.test(hint)) {{
                    lyricsEl = el;
                }} else if (!styleEl && /style|genre|vibe|describe the style|sound/i.test(hint)) {{
                    styleEl = el;
                }} else if (!titleEl && /title|name your song|song name/i.test(hint)) {{
                    titleEl = el;
                }} else if (!negEl && /exclude|negative|avoid/i.test(hint)) {{
                    negEl = el;
                }}
            }}

            // Fallback heuristic by textarea order on suno.com/create (Lyrics = largest/first textarea, Style = second)
            const textareas = fields.filter(el => el.tagName === 'TEXTAREA');
            if (!lyricsEl && textareas.length >= 1) lyricsEl = textareas[0];
            if (!styleEl && textareas.length >= 2) styleEl = textareas[1];

            let filled = [];
            if ((data.mode === 'all' || data.mode === 'title') && data.title && setReactValue(titleEl, data.title)) filled.push('title');
            if ((data.mode === 'all' || data.mode === 'style') && data.style && setReactValue(styleEl, data.style)) filled.push('style');
            if ((data.mode === 'all' || data.mode === 'lyrics') && data.lyrics && setReactValue(lyricsEl, data.lyrics)) filled.push('lyrics');
            if ((data.mode === 'all' || data.mode === 'negative') && data.negative && setReactValue(negEl, data.negative)) filled.push('negative');
            return filled.join(',') || 'copied_fallback';
        }})();
        """

    def _prepared_style_text(self) -> str:
        raw_style = self.txt_style.toPlainText().strip()
        if self.chk_auto_fit_style.isChecked() and raw_style:
            limit = self._get_engine_char_limit()
            if len(raw_style) > limit:
                fitted = self._fit_style_to_limit(raw_style, limit)
                self.txt_style.setPlainText(fitted)
                return fitted
        return raw_style

    def autofill_all_to_suno(self):
        """Inject Title, Style, Lyrics, and Exclude tags into the embedded Suno page in 1 click."""
        self.ensure_browser_initialized()
        title = self.txt_title.text().strip()
        style = self._prepared_style_text()
        lyrics = self.txt_lyrics.toPlainText().strip()
        negative = self.txt_negative.text().strip()

        # Always copy lyrics to clipboard as immediate paste ready backup
        if lyrics:
            QApplication.clipboard().setText(lyrics)

        js = self._build_autofill_js(title, style, lyrics, negative, mode="all")
        self._last_js_executed = js

        if self.web_page is not None:
            self.web_page.runJavaScript(js, self._on_js_autofill_result)
        else:
            self.lbl_download_status.setText("⚡ Auto-Fill payload prepared & Lyrics copied to clipboard!")

        orig = self.btn_autofill_all.text()
        self.btn_autofill_all.setText("✓ Injected into Suno & Copied!")
        QTimer.singleShot(1600, lambda: self.btn_autofill_all.setText(orig))

    def _inject_single_field(self, field_mode: str):
        self.ensure_browser_initialized()
        title = self.txt_title.text().strip()
        style = self._prepared_style_text()
        lyrics = self.txt_lyrics.toPlainText().strip()
        negative = self.txt_negative.text().strip()

        clip_map = {
            "title": title,
            "style": style,
            "lyrics": lyrics,
            "negative": negative,
            "focused": lyrics or style or title,
        }
        clip_val = clip_map.get(field_mode, "")
        if clip_val:
            QApplication.clipboard().setText(clip_val)

        js = self._build_autofill_js(title, style, lyrics, negative, mode=field_mode)
        self._last_js_executed = js
        if self.web_page is not None:
            self.web_page.runJavaScript(js, self._on_js_autofill_result)
        else:
            self.lbl_download_status.setText(f"✓ Copied & prepared '{field_mode}' for Suno!")

    def _on_js_autofill_result(self, result):
        res_str = str(result or "")
        if res_str and res_str not in ("copied_fallback", "no_focus"):
            self.lbl_download_status.setText(f"⚡ Auto-filled Suno fields: {res_str} (also copied to clipboard)")
        else:
            self.lbl_download_status.setText("📋 Copied to clipboard! Click target box in Suno and press Ctrl+V.")

    # ── 5-Theme Adaptive Styling ──
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
            SunoBrowserView {{ background-color: {bg}; color: {pri}; }}
            QFrame#sunoNavBar, QFrame#sunoDockCard, QFrame#sunoBrowserContainer {{
                background-color: {card};
                border: 1px solid {border};
                border-radius: 8px;
            }}
            QFrame#sunoQueueNavFrame, QFrame#sunoDownloadFrame {{
                background-color: {inp};
                border: 1px solid {border};
                border-radius: 6px;
            }}
            QLabel {{ color: {pri}; background: transparent; border: none; }}
            QLineEdit, QPlainTextEdit, QComboBox {{
                background-color: {inp};
                color: {pri};
                border: 1px solid {border};
                border-radius: 5px;
                padding: 3px 6px;
                font-size: 10.5px;
            }}
        """)

        btn_qss = (
            f"background: {t['bg_btn']}; color: {pri}; border: 1px solid {border}; border-radius: 5px; font-weight: 700; font-size: 10px; padding: 2px 7px;"
            if is_dark else
            "background: #ffffff; color: #0f172a; border: 1px solid #cbd5e1; border-radius: 5px; font-weight: 700; font-size: 10px; padding: 2px 7px;"
        )
        for b in [
            self.btn_toggle_dock, self.btn_nav_create, self.btn_nav_library, self.btn_nav_account,
            self.btn_nav_reload, self.btn_zoom_out, self.btn_zoom_in, self.btn_open_ext,
            self.btn_download_link, self.btn_float_hud, self.btn_sync_from_studio, self.btn_prev, self.btn_next,
            self.btn_fill_title, self.btn_fill_style, self.btn_fill_lyrics, self.btn_fill_neg,
            self.btn_fill_focused, self.btn_open_dl_folder, self.btn_load_dl_to_editor,
            self.btn_paste_quick_dl, self.btn_quick_dl, self.btn_open_full_dl,
        ]:
            if hasattr(self, b.__repr__() if False else "") or b is not None:
                b.setStyleSheet(btn_qss)

        self.btn_autofill_all.setStyleSheet(
            f"background: {acc_grad}; color: #ffffff; border: 1px solid {t['border_accent']}; border-radius: 6px; font-weight: 800; font-size: 11px;"
        )
        self.btn_mark_done.setStyleSheet(
            "background: #065f46; color: #ecfdf5; border: 1px solid #10b981; border-radius: 6px; font-weight: 800; font-size: 10.5px;"
            if is_dark else
            "background: #16a34a; color: #ffffff; border: 1px solid #15803d; border-radius: 6px; font-weight: 800; font-size: 10.5px;"
        )
        self.lbl_account_credits.setStyleSheet(
            f"font-size: 10px; font-weight: 800; padding: 2px 7px; border-radius: 5px; background: {t['subtle_pill_bg']}; color: {t['text_accent']}; border: 1px solid {t['border_accent']};"
        )
        self.lbl_style_tag.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {sec};")
        self.lbl_lyrics_tag.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {sec};")
        self.lbl_download_status.setStyleSheet(f"font-size: 9.5px; font-weight: 600; color: {acc};")
        self.refresh_account_badge()
