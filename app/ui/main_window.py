"""
Main Application Window: Orchestrates Layout, Panels, Workers,
File I/O, Exporting, and Studio Session State.
Includes Bisach Suno AI Visual Studio mode and Lyric Editor Studio mode.
"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QPushButton, QSplitter, QFileDialog, QMessageBox,
    QStatusBar, QMenu, QApplication, QDialog, QListWidget, QListWidgetItem,
    QStackedWidget, QFrame, QComboBox, QLayout
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QPixmap, QKeySequence, QShortcut

from app.config import config_manager, GEMINI_MODELS, get_asset_path, APP_VERSION, DEFAULT_UPDATE_URL
from app.license_manager import license_manager
from app.ui.generator_panel import GeneratorPanel
from app.ui.editor_panel import EditorPanel
from app.ui.tools_panel import ToolsPanel
from app.ui.settings_dialog import SettingsDialog
from app.ui.visual_studio_view import VisualStudioView
from app.ui.wizard_view import SongCreationWizardView
from app.ui.batch_generator_view import BatchGeneratorView
from app.ui.styles import STUDIO_THEMES, get_theme
from app.gemini_client import (
    GenerateLyricWorker, RewriteWorker, RhymeWorker, SunoPromptWorker
)
from app.exporter import Exporter

class HistoryDialog(QDialog):
    """Browse and restore recently generated lyric projects."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Lyric Project History")
        self.setFixedSize(500, 400)
        self.selected_item = None

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Select a recent song to restore into the studio:"))

        self.list_widget = QListWidget()
        self.history_items = config_manager.get_history()

        for item in self.history_items:
            title = item.get("title", "Untitled")
            genre = item.get("genre", "Unknown")
            lines = len(item.get("lyrics", "").split("\n"))
            list_item = QListWidgetItem(f"🎵 {title}  [{genre}]  •  {lines} lines")
            self.list_widget.addItem(list_item)

        layout.addWidget(self.list_widget)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton("Close")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        btn_load = QPushButton("Load into Studio")
        btn_load.setObjectName("primaryGenerateButton")
        btn_load.clicked.connect(self._on_load)
        btn_row.addWidget(btn_load)

        layout.addLayout(btn_row)

    def _on_load(self):
        row = self.list_widget.currentRow()
        if 0 <= row < len(self.history_items):
            self.selected_item = self.history_items[row]
            self.accept()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SMG Suno AI Lyric Writer — Global Music Studio")
        self.resize(1380, 880)
        self.setMinimumSize(1020, 680)

        # Set Window Icon
        logo_path = get_asset_path("logo.png")
        if logo_path.exists():
            self.setWindowIcon(QIcon(str(logo_path)))

        self.current_worker = None
        self.current_theme = config_manager.get("theme", "obsidian")
        if self.current_theme in ["dark", "dark_modern"]:
            self.current_theme = "obsidian"
        elif self.current_theme in ["light", "modern_light"]:
            self.current_theme = "canvas_light"
        self.is_dark_theme = get_theme(self.current_theme)["is_dark"]
        self.latest_update_info = None
        self.update_check_worker = None

        self._init_ui()
        self._setup_global_shortcuts()
        self._connect_panels()
        self._apply_all_themes(self.current_theme)
        self._load_last_session()

        # Check for updates in background (2.5s delay to keep UI boot instantaneous)
        if config_manager.get("auto_check_updates", True):
            QTimer.singleShot(2500, self._check_updates_startup)

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        master_layout = QVBoxLayout(central)
        master_layout.setContentsMargins(0, 0, 0, 0)
        master_layout.setSpacing(0)

        # Header Bar (Zone 1: Brand & Stage | Zone 2: Mode Switcher | Zone 3: Production & Utility Capsules)
        header = self._create_header_bar()
        master_layout.addWidget(header)

        # Contextual Studio Workflow Ribbon
        self.workflow_ribbon = self._create_workflow_ribbon()
        master_layout.addWidget(self.workflow_ribbon)

        # Stacked Widget: Easy Wizard vs Visual Studio vs Batch vs Lyric Editor vs Clone
        self.stack = QStackedWidget()

        # View 0: Easy Song Creation Wizard (ទិសដៅនៃការធ្វើបទចម្រៀង)
        self.wizard_view = SongCreationWizardView(self)
        self.stack.addWidget(self.wizard_view)

        # View 1: Visual Studio View (Pill Tags, Khmer Studio, Live Suno Formula Card)
        self.visual_studio = VisualStudioView(self)
        self.stack.addWidget(self.visual_studio)

        # View 2: Batch Multi-Song Studio Pro (បង្កើតបទបានច្រើន)
        self.batch_view = BatchGeneratorView(self)
        self.stack.addWidget(self.batch_view)

        # View 3: 3-Pane Lyric Editor Workbench
        self.editor_workbench = self._create_editor_workbench()
        self.stack.addWidget(self.editor_workbench)

        # View 4: Song DNA & Semantic Meaning Cloner Workstation
        from app.ui.clone_dialog import SongDNAClonerView
        self.clone_view = SongDNAClonerView(parent=self, is_dark=self.is_dark_theme)
        self.clone_view.send_to_editor_requested.connect(self._load_cloned_song_into_editor)
        self.stack.addWidget(self.clone_view)

        master_layout.addWidget(self.stack, stretch=1)

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self._update_status_bar()

        # Set initial studio mode
        self._set_studio_mode(0)

    def _create_workflow_ribbon(self) -> QWidget:
        self.workflow_ribbon = QFrame()
        self.workflow_ribbon.setObjectName("workflowRibbon")
        self.workflow_ribbon.setFixedHeight(34)

        r_layout = QHBoxLayout(self.workflow_ribbon)
        r_layout.setContentsMargins(14, 0, 14, 0)
        r_layout.setSpacing(12)

        self.lbl_ribbon_info = QLabel("🗺️ Wizard Studio • Step-by-step guided song creation")
        self.lbl_ribbon_info.setObjectName("lblRibbonInfo")
        r_layout.addWidget(self.lbl_ribbon_info)

        r_layout.addStretch(1)

        self.lbl_ribbon_hint = QLabel("⌨️ Ctrl+1..5 Modes  •  Ctrl+N New  •  Ctrl+F Focus  •  Ctrl+E Export")
        self.lbl_ribbon_hint.setObjectName("lblRibbonHint")
        r_layout.addWidget(self.lbl_ribbon_hint)

        self.btn_ribbon_action = QPushButton("✍️ Open in Editor ➔")
        self.btn_ribbon_action.setObjectName("btnRibbonAction")
        self.btn_ribbon_action.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ribbon_action.setFixedHeight(24)
        self.btn_ribbon_action.clicked.connect(self._on_ribbon_action_clicked)
        r_layout.addWidget(self.btn_ribbon_action)

        return self.workflow_ribbon

    def _create_editor_workbench(self) -> QWidget:
        container = QWidget()
        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(4, 2, 4, 4)
        c_layout.setSpacing(3)

        # Workbench Top Control Bar (Easy Control & Distraction-Free Focus)
        self.wb_toolbar = QFrame()
        self.wb_toolbar.setObjectName("editorWorkbenchToolbar")
        self.wb_toolbar.setFixedHeight(34)
        wb_layout = QHBoxLayout(self.wb_toolbar)
        wb_layout.setContentsMargins(8, 2, 8, 2)
        wb_layout.setSpacing(8)

        # Left Toggle: Hide/Show Generator Panel
        self.btn_toggle_generator = QPushButton("◀ Generator Panel")
        self.btn_toggle_generator.setCheckable(True)
        self.btn_toggle_generator.setChecked(True)
        self.btn_toggle_generator.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_generator.setToolTip("Toggle AI Lyric Generator Panel (Left Sidebar)")
        self.btn_toggle_generator.clicked.connect(self._toggle_generator_panel)
        wb_layout.addWidget(self.btn_toggle_generator)

        # Focus Mode Button (Full Width Distraction-Free Lyricist View)
        self.btn_focus_mode = QPushButton("🎯 Focus Mode")
        self.btn_focus_mode.setCheckable(True)
        self.btn_focus_mode.setChecked(False)
        self.btn_focus_mode.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_focus_mode.setToolTip("Toggle Focus Mode (Collapse side panels for full-width lyric writing) [Ctrl+F]")
        self.btn_focus_mode.clicked.connect(self._toggle_focus_mode)
        wb_layout.addWidget(self.btn_focus_mode)

        wb_layout.addStretch(1)

        # Dynamic Editor Status & Lyric Metrics
        self.lbl_editor_status = QLabel("📝 0 Words • 0 Lines • 0 Chords")
        self.lbl_editor_status.setObjectName("lblEditorWorkbenchStatus")
        wb_layout.addWidget(self.lbl_editor_status)

        # Quick Copy Suno Button
        self.btn_suno_copy_quick = QPushButton("📋 Quick Copy for Suno")
        self.btn_suno_copy_quick.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_suno_copy_quick.setToolTip("Copy formatted lyrics directly to clipboard for Suno AI prompt [Ctrl+Shift+C]")
        self.btn_suno_copy_quick.clicked.connect(self._quick_copy_suno)
        wb_layout.addWidget(self.btn_suno_copy_quick)

        wb_layout.addStretch(1)

        # Right Toggle: Hide/Show Tools Panel
        self.btn_toggle_tools = QPushButton("Tools Panel ▶")
        self.btn_toggle_tools.setCheckable(True)
        self.btn_toggle_tools.setChecked(True)
        self.btn_toggle_tools.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_tools.setToolTip("Toggle Rhyme, Audition & Hit Inspector Panel (Right Sidebar)")
        self.btn_toggle_tools.clicked.connect(self._toggle_tools_panel)
        wb_layout.addWidget(self.btn_toggle_tools)

        c_layout.addWidget(self.wb_toolbar)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setContentsMargins(2, 2, 2, 2)

        self.generator_panel = GeneratorPanel(self)
        self.editor_panel = EditorPanel(self)
        self.tools_panel = ToolsPanel(self)

        # Connect tools panel with editor getter for TTS audition
        self.tools_panel.get_lyrics_func = self.editor_panel.get_lyrics

        self.splitter.addWidget(self.generator_panel)
        self.splitter.addWidget(self.editor_panel)
        self.splitter.addWidget(self.tools_panel)

        self.splitter.setCollapsible(0, True)
        self.splitter.setCollapsible(1, False)
        self.splitter.setCollapsible(2, True)

        self.generator_panel.setMinimumWidth(0)
        self.tools_panel.setMinimumWidth(0)

        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setStretchFactor(2, 0)

        self._saved_splitter_sizes = [280, 680, 340]
        self.splitter.setSizes(self._saved_splitter_sizes)
        self.splitter.splitterMoved.connect(self._on_splitter_moved)

        # Connect text changes for dynamic status bar in workbench
        if hasattr(self.editor_panel, "editor"):
            self.editor_panel.editor.textChanged.connect(self._update_editor_workbench_metrics)

        c_layout.addWidget(self.splitter)
        return container

    def _on_splitter_moved(self, pos, index):
        sizes = self.splitter.sizes()
        if sizes[0] > 20 and sizes[2] > 20:
            self._saved_splitter_sizes = list(sizes)
        self.btn_toggle_generator.setChecked(sizes[0] > 20)
        self.btn_toggle_tools.setChecked(sizes[2] > 20)
        self._update_focus_mode_state()

    def _toggle_generator_panel(self):
        sizes = self.splitter.sizes()
        if self.generator_panel.isVisible() and sizes[0] > 20:
            self._saved_splitter_sizes[0] = sizes[0]
            self.generator_panel.hide()
            self.splitter.setSizes([0, sizes[1] + sizes[0], sizes[2]])
            self.btn_toggle_generator.setChecked(False)
        else:
            self.generator_panel.show()
            restore_w = self._saved_splitter_sizes[0] if self._saved_splitter_sizes[0] > 50 else 280
            self.splitter.setSizes([restore_w, max(300, sizes[1] - restore_w), sizes[2]])
            self.btn_toggle_generator.setChecked(True)
        self._update_focus_mode_state()

    def _toggle_tools_panel(self):
        sizes = self.splitter.sizes()
        if self.tools_panel.isVisible() and sizes[2] > 20:
            self._saved_splitter_sizes[2] = sizes[2]
            self.tools_panel.hide()
            self.splitter.setSizes([sizes[0], sizes[1] + sizes[2], 0])
            self.btn_toggle_tools.setChecked(False)
        else:
            self.tools_panel.show()
            restore_w = self._saved_splitter_sizes[2] if self._saved_splitter_sizes[2] > 50 else 340
            self.splitter.setSizes([sizes[0], max(300, sizes[1] - restore_w), restore_w])
            self.btn_toggle_tools.setChecked(True)
        self._update_focus_mode_state()

    def _toggle_focus_mode(self):
        sizes = self.splitter.sizes()
        is_focused = not self.generator_panel.isVisible() and not self.tools_panel.isVisible()
        if not is_focused:
            if sizes[0] > 20: self._saved_splitter_sizes[0] = sizes[0]
            if sizes[2] > 20: self._saved_splitter_sizes[2] = sizes[2]
            self.generator_panel.hide()
            self.tools_panel.hide()
            total_w = sum(sizes)
            self.splitter.setSizes([0, total_w, 0])
            self.btn_toggle_generator.setChecked(False)
            self.btn_toggle_tools.setChecked(False)
            self.btn_focus_mode.setChecked(True)
            self.btn_focus_mode.setText("🪟 Normal 3-Pane")
            self.status_bar.showMessage("Entered Lyric Focus Mode (Distraction-Free Full Width)", 2500)
        else:
            self.generator_panel.show()
            self.tools_panel.show()
            left_w = self._saved_splitter_sizes[0] if self._saved_splitter_sizes[0] > 50 else 280
            right_w = self._saved_splitter_sizes[2] if self._saved_splitter_sizes[2] > 50 else 340
            total_w = sum(sizes)
            mid_w = max(350, total_w - left_w - right_w)
            self.splitter.setSizes([left_w, mid_w, right_w])
            self.btn_toggle_generator.setChecked(True)
            self.btn_toggle_tools.setChecked(True)
            self.btn_focus_mode.setChecked(False)
            self.btn_focus_mode.setText("🎯 Focus Mode")
            self.status_bar.showMessage("Restored 3-Pane Studio Workbench", 2500)

    def _update_focus_mode_state(self):
        sizes = self.splitter.sizes()
        is_focus = (sizes[0] <= 10 and sizes[2] <= 10)
        self.btn_focus_mode.setChecked(is_focus)
        if is_focus:
            self.btn_focus_mode.setText("🪟 Normal 3-Pane")
        else:
            self.btn_focus_mode.setText("🎯 Focus Mode")

    def _update_editor_workbench_metrics(self):
        if not hasattr(self, "lbl_editor_status") or not hasattr(self, "editor_panel"):
            return
        try:
            lyrics = self.editor_panel.get_lyrics()
            lines = [line.strip() for line in lyrics.split("\n") if line.strip()]
            line_count = len(lines)
            words = [w for w in lyrics.split() if not (w.startswith("[") and w.endswith("]"))]
            word_count = len(words)
            import re
            chords = re.findall(r'\[([A-G][#b]?(?:m|maj|min|dim|aug|sus[24]?|[0-9])*(?:/[A-G][#b]?)?)\]', lyrics)
            chord_count = len(set(chords))
            self.lbl_editor_status.setText(f"📝 {word_count} Words • {line_count} Lines • {chord_count} Chords")
        except Exception:
            pass

    def _quick_copy_suno(self):
        lyrics = self.editor_panel.get_lyrics().strip()
        if not lyrics:
            self.status_bar.showMessage("Cannot copy: lyrics are currently empty", 3000)
            return
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(lyrics)
            self.status_bar.showMessage("✓ Lyrics copied to clipboard for Suno AI! Ready to paste.", 3500)
            if hasattr(self, "btn_suno_copy_quick"):
                orig = self.btn_suno_copy_quick.text()
                self.btn_suno_copy_quick.setText("✓ Copied!")
                QTimer.singleShot(1500, lambda: self.btn_suno_copy_quick.setText(orig))

    def _on_ribbon_action_clicked(self):
        mode = self.stack.currentIndex()
        if mode == 0:  # Wizard -> Editor
            self._set_studio_mode(3)
            self.status_bar.showMessage("Switched to Lyric Editor Workbench with current Wizard lyrics", 3000)
        elif mode == 1:  # Visual Studio -> Editor
            params = self.visual_studio.get_prompt_parameters()
            self._transfer_to_editor(params)
        elif mode == 2:  # Batch Studio Pro -> Editor
            if hasattr(self, "batch_view"):
                if getattr(self.batch_view, "selected_song", None):
                    self.batch_view._open_selected_in_editor()
                elif getattr(self.batch_view, "all_songs", None) and len(self.batch_view.all_songs) > 0:
                    self.batch_view._forward_to_editor(self.batch_view.all_songs[0])
                else:
                    self._set_studio_mode(3)
        elif mode == 3:  # Editor Workbench -> Visual Studio Arranger
            self._set_studio_mode(1)
            self.status_bar.showMessage("Switched to Suno Visual Arranger", 3000)
        elif mode == 4:  # Song DNA Cloner -> Editor
            if hasattr(self, "clone_view"):
                if hasattr(self.clone_view, "txt_cloned_lyrics") and self.clone_view.txt_cloned_lyrics.toPlainText().strip():
                    self.clone_view._send_to_editor()
                else:
                    self._set_studio_mode(3)

    def _create_header_bar(self) -> QWidget:
        self.header_frame = QFrame()
        self.header_frame.setObjectName("mainHeaderBar")
        layout = QHBoxLayout(self.header_frame)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(12)

        # ── Zone 1: Brand & Stage Badge (Left) ──
        brand_box = QHBoxLayout()
        brand_box.setSpacing(10)

        self.avatar_lbl = QLabel()
        self.avatar_lbl.setFixedSize(36, 36)
        self.avatar_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._update_brand_logo()
        brand_box.addWidget(self.avatar_lbl)

        title_col = QVBoxLayout()
        title_col.setSpacing(1)
        self.header_title_lbl = QLabel("SMG Suno Studio Pro")
        self.header_title_lbl.setObjectName("headerAppTitle")
        title_col.addWidget(self.header_title_lbl)

        self.header_sub_lbl = QLabel("AI Lyric Writer & Music Production DAW")
        self.header_sub_lbl.setObjectName("headerAppSub")
        title_col.addWidget(self.header_sub_lbl)
        brand_box.addLayout(title_col)

        # Dynamic Stage Pill Badge
        self.header_stage_pill = QLabel("🗺️ WIZARD")
        self.header_stage_pill.setObjectName("headerStagePill")
        self.header_stage_pill.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.header_stage_pill.setFixedHeight(22)
        brand_box.addSpacing(6)
        brand_box.addWidget(self.header_stage_pill)

        layout.addLayout(brand_box)
        layout.addStretch(1)

        # ── Zone 2: Segmented Studio Mode Navigator (Center) ──
        self.header_mode_box = QFrame()
        self.header_mode_box.setObjectName("headerModeBox")
        mb_layout = QHBoxLayout(self.header_mode_box)
        mb_layout.setContentsMargins(3, 3, 3, 3)
        mb_layout.setSpacing(2)

        self.btn_mode_wizard = QPushButton("🗺️ Wizard")
        self.btn_mode_wizard.setToolTip("🗺️ ទិសដៅងាយស្រួល (Easy Wizard Studio) [Ctrl+1]")
        self.btn_mode_wizard.setCheckable(True)
        self.btn_mode_wizard.setChecked(True)
        self.btn_mode_wizard.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mode_wizard.clicked.connect(lambda: self._set_studio_mode(0))

        self.btn_mode_visual = QPushButton("🎨 Visual")
        self.btn_mode_visual.setToolTip("🎨 រូបមន្ត Suno (Visual Studio Prompter) [Ctrl+2]")
        self.btn_mode_visual.setCheckable(True)
        self.btn_mode_visual.setChecked(False)
        self.btn_mode_visual.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mode_visual.clicked.connect(lambda: self._set_studio_mode(1))

        self.btn_mode_batch = QPushButton("⚡ Batch")
        self.btn_mode_batch.setToolTip("⚡ បង្កើតបទច្រើន (Batch Studio Pro) [Ctrl+3]")
        self.btn_mode_batch.setCheckable(True)
        self.btn_mode_batch.setChecked(False)
        self.btn_mode_batch.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mode_batch.clicked.connect(lambda: self._set_studio_mode(2))

        self.btn_mode_editor = QPushButton("✍️ Editor")
        self.btn_mode_editor.setToolTip("✍️ សរសេរទំនុកច្រៀង (Lyric Editor Workbench) [Ctrl+4]")
        self.btn_mode_editor.setCheckable(True)
        self.btn_mode_editor.setChecked(False)
        self.btn_mode_editor.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mode_editor.clicked.connect(lambda: self._set_studio_mode(3))

        self.btn_mode_clone = QPushButton("🧬 Clone")
        self.btn_mode_clone.setToolTip("🧬 ម៉ាស៊ីនក្លូនបទចម្រៀងស្របន័យ (Song DNA & Cloner) [Ctrl+5]")
        self.btn_mode_clone.setCheckable(True)
        self.btn_mode_clone.setChecked(False)
        self.btn_mode_clone.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mode_clone.clicked.connect(lambda: self._set_studio_mode(4))

        for btn in [self.btn_mode_wizard, self.btn_mode_visual, self.btn_mode_batch, self.btn_mode_editor, self.btn_mode_clone]:
            btn.setFixedWidth(74)
            btn.setFixedHeight(28)
            mb_layout.addWidget(btn)

        layout.addWidget(self.header_mode_box)
        layout.addStretch(1)

        # ── Zone 3: Grouped Production & Utility Capsules (Right) ──
        right_box = QHBoxLayout()
        right_box.setSpacing(6)
        right_box.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)

        # Production Capsule (New, Export)
        self.capsule_prod = QFrame()
        self.capsule_prod.setObjectName("headerCapsuleProd")
        cp_layout = QHBoxLayout(self.capsule_prod)
        cp_layout.setContentsMargins(3, 2, 3, 2)
        cp_layout.setSpacing(3)
        cp_layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)

        self.header_btn_new = QPushButton("➕ ថ្មី")
        self.header_btn_new.setFixedWidth(52)
        self.header_btn_new.setFixedHeight(28)
        self.header_btn_new.setToolTip("New Lyric Project [Ctrl+N]")
        self.header_btn_new.setCursor(Qt.CursorShape.PointingHandCursor)
        self.header_btn_new.clicked.connect(self._new_song)
        cp_layout.addWidget(self.header_btn_new)

        self.btn_export = QPushButton("💾 Export ▾")
        self.btn_export.setFixedHeight(28)
        self.btn_export.setObjectName("accentButton")
        self.btn_export.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_export.setToolTip("Export song formats [Ctrl+E]")
        self.export_menu = QMenu(self)
        self.export_menu.addAction("📄 Export Video Subtitles (.srt - YouTube / TikTok)", lambda: self._export("srt"))
        self.export_menu.addAction("🎵 Export Timed Karaoke (.lrc - Spotify / Players)", lambda: self._export("lrc"))
        self.export_menu.addAction("🎤 Export Clean Singer Sheet (.txt - Vocals Only)", lambda: self._export("vocal"))
        self.export_menu.addAction("🎸 Export ChordPro Lead Sheet (.cho - Music Stands)", lambda: self._export("chordpro"))
        self.export_menu.addAction("Export as Printable PDF Lead Sheet (.pdf)", lambda: self._export("pdf"))
        self.export_menu.addAction("Export as Printable HTML Lead Sheet (.html)", lambda: self._export("html"))
        self.export_menu.addAction("Export as Structured JSON (.json)", lambda: self._export("json"))
        self.export_menu.addSeparator()
        self.export_menu.addAction("🎼 Export Vocal Topline MIDI (.mid with Lyrics)", self._export_topline_midi)
        self.export_menu.addAction("📄 Export MusicXML Sheet Music (.musicxml)", self._export_musicxml)
        self.export_menu.addAction("🖼️ Export Album Cover Artwork (.png)", self._export_album_cover)
        self.export_menu.addSeparator()
        self.export_menu.addAction("📦 Export Suno & Udio Production Bundle (.zip)", self._export_bundle)
        self.btn_export.setMenu(self.export_menu)
        cp_layout.addWidget(self.btn_export)
        right_box.addWidget(self.capsule_prod)

        # Utilities Capsule (Model, History, Theme, Settings)
        self.capsule_util = QFrame()
        self.capsule_util.setObjectName("headerCapsuleUtil")
        cu_layout = QHBoxLayout(self.capsule_util)
        cu_layout.setContentsMargins(3, 2, 3, 2)
        cu_layout.setSpacing(3)
        cu_layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)

        # Quick Model Engine Selector
        self.header_model_combo = QComboBox()
        self.header_model_combo.setFixedHeight(28)
        self.header_model_combo.setMaximumWidth(110)
        self.header_model_combo.addItems(GEMINI_MODELS)
        current_model = config_manager.get("gemini_model", "gemini-3.5-flash")
        idx = self.header_model_combo.findText(current_model)
        if idx >= 0:
            self.header_model_combo.setCurrentIndex(idx)
        else:
            self.header_model_combo.setCurrentText(current_model)
        self.header_model_combo.setToolTip("Select Gemini Model Engine")
        self.header_model_combo.currentTextChanged.connect(self._on_header_model_changed)
        cu_layout.addWidget(self.header_model_combo)

        self.header_btn_history = QPushButton("📜 ប្រវត្តិ")
        self.header_btn_history.setFixedHeight(28)
        self.header_btn_history.setToolTip("Lyric Project History [Ctrl+H]")
        self.header_btn_history.setCursor(Qt.CursorShape.PointingHandCursor)
        self.header_btn_history.clicked.connect(self._open_history)
        cu_layout.addWidget(self.header_btn_history)

        self.header_btn_theme = QPushButton("🌌")
        self.header_btn_theme.setFixedHeight(28)
        self.header_btn_theme.setCursor(Qt.CursorShape.PointingHandCursor)
        self.header_btn_theme.setToolTip("Select Studio Theme (5 Modern Clean Palettes) [Ctrl+T]")
        self.theme_menu = QMenu(self)
        self._populate_theme_menu()
        self.header_btn_theme.setMenu(self.theme_menu)
        self._update_theme_btn_label()
        cu_layout.addWidget(self.header_btn_theme)

        self.header_btn_settings = QPushButton("⚙️ Settings")
        self.header_btn_settings.setFixedHeight(28)
        self.header_btn_settings.setCursor(Qt.CursorShape.PointingHandCursor)
        self.header_btn_settings.setToolTip("Studio Settings & API Keys [Ctrl+,]")
        self.header_btn_settings.clicked.connect(self._open_settings)
        cu_layout.addWidget(self.header_btn_settings)

        # In-App Live Auto-Updater Pill Button
        self.header_btn_update = QPushButton("🚀 Update Ready")
        self.header_btn_update.setObjectName("headerBtnUpdate")
        self.header_btn_update.setFixedHeight(28)
        self.header_btn_update.setCursor(Qt.CursorShape.PointingHandCursor)
        self.header_btn_update.setToolTip("New update available! Click to view details, restart, or download installer")
        self.header_btn_update.clicked.connect(lambda: self._open_update_dialog())
        self.header_btn_update.hide()  # Hidden until update is found
        cu_layout.addWidget(self.header_btn_update)

        # License Status & Activation Pill Button
        self.header_btn_license = QPushButton("🔑 Activate Pro")
        self.header_btn_license.setObjectName("headerBtnLicense")
        self.header_btn_license.setFixedHeight(28)
        self.header_btn_license.setCursor(Qt.CursorShape.PointingHandCursor)
        self.header_btn_license.clicked.connect(self._open_license_dialog)
        cu_layout.addWidget(self.header_btn_license)

        right_box.addWidget(self.capsule_util)
        layout.addLayout(right_box)

        self._apply_header_theme(self.is_dark_theme)
        return self.header_frame

    def _update_brand_logo(self):
        logo_path = get_asset_path("logo.png")
        if logo_path.exists():
            pix = QPixmap(str(logo_path)).scaled(
                36, 36,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.avatar_lbl.setPixmap(pix)
            self.avatar_lbl.setStyleSheet("border-radius: 8px; border: 1px solid #4338ca; background: #0f172a;")
        else:
            self.avatar_lbl.setText("SMG")
            self.avatar_lbl.setStyleSheet("""
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6366f1, stop:1 #a855f7);
                color: #ffffff;
                font-size: 11px;
                font-weight: 900;
                border-radius: 8px;
                border: 1px solid #818cf8;
            """)

    def _populate_theme_menu(self):
        self.theme_menu.clear()
        for t_key, t_data in STUDIO_THEMES.items():
            is_active = (t_key == getattr(self, "current_theme", "obsidian"))
            mark = "✓ " if is_active else "   "
            action = self.theme_menu.addAction(f"{mark}{t_data['icon']} {t_data['name']}")
            action.triggered.connect(lambda _, k=t_key: self.set_theme(k))

    def _update_theme_btn_label(self):
        t_data = get_theme(getattr(self, "current_theme", "obsidian"))
        self.header_btn_theme.setText(f"{t_data['icon']} ▾")
        self.header_btn_theme.setToolTip(f"Studio Theme: {t_data['name']}\nClick to select from 5 Modern Studio Themes")
        self.header_btn_theme.setFixedWidth(46)

    def set_theme(self, theme_id: str):
        t_data = get_theme(theme_id)
        self.current_theme = t_data["id"]
        self.is_dark_theme = t_data["is_dark"]
        config_manager.set("theme", self.current_theme)

        app = QApplication.instance()
        if app:
            app.setStyleSheet(t_data["qss"])

        self._apply_all_themes(self.current_theme)
        self._update_theme_btn_label()
        self._populate_theme_menu()
        self.status_bar.showMessage(f"Switched to {t_data['name']} Studio Theme", 2500)

    def _toggle_theme(self):
        theme_keys = list(STUDIO_THEMES.keys())
        cur_idx = theme_keys.index(self.current_theme) if self.current_theme in theme_keys else 0
        next_key = theme_keys[(cur_idx + 1) % len(theme_keys)]
        self.set_theme(next_key)

    def _apply_header_theme(self, theme_or_dark=None):
        if isinstance(theme_or_dark, str):
            theme_key = theme_or_dark
        elif isinstance(theme_or_dark, bool):
            theme_key = "obsidian" if theme_or_dark else "canvas_light"
        else:
            theme_key = getattr(self, "current_theme", "obsidian")

        t_data = get_theme(theme_key)
        self.is_dark_theme = t_data["is_dark"]
        self._update_brand_logo()

        h_start = t_data.get("header_start", "#111424")
        h_end = t_data.get("header_end", "#0a0c16")
        border = t_data.get("border", "#1e2540")
        accent = t_data.get("accent", "#8b5cf6")
        accent_sec = t_data.get("accent_secondary", "#7c3aed")
        text_pri = t_data.get("text_primary", "#ffffff")
        text_sec = t_data.get("text_secondary", "#94a3b8")
        sub_text = t_data.get("header_sub_text", "#38bdf8")
        btn_bg = t_data.get("bg_btn", "#161b2e")
        btn_hover = t_data.get("bg_btn_hover", "#222944")
        border_subtle = t_data.get("border_subtle", "#283256")
        bg_card = t_data.get("bg_card", "#111526")

        if t_data["is_dark"]:
            self.header_frame.setStyleSheet(f"""
                QFrame#mainHeaderBar {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {h_start}, stop:1 {h_end});
                    border-bottom: 1px solid {border};
                    padding: 4px 10px;
                }}
            """)
            self.header_title_lbl.setStyleSheet(f"font-size: 15px; font-weight: 800; color: {text_pri}; background: transparent;")
            self.header_sub_lbl.setStyleSheet(f"font-size: 11px; color: {sub_text}; font-weight: 600; background: transparent;")
            
            if hasattr(self, "header_stage_pill"):
                self.header_stage_pill.setStyleSheet(f"""
                    QLabel#headerStagePill {{
                        background: {bg_card};
                        color: {accent};
                        font-size: 10px;
                        font-weight: 800;
                        padding: 2px 8px;
                        border-radius: 11px;
                        border: 1px solid {accent_sec};
                    }}
                """)

            self.header_mode_box.setStyleSheet(f"background-color: {h_end}; border: 1px solid {border}; border-radius: 8px; padding: 2px;")
            
            mode_btn_qss = f"""
                QPushButton {{
                    background-color: transparent;
                    color: {text_sec};
                    font-weight: 700;
                    padding: 4px 8px;
                    border: none;
                    border-radius: 6px;
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    color: {text_pri};
                    background-color: {btn_hover};
                }}
                QPushButton:checked {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {accent_sec}, stop:1 {accent});
                    color: #ffffff;
                    font-weight: 800;
                    border: 1px solid {accent};
                }}
            """
            for btn in [self.btn_mode_wizard, self.btn_mode_visual, self.btn_mode_batch, self.btn_mode_editor, self.btn_mode_clone]:
                btn.setStyleSheet(mode_btn_qss)

            capsule_qss = f"""
                QFrame {{
                    background-color: {bg_card};
                    border: 1px solid {border};
                    border-radius: 8px;
                }}
            """
            if hasattr(self, "capsule_prod"):
                self.capsule_prod.setStyleSheet(capsule_qss)
            if hasattr(self, "capsule_util"):
                self.capsule_util.setStyleSheet(capsule_qss)

            self.header_model_combo.setStyleSheet(f"""
                QComboBox {{
                    background-color: {btn_bg};
                    color: {sub_text};
                    font-weight: 700;
                    font-size: 9pt;
                    border: 1px solid {border_subtle};
                    border-radius: 6px;
                    padding: 3px 6px;
                }}
                QComboBox:hover {{
                    border-color: {accent};
                }}
                QComboBox QAbstractItemView {{
                    background-color: {bg_card};
                    color: {text_pri};
                    selection-background-color: {accent_sec};
                }}
            """)
            header_sub_btn_qss = f"""
                QPushButton {{
                    background-color: {btn_bg};
                    color: {text_pri};
                    border: 1px solid {border_subtle};
                    font-weight: 600;
                    font-size: 9pt;
                    padding: 4px 8px;
                    border-radius: 6px;
                }}
                QPushButton:hover {{
                    background-color: {btn_hover};
                    color: #ffffff;
                    border-color: {accent};
                }}
            """
            for b in [self.header_btn_new, self.btn_export, self.header_btn_history, self.header_btn_theme, self.header_btn_settings]:
                b.setStyleSheet(header_sub_btn_qss)
            if hasattr(self, "header_btn_update"):
                self.header_btn_update.setStyleSheet(f"""
                    QPushButton {{
                        background: {t_data.get('accent_gradient', 'qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8b5cf6, stop:1 #ec4899)')};
                        color: #ffffff;
                        border: 1px solid rgba(255, 255, 255, 0.4);
                        font-weight: 800;
                        font-size: 9pt;
                        padding: 4px 10px;
                        border-radius: 6px;
                    }}
                    QPushButton:hover {{
                        border-color: #ffffff;
                        opacity: 0.92;
                    }}
                """)
            self.export_menu.setStyleSheet(f"background-color: {bg_card}; color: {text_pri}; border: 1px solid {border_subtle}; padding: 4px;")
            self.theme_menu.setStyleSheet(f"background-color: {bg_card}; color: {text_pri}; border: 1px solid {border_subtle}; padding: 4px;")
            self._update_license_btn_style()

            # Style Workflow Ribbon
            if hasattr(self, "workflow_ribbon"):
                self.workflow_ribbon.setStyleSheet(f"""
                    QFrame#workflowRibbon {{
                        background: {h_end};
                        border-bottom: 1px solid {border};
                    }}
                """)
                self.lbl_ribbon_info.setStyleSheet(f"color: {text_pri}; font-size: 11px; font-weight: 600; background: transparent;")
                self.lbl_ribbon_hint.setStyleSheet(f"color: {text_sec}; font-size: 10px; font-weight: 500; background: transparent;")
                self.btn_ribbon_action.setStyleSheet(f"""
                    QPushButton#btnRibbonAction {{
                        background: {accent_sec};
                        color: #ffffff;
                        font-weight: 700;
                        font-size: 11px;
                        padding: 3px 12px;
                        border-radius: 6px;
                        border: 1px solid {accent};
                    }}
                    QPushButton#btnRibbonAction:hover {{
                        background: {accent};
                    }}
                """)

            # Style Editor Workbench Toolbar
            if hasattr(self, "wb_toolbar"):
                self.wb_toolbar.setStyleSheet(f"""
                    QFrame#editorWorkbenchToolbar {{
                        background-color: {bg_card};
                        border: 1px solid {border};
                        border-radius: 8px;
                    }}
                """)
                wb_btn_qss = f"""
                    QPushButton {{
                        background-color: {btn_bg};
                        color: {text_pri};
                        border: 1px solid {border_subtle};
                        font-weight: 700;
                        font-size: 11px;
                        padding: 4px 10px;
                        border-radius: 6px;
                    }}
                    QPushButton:hover {{
                        background-color: {btn_hover};
                        border-color: {accent};
                    }}
                    QPushButton:checked {{
                        background-color: {accent_sec};
                        color: #ffffff;
                        border-color: {accent};
                    }}
                """
                self.btn_toggle_generator.setStyleSheet(wb_btn_qss)
                self.btn_toggle_tools.setStyleSheet(wb_btn_qss)
                self.btn_focus_mode.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {btn_bg};
                        color: #38bdf8;
                        border: 1px solid {border_subtle};
                        font-weight: 700;
                        font-size: 11px;
                        padding: 4px 10px;
                        border-radius: 6px;
                    }}
                    QPushButton:hover {{
                        background-color: {btn_hover};
                        border-color: #38bdf8;
                    }}
                    QPushButton:checked {{
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #38bdf8);
                        color: #ffffff;
                        border-color: #38bdf8;
                    }}
                """)
                self.btn_suno_copy_quick.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {btn_bg};
                        color: #34d399;
                        border: 1px solid #059669;
                        font-weight: 700;
                        font-size: 11px;
                        padding: 4px 10px;
                        border-radius: 6px;
                    }}
                    QPushButton:hover {{
                        background-color: #065f46;
                        color: #ffffff;
                    }}
                """)
                self.lbl_editor_status.setStyleSheet(f"color: {text_sec}; font-size: 11px; font-weight: 600; background: transparent;")
        else:
            self.header_frame.setStyleSheet("""
                QFrame#mainHeaderBar {
                    background-color: #ffffff;
                    border-bottom: 1px solid #cbd5e1;
                    padding: 4px 10px;
                }
            """)
            self.header_title_lbl.setStyleSheet("font-size: 15px; font-weight: 800; color: #0f172a; background: transparent;")
            self.header_sub_lbl.setStyleSheet("font-size: 11px; color: #1e293b; font-weight: 600; background: transparent;")

            if hasattr(self, "header_stage_pill"):
                self.header_stage_pill.setStyleSheet("""
                    QLabel#headerStagePill {
                        background: #eff6ff;
                        color: #1d4ed8;
                        font-size: 10px;
                        font-weight: 800;
                        padding: 2px 8px;
                        border-radius: 11px;
                        border: 1px solid #93c5fd;
                    }
                """)

            self.header_mode_box.setStyleSheet("background-color: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 8px; padding: 2px;")
            mode_btn_qss = """
                QPushButton {
                    background-color: transparent;
                    color: #1e293b;
                    font-weight: 700;
                    padding: 4px 8px;
                    border: none;
                    border-radius: 6px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    color: #2563eb;
                    background-color: #e2e8f0;
                }
                QPushButton:checked {
                    background-color: #2563eb;
                    color: #ffffff;
                    font-weight: 800;
                }
            """
            for btn in [self.btn_mode_wizard, self.btn_mode_visual, self.btn_mode_batch, self.btn_mode_editor, self.btn_mode_clone]:
                btn.setStyleSheet(mode_btn_qss)

            capsule_qss = """
                QFrame {
                    background-color: #ffffff;
                    border: 1px solid #cbd5e1;
                    border-radius: 8px;
                }
            """
            if hasattr(self, "capsule_prod"):
                self.capsule_prod.setStyleSheet(capsule_qss)
            if hasattr(self, "capsule_util"):
                self.capsule_util.setStyleSheet(capsule_qss)

            self.header_model_combo.setStyleSheet("""
                QComboBox {
                    background-color: #ffffff;
                    color: #1d4ed8;
                    font-weight: 700;
                    font-size: 9pt;
                    border: 1px solid #93c5fd;
                    border-radius: 6px;
                    padding: 3px 6px;
                }
                QComboBox:hover {
                    border-color: #2563eb;
                }
                QComboBox QAbstractItemView {
                    background-color: #ffffff;
                    color: #0f172a;
                    selection-background-color: #2563eb;
                    selection-color: #ffffff;
                }
            """)
            header_sub_btn_qss = """
                QPushButton {
                    background-color: #ffffff;
                    color: #0f172a;
                    border: 1px solid #cbd5e1;
                    font-weight: 700;
                    font-size: 9pt;
                    padding: 4px 8px;
                    border-radius: 6px;
                }
                QPushButton:hover {
                    background-color: #f1f5f9;
                    border-color: #2563eb;
                    color: #2563eb;
                }
            """
            for b in [self.header_btn_new, self.btn_export, self.header_btn_history, self.header_btn_theme, self.header_btn_settings]:
                b.setStyleSheet(header_sub_btn_qss)
            if hasattr(self, "header_btn_update"):
                self.header_btn_update.setStyleSheet(f"""
                    QPushButton {{
                        background: {t_data.get('accent_gradient', 'qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8b5cf6, stop:1 #ec4899)')};
                        color: #ffffff;
                        border: 1px solid rgba(255, 255, 255, 0.4);
                        font-weight: 800;
                        font-size: 9pt;
                        padding: 4px 10px;
                        border-radius: 6px;
                    }}
                    QPushButton:hover {{
                        border-color: #ffffff;
                        opacity: 0.92;
                    }}
                """)
            self.export_menu.setStyleSheet("background-color: #ffffff; color: #0f172a; border: 1px solid #cbd5e1; padding: 4px;")
            self.theme_menu.setStyleSheet("background-color: #ffffff; color: #0f172a; border: 1px solid #cbd5e1; padding: 4px;")
            self._update_license_btn_style()

            # Style Workflow Ribbon
            if hasattr(self, "workflow_ribbon"):
                self.workflow_ribbon.setStyleSheet("""
                    QFrame#workflowRibbon {
                        background: #f1f5f9;
                        border-bottom: 1px solid #cbd5e1;
                    }
                """)
                self.lbl_ribbon_info.setStyleSheet("color: #0f172a; font-size: 11px; font-weight: 700; background: transparent;")
                self.lbl_ribbon_hint.setStyleSheet("color: #334155; font-size: 10px; font-weight: 600; background: transparent;")
                self.btn_ribbon_action.setStyleSheet("""
                    QPushButton#btnRibbonAction {
                        background: #2563eb;
                        color: #ffffff;
                        font-weight: 700;
                        font-size: 11px;
                        padding: 3px 12px;
                        border-radius: 6px;
                        border: 1px solid #1d4ed8;
                    }
                    QPushButton#btnRibbonAction:hover {
                        background: #1d4ed8;
                    }
                """)

            # Style Editor Workbench Toolbar
            if hasattr(self, "wb_toolbar"):
                self.wb_toolbar.setStyleSheet("""
                    QFrame#editorWorkbenchToolbar {
                        background-color: #f8fafc;
                        border: 1px solid #e2e8f0;
                        border-radius: 8px;
                    }
                """)
                wb_btn_qss = """
                    QPushButton {
                        background-color: #ffffff;
                        color: #334155;
                        border: 1px solid #cbd5e1;
                        font-weight: 700;
                        font-size: 11px;
                        padding: 4px 10px;
                        border-radius: 6px;
                    }
                    QPushButton:hover {
                        background-color: #f1f5f9;
                        border-color: #94a3b8;
                    }
                    QPushButton:checked {
                        background-color: #2563eb;
                        color: #ffffff;
                        border-color: #1d4ed8;
                    }
                """
                self.btn_toggle_generator.setStyleSheet(wb_btn_qss)
                self.btn_toggle_tools.setStyleSheet(wb_btn_qss)
                self.btn_focus_mode.setStyleSheet("""
                    QPushButton {
                        background-color: #eff6ff;
                        color: #0284c7;
                        border: 1px solid #7dd3fc;
                        font-weight: 700;
                        font-size: 11px;
                        padding: 4px 10px;
                        border-radius: 6px;
                    }
                    QPushButton:hover {
                        background-color: #e0f2fe;
                        border-color: #0284c7;
                    }
                    QPushButton:checked {
                        background-color: #0284c7;
                        color: #ffffff;
                        border-color: #0369a1;
                    }
                """)
                self.btn_suno_copy_quick.setStyleSheet("""
                    QPushButton {
                        background-color: #f0fdf4;
                        color: #15803d;
                        border: 1px solid #86efac;
                        font-weight: 700;
                        font-size: 11px;
                        padding: 4px 10px;
                        border-radius: 6px;
                    }
                    QPushButton:hover {
                        background-color: #dcfce7;
                        border-color: #16a34a;
                    }
                """)
                self.lbl_editor_status.setStyleSheet("color: #334155; font-size: 11px; font-weight: 700; background: transparent;")

    def _set_studio_mode(self, index: int):
        self.btn_mode_wizard.setChecked(index == 0)
        self.btn_mode_visual.setChecked(index == 1)
        self.btn_mode_batch.setChecked(index == 2)
        self.btn_mode_editor.setChecked(index == 3)
        self.btn_mode_clone.setChecked(index == 4)
        self.stack.setCurrentIndex(index)

        mode_titles = ["🗺️ WIZARD", "🎨 VISUAL", "⚡ BATCH", "✍️ EDITOR", "🧬 CLONE"]
        ribbon_infos = [
            "🗺️ Wizard Studio • Step-by-step guided song creation with automatic genre & prompt setup",
            "🎨 Visual Arranger • Suno AI visual prompt tags, mood matrix & live formula preview",
            "⚡ Batch Studio Pro • Multi-song generation, anti-cliché shuffler & album story arcs",
            "✍️ Lyric Editor Workbench • 3-pane DAW lyric writing, syllable meter, chord transposer & takes",
            "🧬 Song DNA Cloner • Deep structure & cadence cloner with twin rhyme scheme generator"
        ]
        action_labels = [
            "✍️ Open in Editor ➔",
            "✍️ Open in Editor ➔",
            "✍️ Open in Editor ➔",
            "🎨 Open in Arranger ➔",
            "✍️ Open in Editor ➔"
        ]

        if hasattr(self, "header_stage_pill") and 0 <= index < len(mode_titles):
            self.header_stage_pill.setText(mode_titles[index])
        if hasattr(self, "lbl_ribbon_info") and 0 <= index < len(ribbon_infos):
            self.lbl_ribbon_info.setText(ribbon_infos[index])
        if hasattr(self, "btn_ribbon_action") and 0 <= index < len(action_labels):
            self.btn_ribbon_action.setText(action_labels[index])

        if index == 1 and hasattr(self, "visual_studio") and hasattr(self.visual_studio, "_check_and_update_columns"):
            QTimer.singleShot(0, self.visual_studio._check_and_update_columns)
        elif index == 2 and hasattr(self, "batch_view") and hasattr(self.batch_view, "_check_and_update_columns"):
            QTimer.singleShot(0, self.batch_view._check_and_update_columns)
        elif index == 3 and hasattr(self, "splitter"):
            if hasattr(self, "_update_editor_workbench_metrics"):
                self._update_editor_workbench_metrics()
        elif index == 4 and hasattr(self, "clone_view"):
            cur_lyrics = self.editor_panel.get_lyrics()
            if cur_lyrics and len(cur_lyrics.strip()) > 30:
                self.clone_view.set_reference(cur_lyrics, self.editor_panel.get_title())

    def _setup_global_shortcuts(self):
        # Studio Modes 1-5
        QShortcut(QKeySequence("Ctrl+1"), self).activated.connect(lambda: self._set_studio_mode(0))
        QShortcut(QKeySequence("Ctrl+2"), self).activated.connect(lambda: self._set_studio_mode(1))
        QShortcut(QKeySequence("Ctrl+3"), self).activated.connect(lambda: self._set_studio_mode(2))
        QShortcut(QKeySequence("Ctrl+4"), self).activated.connect(lambda: self._set_studio_mode(3))
        QShortcut(QKeySequence("Ctrl+5"), self).activated.connect(lambda: self._set_studio_mode(4))

        # Workflow Actions
        QShortcut(QKeySequence("Ctrl+N"), self).activated.connect(self._new_song)
        QShortcut(QKeySequence("Ctrl+O"), self).activated.connect(self._open_file)
        QShortcut(QKeySequence("Ctrl+E"), self).activated.connect(self._show_export_menu)
        QShortcut(QKeySequence("Ctrl+H"), self).activated.connect(self._open_history)
        QShortcut(QKeySequence("Ctrl+,"), self).activated.connect(self._open_settings)
        QShortcut(QKeySequence("Ctrl+T"), self).activated.connect(self._toggle_theme)
        QShortcut(QKeySequence("Ctrl+F"), self).activated.connect(self._toggle_focus_mode)
        QShortcut(QKeySequence("Ctrl+Shift+C"), self).activated.connect(self._quick_copy_suno)
        QShortcut(QKeySequence("F11"), self).activated.connect(self._toggle_fullscreen)

    def _show_export_menu(self):
        if hasattr(self, "export_menu") and hasattr(self, "btn_export"):
            self.export_menu.popup(self.btn_export.mapToGlobal(self.btn_export.rect().bottomLeft()))

    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def _apply_all_themes(self, theme_or_dark=None):
        if isinstance(theme_or_dark, str):
            theme_key = theme_or_dark
        elif isinstance(theme_or_dark, bool):
            theme_key = "obsidian" if theme_or_dark else "canvas_light"
        else:
            theme_key = getattr(self, "current_theme", "obsidian")

        t_data = get_theme(theme_key)
        self.current_theme = t_data["id"]
        is_dark = t_data["is_dark"]
        self.is_dark_theme = is_dark

        app = QApplication.instance()
        if app:
            app.setStyleSheet(t_data["qss"])

        self._apply_header_theme(theme_key)
        if hasattr(self, "generator_panel"):
            self.generator_panel.apply_theme(theme_key)
        if hasattr(self, "editor_panel"):
            self.editor_panel.apply_theme(theme_key)
        if hasattr(self, "tools_panel"):
            self.tools_panel.apply_theme(theme_key)
        if hasattr(self, "visual_studio"):
            self.visual_studio.apply_theme(theme_key)
        if hasattr(self, "wizard_view"):
            self.wizard_view.apply_theme(theme_key)
        if hasattr(self, "batch_view"):
            self.batch_view.apply_theme(theme_key)
        if hasattr(self, "clone_view") and self.clone_view:
            self.clone_view.apply_theme(theme_key)

    def _connect_panels(self):
        # Master Studio Transport Bar removed: each tab has its own dedicated controls

        # Easy Songwriting Wizard signals
        self.wizard_view.generate_requested.connect(self._start_generation)
        self.wizard_view.open_editor_requested.connect(lambda: self._set_studio_mode(3))
        self.wizard_view.open_batch_requested.connect(self._send_wizard_to_batch)
        self.wizard_view.export_bundle_requested.connect(self._export_bundle)
        self.wizard_view.btn_w_metro.clicked.connect(self.editor_panel._toggle_metronome)
        self.wizard_view.btn_w_record.clicked.connect(self._on_wizard_toggle_recording)
        self.wizard_view.btn_w_play_rec.clicked.connect(self.tools_panel._play_scratch_take)

        # Visual Studio signals
        self.visual_studio.generate_requested.connect(self._start_generation_from_visual)
        self.visual_studio.demo_requested.connect(self._load_demo_from_visual)
        self.visual_studio.open_editor_requested.connect(self._transfer_to_editor)
        self.visual_studio.open_batch_requested.connect(self._send_visual_to_batch)
        self.visual_studio.export_bundle_requested.connect(self._export_bundle)

        # Batch Multi-Song Studio Pro signals
        self.batch_view.open_editor_requested.connect(self._load_song_from_batch)
        self.batch_view.open_visual_requested.connect(self._load_song_into_visual_arranger)

        # Editor Panel signals
        self.editor_panel.visual_arranger_requested.connect(lambda: self._set_studio_mode(1))
        self.editor_panel.transpose_requested.connect(self._on_transpose_chords)
        self.editor_panel.rhyme_search_requested.connect(self._search_rhyme_from_editor)
        self.editor_panel.clone_song_requested.connect(self._open_song_cloner)

        # Generator Panel triggers
        self.generator_panel.generate_requested.connect(self._start_generation)
        self.generator_panel.demo_requested.connect(self._load_demo)
        self.generator_panel.load_skeleton_requested.connect(self._on_skeleton_loaded)

        # Editor Panel triggers
        self.editor_panel.rewrite_requested.connect(self._start_rewrite)

        # Tools Panel triggers
        self.tools_panel.rhyme_requested.connect(self._start_rhyme_search)
        self.tools_panel.suno_prompt_requested.connect(self._start_suno_prompt)
        self.tools_panel.transpose_requested.connect(self._on_transpose_chords)
        self.tools_panel.insert_text_requested.connect(self.editor_panel.insert_text_at_cursor)

    def _load_song_from_batch(self, song_data: dict):
        title = song_data.get("title", "Untitled Track")
        lyrics = song_data.get("lyrics", "")
        style = song_data.get("style_prompt", "")
        bpm_str = song_data.get("bpm", "120 BPM")
        key = song_data.get("key", "C")

        self.editor_panel.set_title(title)
        self.editor_panel.set_lyrics(lyrics)
        try:
            bpm_val = int("".join(filter(str.isdigit, str(bpm_str)[:4])))
            self.editor_panel.metro_bpm_spin.setValue(bpm_val)
        except Exception:
            pass

        self._set_studio_mode(3) # Switch to Lyric Editor
        self.status_bar.showMessage(f"Loaded '{title}' into Lyric Editor Workbench", 3000)

    def _on_wizard_toggle_recording(self):
        self.tools_panel._toggle_mic_recording()
        if self.tools_panel.melody_recorder.is_recording:
            self.wizard_view.btn_w_record.setText("⏹ Stop Recording")
            self.wizard_view.btn_w_record.setStyleSheet("background-color: #dc2626; color: #ffffff; font-weight: 700; border-radius: 6px; padding: 10px;")
            self.wizard_view.lbl_w_rec_status.setText("Recording from microphone... Sing or hum your melody take")
            self.wizard_view.btn_w_play_rec.setEnabled(False)
        else:
            self.wizard_view.btn_w_record.setText("🔴 Record Scratch Melody (Mic)")
            self.wizard_view.btn_w_record.setStyleSheet("background-color: #fee2e2; color: #dc2626; font-weight: 700; border: 1px solid #fca5a5; border-radius: 6px; padding: 10px;")
            self.wizard_view.lbl_w_rec_status.setText("Voice take saved successfully!")
            self.wizard_view.btn_w_play_rec.setEnabled(True)

    def _on_transpose_chords(self, semitones: int):
        from app.chord_engine import ChordEngine
        lyrics = self.editor_panel.get_lyrics()
        if lyrics:
            transposed = ChordEngine.transpose_lyrics_with_chords(lyrics, semitones)
            self.editor_panel.set_lyrics(transposed)
            dir_str = f"+{semitones}" if semitones > 0 else f"{semitones}"
            self.status_bar.showMessage(f"Transposed chords in lyrics by {dir_str} semitone(s)", 3000)
        self.visual_studio._transpose_chords(semitones)

    def _transfer_to_editor(self, params: dict):
        self._set_studio_mode(3)
        # Update generator panel inputs to match visual studio
        self.generator_panel.custom_notes.setText(params.get("user_notes", ""))
        if "genre" in params:
            idx = self.generator_panel.genre_combo.findText(params["genre"])
            if idx >= 0:
                self.generator_panel.genre_combo.setCurrentIndex(idx)
        if "bpm" in params:
            try:
                bpm_val = int("".join(filter(str.isdigit, str(params["bpm"])[:4])))
                self.editor_panel.metro_bpm_spin.setValue(bpm_val)
            except Exception:
                pass
        if "theme" in params and params["theme"]:
            t_clean = params["theme"][:40]
            self.editor_panel.set_title(t_clean)
        self.status_bar.showMessage("Transferred formula parameters to Lyric Editor Workbench", 3000)

    def _load_song_into_visual_arranger(self, song_data: dict):
        title = song_data.get("title", "Untitled Track")
        genre = song_data.get("genre", "Modern Pop")
        bpm_str = song_data.get("bpm", "120 BPM")
        key = song_data.get("key", "C")
        style = song_data.get("style_prompt", "")

        # Sync visual studio properties directly

        # Update Visual Studio properties
        self.visual_studio.current_bpm = f"{bpm_str}"
        self.visual_studio.current_key = key
        self.visual_studio.current_genre = genre
        if hasattr(self.visual_studio, "lbl_bpm_display"):
            self.visual_studio.lbl_bpm_display.setText(f"{bpm_str}")
        if hasattr(self.visual_studio, "lbl_key_display"):
            self.visual_studio.lbl_key_display.setText(f"{key}")
        if hasattr(self.visual_studio, "txt_suno_prompt"):
            self.visual_studio.txt_suno_prompt.setPlainText(style)
        self.visual_studio._update_formula_card()

        # Switch to Visual Studio tab (index 1)
        self._set_studio_mode(1)
        self.status_bar.showMessage(f"Loaded '{title}' into Visual Arranger (DAW Timeline & Chords)", 3000)

    def _send_visual_to_batch(self, params: dict):
        genre = params.get("genre", "sad song")
        mood = params.get("mood", "emotional")
        theme_txt = f"{genre}, {mood}".strip(", ")
        self.batch_view.txt_theme.setPlainText(theme_txt if theme_txt else "sad song")
        if "user_notes" in params:
            self.batch_view.txt_story_seed.setPlainText(params["user_notes"])
        lang = params.get("language", "Both")
        self.batch_view._set_language("Khmer" if "Khmer" in lang else ("English" if "English" in lang else "Both"))
        self._set_studio_mode(2)
        self.status_bar.showMessage(f"Loaded formula into Batch Studio Pro: '{theme_txt}'", 3000)

    def _send_wizard_to_batch(self, params: dict):
        genre = params.get("genre", "sad song")
        mood = params.get("mood", "emotional")
        theme_txt = f"{genre}, {mood}".strip(", ")
        self.batch_view.txt_theme.setPlainText(theme_txt if theme_txt else "sad song")
        story = params.get("storyline", "") or params.get("theme", "")
        if story:
            self.batch_view.txt_story_seed.setPlainText(story)
        lang = params.get("language", "Both")
        self.batch_view._set_language("Khmer" if "Khmer" in lang else ("English" if "English" in lang else "Both"))
        self._set_studio_mode(2)
        self.status_bar.showMessage(f"Loaded Wizard concept into Batch Studio Pro: '{theme_txt}'", 3000)

    def _start_generation_from_visual(self, params: dict):
        # Switch to editor to see the generated lyrics
        self._set_studio_mode(3)
        self._start_generation(params)

    def _load_demo_from_visual(self, params: dict):
        self._set_studio_mode(3)
        self._load_demo(params)

    def _on_skeleton_loaded(self, skeleton_text: str):
        self.editor_panel.set_lyrics(skeleton_text)
        preset_name = self.generator_panel.preset_combo.currentText()
        if preset_name and not preset_name.startswith("—"):
            import re
            raw_title = preset_name.split("(")[0]
            clean_title = re.sub(r'[^\w\s\-\u1780-\u17FF]', '', raw_title).strip()
            self.editor_panel.set_title(clean_title if clean_title else "Untitled Track")
        self.status_bar.showMessage("Loaded song structure template into editor", 3000)

    def _start_generation(self, params: dict):
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.wait(1000)

        self.generator_panel.set_loading(True)
        self.status_bar.showMessage(f"Composing {params.get('genre')} lyrics with Gemini...")

        self.current_worker = GenerateLyricWorker(params)
        self.current_worker.finished.connect(self._on_generation_finished)
        self.current_worker.error.connect(self._on_worker_error)
        self.current_worker.status_update.connect(lambda msg: self.status_bar.showMessage(msg))
        self.current_worker.start()

    def _load_demo(self, params: dict):
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.wait(1000)

        self.generator_panel.set_loading(True)
        fake_params = params.copy()
        fake_params["demo_only"] = True
        self.current_worker = GenerateLyricWorker(fake_params)
        self.current_worker.finished.connect(self._on_generation_finished)
        self.current_worker.error.connect(self._on_worker_error)
        self.current_worker.start()

    def _on_generation_finished(self, title: str, lyrics: str):
        self.generator_panel.set_loading(False)
        self.editor_panel.set_title(title)
        self.editor_panel.set_lyrics(lyrics)
        self.wizard_view.set_generated_lyrics(title, lyrics)
        self.status_bar.showMessage(f"Lyrics successfully generated: '{title}'", 5000)

        # Save to history
        params = self.generator_panel.get_generation_parameters()
        history_entry = {
            "title": title,
            "lyrics": lyrics,
            "genre": params.get("genre", "Pop"),
            "region": params.get("region", "Global"),
            "language": params.get("language", "English")
        }
        config_manager.add_history(history_entry)

    def _start_rewrite(self, selected_text: str, instruction: str):
        params = self.generator_panel.get_generation_parameters()
        genre = params.get("genre", "Pop")
        self.status_bar.showMessage(f"Refining selection: {instruction}...")

        self.rewrite_worker = RewriteWorker(selected_text, instruction, genre)
        self.rewrite_worker.finished.connect(self._on_rewrite_finished)
        self.rewrite_worker.error.connect(self._on_worker_error)
        self.rewrite_worker.start()

    def _on_rewrite_finished(self, rewritten_text: str):
        self.editor_panel.replace_selection(rewritten_text)
        self.status_bar.showMessage("Selection successfully updated with Gemini!", 4000)

    def _search_rhyme_from_editor(self, word: str):
        if hasattr(self, "tools_panel"):
            self.tools_panel.tabs.setCurrentIndex(0)
            self.tools_panel.rhyme_input.setText(word)
        self._start_rhyme_search(word)

    def _start_rhyme_search(self, word: str):
        params = self.generator_panel.get_generation_parameters()
        genre = params.get("genre", "Pop")
        self.rhyme_worker = RhymeWorker(word, genre)
        self.rhyme_worker.finished.connect(lambda res: self.tools_panel.set_rhyme_results(res))
        self.rhyme_worker.error.connect(self._on_worker_error)
        self.rhyme_worker.start()

    def _start_suno_prompt(self):
        params = self.generator_panel.get_generation_parameters()
        lyrics = self.editor_panel.get_lyrics()
        self.tools_panel.set_suno_results("Generating Suno & Udio prompts with Gemini...")

        self.suno_worker = SunoPromptWorker(
            genre=params.get("genre", "Pop"),
            region=params.get("region", "Global"),
            mood=params.get("mood", "Euphoric"),
            lyrics_sample=lyrics
        )
        self.suno_worker.finished.connect(lambda res: self.tools_panel.set_suno_results(res))
        self.suno_worker.error.connect(self._on_worker_error)
        self.suno_worker.start()

    def _on_worker_error(self, err_msg: str):
        self.generator_panel.set_loading(False)
        self.status_bar.showMessage(f"Error: {err_msg}", 6000)
        QMessageBox.warning(self, "AI Generation Notice", f"Notice:\n\n{err_msg}\n\nTip: You can add or verify your free API key in Settings, or use 'Load Genre Demo Track'.")

    def _new_song(self):
        # If in Batch Multi-Song Studio Pro mode (tab index 2), delegate to Batch New Project
        if hasattr(self, "stack") and self.stack.currentIndex() == 2 and hasattr(self, "batch_view"):
            self.batch_view.new_batch_project()
            return

        cur_text = self.editor_panel.get_lyrics().strip()
        if cur_text:
            reply = QMessageBox.question(
                self, "New Song", "Start a new lyric sheet? Any unsaved edits will be cleared.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        self.editor_panel.set_title("Untitled Song")
        self.editor_panel.set_lyrics("")
        self.status_bar.showMessage("New lyric session started", 3000)

    def _open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Lyrics", "", "Lyric Files (*.txt *.lrc *.json);;All Files (*.*)"
        )
        if not path:
            return

        p = Path(path)
        try:
            with open(p, "r", encoding="utf-8") as f:
                content = f.read()

            self.editor_panel.set_title(p.stem)
            self.editor_panel.set_lyrics(content)
            self._set_studio_mode(3) # Switch to Lyric Editor
            self.status_bar.showMessage(f"Loaded: {p.name}", 4000)
        except Exception as e:
            QMessageBox.critical(self, "Error Loading File", str(e))

    def _export(self, fmt: str):
        title = self.editor_panel.get_title()
        lyrics = self.editor_panel.get_lyrics()
        if not lyrics.strip():
            QMessageBox.warning(self, "Export", "There are no lyrics to export yet. Generate or write lyrics first.")
            return

        metadata = self.generator_panel.get_generation_parameters()
        safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "_", "-")).strip()

        ext_map = {
            "srt": ("Video Subtitles (*.srt)", f"{safe_title}.srt"),
            "lrc": ("Karaoke Timed Lyrics (*.lrc)", f"{safe_title}.lrc"),
            "vocal": ("Singer Vocal Sheet (*.txt)", f"{safe_title}_vocals.txt"),
            "chordpro": ("ChordPro Lead Sheet (*.cho)", f"{safe_title}.cho"),
            "txt": ("Complete Lyric Sheet (*.txt)", f"{safe_title}.txt"),
            "lrc": ("Karaoke Timed Lyrics (*.lrc)", f"{safe_title}.lrc"),
            "pdf": ("Printable PDF Lead Sheet (*.pdf)", f"{safe_title}.pdf"),
            "html": ("Interactive Printable HTML Lead Sheet (*.html)", f"{safe_title}.html"),
            "json": ("Structured JSON (*.json)", f"{safe_title}.json")
        }

        filter_str, default_name = ext_map.get(fmt, ("All Files (*.*)", f"{safe_title}.{fmt}"))
        filepath, _ = QFileDialog.getSaveFileName(self, f"Export as {fmt.upper()}", default_name, filter_str)

        if not filepath:
            return

        try:
            if fmt == "srt":
                Exporter.export_srt(filepath, title, lyrics, metadata.get("bpm", "120"))
            elif fmt == "vocal":
                Exporter.export_clean_vocal_sheet(filepath, title, lyrics)
            elif fmt == "chordpro":
                Exporter.export_chordpro(filepath, title, lyrics, metadata)
            elif fmt == "txt":
                Exporter.export_txt(filepath, title, lyrics, metadata)
            elif fmt == "lrc":
                Exporter.export_lrc(filepath, title, lyrics, metadata.get("bpm", "120"))
            elif fmt == "pdf":
                Exporter.export_pdf(filepath, title, lyrics, metadata)
            elif fmt == "html":
                Exporter.export_html_lead_sheet(filepath, title, lyrics, metadata)
            elif fmt == "json":
                Exporter.export_json(filepath, title, lyrics, metadata)

            self.status_bar.showMessage(f"Successfully exported to {filepath}", 5000)
            QMessageBox.information(self, "Export Successful", f"Song successfully exported to:\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export: {e}")

    def _export_bundle(self):
        from app.production_packager import ProductionPackager
        from app.chord_engine import CHORD_PROGRESSIONS

        title = self.editor_panel.get_title()
        lyrics = self.editor_panel.get_lyrics()
        if not lyrics.strip():
            QMessageBox.warning(self, "No Lyrics", "Please generate or write some lyrics before exporting.")
            return

        metadata = self.generator_panel.get_generation_parameters()
        safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "_", "-")).strip() or "Suno_Project"
        filepath, _ = QFileDialog.getSaveFileName(self, "Export Suno & Udio Production Bundle", f"{safe_title}_Suno_Bundle.zip", "ZIP Archive (*.zip)")

        if not filepath:
            return

        suno_prompt = self.visual_studio.txt_suno_prompt.toPlainText().strip()
        if not suno_prompt:
            suno_prompt = f"{metadata.get('genre', 'Pop')}, {metadata.get('mood', 'Uplifting')}, {metadata.get('bpm', '120 BPM')}"
        negative_prompt = self.visual_studio.txt_negative.text().strip()

        prog_name = self.tools_panel.prog_combo.currentText()
        chords = CHORD_PROGRESSIONS.get(prog_name, {}).get("chords_in_c", ["C", "G", "Am", "F"])

        try:
            ProductionPackager.create_production_bundle(
                output_zip_path=filepath,
                title=title,
                lyrics=lyrics,
                suno_style_prompt=suno_prompt,
                negative_prompt=negative_prompt,
                chord_progression_name=prog_name,
                chords=chords,
                metadata=metadata
            )
            self.status_bar.showMessage(f"Production bundle exported: {filepath}", 5000)
            QMessageBox.information(
                self,
                "Bundle Exported Successfully",
                f"Suno & Udio Production Bundle created successfully!\n\nSaved to:\n{filepath}\n\nAssets in ZIP:\n1. Suno Style Prompt Card (.txt)\n2. Lyrics with Audio Tags (.txt)\n3. DAW MIDI Chords (.mid for FL Studio/Ableton)\n4. Printable HTML Lead Sheet (.html)\n5. Project Metadata (.json)\n6. Vocal Topline Melody Guide (.mid with Lyrics)\n7. MusicXML Sheet Music (.musicxml)\n8. High-Res Album Cover Artwork (.png)"
            )
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to create bundle: {e}")

    def _export_topline_midi(self):
        title = self.editor_panel.get_title()
        lyrics = self.editor_panel.get_lyrics()
        if not lyrics.strip():
            QMessageBox.warning(self, "No Lyrics", "Please generate or write some lyrics first.")
            return
        from app.vocal_melody_generator import VocalToplineGenerator
        bpm = 120
        try:
            bpm = self.editor_panel.metro_bpm_spin.value()
        except Exception:
            pass
        safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "_", "-")).strip() or "Track"
        filepath, _ = QFileDialog.getSaveFileName(self, "Export Vocal Topline MIDI", f"{safe_title}_Vocal_Topline.mid", "MIDI Files (*.mid)")
        if filepath:
            try:
                events = VocalToplineGenerator.generate_melody_events(lyrics, key="C", scale="Major", bpm=bpm)
                VocalToplineGenerator.export_midi(events, filepath, bpm=bpm, title=title)
                QMessageBox.information(self, "MIDI Exported", f"Successfully exported Type 1 MIDI with lyric events to:\n{filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export MIDI: {e}")

    def _export_musicxml(self):
        title = self.editor_panel.get_title()
        lyrics = self.editor_panel.get_lyrics()
        if not lyrics.strip():
            QMessageBox.warning(self, "No Lyrics", "Please generate or write some lyrics first.")
            return
        from app.vocal_melody_generator import VocalToplineGenerator
        bpm = 120
        try:
            bpm = self.editor_panel.metro_bpm_spin.value()
        except Exception:
            pass
        safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "_", "-")).strip() or "Track"
        filepath, _ = QFileDialog.getSaveFileName(self, "Export MusicXML Sheet Music", f"{safe_title}_Sheet_Music.musicxml", "MusicXML Files (*.musicxml *.xml)")
        if filepath:
            try:
                events = VocalToplineGenerator.generate_melody_events(lyrics, key="C", scale="Major", bpm=bpm)
                VocalToplineGenerator.export_musicxml(events, filepath, title=title, bpm=bpm)
                QMessageBox.information(self, "MusicXML Exported", f"Successfully exported sheet music to:\n{filepath}\n\nOpen in MuseScore, Sibelius, or Dorico.")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export MusicXML: {e}")

    def _export_album_cover(self):
        title = self.editor_panel.get_title()
        from app.ui.cover_art_dialog import CoverArtDialog
        dlg = CoverArtDialog(self, is_dark=self.is_dark_theme, title=title, lyrics=self.editor_panel.get_lyrics())
        dlg.exec()

    def _open_history(self):
        dlg = HistoryDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.selected_item:
            item = dlg.selected_item
            self.editor_panel.set_title(item.get("title", "Untitled"))
            self.editor_panel.set_lyrics(item.get("lyrics", ""))
            self._set_studio_mode(3)
            self.status_bar.showMessage(f"Restored from history: {item.get('title')}", 4000)

    def _open_song_cloner(self):
        lyrics = self.editor_panel.get_lyrics()
        title = self.editor_panel.get_title()
        if hasattr(self, "clone_view"):
            if lyrics and len(lyrics.strip()) > 30:
                self.clone_view.set_reference(lyrics, title)
        self._set_studio_mode(4)
        self.status_bar.showMessage("Switched to Song DNA Cloner Workstation", 2500)

    def _load_cloned_song_into_editor(self, title: str, lyrics: str):
        self.editor_panel.set_title(title)
        self.editor_panel.set_lyrics(lyrics)
        self._set_studio_mode(3)
        self.status_bar.showMessage(f"Loaded cloned track into Editor: '{title}'", 3500)

    def _open_settings(self):
        dlg = SettingsDialog(self, is_dark=self.is_dark_theme)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            saved_theme = config_manager.get("theme", "obsidian")
            if saved_theme != self.current_theme:
                self.set_theme(saved_theme)
            cur_model = config_manager.get("gemini_model", "gemini-flash-lite-latest")
            idx = self.header_model_combo.findText(cur_model)
            if idx >= 0:
                self.header_model_combo.setCurrentIndex(idx)
            self._update_status_bar()
            self.status_bar.showMessage("Settings saved successfully", 3000)

    def _on_header_model_changed(self, new_model: str):
        config_manager.set("gemini_model", new_model)
        self._update_status_bar()
        self.status_bar.showMessage(f"AI Engine switched to: {new_model}", 3000)

    def _update_status_bar(self):
        key_count = config_manager.get_key_count()
        model = config_manager.get("gemini_model", "gemini-3.5-flash")
        lic_info = license_manager.get_license_info()
        lic_badge = "💎 PRO" if lic_info["is_active"] else "🟡 DEMO"
        if key_count > 0:
            tag = "🟢 Gemini Pro Active" if "pro" in model else "⚡ Gemini Flash Active"
            badge = f"Pool: {key_count} keys verified" if key_count > 1 else "Key Verified"
            self.status_bar.showMessage(f"[{lic_badge}] {tag} | Model: {model} | ✓ {badge}")
        else:
            self.status_bar.showMessage(f"[{lic_badge}] 🟡 Demo Mode (Add API Key in Settings) | Engine: {model}")

    def _load_last_session(self):
        last_lyrics = config_manager.get("last_lyrics", "")
        last_title = config_manager.get("last_title", "")
        if last_lyrics:
            self.editor_panel.set_title(last_title)
            self.editor_panel.set_lyrics(last_lyrics)

        # Apply initial theme across all views
        self._apply_all_themes(self.is_dark_theme)

    def _check_updates_startup(self):
        """Silently queries update manifest in background after boot without interrupting user workflow."""
        try:
            from app.updater import UpdateCheckWorker
            update_url = config_manager.get("update_url", DEFAULT_UPDATE_URL)
            self.update_check_worker = UpdateCheckWorker(
                update_url=update_url,
                current_version=APP_VERSION,
                parent=self
            )
            self.update_check_worker.update_available.connect(self._on_update_detected)
            self.update_check_worker.start()
        except Exception as e:
            print(f"Startup update check error: {e}")

    def _on_update_detected(self, manifest: dict):
        """Notifies user via a glowing Update Ready header pill and friendly status message."""
        self.latest_update_info = manifest
        new_ver = manifest.get("version", "")
        if hasattr(self, "header_btn_update"):
            self.header_btn_update.setText(f"🚀 Update Ready (v{new_ver})")
            self.header_btn_update.show()
            self.capsule_util.adjustSize()
            self.header_frame.adjustSize()
        # Non-intrusive status bar hint matching user instruction
        self.status_bar.showMessage(
            f"🚀 កំណែថ្មី v{new_ver} បានត្រៀមរួចរាល់! ចុចប៊ូតុង 'Update Ready' ដើម្បី Restart ឬទាញយក installer ថ្មី",
            12000
        )

    def _open_update_dialog(self, manifest: dict = None):
        """Opens the full Studio Update Inspector dialog."""
        info = manifest or self.latest_update_info or {}
        from app.ui.update_dialog import StudioUpdateDialog
        dlg = StudioUpdateDialog(self, manifest=info, theme_key=self.current_theme)
        dlg.exec()

    def _open_license_dialog(self):
        """Opens the License Activation Dialog."""
        from app.ui.activation_dialog import LicenseActivationDialog
        dlg = LicenseActivationDialog(self, theme_key=self.current_theme)
        dlg.exec()
        self._update_license_btn_style()
        self._update_status_bar()

    def _update_license_btn_style(self):
        """Updates the Header License Button appearance based on activation state."""
        if not hasattr(self, "header_btn_license"):
            return
        info = license_manager.get_license_info()
        t_data = get_theme(self.current_theme)
        is_dark = t_data.get("is_dark", True)

        if info["is_active"]:
            self.header_btn_license.setText("💎 PRO")
            self.header_btn_license.setToolTip(f"{info['plan_name']} (Active) • Click to view license details")
            if is_dark:
                self.header_btn_license.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #10b981);
                        color: #ffffff;
                        border: 1px solid #6ee7b7;
                        font-weight: 800;
                        font-size: 8.5pt;
                        padding: 3px 8px;
                        border-radius: 6px;
                    }
                    QPushButton:hover {
                        opacity: 0.92;
                    }
                """)
            else:
                self.header_btn_license.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #10b981);
                        color: #ffffff;
                        border: 1px solid #047857;
                        font-weight: 800;
                        font-size: 8.5pt;
                        padding: 3px 8px;
                        border-radius: 6px;
                    }
                    QPushButton:hover {
                        opacity: 0.92;
                    }
                """)
        else:
            self.header_btn_license.setText("🔑 Activate Pro")
            self.header_btn_license.setToolTip("Free Demo Mode • Click to activate Studio Pro License")
            self.header_btn_license.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #d97706, stop:1 #f59e0b);
                    color: #ffffff;
                    border: 1px solid #fde68a;
                    font-weight: 800;
                    font-size: 8.5pt;
                    padding: 3px 8px;
                    border-radius: 6px;
                }
                QPushButton:hover {
                    opacity: 0.92;
                }
            """)
        self.capsule_util.adjustSize()
        self.header_frame.adjustSize()

    def closeEvent(self, event):
        workers_to_stop = [
            self.current_worker,
            getattr(self, "rewrite_worker", None),
            getattr(self, "rhyme_worker", None),
            getattr(self, "suno_worker", None),
            getattr(self, "update_check_worker", None)
        ]
        for worker in workers_to_stop:
            if worker and worker.isRunning():
                worker.quit()
                worker.wait(500)

        config_manager.set("last_lyrics", self.editor_panel.get_lyrics())
        config_manager.set("last_title", self.editor_panel.get_title())
        super().closeEvent(event)
