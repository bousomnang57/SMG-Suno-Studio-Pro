"""
Studio Update Inspector Dialog for SMG Suno Studio Pro.
Presents version diff, bilingual Khmer/English release highlights, live download progress,
and seamless one-click Detached Restart & Install.
"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QTabWidget, QTextEdit, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QIcon

from app.config import APP_VERSION, APP_NAME, get_asset_path
from app.ui.styles import get_theme
from app.updater import UpdateDownloadWorker, restart_and_install, open_download_url

class StudioUpdateDialog(QDialog):
    """
    Modern modal dialog notifying the user of an available application update.
    Provides direct in-app download with live progress and automatic detached restart installer.
    """
    def __init__(self, parent=None, manifest: dict = None, theme_key: str = "obsidian"):
        super().__init__(parent)
        self.manifest = manifest or {}
        self.theme_key = theme_key
        self.theme = get_theme(theme_key)
        self.download_worker = None
        self.downloaded_installer_path = ""

        self.setWindowTitle(f"🚀 {APP_NAME} — Update Available")
        self.setFixedSize(620, 560)
        self.setModal(True)

        logo_path = get_asset_path("logo.png")
        if logo_path.exists():
            self.setWindowIcon(QIcon(str(logo_path)))

        self._init_ui()
        self.apply_theme(self.theme_key)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 18)
        layout.setSpacing(14)

        # ── Zone 1: Header Brand & Instruction ──
        header_box = QHBoxLayout()
        header_box.setSpacing(12)

        icon_lbl = QLabel("🚀")
        icon_lbl.setStyleSheet("font-size: 32px;")
        header_box.addWidget(icon_lbl)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)

        self.lbl_title = QLabel(f"កំណែថ្មីបានត្រៀមរួចរាល់ • New Update Available")
        self.lbl_title.setStyleSheet("font-size: 16px; font-weight: 800;")
        title_col.addWidget(self.lbl_title)

        self.lbl_subtitle = QLabel("របៀប update៖ បើក app ហើយរង់ចាំប៊ូតុង \"Update ready\" រួចចុច Restart ឬទាញយក installer ថ្មី")
        self.lbl_subtitle.setStyleSheet("font-size: 11px;")
        self.lbl_subtitle.setWordWrap(True)
        title_col.addWidget(self.lbl_subtitle)
        header_box.addLayout(title_col, stretch=1)
        layout.addLayout(header_box)

        # ── Zone 2: Version Diff & Release Specs Card ──
        self.version_card = QFrame()
        self.version_card.setObjectName("updateVersionCard")
        vc_layout = QVBoxLayout(self.version_card)
        vc_layout.setContentsMargins(14, 10, 14, 10)
        vc_layout.setSpacing(6)

        pill_row = QHBoxLayout()
        pill_row.setSpacing(10)

        cur_ver = APP_VERSION
        new_ver = self.manifest.get("version", "Latest")

        self.pill_current = QLabel(f"Current: v{cur_ver}")
        self.pill_current.setObjectName("pillCurrentVer")
        self.pill_current.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pill_current.setFixedHeight(26)
        pill_row.addWidget(self.pill_current)

        arrow_lbl = QLabel("➔")
        arrow_lbl.setStyleSheet("font-size: 14px; font-weight: 900;")
        pill_row.addWidget(arrow_lbl)

        self.pill_new = QLabel(f"New Version: v{new_ver} ✨")
        self.pill_new.setObjectName("pillNewVer")
        self.pill_new.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pill_new.setFixedHeight(26)
        pill_row.addWidget(self.pill_new)

        pill_row.addStretch(1)
        vc_layout.addLayout(pill_row)

        # Release Details Line
        rel_date = self.manifest.get("release_date", "2026")
        file_size = self.manifest.get("file_size_mb", 68.8)
        min_os = self.manifest.get("min_os_version", "Windows 10 / 11")
        self.lbl_specs = QLabel(f"📅 កាលបរិច្ឆេទ: {rel_date}  •  📦 ទំហំ: ~{file_size} MB  •  💻 ប្រព័ន្ធ: {min_os}")
        self.lbl_specs.setStyleSheet("font-size: 11px;")
        vc_layout.addWidget(self.lbl_specs)

        layout.addWidget(self.version_card)

        # ── Zone 3: Bilingual Release Highlights (Khmer & English Tabs) ──
        self.tabs_changelog = QTabWidget()
        self.tabs_changelog.setObjectName("updateTabs")

        # Khmer Tab
        kh_text = QTextEdit()
        kh_text.setReadOnly(True)
        kh_items = self.manifest.get("changelog_kh", [])
        if not kh_items:
            kh_items = ["កំណែថ្មីនេះបង្កើនល្បឿន និងបន្ថែមមុខងារពិសេសសម្រាប់ផលិតបទចម្រៀង។"]
        kh_html = "<div style='line-height: 1.6; font-size: 12px;'>"
        for item in kh_items:
            kh_html += f"<p style='margin: 4px 0;'><b>{item}</b></p>"
        kh_html += "</div>"
        kh_text.setHtml(kh_html)
        self.tabs_changelog.addTab(kh_text, "🇰🇭 មុខងារថ្មីៗ (Changelog)")

        # English Tab
        en_text = QTextEdit()
        en_text.setReadOnly(True)
        en_items = self.manifest.get("changelog_en", [])
        if not en_items:
            en_items = ["Performance improvements and new studio features."]
        en_html = "<div style='line-height: 1.6; font-size: 12px;'>"
        for item in en_items:
            en_html += f"<p style='margin: 4px 0;'><b>{item}</b></p>"
        en_html += "</div>"
        en_text.setHtml(en_html)
        self.tabs_changelog.addTab(en_text, "🇬🇧 What's New (English)")

        layout.addWidget(self.tabs_changelog, stretch=1)

        # ── Zone 4: Live Download Progress Bar Container (Hidden by default) ──
        self.progress_container = QFrame()
        self.progress_container.setObjectName("updateProgressContainer")
        p_layout = QVBoxLayout(self.progress_container)
        p_layout.setContentsMargins(10, 8, 10, 8)
        p_layout.setSpacing(6)

        p_info_row = QHBoxLayout()
        self.lbl_progress_status = QLabel("⏳ កំពុងរៀបចំទាញយក... (Preparing download...)")
        self.lbl_progress_status.setStyleSheet("font-weight: 700; font-size: 11px;")
        p_info_row.addWidget(self.lbl_progress_status)
        p_info_row.addStretch(1)

        self.lbl_progress_metric = QLabel("0% (0 MB / 0 MB)")
        self.lbl_progress_metric.setStyleSheet("font-size: 11px;")
        p_info_row.addWidget(self.lbl_progress_metric)
        p_layout.addLayout(p_info_row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(14)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        p_layout.addWidget(self.progress_bar)

        self.progress_container.hide()
        layout.addWidget(self.progress_container)

        # ── Zone 5: Bottom Interactive Buttons ──
        btn_box = QHBoxLayout()
        btn_box.setSpacing(8)

        # Remind Later Button
        self.btn_later = QPushButton("✖️ រំលឹកពេលក្រោយ")
        self.btn_later.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_later.setFixedHeight(34)
        self.btn_later.clicked.connect(self.reject)
        btn_box.addWidget(self.btn_later)

        # Manual Browser Download Button
        self.btn_browser = QPushButton("🌐 ទាញយកតាម Browser")
        self.btn_browser.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_browser.setFixedHeight(34)
        self.btn_browser.setToolTip("Open official download link in your default web browser")
        self.btn_browser.clicked.connect(self._open_browser_download)
        btn_box.addWidget(self.btn_browser)

        btn_box.addStretch(1)

        # One-Click Auto Download / Restart Button
        self.btn_action = QPushButton("⚡ ទាញយក && ដំឡើងភ្លាមៗ")
        self.btn_action.setObjectName("btnPrimaryUpdate")
        self.btn_action.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_action.setFixedHeight(34)
        self.btn_action.clicked.connect(self._on_action_clicked)
        btn_box.addWidget(self.btn_action)

        layout.addLayout(btn_box)

    def apply_theme(self, theme_key: str):
        t = get_theme(theme_key)
        self.theme = t
        self.theme_key = theme_key
        is_dark = t.get("is_dark", True)

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {t['bg_window']};
                color: {t['text_primary']};
            }}
            QLabel {{
                color: {t['text_primary']};
                background: transparent;
            }}
            QTabWidget::pane {{
                border: 1px solid {t['border']};
                border-radius: 8px;
                background-color: {t['bg_card']};
                top: -1px;
            }}
            QTabBar::tab {{
                background-color: {t['bg_window']};
                color: {t['text_secondary']};
                padding: 6px 14px;
                border: 1px solid {t['border']};
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 3px;
                font-weight: 700;
                font-size: 11px;
            }}
            QTabBar::tab:selected {{
                background-color: {t['bg_card']};
                color: {t['accent']};
                border-color: {t['border_accent']};
            }}
            QTextEdit {{
                background-color: {t['bg_card']};
                color: {t['text_primary']};
                border: none;
                border-radius: 8px;
                padding: 8px;
            }}
            #updateVersionCard {{
                background-color: {t['bg_card']};
                border: 1px solid {t['border']};
                border-radius: 10px;
            }}
            #updateProgressContainer {{
                background-color: {t['bg_card']};
                border: 1px solid {t['border_accent']};
                border-radius: 10px;
            }}
            #pillCurrentVer {{
                background-color: {t['subtle_pill_bg']};
                color: {t['text_secondary']};
                border: 1px solid {t['border']};
                border-radius: 13px;
                padding: 2px 10px;
                font-weight: 700;
                font-size: 11px;
            }}
            #pillNewVer {{
                background: {t['accent_gradient']};
                color: #ffffff;
                border-radius: 13px;
                padding: 2px 12px;
                font-weight: 800;
                font-size: 11px;
            }}
            QProgressBar {{
                background-color: {t['bg_input']};
                border: 1px solid {t['border']};
                border-radius: 7px;
            }}
            QProgressBar::chunk {{
                background: {t['accent_gradient']};
                border-radius: 6px;
            }}
            QPushButton {{
                background-color: {t['bg_card']};
                color: {t['text_primary']};
                border: 1px solid {t['border']};
                border-radius: 8px;
                padding: 6px 14px;
                font-size: 11px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                border-color: {t['accent']};
                color: {t['text_primary']};
            }}
            #btnPrimaryUpdate {{
                background: {t['accent_gradient']};
                color: #ffffff;
                border: 1px solid {t['border_accent']};
                border-radius: 8px;
                font-weight: 800;
                padding: 6px 16px;
            }}
            #btnPrimaryUpdate:hover {{
                opacity: 0.92;
            }}
        """)

    def _open_browser_download(self):
        download_url = self.manifest.get("download_url", "")
        if download_url:
            open_download_url(download_url)
        else:
            QMessageBox.warning(self, "No URL", "No download URL found in manifest.")

    def _on_action_clicked(self):
        # State 1: Download not started -> start download
        if not self.downloaded_installer_path:
            download_url = self.manifest.get("download_url", "")
            if not download_url:
                QMessageBox.warning(self, "Download Error", "Manifest has no direct download URL.")
                return

            installer_name = self.manifest.get("installer_name", "SMG_Suno_Studio_Pro_Update.exe")
            self.progress_container.show()
            self.btn_action.setEnabled(False)
            self.btn_action.setText("⏳ កំពុងទាញយក... (Downloading...)")
            self.lbl_progress_status.setText("⏳ កំពុងទាញយក Installer ថ្មី...")

            self.download_worker = UpdateDownloadWorker(download_url, target_filename=installer_name, parent=self)
            self.download_worker.progress.connect(self._on_download_progress)
            self.download_worker.finished.connect(self._on_download_finished)
            self.download_worker.failed.connect(self._on_download_failed)
            self.download_worker.start()

        # State 2: Download completed -> user clicks Restart Now!
        else:
            self._trigger_restart()

    def _on_download_progress(self, bytes_read: int, total_bytes: int, percent: int, speed_str: str):
        self.progress_bar.setValue(percent)
        cur_mb = bytes_read / (1024 * 1024)
        tot_mb = total_bytes / (1024 * 1024) if total_bytes > 0 else 0
        self.lbl_progress_metric.setText(f"{percent}% ({cur_mb:.1f} MB / {tot_mb:.1f} MB) • {speed_str}")

    def _on_download_finished(self, installer_path: str):
        self.downloaded_installer_path = installer_path
        self.progress_bar.setValue(100)
        self.lbl_progress_status.setText("✅ ទាញយកជោគជ័យ! ចុច Restart ដើម្បីដំឡើងភ្លាមៗ")
        self.lbl_progress_metric.setText("100% Complete")

        # Transform action button into prominent restart button
        self.btn_action.setEnabled(True)
        self.btn_action.setText("🔄 Restart && Install Now (ចុចដើម្បី Restart)")
        self.btn_action.setStyleSheet(f"""
            background: {self.theme['accent_gradient']};
            color: #ffffff;
            font-size: 12px;
            font-weight: 900;
            border: 2px solid #ffffff;
            border-radius: 8px;
            padding: 6px 18px;
        """)

    def _on_download_failed(self, error_msg: str):
        self.progress_container.hide()
        self.btn_action.setEnabled(True)
        self.btn_action.setText("⚡ ព្យាយាមទាញយកម្តងទៀត")
        QMessageBox.warning(
            self,
            "Download Error",
            f"ការទាញយកមានបញ្ហា៖\n{error_msg}\n\nលោកអ្នកអាចចុច 'ទាញយកតាម Browser' ដើម្បីទាញយកដោយផ្ទាល់។"
        )

    def _trigger_restart(self):
        if not self.downloaded_installer_path or not Path(self.downloaded_installer_path).exists():
            QMessageBox.critical(self, "Error", "Installer file not found.")
            return

        reply = QMessageBox.question(
            self,
            "Restart Application",
            "កម្មវិធីនឹងបិទជាបណ្តោះអាសន្នដើម្បីដំឡើងកំណែថ្មី។ តើលោកអ្នកចង់បន្តឥឡូវនេះទេ?\n\nThe app will now exit and launch the installer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                restart_and_install(self.downloaded_installer_path, run_silent=False)
            except Exception as e:
                QMessageBox.critical(self, "Launch Error", f"Failed to launch installer: {e}")

    def closeEvent(self, event):
        if self.download_worker and self.download_worker.isRunning():
            self.download_worker.cancel()
            self.download_worker.wait(1000)
        event.accept()
