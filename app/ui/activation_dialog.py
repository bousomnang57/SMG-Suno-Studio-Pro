"""
License Activation Dialog for SMG Suno Studio Pro.
Allows end-users to view and copy their unique Machine ID,
paste their purchased license key, and activate their software cleanly.
"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QIcon, QClipboard, QDesktopServices

from app.config import APP_NAME, get_asset_path
from app.ui.styles import get_theme
from app.license_manager import license_manager

class LicenseActivationDialog(QDialog):
    """
    Modern theme-aware modal dialog for activating SMG Suno Studio Pro.
    """
    def __init__(self, parent=None, theme_key: str = "obsidian"):
        super().__init__(parent)
        self.theme_key = theme_key
        self.theme = get_theme(theme_key)

        self.setWindowTitle(f"🔑 {APP_NAME} — License Activation")
        self.setFixedSize(560, 480)
        self.setModal(True)

        logo_path = get_asset_path("logo.png")
        if logo_path.exists():
            self.setWindowIcon(QIcon(str(logo_path)))

        self._init_ui()
        self.apply_theme(self.theme_key)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Header Title
        header_row = QHBoxLayout()
        header_row.setSpacing(12)

        icon_lbl = QLabel("🔑")
        icon_lbl.setStyleSheet("font-size: 30px;")
        header_row.addWidget(icon_lbl)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)

        self.lbl_title = QLabel("ធ្វើឱ្យកម្មវិធីសកម្ម • Software License Activation")
        self.lbl_title.setStyleSheet("font-size: 15px; font-weight: 800;")
        title_col.addWidget(self.lbl_title)

        self.lbl_sub = QLabel("បញ្ចូល License Key ដើម្បីដោះសោមុខងារ Studio Pro គ្មានដែនកំណត់")
        self.lbl_sub.setStyleSheet("font-size: 11px;")
        title_col.addWidget(self.lbl_sub)

        header_row.addLayout(title_col, stretch=1)
        layout.addLayout(header_row)

        # Card 1: Machine ID (HWID)
        self.hwid_card = QFrame()
        self.hwid_card.setObjectName("hwidCard")
        hc_layout = QVBoxLayout(self.hwid_card)
        hc_layout.setContentsMargins(14, 12, 14, 12)
        hc_layout.setSpacing(8)

        hc_layout.addWidget(QLabel("ជំហានទី ១៖ កូដសម្គាល់កុំព្យូទ័ររបស់អ្នក (Your Unique Machine ID):"))

        id_row = QHBoxLayout()
        id_row.setSpacing(8)

        self.input_hwid = QLineEdit(license_manager.machine_id)
        self.input_hwid.setReadOnly(True)
        self.input_hwid.setObjectName("inputHwid")
        id_row.addWidget(self.input_hwid, stretch=1)

        self.btn_copy_hwid = QPushButton("📋 Copy ID")
        self.btn_copy_hwid.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_copy_hwid.setFixedHeight(34)
        self.btn_copy_hwid.clicked.connect(self._copy_hwid)
        id_row.addWidget(self.btn_copy_hwid)

        hc_layout.addLayout(id_row)

        self.lbl_hwid_note = QLabel("ℹ️ សូម Copy កូដនេះផ្ញើទៅកាន់ Admin ដើម្បីទទួលបាន License Key សម្រាប់កុំព្យូទ័រនេះ។")
        self.lbl_hwid_note.setStyleSheet("font-size: 10.5px;")
        hc_layout.addWidget(self.lbl_hwid_note)

        layout.addWidget(self.hwid_card)

        # Card 2: License Key Input
        self.key_card = QFrame()
        self.key_card.setObjectName("keyCard")
        kc_layout = QVBoxLayout(self.key_card)
        kc_layout.setContentsMargins(14, 12, 14, 12)
        kc_layout.setSpacing(8)

        kc_layout.addWidget(QLabel("ជំហានទី ២៖ បញ្ចូល License Key ដែលទទួលបានពី Admin:"))

        self.input_key = QLineEdit()
        self.input_key.setPlaceholderText("SMG-LIFE-XXXX-XXXX-XXXX")
        self.input_key.setObjectName("inputKey")
        self.input_key.setFixedHeight(36)
        kc_layout.addWidget(self.input_key)

        layout.addWidget(self.key_card)

        # Live Status Feedback
        self.lbl_status = QLabel()
        self._refresh_status_label()
        layout.addWidget(self.lbl_status)

        layout.addStretch(1)

        # Bottom Buttons
        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)

        self.btn_close = QPushButton("បិទ (Close)")
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.setFixedHeight(36)
        self.btn_close.clicked.connect(self.reject)
        btn_box.addWidget(self.btn_close)

        btn_box.addStretch(1)

        self.btn_activate = QPushButton("⚡ ធ្វើឱ្យសកម្មឥឡូវនេះ (Activate Now)")
        self.btn_activate.setObjectName("btnActivate")
        self.btn_activate.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_activate.setFixedHeight(36)
        self.btn_activate.clicked.connect(self._do_activate)
        btn_box.addWidget(self.btn_activate)

        layout.addLayout(btn_box)

    def _refresh_status_label(self):
        info = license_manager.get_license_info()
        if info["is_active"]:
            self.lbl_status.setText(f"✅ កម្មវិធីដំណើរការពេញលេញ៖ {info['plan_name']} ({info['expiry_text']})")
            self.lbl_status.setStyleSheet("color: #34d399; font-weight: 700; font-size: 11px;")
        else:
            self.lbl_status.setText("🟡 ស្ថានភាព៖ Free Demo Mode (មុខងារមួយចំនួនត្រូវបានកំណត់)")
            self.lbl_status.setStyleSheet("color: #fbbf24; font-weight: 700; font-size: 11px;")

    def _copy_hwid(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.input_hwid.text())
        self.btn_copy_hwid.setText("✓ Copied!")
        self.btn_copy_hwid.setEnabled(False)
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(2000, lambda: (self.btn_copy_hwid.setText("📋 Copy ID"), self.btn_copy_hwid.setEnabled(True)))

    def _do_activate(self):
        key = self.input_key.text().strip()
        if not key:
            QMessageBox.warning(self, "No Key", "សូមបញ្ចូល License Key មុននឹងចុច Activate។")
            return

        success, msg = license_manager.activate(key)
        if success:
            self._refresh_status_label()
            QMessageBox.information(
                self,
                "ជោគជ័យ!",
                f"🎉 {msg}\n\nសូមអរគុណសម្រាប់ការគាំទ្រ SMG Suno Studio Pro!\nមុខងារ Pro ទាំងអស់ត្រូវបានដោះសោជូនលោកអ្នករួចរាល់ហើយ។"
            )
            self.accept()
        else:
            QMessageBox.critical(
                self,
                "បរាជ័យ",
                f"❌ មិនអាចធ្វើឱ្យសកម្មបានទេ៖\n{msg}\n\nសូមពិនិត្យមើល Machine ID ឬទាក់ទងមក Admin ម្ដងទៀត។"
            )

    def apply_theme(self, theme_key: str):
        t = get_theme(theme_key)
        self.theme = t
        self.theme_key = theme_key

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {t['bg_window']};
                color: {t['text_primary']};
            }}
            QLabel {{
                color: {t['text_primary']};
                background: transparent;
            }}
            #hwidCard, #keyCard {{
                background-color: {t['bg_card']};
                border: 1px solid {t['border']};
                border-radius: 10px;
            }}
            #inputHwid {{
                background-color: {t['bg_input']};
                color: {t['text_primary']};
                border: 1px solid {t['border']};
                border-radius: 6px;
                padding: 6px 10px;
                font-family: Consolas, 'Fira Code', monospace;
                font-weight: 800;
                font-size: 12px;
            }}
            #inputKey {{
                background-color: {t['bg_input']};
                color: {t['text_primary']};
                border: 1px solid {t['border_accent']};
                border-radius: 6px;
                padding: 6px 10px;
                font-family: Consolas, 'Fira Code', monospace;
                font-weight: 700;
                font-size: 12px;
            }}
            QPushButton {{
                background-color: {t['bg_card']};
                color: {t['text_primary']};
                border: 1px solid {t['border']};
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 11px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                border-color: {t['accent']};
                color: {t['text_primary']};
            }}
            #btnActivate {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #f59e0b, stop:1 #ef4444);
                color: #ffffff;
                border: 1px solid #fef08a;
                border-radius: 6px;
                font-weight: 800;
                padding: 6px 18px;
            }}
            #btnActivate:hover {{
                opacity: 0.92;
            }}
        """)

