"""
8th Studio Tab (Mode 7): DistroKid & TuneCore Single & Album Auto-Upload Studio.

Provides a clean, English-focused split-screen workstation:
- Top Bar: Distributor Switcher (DistroKid | TuneCore), Persistent Multi-Account Profile Selector,
  Quick Portal Shortcuts (New Upload, My Releases, Store Lyrics, Royalties), URL Bar, Zoom & Full Screen.
- Left Release Builder Dock (Clean 3-Step Tabs + Pinned 1-2 Upload Footer):
  * Mode Switcher: Single Song (1 Track) vs. Full Album / EP (2-30 Tracks)
  * 1-Click Studio Sync: Pull from Mastered Queue, Batch Album, or Active Lyric Editor
  * Step 1 Tab (Release & Cover): Metadata, Real Legal Songwriter Name, & 3000x3000 RGB Cover Generator
  * Step 2 Tab (Tracklist & Audio): Tracklist Table, 24-bit WAV Attacher, & Apple/Spotify Clean Store Lyrics
  * Step 3 Tab (Store QC Report): Live 100-Point Pre-Flight Validator & Staged Folder Inspector
  * Pinned Action Footer: [Step 1: Build Staged Release Pack] -> [Step 2: Auto-Fill Upload Form]
- Right Pane: Embedded Chromium QWebEngineView with persistent login cookies where the user signs in
  directly to their own DistroKid or TuneCore account, auto-fills form fields, attaches staged files,
  and reviews before publishing.
"""

from __future__ import annotations

import datetime
import os
import re
from pathlib import Path
from typing import Dict, List, Optional

from PIL.ImageQt import ImageQt
from PyQt6.QtCore import Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices, QPixmap
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.config import config_manager
from app.cover_art_generator import STYLE_PRESETS
from app.distro_packager import (
    DISTRO_GENRES,
    DISTRO_LANGUAGES,
    DISTRO_PLATFORMS,
    DistroAutoFillBuilder,
    DistroPreflightValidator,
    DistroStagePackager,
    clean_lyrics_for_stores,
    generate_store_cover_3000,
    inspect_audio_file_quick,
    normalize_image_to_store_3000,
    validate_cover_art,
)
from app.ui.styles import get_theme


class DistroUploadView(QWidget):
    """Mode 7 Studio Tab: DistroKid & TuneCore Single & Album Auto-Upload Workstation."""

    pull_from_master_requested = pyqtSignal()
    pull_from_batch_requested = pyqtSignal()
    pull_from_editor_requested = pyqtSignal()
    toggle_fullscreen_requested = pyqtSignal(bool)

    def __init__(self, parent: Optional[QWidget] = None, theme_key: str = "obsidian"):
        super().__init__(parent)
        self.theme_key = theme_key
        self.current_platform: str = config_manager.get("distro_active_platform", "DistroKid")
        if self.current_platform not in DISTRO_PLATFORMS:
            self.current_platform = "DistroKid"

        self.release_mode: str = "single"  # "single" or "album"
        self.account_slots: List[str] = [
            "Account 1 (Main Artist)",
            "Account 2 (Label / Alias)",
            "Account 3 (Client Release)",
        ]
        self.current_account_slot: str = config_manager.get("distro_active_account_slot", self.account_slots[0])
        if self.current_account_slot not in self.account_slots:
            self.current_account_slot = self.account_slots[0]

        self.tracks: List[Dict[str, object]] = [
            {
                "title": "Midnight Neon Lights",
                "audio_path": "",
                "lyrics": (
                    "Streetlights flicker on the wet windshield glass\n"
                    "Every mile marker lets the old doubts pass\n\n"
                    "Underneath the midnight neon lights\n"
                    "We are turning broken yesterdays to flights"
                ),
                "featured_artist": "",
                "isrc": "",
                "explicit": False,
                "instrumental": False,
            }
        ]
        self.selected_track_idx: int = 0
        self.cover_path: str = ""
        self.last_stage_dir: str = ""
        self._last_js_executed: str = ""
        self._updating_track_fields: bool = False

        self.web_view = None
        self.web_profile = None
        self.web_page = None
        self._browser_initialized: bool = False
        self._zoom_factor: float = 1.0
        self._is_fullscreen_active: bool = False
        self._pre_fs_dock_visible: bool = True

        self._setup_ui()
        self._ensure_default_cover()
        self._refresh_track_table()
        self._load_track_into_inspector(0)
        self.run_preflight_qc()
        self.apply_theme(self.theme_key)

    def _profile_dir(self, slot_name: str) -> Path:
        safe = re.sub(r"[^a-zA-Z0-9_-]+", "_", slot_name).strip("_") or "default"
        base = Path.home() / ".lyric_ai_writer" / "distro_profiles" / safe
        base.mkdir(parents=True, exist_ok=True)
        return base

    def _default_cover_cache_path(self) -> Path:
        d = Path.home() / ".lyric_ai_writer" / "distro_covers"
        d.mkdir(parents=True, exist_ok=True)
        return d / "Preview_Cover_3000x3000.jpg"

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(6, 4, 6, 6)
        root.setSpacing(5)

        # ── 1. Top Distributor, Account & Portal Bar ──
        self.nav_bar = QFrame()
        self.nav_bar.setObjectName("distroNavBar")
        self.nav_bar.setFixedHeight(38)
        nav = QHBoxLayout(self.nav_bar)
        nav.setContentsMargins(8, 4, 8, 4)
        nav.setSpacing(5)

        self.btn_toggle_dock = QPushButton("◀ Dock")
        self.btn_toggle_dock.setCheckable(True)
        self.btn_toggle_dock.setChecked(True)
        self.btn_toggle_dock.setFixedHeight(26)
        self.btn_toggle_dock.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_dock.setToolTip("Collapse or expand the Release Builder dock")
        self.btn_toggle_dock.clicked.connect(self._toggle_left_dock)
        nav.addWidget(self.btn_toggle_dock)

        # Platform Selector Pills (DistroKid | TuneCore)
        self.btn_plat_distrokid = QPushButton("🟦 DistroKid")
        self.btn_plat_distrokid.setCheckable(True)
        self.btn_plat_distrokid.setChecked(self.current_platform == "DistroKid")
        self.btn_plat_distrokid.setFixedHeight(26)
        self.btn_plat_distrokid.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_plat_distrokid.setToolTip("Switch portal & auto-fill target to DistroKid (Single & Album Upload)")
        self.btn_plat_distrokid.clicked.connect(lambda: self.set_platform("DistroKid"))
        nav.addWidget(self.btn_plat_distrokid)

        self.btn_plat_tunecore = QPushButton("🟪 TuneCore")
        self.btn_plat_tunecore.setCheckable(True)
        self.btn_plat_tunecore.setChecked(self.current_platform == "TuneCore")
        self.btn_plat_tunecore.setFixedHeight(26)
        self.btn_plat_tunecore.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_plat_tunecore.setToolTip("Switch portal & auto-fill target to TuneCore (Single & Album Upload)")
        self.btn_plat_tunecore.clicked.connect(lambda: self.set_platform("TuneCore"))
        nav.addWidget(self.btn_plat_tunecore)

        # Persistent Multi-Account Profile Selector
        self.combo_account_slot = QComboBox()
        self.combo_account_slot.setFixedHeight(26)
        self.combo_account_slot.setMinimumWidth(165)
        self.combo_account_slot.addItems(self.account_slots)
        self.combo_account_slot.setCurrentText(self.current_account_slot)
        self.combo_account_slot.setToolTip(
            "Persistent Browser Login Profile: stay signed into DistroKid & TuneCore across restarts"
        )
        self.combo_account_slot.currentTextChanged.connect(self._on_account_slot_changed)
        nav.addWidget(self.combo_account_slot)

        # Quick Portal Buttons
        self.btn_portal_upload = QPushButton("➕ New Upload")
        self.btn_portal_upload.setFixedHeight(26)
        self.btn_portal_upload.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_portal_upload.setToolTip("Open New Single / Album Upload page on active distributor")
        self.btn_portal_upload.clicked.connect(lambda: self._open_portal_section("new_upload_url"))
        nav.addWidget(self.btn_portal_upload)

        self.btn_portal_releases = QPushButton("💿 Releases")
        self.btn_portal_releases.setFixedHeight(26)
        self.btn_portal_releases.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_portal_releases.setToolTip("View uploaded Singles & Albums discography")
        self.btn_portal_releases.clicked.connect(lambda: self._open_portal_section("releases_url"))
        nav.addWidget(self.btn_portal_releases)

        self.btn_portal_lyrics = QPushButton("📝 Lyrics")
        self.btn_portal_lyrics.setFixedHeight(26)
        self.btn_portal_lyrics.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_portal_lyrics.setToolTip("Open Store Lyrics / Synced Karaoke page")
        self.btn_portal_lyrics.clicked.connect(lambda: self._open_portal_section("lyrics_url"))
        nav.addWidget(self.btn_portal_lyrics)

        self.btn_portal_royalties = QPushButton("💰 Royalties")
        self.btn_portal_royalties.setFixedHeight(26)
        self.btn_portal_royalties.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_portal_royalties.setToolTip("Open Royalties & Earnings dashboard")
        self.btn_portal_royalties.clicked.connect(lambda: self._open_portal_section("royalties_url"))
        nav.addWidget(self.btn_portal_royalties)

        # URL Bar & Reload
        self.txt_url = QLineEdit(DISTRO_PLATFORMS[self.current_platform]["new_upload_url"])
        self.txt_url.setFixedHeight(26)
        self.txt_url.returnPressed.connect(lambda: self.navigate_to(self.txt_url.text().strip()))
        nav.addWidget(self.txt_url, stretch=1)

        self.btn_reload = QPushButton("↻")
        self.btn_reload.setFixedSize(26, 26)
        self.btn_reload.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_reload.setToolTip("Reload page")
        self.btn_reload.clicked.connect(self._reload_page)
        nav.addWidget(self.btn_reload)

        self.btn_zoom_out = QPushButton("−")
        self.btn_zoom_out.setFixedSize(24, 26)
        self.btn_zoom_out.clicked.connect(lambda: self._adjust_zoom(-0.1))
        nav.addWidget(self.btn_zoom_out)

        self.lbl_zoom = QLabel("100%")
        self.lbl_zoom.setFixedWidth(36)
        self.lbl_zoom.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_zoom.setStyleSheet("font-size: 10px; font-weight: 700;")
        nav.addWidget(self.lbl_zoom)

        self.btn_zoom_in = QPushButton("+")
        self.btn_zoom_in.setFixedSize(24, 26)
        self.btn_zoom_in.clicked.connect(lambda: self._adjust_zoom(0.1))
        nav.addWidget(self.btn_zoom_in)

        self.btn_ext_browser = QPushButton("↗ Browser")
        self.btn_ext_browser.setFixedHeight(26)
        self.btn_ext_browser.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ext_browser.setToolTip("Open current distributor page in external system browser")
        self.btn_ext_browser.clicked.connect(self._open_external_browser)
        nav.addWidget(self.btn_ext_browser)

        self.btn_fullscreen = QPushButton("⛶ Full Screen")
        self.btn_fullscreen.setFixedHeight(26)
        self.btn_fullscreen.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_fullscreen.setToolTip("Toggle Full Screen for Distributor Browser [F11 / Esc]")
        self.btn_fullscreen.clicked.connect(self._toggle_fullscreen_view)
        nav.addWidget(self.btn_fullscreen)

        root.addWidget(self.nav_bar)

        # ── 2. Split Workbench: Left Clean Release Builder | Right Embedded Browser ──
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        self.dock_card = QFrame()
        self.dock_card.setObjectName("distroDockCard")
        self.dock_card.setMinimumWidth(445)
        self.dock_card.setMaximumWidth(520)
        d_lay = QVBoxLayout(self.dock_card)
        d_lay.setContentsMargins(10, 8, 10, 8)
        d_lay.setSpacing(6)

        # Release Mode Switcher: Single Song vs. Full Album / EP
        mode_row = QHBoxLayout()
        mode_row.setSpacing(6)
        self.btn_mode_single = QPushButton("🎵 Single Song (1 Track)")
        self.btn_mode_single.setCheckable(True)
        self.btn_mode_single.setChecked(True)
        self.btn_mode_single.setFixedHeight(30)
        self.btn_mode_single.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mode_single.setToolTip("Prepare & auto-fill a 1-track Single release")
        self.btn_mode_single.clicked.connect(lambda: self.set_release_mode("single"))
        mode_row.addWidget(self.btn_mode_single, stretch=1)

        self.btn_mode_album = QPushButton("💿 Album / EP (2–30 Tracks)")
        self.btn_mode_album.setCheckable(True)
        self.btn_mode_album.setChecked(False)
        self.btn_mode_album.setFixedHeight(30)
        self.btn_mode_album.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mode_album.setToolTip("Prepare & auto-fill a multi-track EP (2–6 tracks) or Album (7–30 tracks)")
        self.btn_mode_album.clicked.connect(lambda: self.set_release_mode("album"))
        mode_row.addWidget(self.btn_mode_album, stretch=1)
        d_lay.addLayout(mode_row)

        # Quick Pull from Studio Bar
        sync_row = QHBoxLayout()
        sync_row.setSpacing(4)
        lbl_pull = QLabel("Import:")
        lbl_pull.setStyleSheet("font-size: 10px; font-weight: 800;")
        sync_row.addWidget(lbl_pull)

        self.btn_pull_master = QPushButton("🎛️ Master Queue")
        self.btn_pull_master.setFixedHeight(24)
        self.btn_pull_master.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_pull_master.setToolTip("Import mastered single or album queue from Mode 6 Mastering Studio")
        self.btn_pull_master.clicked.connect(self.pull_from_master_requested.emit)
        sync_row.addWidget(self.btn_pull_master, stretch=1)

        self.btn_pull_batch = QPushButton("⚡ Batch Album")
        self.btn_pull_batch.setFixedHeight(24)
        self.btn_pull_batch.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_pull_batch.setToolTip("Import multi-song album tracklist & lyrics from Mode 2 Batch Studio")
        self.btn_pull_batch.clicked.connect(self.pull_from_batch_requested.emit)
        sync_row.addWidget(self.btn_pull_batch, stretch=1)

        self.btn_pull_editor = QPushButton("✍️ Editor Song")
        self.btn_pull_editor.setFixedHeight(24)
        self.btn_pull_editor.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_pull_editor.setToolTip("Import active song title, audio stem & clean lyrics from Mode 3 Editor")
        self.btn_pull_editor.clicked.connect(self.pull_from_editor_requested.emit)
        sync_row.addWidget(self.btn_pull_editor, stretch=1)
        d_lay.addLayout(sync_row)

        # Clean 3-Step Sub-Tabs (All 3 Always Visible — Zero Scroll Arrows!)
        self.dock_tabs = QTabWidget()
        self.dock_tabs.setUsesScrollButtons(False)
        self.dock_tabs.addTab(self._build_step1_release_tab(), "1. Release && Art")
        self.dock_tabs.addTab(self._build_step2_tracklist_tab(), "2. Tracks && Audio")
        self.dock_tabs.addTab(self._build_step3_qc_tab(), "3. QC (100%)")
        d_lay.addWidget(self.dock_tabs, stretch=1)

        # ── Pinned 1-2-3 Upload Action Footer (Always Visible) ──
        self.action_footer = QFrame()
        self.action_footer.setObjectName("distroActionFooter")
        af_lay = QVBoxLayout(self.action_footer)
        af_lay.setContentsMargins(8, 7, 8, 7)
        af_lay.setSpacing(5)

        self.btn_build_stage = QPushButton("📦 Step 1: Build Staged Release Pack (24-bit WAV + 3000px Cover)")
        self.btn_build_stage.setFixedHeight(32)
        self.btn_build_stage.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_build_stage.setToolTip(
            "Validates metadata, generates/verifies 3000x3000 RGB Cover Art, masters tracks to 24-bit WAV, "
            "cleans store lyrics, and copies the folder path to your clipboard"
        )
        self.btn_build_stage.clicked.connect(self.build_staged_release_pack)
        af_lay.addWidget(self.btn_build_stage)

        self.btn_autofill_form = QPushButton("⚡ Step 2: Auto-Fill DistroKid Upload Form (Single)")
        self.btn_autofill_form.setFixedHeight(34)
        self.btn_autofill_form.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_autofill_form.setToolTip(
            "Automatically populates Artist, Release Title, Genre, Release Date, Legal Songwriter, "
            "and Track Titles on the open DistroKid / TuneCore upload form"
        )
        self.btn_autofill_form.clicked.connect(self.autofill_active_portal_form)
        af_lay.addWidget(self.btn_autofill_form)

        sub_act_row = QHBoxLayout()
        sub_act_row.setSpacing(5)
        self.btn_autofill_lyrics = QPushButton("📝 Auto-Fill Store Lyrics")
        self.btn_autofill_lyrics.setFixedHeight(25)
        self.btn_autofill_lyrics.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_autofill_lyrics.setToolTip("Inject clean plain-text lyrics (no [Tags]) into open store lyrics box & copy")
        self.btn_autofill_lyrics.clicked.connect(self.autofill_current_track_lyrics)
        sub_act_row.addWidget(self.btn_autofill_lyrics, stretch=1)

        self.btn_open_folder_bottom = QPushButton("📂 Open Staged Folder")
        self.btn_open_folder_bottom.setFixedHeight(25)
        self.btn_open_folder_bottom.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open_folder_bottom.setToolTip("Open the staged release folder containing 3000x3000 Cover & 24-bit WAVs")
        self.btn_open_folder_bottom.clicked.connect(self._open_staged_folder)
        sub_act_row.addWidget(self.btn_open_folder_bottom, stretch=1)
        af_lay.addLayout(sub_act_row)

        self.lbl_status = QLabel("✅ Ready • Sign into DistroKid or TuneCore on the right, then click Step 1 & Step 2")
        self.lbl_status.setWordWrap(True)
        self.lbl_status.setStyleSheet("font-size: 9.5px; font-weight: 700;")
        af_lay.addWidget(self.lbl_status)

        d_lay.addWidget(self.action_footer)

        # ── Right Pane: Embedded Distributor Browser ──
        self.browser_container = QFrame()
        self.browser_container.setObjectName("distroBrowserContainer")
        self.browser_layout = QVBoxLayout(self.browser_container)
        self.browser_layout.setContentsMargins(0, 0, 0, 0)
        self.browser_layout.setSpacing(0)

        self.lbl_browser_placeholder = QLabel(
            f"🚀 Embedded {self.current_platform} Upload Browser\n\n"
            f"Persistent Login Profile: {self.current_account_slot}\n"
            f"Sign into your {self.current_platform} account here to upload Singles & Full Albums."
        )
        self.lbl_browser_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_browser_placeholder.setStyleSheet("font-size: 13px; font-weight: 700; padding: 24px;")
        self.browser_layout.addWidget(self.lbl_browser_placeholder)

        # Floating Overlay Bar for Full Screen Mode
        self.floating_fs_bar = QFrame(self.browser_container)
        self.floating_fs_bar.setObjectName("distroFloatingFsBar")
        fs_lay = QHBoxLayout(self.floating_fs_bar)
        fs_lay.setContentsMargins(10, 4, 10, 4)
        fs_lay.setSpacing(8)

        self.lbl_fs_info = QLabel("🚀 Distro Upload Full Screen")
        self.lbl_fs_info.setStyleSheet("color: #38bdf8; font-weight: 800; font-size: 11px;")
        fs_lay.addWidget(self.lbl_fs_info)

        self.btn_fs_toggle_dock = QPushButton("◀ Show Dock")
        self.btn_fs_toggle_dock.setFixedHeight(24)
        self.btn_fs_toggle_dock.clicked.connect(self._toggle_left_dock)
        fs_lay.addWidget(self.btn_fs_toggle_dock)

        self.btn_fs_autofill = QPushButton("⚡ Auto-Fill Form")
        self.btn_fs_autofill.setFixedHeight(24)
        self.btn_fs_autofill.clicked.connect(self.autofill_active_portal_form)
        fs_lay.addWidget(self.btn_fs_autofill)

        self.btn_fs_exit = QPushButton("⛷️ Exit Full Screen (Esc / F11)")
        self.btn_fs_exit.setFixedHeight(24)
        self.btn_fs_exit.clicked.connect(self._exit_fullscreen_view)
        fs_lay.addWidget(self.btn_fs_exit)
        self.floating_fs_bar.hide()

        self.splitter.addWidget(self.dock_card)
        self.splitter.addWidget(self.browser_container)
        self.splitter.setCollapsible(0, True)
        self.splitter.setCollapsible(1, False)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([455, 895])

        root.addWidget(self.splitter, stretch=1)
        self._update_autofill_button_label()

    def _build_step1_release_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.setSpacing(6)

        grid = QGridLayout()
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(5)

        self.lbl_release_title = QLabel("Single Title:")
        self.lbl_release_title.setStyleSheet("font-size: 10px; font-weight: 700;")
        self.txt_release_title = QLineEdit("Midnight Neon Lights")
        self.txt_release_title.setPlaceholderText("Song Title (Single) or Album / EP Title...")
        self.txt_release_title.textChanged.connect(self._on_release_title_edited)
        grid.addWidget(self.lbl_release_title, 0, 0)
        grid.addWidget(self.txt_release_title, 0, 1, 1, 3)

        lbl_art = QLabel("Artist / Band:")
        lbl_art.setStyleSheet("font-size: 10px; font-weight: 700;")
        self.txt_artist_name = QLineEdit("SMG Studio Artist")
        self.txt_artist_name.setPlaceholderText("Stage / Artist / Band Name...")
        self.txt_artist_name.textChanged.connect(lambda _: self.run_preflight_qc())
        grid.addWidget(lbl_art, 1, 0)
        grid.addWidget(self.txt_artist_name, 1, 1, 1, 3)

        lbl_sw = QLabel("Legal Writer:")
        lbl_sw.setStyleSheet("font-size: 10px; font-weight: 700;")
        lbl_sw.setToolTip("DistroKid & TuneCore require the songwriter's REAL legal First & Last Name (no stage names)")
        self.txt_sw_first = QLineEdit("Alex")
        self.txt_sw_first.setPlaceholderText("Legal First Name")
        self.txt_sw_first.textChanged.connect(lambda _: self.run_preflight_qc())
        self.txt_sw_last = QLineEdit("Rivers")
        self.txt_sw_last.setPlaceholderText("Legal Last Name")
        self.txt_sw_last.textChanged.connect(lambda _: self.run_preflight_qc())
        grid.addWidget(lbl_sw, 2, 0)
        grid.addWidget(self.txt_sw_first, 2, 1)
        grid.addWidget(self.txt_sw_last, 2, 2, 1, 2)

        lbl_gen = QLabel("Genre / Lang:")
        lbl_gen.setStyleSheet("font-size: 10px; font-weight: 700;")
        self.combo_genre = QComboBox()
        self.combo_genre.addItems(DISTRO_GENRES)
        self.combo_language = QComboBox()
        self.combo_language.addItems(DISTRO_LANGUAGES)
        self.combo_language.setCurrentText("English")
        grid.addWidget(lbl_gen, 3, 0)
        grid.addWidget(self.combo_genre, 3, 1, 1, 2)
        grid.addWidget(self.combo_language, 3, 3)

        default_date = (datetime.date.today() + datetime.timedelta(days=7)).isoformat()
        lbl_dt = QLabel("Date / Label:")
        lbl_dt.setStyleSheet("font-size: 10px; font-weight: 700;")
        self.txt_release_date = QLineEdit(default_date)
        self.txt_release_date.setPlaceholderText("YYYY-MM-DD")
        self.txt_record_label = QLineEdit("SMG Independent Records")
        self.txt_record_label.setPlaceholderText("Record Label / Copyright Holder")
        grid.addWidget(lbl_dt, 4, 0)
        grid.addWidget(self.txt_release_date, 4, 1)
        grid.addWidget(self.txt_record_label, 4, 2, 1, 2)

        lay.addLayout(grid)

        flags_row = QHBoxLayout()
        flags_row.setSpacing(8)
        self.chk_explicit = QCheckBox("Explicit Lyrics")
        self.chk_explicit.setChecked(False)
        self.chk_auto_master = QCheckBox("Auto-Master Tracks to 24-bit -14 LUFS WAV")
        self.chk_auto_master.setChecked(True)
        self.chk_auto_master.setToolTip("Automatically renders attached MP3/WAV tracks to store-ready 24-bit 44.1kHz Stereo WAV")
        flags_row.addWidget(self.chk_explicit)
        flags_row.addWidget(self.chk_auto_master, stretch=1)
        lay.addLayout(flags_row)

        # 3000x3000 Store-Compliant Cover Art Card
        self.cover_card = QFrame()
        self.cover_card.setObjectName("distroCoverCard")
        cc_lay = QHBoxLayout(self.cover_card)
        cc_lay.setContentsMargins(8, 8, 8, 8)
        cc_lay.setSpacing(10)

        self.lbl_cover_thumb = QLabel("3000×3000\nRGB")
        self.lbl_cover_thumb.setFixedSize(96, 96)
        self.lbl_cover_thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_cover_thumb.setStyleSheet(
            "border: 1px solid #38bdf8; border-radius: 8px; font-size: 10px; font-weight: 800;"
        )
        cc_lay.addWidget(self.lbl_cover_thumb)

        cov_right = QVBoxLayout()
        cov_right.setSpacing(4)
        lbl_cov_hdr = QLabel("🖼️ Store Cover Art (Strict 3000×3000 RGB • Zero Store Badges)")
        lbl_cov_hdr.setWordWrap(True)
        lbl_cov_hdr.setStyleSheet("font-size: 10px; font-weight: 800;")
        cov_right.addWidget(lbl_cov_hdr)

        self.combo_cover_style = QComboBox()
        for s_key, s_info in STYLE_PRESETS.items():
            self.combo_cover_style.addItem(s_info["name"], s_key)
        cov_right.addWidget(self.combo_cover_style)

        cov_btns = QHBoxLayout()
        cov_btns.setSpacing(4)
        self.btn_gen_cover = QPushButton("🎨 Generate 3000px")
        self.btn_gen_cover.setFixedHeight(25)
        self.btn_gen_cover.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_gen_cover.clicked.connect(self._generate_3000_cover)
        cov_btns.addWidget(self.btn_gen_cover)

        self.btn_browse_cover = QPushButton("📂 Browse Image")
        self.btn_browse_cover.setFixedHeight(25)
        self.btn_browse_cover.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_browse_cover.setToolTip("Select any JPG/PNG and auto-fit to exact 3000×3000 RGB")
        self.btn_browse_cover.clicked.connect(self._browse_and_fit_cover)
        cov_btns.addWidget(self.btn_browse_cover)
        cov_right.addLayout(cov_btns)

        self.lbl_cover_status = QLabel("✅ Verified 3000×3000 px RGB")
        self.lbl_cover_status.setWordWrap(True)
        self.lbl_cover_status.setStyleSheet("font-size: 9.5px; font-weight: 700; color: #10b981;")
        cov_right.addWidget(self.lbl_cover_status)

        cc_lay.addLayout(cov_right, stretch=1)
        lay.addWidget(self.cover_card)
        lay.addStretch(1)
        return w

    def _build_step2_tracklist_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.setSpacing(5)

        top_bar = QHBoxLayout()
        top_bar.setSpacing(4)
        self.lbl_tracklist_banner = QLabel("🎵 Single Release: 1 Track")
        self.lbl_tracklist_banner.setStyleSheet("font-size: 10.5px; font-weight: 800;")
        top_bar.addWidget(self.lbl_tracklist_banner, stretch=1)

        self.btn_add_audio = QPushButton("+ Add Audio")
        self.btn_add_audio.setFixedHeight(23)
        self.btn_add_audio.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add_audio.setToolTip("Add WAV/MP3/FLAC file(s) to tracklist (2+ files automatically switch to Album/EP mode)")
        self.btn_add_audio.clicked.connect(self._browse_add_audio_tracks)
        top_bar.addWidget(self.btn_add_audio)

        self.btn_add_empty_track = QPushButton("+ Track")
        self.btn_add_empty_track.setFixedHeight(23)
        self.btn_add_empty_track.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add_empty_track.clicked.connect(self._add_blank_album_track)
        top_bar.addWidget(self.btn_add_empty_track)

        self.btn_move_up = QPushButton("▲")
        self.btn_move_up.setFixedSize(24, 23)
        self.btn_move_up.clicked.connect(lambda: self._move_selected_track(-1))
        top_bar.addWidget(self.btn_move_up)

        self.btn_move_down = QPushButton("▼")
        self.btn_move_down.setFixedSize(24, 23)
        self.btn_move_down.clicked.connect(lambda: self._move_selected_track(1))
        top_bar.addWidget(self.btn_move_down)

        self.btn_remove_track = QPushButton("✕")
        self.btn_remove_track.setFixedSize(24, 23)
        self.btn_remove_track.setToolTip("Remove selected track")
        self.btn_remove_track.clicked.connect(self._remove_selected_track)
        top_bar.addWidget(self.btn_remove_track)
        lay.addLayout(top_bar)

        self.table_tracks = QTableWidget(0, 4)
        self.table_tracks.setHorizontalHeaderLabels(["#", "Track Title", "WAV", "Lyrics"])
        self.table_tracks.verticalHeader().setVisible(False)
        self.table_tracks.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_tracks.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_tracks.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_tracks.setFixedHeight(118)
        hdr = self.table_tracks.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table_tracks.setColumnWidth(0, 28)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table_tracks.setColumnWidth(2, 68)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table_tracks.setColumnWidth(3, 68)
        self.table_tracks.itemSelectionChanged.connect(self._on_track_selection_changed)
        lay.addWidget(self.table_tracks)

        # Selected Track Editor
        tr_grid = QGridLayout()
        tr_grid.setHorizontalSpacing(5)
        tr_grid.setVerticalSpacing(4)
        tr_grid.setColumnStretch(1, 1)

        tr_grid.addWidget(QLabel("Track Title:"), 0, 0)
        self.txt_track_title = QLineEdit()
        self.txt_track_title.setPlaceholderText("Track Title...")
        self.txt_track_title.textChanged.connect(self._on_inspector_track_edited)
        tr_grid.addWidget(self.txt_track_title, 0, 1)

        self.txt_track_isrc = QLineEdit()
        self.txt_track_isrc.setPlaceholderText("ISRC Opt.")
        self.txt_track_isrc.setFixedWidth(90)
        self.txt_track_isrc.textChanged.connect(self._on_inspector_track_edited)
        tr_grid.addWidget(self.txt_track_isrc, 0, 2)

        tr_grid.addWidget(QLabel("Audio File:"), 1, 0)
        self.txt_track_audio = QLineEdit()
        self.txt_track_audio.setPlaceholderText("Attach mastered .wav / .mp3 file...")
        self.txt_track_audio.textChanged.connect(self._on_inspector_track_edited)
        tr_grid.addWidget(self.txt_track_audio, 1, 1)

        self.btn_attach_track_audio = QPushButton("📂 WAV/MP3")
        self.btn_attach_track_audio.setFixedHeight(24)
        self.btn_attach_track_audio.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_attach_track_audio.clicked.connect(self._attach_audio_for_selected_track)
        tr_grid.addWidget(self.btn_attach_track_audio, 1, 2)
        lay.addLayout(tr_grid)

        lyr_hdr = QHBoxLayout()
        lbl_lyr = QLabel("Store-Ready Plain Lyrics (No [Chorus] or [Chords]):")
        lbl_lyr.setStyleSheet("font-size: 9.5px; font-weight: 800;")
        lyr_hdr.addWidget(lbl_lyr, stretch=1)

        self.btn_clean_lyrics = QPushButton("🧹 Auto-Clean All Lyrics")
        self.btn_clean_lyrics.setFixedHeight(22)
        self.btn_clean_lyrics.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clean_lyrics.setToolTip("Strip [Verse], [Chorus], [Am] chords & punctuation for Apple Music / Spotify compliance")
        self.btn_clean_lyrics.clicked.connect(self.clean_all_track_lyrics)
        lyr_hdr.addWidget(self.btn_clean_lyrics)
        lay.addLayout(lyr_hdr)

        self.txt_track_lyrics = QPlainTextEdit()
        self.txt_track_lyrics.setPlaceholderText("Plain sung lyrics for Apple Music, Spotify, DistroKid & TuneCore...")
        self.txt_track_lyrics.textChanged.connect(self._on_inspector_track_edited)
        lay.addWidget(self.txt_track_lyrics, stretch=1)
        return w

    def _build_step3_qc_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.setSpacing(6)

        hdr_row = QHBoxLayout()
        self.lbl_qc_score = QLabel("🛡️ Store Pre-Flight Score: 100/100")
        self.lbl_qc_score.setStyleSheet("font-size: 11px; font-weight: 800;")
        hdr_row.addWidget(self.lbl_qc_score, stretch=1)

        self.btn_run_qc = QPushButton("🔄 Run QC Check")
        self.btn_run_qc.setFixedHeight(24)
        self.btn_run_qc.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_run_qc.clicked.connect(self.run_preflight_qc)
        hdr_row.addWidget(self.btn_run_qc)
        lay.addLayout(hdr_row)

        self.txt_qc_report = QTextEdit()
        self.txt_qc_report.setReadOnly(True)
        self.txt_qc_report.setStyleSheet("font-family: 'Consolas', monospace; font-size: 9.5px;")
        lay.addWidget(self.txt_qc_report, stretch=1)

        self.lbl_stage_path = QLabel("📁 Staged Release Folder: Not built yet (Click Step 1 below)")
        self.lbl_stage_path.setWordWrap(True)
        self.lbl_stage_path.setStyleSheet("font-size: 9.5px; font-weight: 700;")
        lay.addWidget(self.lbl_stage_path)

        st_btns = QHBoxLayout()
        st_btns.setSpacing(5)
        self.btn_copy_stage_path = QPushButton("📋 Copy Folder Path")
        self.btn_copy_stage_path.setFixedHeight(24)
        self.btn_copy_stage_path.clicked.connect(self._copy_stage_path)
        st_btns.addWidget(self.btn_copy_stage_path)

        self.btn_open_stage_dir = QPushButton("📂 Open Staged Folder")
        self.btn_open_stage_dir.setFixedHeight(24)
        self.btn_open_stage_dir.clicked.connect(self._open_staged_folder)
        st_btns.addWidget(self.btn_open_stage_dir)
        lay.addLayout(st_btns)
        return w

    # ── Cover Art Generation & Validation ──
    def _ensure_default_cover(self):
        cache_p = self._default_cover_cache_path()
        if not cache_p.exists():
            generate_store_cover_3000(
                title=self.txt_release_title.text().strip() or "Midnight Neon Lights",
                artist=self.txt_artist_name.text().strip() or "SMG Studio Artist",
                style_key="cyberpunk_neon",
                output_path=cache_p,
            )
        self._set_cover_file(str(cache_p))

    def _generate_3000_cover(self):
        style_key = self.combo_cover_style.currentData() or "cyberpunk_neon"
        out_p = self._default_cover_cache_path()
        generate_store_cover_3000(
            title=self.txt_release_title.text().strip() or "Untitled Release",
            artist=self.txt_artist_name.text().strip() or "Independent Artist",
            style_key=str(style_key),
            output_path=out_p,
        )
        self._set_cover_file(str(out_p))
        self.lbl_status.setText("🎨 Generated store-compliant 3000×3000 px RGB Cover Art (zero forbidden badges)")

    def _browse_and_fit_cover(self):
        fn, _ = QFileDialog.getOpenFileName(
            self,
            "Select Cover Image (Auto-Fits to 3000×3000 RGB)",
            str(Path.home()),
            "Images (*.jpg *.jpeg *.png *.webp *.bmp)",
        )
        if not fn:
            return
        out_p = Path.home() / ".lyric_ai_writer" / "distro_covers" / "Custom_Cover_3000x3000.jpg"
        normalize_image_to_store_3000(fn, out_p)
        self._set_cover_file(str(out_p))
        self.lbl_status.setText("✅ Image center-cropped and normalized to exact 3000×3000 px RGB")

    def _set_cover_file(self, path_str: str):
        self.cover_path = path_str
        info = validate_cover_art(path_str)
        if Path(path_str).exists():
            pix = QPixmap(path_str)
            if not pix.isNull():
                self.lbl_cover_thumb.setPixmap(
                    pix.scaled(
                        94,
                        94,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
        if info["ok"]:
            self.lbl_cover_status.setText(f"✅ {info['detail']}")
            self.lbl_cover_status.setStyleSheet("font-size: 9.5px; font-weight: 700; color: #10b981;")
        else:
            self.lbl_cover_status.setText(f"⚠️ {info['detail']}")
            self.lbl_cover_status.setStyleSheet("font-size: 9.5px; font-weight: 700; color: #f59e0b;")
        self.run_preflight_qc()

    # ── Single vs. Album Mode & Tracklist Management ──
    def set_release_mode(self, mode: str):
        mode = "album" if str(mode).lower() == "album" else "single"
        self.release_mode = mode
        self.btn_mode_single.setChecked(mode == "single")
        self.btn_mode_album.setChecked(mode == "album")
        self.lbl_release_title.setText("Single Title:" if mode == "single" else "Album / EP Title:")

        if mode == "album" and len(self.tracks) < 2:
            self.tracks.append({
                "title": "Electric Horizon",
                "audio_path": "",
                "lyrics": "Chasing electric horizons across the open sky\nNothing gonna dim the fire tonight",
                "featured_artist": "",
                "isrc": "",
                "explicit": False,
                "instrumental": False,
            })

        self._refresh_track_table()
        self._update_autofill_button_label()
        self.run_preflight_qc()

    def set_platform(self, platform_name: str):
        if platform_name not in DISTRO_PLATFORMS:
            return
        self.current_platform = platform_name
        config_manager.set("distro_active_platform", platform_name)
        self.btn_plat_distrokid.setChecked(platform_name == "DistroKid")
        self.btn_plat_tunecore.setChecked(platform_name == "TuneCore")
        target_url = DISTRO_PLATFORMS[platform_name]["new_upload_url"]
        self.txt_url.setText(target_url)
        if self._browser_initialized:
            if os.environ.get("QT_QPA_PLATFORM", "").lower() == "offscreen":
                self.lbl_browser_placeholder.setText(
                    f"🚀 Embedded {self.current_platform} Browser Ready ({self.current_account_slot})\nURL: {target_url}"
                )
            elif self.web_view is not None:
                self.web_view.setUrl(QUrl(target_url))
        else:
            self.lbl_browser_placeholder.setText(
                f"🚀 Embedded {self.current_platform} Upload Browser\n\n"
                f"Persistent Login Profile: {self.current_account_slot}\n"
                f"Sign into your {self.current_platform} account here to upload Singles & Full Albums."
            )
        self._update_autofill_button_label()
        self.run_preflight_qc()
        self.lbl_status.setText(f"🚀 Switched target store portal to {platform_name}")

    def _open_portal_section(self, url_key: str):
        info = DISTRO_PLATFORMS.get(self.current_platform, DISTRO_PLATFORMS["DistroKid"])
        url = info.get(url_key, info["new_upload_url"])
        self.navigate_to(url)

    def _update_autofill_button_label(self):
        visible_count = 1 if self.release_mode == "single" else len(self.tracks)
        fmt = "Single" if self.release_mode == "single" else f"Album • {visible_count} Tracks"
        self.btn_autofill_form.setText(f"⚡ Step 2: Auto-Fill {self.current_platform} Form ({fmt})")

    def _on_release_title_edited(self, text: str):
        if self.release_mode == "single" and self.tracks:
            self.tracks[0]["title"] = text.strip()
            if self.selected_track_idx == 0 and not self._updating_track_fields:
                self._updating_track_fields = True
                self.txt_track_title.setText(text.strip())
                self._updating_track_fields = False
            self._refresh_track_table()
        self.run_preflight_qc()

    def _visible_tracks(self) -> List[Dict[str, object]]:
        if self.release_mode == "single":
            return self.tracks[:1]
        return self.tracks

    def _refresh_track_table(self):
        vis = self._visible_tracks()
        fmt = DistroPreflightValidator.classify_release_format(len(vis), self.release_mode)
        self.lbl_tracklist_banner.setText(f"{'🎵' if self.release_mode == 'single' else '💿'} {fmt}")

        self.table_tracks.blockSignals(True)
        self.table_tracks.setRowCount(0)
        self.table_tracks.clearContents()
        self.table_tracks.setRowCount(len(vis))

        for r, tr in enumerate(vis):
            num_item = QTableWidgetItem(f"{r + 1:02d}")
            num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            title_item = QTableWidgetItem(str(tr.get("title", "")).strip() or f"Track {r + 1}")

            ap = str(tr.get("audio_path", "")).strip()
            if ap and Path(ap).exists():
                ext = Path(ap).suffix.upper().lstrip(".")
                aud_str = f"✓ {ext}"
            else:
                aud_str = "+ WAV"
            aud_item = QTableWidgetItem(aud_str)
            aud_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            lyr = str(tr.get("lyrics", "")).strip()
            if not lyr:
                lyr_str = "—"
            elif "[" in lyr or "]" in lyr:
                lyr_str = "Clean!"
            else:
                lyr_str = "✓ Ready"
            lyr_item = QTableWidgetItem(lyr_str)
            lyr_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self.table_tracks.setItem(r, 0, num_item)
            self.table_tracks.setItem(r, 1, title_item)
            self.table_tracks.setItem(r, 2, aud_item)
            self.table_tracks.setItem(r, 3, lyr_item)

        sel_row = min(max(0, self.selected_track_idx), max(0, len(vis) - 1))
        self.selected_track_idx = sel_row
        if len(vis) > 0:
            self.table_tracks.selectRow(sel_row)
        self.table_tracks.blockSignals(False)
        self._update_autofill_button_label()

    def _on_track_selection_changed(self):
        row = self.table_tracks.currentRow()
        if row >= 0:
            self._load_track_into_inspector(row)

    def _load_track_into_inspector(self, idx: int):
        vis = self._visible_tracks()
        if not vis or idx < 0 or idx >= len(vis):
            return
        self.selected_track_idx = idx
        tr = vis[idx]
        self._updating_track_fields = True
        self.txt_track_title.setText(str(tr.get("title", "")))
        self.txt_track_isrc.setText(str(tr.get("isrc", "")))
        self.txt_track_audio.setText(str(tr.get("audio_path", "")))
        self.txt_track_lyrics.setPlainText(str(tr.get("lyrics", "")))
        self._updating_track_fields = False

    def _on_inspector_track_edited(self):
        if self._updating_track_fields:
            return
        vis = self._visible_tracks()
        if not vis or self.selected_track_idx >= len(vis):
            return
        tr = self.tracks[self.selected_track_idx]
        tr["title"] = self.txt_track_title.text().strip()
        tr["isrc"] = self.txt_track_isrc.text().strip()
        tr["audio_path"] = self.txt_track_audio.text().strip()
        tr["lyrics"] = self.txt_track_lyrics.toPlainText()

        if self.release_mode == "single" and self.selected_track_idx == 0:
            self.txt_release_title.blockSignals(True)
            self.txt_release_title.setText(str(tr["title"]))
            self.txt_release_title.blockSignals(False)

        self._refresh_track_table()
        self.run_preflight_qc()

    def _browse_add_audio_tracks(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Mastered WAV / FLAC / MP3 Track(s)",
            str(Path.home()),
            "Audio Files (*.wav *.flac *.mp3 *.m4a *.ogg)",
        )
        if not files:
            return
        self.import_audio_files(files)

    def import_audio_files(self, file_paths: List[str], release_title: str = ""):
        valid = [str(p) for p in file_paths if p and Path(p).exists()]
        if not valid:
            return
        if len(valid) == 1 and self.release_mode == "single":
            p = Path(valid[0])
            stem_title = release_title or p.stem.replace("_", " ").strip()
            self.tracks[0]["audio_path"] = str(p)
            if stem_title:
                self.tracks[0]["title"] = stem_title
                self.txt_release_title.setText(stem_title)
            self._refresh_track_table()
            self._load_track_into_inspector(0)
            self.run_preflight_qc()
            return

        # Multi-file import -> switch to Album / EP mode if >= 2 tracks
        new_tracks = []
        for p_str in valid[:30]:
            p = Path(p_str)
            clean_t = re.sub(r"^\d+[\s._-]+", "", p.stem.replace("_", " ")).strip() or p.stem
            new_tracks.append({
                "title": clean_t,
                "audio_path": str(p),
                "lyrics": "",
                "featured_artist": "",
                "isrc": "",
                "explicit": self.chk_explicit.isChecked(),
                "instrumental": False,
            })
        self.tracks = new_tracks
        if len(new_tracks) >= 2:
            self.set_release_mode("album")
            if release_title:
                self.txt_release_title.setText(release_title)
        else:
            self.set_release_mode("single")
        self._refresh_track_table()
        self._load_track_into_inspector(0)
        self.run_preflight_qc()

    def load_tracks_from_studio(
        self,
        tracks_list: List[Dict[str, object]],
        release_title: str = "",
        artist_name: str = "",
        genre: str = "",
    ):
        """Bridge receiver for Mastered Queue, Batch Album, or Active Editor Song."""
        if not tracks_list:
            return
        normalized: List[Dict[str, object]] = []
        for idx, item in enumerate(tracks_list[:30], 1):
            raw_lyr = str(item.get("lyrics", "") or "")
            cleaned_lyr = clean_lyrics_for_stores(raw_lyr) if raw_lyr else ""
            normalized.append({
                "title": str(item.get("title", "")).strip() or f"Track {idx}",
                "audio_path": str(item.get("audio_path", "") or item.get("master_path", "") or item.get("path", "")).strip(),
                "lyrics": cleaned_lyr,
                "featured_artist": str(item.get("featured_artist", "")).strip(),
                "isrc": str(item.get("isrc", "")).strip(),
                "explicit": bool(item.get("explicit", False)),
                "instrumental": bool(item.get("instrumental", False)),
            })

        self.tracks = normalized
        if artist_name:
            self.txt_artist_name.setText(artist_name)
        if genre:
            g_idx = self.combo_genre.findText(genre, Qt.MatchFlag.MatchContains)
            if g_idx >= 0:
                self.combo_genre.setCurrentIndex(g_idx)

        if len(normalized) >= 2:
            self.set_release_mode("album")
            if release_title:
                self.txt_release_title.setText(release_title)
            elif self.txt_release_title.text().strip() == normalized[0]["title"]:
                self.txt_release_title.setText(f"{normalized[0]['title']} (Album)")
        else:
            self.set_release_mode("single")
            single_t = release_title or str(normalized[0]["title"])
            self.txt_release_title.setText(single_t)

        self._refresh_track_table()
        self._load_track_into_inspector(0)
        self._generate_3000_cover()
        self.run_preflight_qc()
        self.lbl_status.setText(
            f"🚀 Loaded {len(normalized)} track(s) into {self.current_platform} Release Studio (Lyrics auto-cleaned!)"
        )

    def _add_blank_album_track(self):
        if self.release_mode == "single":
            self.set_release_mode("album")
        if len(self.tracks) >= 30:
            return
        idx = len(self.tracks) + 1
        self.tracks.append({
            "title": f"Track {idx}",
            "audio_path": "",
            "lyrics": "",
            "featured_artist": "",
            "isrc": "",
            "explicit": self.chk_explicit.isChecked(),
            "instrumental": False,
        })
        self._refresh_track_table()
        self._load_track_into_inspector(len(self.tracks) - 1)
        self.run_preflight_qc()

    def _move_selected_track(self, delta: int):
        if self.release_mode == "single" or len(self.tracks) < 2:
            return
        cur = self.selected_track_idx
        nxt = cur + delta
        if 0 <= nxt < len(self.tracks):
            self.tracks[cur], self.tracks[nxt] = self.tracks[nxt], self.tracks[cur]
            self.selected_track_idx = nxt
            self._refresh_track_table()
            self._load_track_into_inspector(nxt)

    def _remove_selected_track(self):
        if len(self.tracks) <= 1:
            self.tracks[0]["audio_path"] = ""
            self._refresh_track_table()
            self._load_track_into_inspector(0)
            self.run_preflight_qc()
            return
        del self.tracks[self.selected_track_idx]
        if len(self.tracks) == 1 and self.release_mode == "album":
            self.set_release_mode("single")
        else:
            self.selected_track_idx = max(0, min(self.selected_track_idx, len(self.tracks) - 1))
            self._refresh_track_table()
            self._load_track_into_inspector(self.selected_track_idx)
            self.run_preflight_qc()

    def _attach_audio_for_selected_track(self):
        fn, _ = QFileDialog.getOpenFileName(
            self,
            "Select Audio File for Selected Track",
            str(Path.home()),
            "Audio Files (*.wav *.flac *.mp3 *.m4a *.ogg)",
        )
        if not fn:
            return
        self.txt_track_audio.setText(fn)

    def clean_all_track_lyrics(self):
        for tr in self.tracks:
            tr["lyrics"] = clean_lyrics_for_stores(str(tr.get("lyrics", "")))
        self._load_track_into_inspector(self.selected_track_idx)
        self._refresh_track_table()
        self.run_preflight_qc()
        self.lbl_status.setText("🧹 Stripped all [Section] & [Chord] tags for Apple Music / Spotify / DistroKid compliance")

    # ── Project Snapshot, Pre-Flight QC & Release Staging ──
    def build_project_dict(self) -> Dict[str, object]:
        return {
            "platform": self.current_platform,
            "release_mode": self.release_mode,
            "artist_name": self.txt_artist_name.text().strip(),
            "release_title": self.txt_release_title.text().strip(),
            "songwriter_first": self.txt_sw_first.text().strip(),
            "songwriter_middle": "",
            "songwriter_last": self.txt_sw_last.text().strip(),
            "primary_genre": self.combo_genre.currentText(),
            "secondary_genre": "",
            "language": self.combo_language.currentText(),
            "release_date": self.txt_release_date.text().strip(),
            "record_label": self.txt_record_label.text().strip(),
            "copyright_year": str(datetime.date.today().year),
            "explicit": self.chk_explicit.isChecked(),
            "cover_path": self.cover_path,
            "cover_style": str(self.combo_cover_style.currentData() or "cyberpunk_neon"),
            "stage_dir": self.last_stage_dir,
            "tracks": [dict(t) for t in self.tracks],
        }

    def run_preflight_qc(self) -> Dict[str, object]:
        proj = self.build_project_dict()
        res = DistroPreflightValidator.validate_release(proj)
        score = res["score"]
        self.lbl_qc_score.setText(f"🛡️ Store Pre-Flight Score: {score}/100 ({res['format_label']})")
        color = "#10b981" if score >= 85 else ("#f59e0b" if score >= 60 else "#ef4444")
        self.lbl_qc_score.setStyleSheet(f"font-size: 11px; font-weight: 800; color: {color};")
        self.txt_qc_report.setPlainText(str(res["summary_text"]))
        self.dock_tabs.setTabText(2, f"3. QC ({score}%)")
        return res

    def build_staged_release_pack(self) -> Dict[str, object]:
        self.clean_all_track_lyrics()
        proj = self.build_project_dict()
        pack = DistroStagePackager.build_staged_release(
            proj,
            auto_master_wav=self.chk_auto_master.isChecked(),
        )
        self.last_stage_dir = str(pack["stage_dir"])
        self.cover_path = str(pack["cover_path"])

        # Update track audio paths to staged 24-bit WAVs when exported
        for idx, et in enumerate(pack["tracks"]):
            if idx < len(self.tracks) and et.get("wav_path"):
                self.tracks[idx]["audio_path"] = et["wav_path"]

        self._set_cover_file(self.cover_path)
        self._refresh_track_table()
        self._load_track_into_inspector(self.selected_track_idx)
        self.lbl_stage_path.setText(f"📁 Staged Release Folder: {self.last_stage_dir}")

        cb = QApplication.clipboard()
        if cb:
            cb.setText(self.last_stage_dir)

        self.run_preflight_qc()
        self.lbl_status.setText(
            f"📦 Built staged release pack ({len(pack['tracks'])} track(s)) & copied folder path to clipboard!"
        )
        return pack

    # ── Transparent Client-Side Form Auto-Fill ──
    def autofill_active_portal_form(self):
        proj = self.build_project_dict()
        js = DistroAutoFillBuilder.build_autofill_js(self.current_platform, proj)
        self._last_js_executed = js

        if self.last_stage_dir:
            cb = QApplication.clipboard()
            if cb:
                cb.setText(self.last_stage_dir)

        self.ensure_browser_initialized()
        if self.web_view is not None and self.web_page is not None:
            self.web_page.runJavaScript(js, self._on_autofill_js_completed)
        else:
            tr_count = 1 if self.release_mode == "single" else len(self.tracks)
            self.lbl_status.setText(
                f"⚡ Prepared {self.current_platform} Auto-Fill script ({tr_count} track(s))"
            )

    def _on_autofill_js_completed(self, result):
        if isinstance(result, dict):
            if result.get("reason") == "auth_page":
                self.lbl_status.setText(
                    f"🔑 Please sign into your {self.current_platform} account first, open New Upload, then click Auto-Fill."
                )
                return
            filled = result.get("filled", 0)
            t_cnt = result.get("trackCount", 1)
            self.lbl_status.setText(
                f"✅ Auto-filled {filled} field(s) for {t_cnt} track(s) on {self.current_platform}! Now select Cover & WAV files."
            )

    def autofill_current_track_lyrics(self):
        vis = self._visible_tracks()
        if not vis:
            return
        tr = vis[min(self.selected_track_idx, len(vis) - 1)]
        clean_lyr = clean_lyrics_for_stores(str(tr.get("lyrics", "")))
        cb = QApplication.clipboard()
        if cb:
            cb.setText(clean_lyr)
        js = DistroAutoFillBuilder.build_lyrics_autofill_js(clean_lyr, str(tr.get("title", "")))
        self._last_js_executed = js
        if self.web_page is not None:
            self.web_page.runJavaScript(js)
        self.lbl_status.setText(f"📝 Clean store lyrics for '{tr.get('title', 'Track')}' injected & copied to clipboard!")

    def _copy_stage_path(self):
        if not self.last_stage_dir:
            self.build_staged_release_pack()
        cb = QApplication.clipboard()
        if cb and self.last_stage_dir:
            cb.setText(self.last_stage_dir)
            self.lbl_status.setText(f"📋 Copied staged folder path: {self.last_stage_dir}")

    def _open_staged_folder(self):
        target = Path(self.last_stage_dir) if self.last_stage_dir else (Path.home() / ".lyric_ai_writer" / "distro_releases")
        target.mkdir(parents=True, exist_ok=True)
        if os.environ.get("QT_QPA_PLATFORM", "").lower() != "offscreen":
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(target)))

    # ── Embedded WebEngine Lifecycle & Multi-Account Profiles ──
    def ensure_browser_initialized(self):
        if self._browser_initialized:
            return
        self._browser_initialized = True

        if os.environ.get("QT_QPA_PLATFORM", "").lower() == "offscreen":
            self.lbl_browser_placeholder.setText(
                f"🚀 Embedded {self.current_platform} Browser Ready ({self.current_account_slot})\n"
                f"URL: {self.txt_url.text()}"
            )
            return

        try:
            from PyQt6.QtWebEngineWidgets import QWebEngineView

            self.lbl_browser_placeholder.hide()
            self.web_view = QWebEngineView(self.browser_container)
            self.browser_layout.addWidget(self.web_view, stretch=1)
            self._mount_account_profile(self.current_account_slot)
        except Exception as exc:
            self._browser_initialized = False
            self.lbl_browser_placeholder.show()
            self.lbl_browser_placeholder.setText(
                f"⚠️ Embedded WebEngine unavailable ({exc}).\n"
                "Click '↗ Browser' above to open DistroKid / TuneCore in your system browser."
            )

    def _mount_account_profile(self, slot_name: str):
        if os.environ.get("QT_QPA_PLATFORM", "").lower() == "offscreen" or self.web_view is None:
            return
        try:
            from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineSettings

            p_dir = self._profile_dir(slot_name)
            storage_name = f"SMGDistro_{re.sub(r'[^a-zA-Z0-9]', '', slot_name)}"
            profile = QWebEngineProfile(storage_name, self)
            profile.setPersistentStoragePath(str(p_dir / "storage"))
            profile.setCachePath(str(p_dir / "cache"))
            profile.setPersistentCookiesPolicy(
                QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies
            )

            page = QWebEnginePage(profile, self.web_view)
            settings = page.settings()
            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)

            self.web_view.setPage(page)
            self.web_profile = profile
            self.web_page = page
            self.web_view.urlChanged.connect(lambda u: self.txt_url.setText(u.toString()))
            self.web_view.loadProgress.connect(
                lambda p: self.lbl_status.setText(f"🌐 Loading {self.current_platform}: {p}%")
                if p < 100
                else self.lbl_status.setText(f"✅ {self.current_platform} Ready • {slot_name} • Auto-Fill Armed")
            )
            target_url = self.txt_url.text().strip() or DISTRO_PLATFORMS[self.current_platform]["new_upload_url"]
            self.web_view.setUrl(QUrl(target_url))
            self.web_view.setZoomFactor(self._zoom_factor)
        except Exception as exc:
            self.lbl_status.setText(f"⚠️ Profile switch error: {exc}")

    def _on_account_slot_changed(self, slot_name: str):
        if not slot_name:
            return
        self.current_account_slot = slot_name
        config_manager.set("distro_active_account_slot", slot_name)
        if self._browser_initialized:
            if os.environ.get("QT_QPA_PLATFORM", "").lower() == "offscreen":
                self.lbl_browser_placeholder.setText(
                    f"🚀 Embedded {self.current_platform} Browser Ready ({slot_name})\nURL: {self.txt_url.text()}"
                )
            else:
                self._mount_account_profile(slot_name)
        self.lbl_status.setText(f"👤 Switched distributor profile to: {slot_name}")

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

    def _open_external_browser(self):
        url = self.txt_url.text().strip() or DISTRO_PLATFORMS[self.current_platform]["new_upload_url"]
        if os.environ.get("QT_QPA_PLATFORM", "").lower() != "offscreen":
            QDesktopServices.openUrl(QUrl(url))

    def _toggle_left_dock(self):
        vis = not self.dock_card.isVisible()
        self.dock_card.setVisible(vis)
        self.btn_toggle_dock.setChecked(vis)
        self.btn_toggle_dock.setText("◀ Dock" if vis else "▶ Dock")
        self.btn_fs_toggle_dock.setText("▶ Hide Dock" if vis else "◀ Show Dock")
        self._reposition_floating_bar()

    # ── Full Screen Mode ──
    def _reposition_floating_bar(self):
        if self.floating_fs_bar.isVisible():
            bw = self.browser_container.width()
            fw = self.floating_fs_bar.sizeHint().width()
            fh = self.floating_fs_bar.sizeHint().height()
            self.floating_fs_bar.setGeometry(max(10, (bw - fw) // 2), 10, fw, fh)
            self.floating_fs_bar.raise_()

    def set_fullscreen_active(self, is_active: bool):
        self._is_fullscreen_active = is_active
        if is_active:
            self._pre_fs_dock_visible = self.dock_card.isVisible()
            self.dock_card.hide()
            self.btn_toggle_dock.setChecked(False)
            self.btn_toggle_dock.setText("▶ Dock")
            self.btn_fullscreen.setText("⛷️ Exit Full Screen")
            self.btn_fs_toggle_dock.setText("◀ Show Dock")
            self.floating_fs_bar.show()
            self.floating_fs_bar.raise_()
            self._reposition_floating_bar()
        else:
            self.floating_fs_bar.hide()
            self.btn_fullscreen.setText("⛶ Full Screen")
            if self._pre_fs_dock_visible:
                self.dock_card.show()
                self.btn_toggle_dock.setChecked(True)
                self.btn_toggle_dock.setText("◀ Dock")

    def _toggle_fullscreen_view(self):
        new_state = not self._is_fullscreen_active
        self.set_fullscreen_active(new_state)
        self.toggle_fullscreen_requested.emit(new_state)

    def _exit_fullscreen_view(self):
        if self._is_fullscreen_active:
            self.set_fullscreen_active(False)
            self.toggle_fullscreen_requested.emit(False)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reposition_floating_bar()

    # ── 5-Theme Adaptive Styling ──
    def apply_theme(self, theme_key: str):
        t = get_theme(theme_key)
        self.theme_key = t["id"]
        is_dark = t["is_dark"]

        bg_card = t.get("bg_card", "#111526")
        bg_input = t.get("bg_input", "#0c0f1d")
        border = t.get("border", "#1e2540")
        border_sub = t.get("border_subtle", "#283256")
        text_pri = t.get("text_primary", "#f8fafc")
        text_sec = t.get("text_secondary", "#94a3b8")
        accent = t.get("accent", "#8b5cf6")
        accent_sec = t.get("accent_secondary", "#7c3aed")
        btn_bg = t.get("bg_btn", "#161b2e")
        btn_hover = t.get("bg_btn_hover", "#222944")

        self.setStyleSheet(f"""
            QFrame#distroNavBar, QFrame#distroDockCard, QFrame#distroBrowserContainer {{
                background-color: {bg_card};
                border: 1px solid {border};
                border-radius: 8px;
            }}
            QFrame#distroCoverCard, QFrame#distroActionFooter {{
                background-color: {bg_input};
                border: 1px solid {border_sub};
                border-radius: 8px;
            }}
            QFrame#distroFloatingFsBar {{
                background-color: {'rgba(15, 23, 42, 0.94)' if is_dark else 'rgba(255, 255, 255, 0.96)'};
                border: 1px solid {accent};
                border-radius: 8px;
            }}
            QFrame#distroNavBar QPushButton, QFrame#distroDockCard QPushButton {{
                background-color: {btn_bg};
                color: {text_pri};
                border: 1px solid {border_sub};
                border-radius: 6px;
                font-size: 10.5px;
                font-weight: 700;
                padding: 2px 7px;
            }}
            QFrame#distroNavBar QPushButton:hover, QFrame#distroDockCard QPushButton:hover {{
                background-color: {btn_hover};
                border-color: {accent};
            }}
        """)

        icon_btn_qss = f"""
            QPushButton {{
                background-color: {btn_bg};
                color: {text_pri};
                border: 1px solid {border_sub};
                border-radius: 6px;
                font-size: 11px;
                font-weight: 800;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {btn_hover};
                border-color: {accent};
            }}
        """
        for ib in (
            self.btn_reload,
            self.btn_zoom_out,
            self.btn_zoom_in,
            self.btn_move_up,
            self.btn_move_down,
            self.btn_remove_track,
        ):
            ib.setStyleSheet(icon_btn_qss)

        pill_qss = f"""
            QPushButton {{
                background-color: {btn_bg};
                color: {text_pri};
                border: 1px solid {border_sub};
                border-radius: 6px;
                font-size: 10.5px;
                font-weight: 700;
                padding: 3px 8px;
            }}
            QPushButton:hover {{
                background-color: {btn_hover};
                border-color: {accent};
            }}
            QPushButton:checked {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {accent_sec}, stop:1 {accent});
                color: #ffffff;
                border: 1px solid {accent};
                font-weight: 800;
            }}
        """
        for b in (
            self.btn_plat_distrokid,
            self.btn_plat_tunecore,
            self.btn_mode_single,
            self.btn_mode_album,
            self.btn_toggle_dock,
        ):
            b.setStyleSheet(pill_qss)

        self.btn_build_stage.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #0ea5e9);
                color: #ffffff;
                font-size: 10.5px;
                font-weight: 800;
                border-radius: 6px;
                border: 1px solid #38bdf8;
                padding: 4px 10px;
            }
            QPushButton:hover {
                background: #0369a1;
            }
        """)

        self.btn_autofill_form.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #10b981);
                color: #ffffff;
                font-size: 11px;
                font-weight: 900;
                border-radius: 6px;
                border: 1px solid #34d399;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background: #047857;
            }
        """)

        self.lbl_status.setStyleSheet(f"font-size: 9.5px; font-weight: 700; color: {text_sec};")
        self.lbl_browser_placeholder.setStyleSheet(
            f"font-size: 13px; font-weight: 700; padding: 24px; color: {text_pri};"
        )
