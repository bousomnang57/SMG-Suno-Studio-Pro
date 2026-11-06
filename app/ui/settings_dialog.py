"""
Settings Dialog: Configure Gemini API Key Pool, Model Selection, and Application Preferences.
Engineered for clean UI fit, high contrast, responsive feedback, and seamless Light/Dark themes.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QGroupBox, QMessageBox, QFrame, QCheckBox
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QIcon
from app.config import config_manager, GEMINI_MODELS, get_asset_path, APP_VERSION, APP_NAME, DEFAULT_UPDATE_URL
from app.ui.styles import STUDIO_THEMES, get_theme
from app.gemini_client import ConnectionTestWorker
from app.ui.multi_key_dialog import MultiKeyDialog
from app.license_manager import license_manager

class SettingsDialog(QDialog):
    def __init__(self, parent=None, is_dark: bool = None):
        super().__init__(parent)
        self.setWindowTitle(f"{APP_NAME} — Settings")
        self.setFixedSize(620, 715)
        self.setModal(True)
        self.update_worker = None

        # Selected Studio Theme
        raw_t = config_manager.get("theme", "obsidian")
        if raw_t in ["dark", "dark_modern"]:
            raw_t = "obsidian"
        elif raw_t in ["light", "modern_light"]:
            raw_t = "canvas_light"
        self.selected_theme = raw_t if raw_t in STUDIO_THEMES else "obsidian"
        self.theme_cards = {}

        if is_dark is None:
            if parent and hasattr(parent, "is_dark_theme"):
                is_dark = parent.is_dark_theme
            elif parent and hasattr(parent, "is_dark"):
                is_dark = parent.is_dark
            else:
                is_dark = STUDIO_THEMES[self.selected_theme]["is_dark"]
        self.is_dark = is_dark

        logo_path = get_asset_path("logo.png")
        if logo_path.exists():
            self.setWindowIcon(QIcon(str(logo_path)))

        self._init_ui()
        self.apply_theme(self.is_dark)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(14)

        # Header Title
        self.title_lbl = QLabel("⚙️ AI Studio Settings")
        self.title_lbl.setObjectName("headingLabel")
        layout.addWidget(self.title_lbl)

        # Gemini API Box Card
        self.api_group = QGroupBox("Google Gemini API Configuration")
        g_layout = QVBoxLayout(self.api_group)
        g_layout.setContentsMargins(14, 16, 14, 14)
        g_layout.setSpacing(9)

        self.lbl_key_title = QLabel("Gemini API Key (Single or Multi-Key Pool):")
        self.lbl_key_title.setStyleSheet("font-weight: 700; font-size: 11px;")
        g_layout.addWidget(self.lbl_key_title)

        key_row = QHBoxLayout()
        key_row.setSpacing(6)

        self.key_input = QLineEdit()
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_input.setPlaceholderText("Paste Gemini API Key(s) (AIzaSy...)")
        self.key_input.setText(config_manager.get("gemini_api_key", ""))
        self.key_input.textChanged.connect(self._on_key_text_changed)
        key_row.addWidget(self.key_input, stretch=1)

        self.btn_toggle_key = QPushButton("👁")
        self.btn_toggle_key.setFixedSize(36, 30)
        self.btn_toggle_key.setCheckable(True)
        self.btn_toggle_key.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_key.setToolTip("Show / Hide API Key")
        self.btn_toggle_key.clicked.connect(self._toggle_key_visibility)
        key_row.addWidget(self.btn_toggle_key)

        self.btn_pool = QPushButton("📋 Pool")
        self.btn_pool.setFixedWidth(92)
        self.btn_pool.setFixedHeight(30)
        self.btn_pool.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_pool.setToolTip("Manage multi-key rotation pool for high-volume batch generations")
        self.btn_pool.clicked.connect(self._open_key_pool)
        key_row.addWidget(self.btn_pool)

        g_layout.addLayout(key_row)

        # Live Status Badge Capsule
        self.lbl_key_badge = QLabel()
        self._update_badge_style()
        g_layout.addWidget(self.lbl_key_badge)

        # Link to Google AI Studio
        self.link_btn = QPushButton("🔑 Get Gemini API Key (Google AI Studio)")
        self.link_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.link_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://aistudio.google.com/app/apikey")))
        g_layout.addWidget(self.link_btn)

        # Model Selector
        self.lbl_model_title = QLabel("AI Model Engine:")
        self.lbl_model_title.setStyleSheet("font-weight: 700; font-size: 11px;")
        g_layout.addWidget(self.lbl_model_title)

        self.model_combo = QComboBox()
        self.model_combo.addItems(GEMINI_MODELS)
        current_model = config_manager.get("gemini_model", "gemini-2.5-flash")
        idx = self.model_combo.findText(current_model)
        if idx >= 0:
            self.model_combo.setCurrentIndex(idx)
        else:
            self.model_combo.setCurrentText(current_model)
        g_layout.addWidget(self.model_combo)

        self.tip_lbl = QLabel(
            "⚡ 'gemini-flash-lite-latest' & 'gemini-3.5-flash-lite': Ultra-fast (~1s) response, maximum quota, zero lag.\n"
            "🌟 'gemini-3.5-flash': Studio-grade lyrical nuance, vivid sensory metaphors, and complex rhythm matching."
        )
        self.tip_lbl.setWordWrap(True)
        g_layout.addWidget(self.tip_lbl)

        # Test Connection Button & Live Status
        test_box = QVBoxLayout()
        test_box.setSpacing(4)

        t_btn_row = QHBoxLayout()
        t_btn_row.setSpacing(8)

        self.btn_test = QPushButton("⚡ Test Connection")
        self.btn_test.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_test.setFixedHeight(32)
        self.btn_test.clicked.connect(self._test_connection)
        t_btn_row.addWidget(self.btn_test)

        self.lbl_test_status = QLabel("⚪ Click to test connection")
        t_btn_row.addWidget(self.lbl_test_status, stretch=1)
        test_box.addLayout(t_btn_row)

        g_layout.addLayout(test_box)
        layout.addWidget(self.api_group)

        # 🎨 Studio Theme & Appearance Group
        self.theme_group = QGroupBox("🎨 Studio Theme && Appearance (5 Modern Clean Palettes)")
        t_layout = QVBoxLayout(self.theme_group)
        t_layout.setContentsMargins(12, 14, 12, 12)
        t_layout.setSpacing(8)

        t_cards_row = QHBoxLayout()
        t_cards_row.setSpacing(8)

        for t_id, t_info in STUDIO_THEMES.items():
            card = QPushButton()
            card.setCursor(Qt.CursorShape.PointingHandCursor)
            card.setFixedHeight(68)
            card.setToolTip(f"{t_info['name']}\n{t_info['tagline']}")
            card.clicked.connect(lambda _, k=t_id: self._select_theme_card(k))
            t_cards_row.addWidget(card)
            self.theme_cards[t_id] = card

        t_layout.addLayout(t_cards_row)
        layout.addWidget(self.theme_group)
        self._update_theme_cards_ui()

        # ── 🚀 Application Updates & License Section ──
        self.update_group = QGroupBox("🚀 Application Updates && License")
        u_layout = QVBoxLayout(self.update_group)
        u_layout.setContentsMargins(14, 12, 14, 12)
        u_layout.setSpacing(6)

        u_row = QHBoxLayout()
        u_row.setSpacing(10)

        self.lbl_app_ver = QLabel(f"Version: <b>v{APP_VERSION}</b> (Official Stable)")
        u_row.addWidget(self.lbl_app_ver)

        u_row.addStretch(1)

        self.chk_auto_update = QCheckBox("Auto-check on startup")
        self.chk_auto_update.setChecked(config_manager.get("auto_check_updates", True))
        self.chk_auto_update.setCursor(Qt.CursorShape.PointingHandCursor)
        u_row.addWidget(self.chk_auto_update)

        self.btn_check_update = QPushButton("🔄 Check for Updates")
        self.btn_check_update.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_check_update.setFixedHeight(28)
        self.btn_check_update.clicked.connect(self._check_for_updates)
        u_row.addWidget(self.btn_check_update)

        u_layout.addLayout(u_row)

        self.lbl_update_status = QLabel("● Ready to check for updates")
        self.lbl_update_status.setStyleSheet("font-size: 10.5px;")
        u_layout.addWidget(self.lbl_update_status)

        # ── License Status & Activation Row ──
        self.lic_separator = QFrame()
        self.lic_separator.setFrameShape(QFrame.Shape.HLine)
        self.lic_separator.setFrameShadow(QFrame.Shadow.Sunken)
        u_layout.addWidget(self.lic_separator)

        lic_row = QHBoxLayout()
        lic_row.setSpacing(10)

        self.lbl_license_status = QLabel()
        self.lbl_license_status.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        lic_row.addWidget(self.lbl_license_status, 1)

        self.btn_manage_license = QPushButton("🔑 Activate Pro")
        self.btn_manage_license.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_manage_license.setFixedHeight(28)
        self.btn_manage_license.clicked.connect(self._open_license_dialog)
        lic_row.addWidget(self.btn_manage_license)

        u_layout.addLayout(lic_row)

        layout.addWidget(self.update_group)

        # Bottom Action Buttons
        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)
        btn_box.addStretch()

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(self.btn_cancel)

        self.btn_save = QPushButton("Save Settings")
        self.btn_save.setObjectName("primaryGenerateButton")
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.clicked.connect(self._save_settings)
        btn_box.addWidget(self.btn_save)

        layout.addLayout(btn_box)

    def _select_theme_card(self, theme_id: str):
        self.selected_theme = theme_id
        is_dark = STUDIO_THEMES[theme_id]["is_dark"]
        self.apply_theme(is_dark)
        self._update_theme_cards_ui()

    def _update_theme_cards_ui(self):
        for t_id, card in self.theme_cards.items():
            t_info = STUDIO_THEMES[t_id]
            is_active = (t_id == self.selected_theme)
            active_mark = "✓ Active" if is_active else "Select"
            short_name = t_info["name"].split()[0]
            card.setText(f"{t_info['icon']} {short_name}\n● ● ●\n{active_mark}")

            accent = t_info["accent"]
            if self.is_dark:
                bg_surface = t_info["bg_card"] if is_active else t_info["bg_window"]
                text_c = "#ffffff" if is_active else "#94a3b8"
                border_c = accent if is_active else t_info["border"]
            else:
                bg_surface = "#eff6ff" if is_active else "#ffffff"
                text_c = "#1d4ed8" if is_active else "#475569"
                border_c = accent if is_active else "#cbd5e1"
            border_w = "2px" if is_active else "1px"

            card.setStyleSheet(f"""
                QPushButton {{
                    background-color: {bg_surface};
                    color: {text_c};
                    border: {border_w} solid {border_c};
                    border-radius: 8px;
                    font-size: 10px;
                    font-weight: {'800' if is_active else '600'};
                    padding: 5px;
                    line-height: 1.3;
                }}
                QPushButton:hover {{
                    border-color: {accent};
                    color: {'#ffffff' if self.is_dark else '#0f172a'};
                }}
            """)

    def apply_theme(self, theme_or_dark):
        t = get_theme(theme_or_dark)
        self.theme = t
        self.theme_key = t.get("id", "obsidian")
        is_dark = t.get("is_dark", True)
        self.is_dark = is_dark
        chevron_light = str(get_asset_path("chevron_down_light.svg")).replace(chr(92), "/")
        chevron_dark = str(get_asset_path("chevron_down_dark.svg")).replace(chr(92), "/")

        if is_dark:
            self.setStyleSheet(f"""
                QDialog {{
                    background-color: {t['bg_window']};
                    color: {t['text_primary']};
                }}
            """)
            self.title_lbl.setStyleSheet(f"font-size: 15px; font-weight: 800; color: {t['text_primary']}; background: transparent;")
            self.api_group.setStyleSheet(f"""
                QGroupBox {{
                    background-color: {t['bg_card']};
                    border: 1px solid {t['border']};
                    border-radius: 8px;
                    margin-top: 14px;
                    padding: 16px 14px 14px 14px;
                    font-weight: 700;
                    font-size: 11px;
                    color: {t['text_secondary']};
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    left: 10px;
                    padding: 0 6px;
                    background-color: {t['bg_card']};
                    color: {t['text_accent']};
                }}
            """)
            if hasattr(self, "theme_group"):
                self.theme_group.setStyleSheet(f"""
                    QGroupBox {{
                        background-color: {t['bg_card']};
                        border: 1px solid {t['border']};
                        border-radius: 8px;
                        margin-top: 14px;
                        padding: 14px 12px 12px 12px;
                        font-weight: 700;
                        font-size: 11px;
                        color: {t['text_secondary']};
                    }}
                    QGroupBox::title {{
                        subcontrol-origin: margin;
                        subcontrol-position: top left;
                        left: 10px;
                        padding: 0 6px;
                        background-color: {t['bg_card']};
                        color: {t['text_accent']};
                    }}
                """)
            if hasattr(self, "update_group"):
                self.update_group.setStyleSheet(f"""
                    QGroupBox {{
                        background-color: {t['bg_card']};
                        border: 1px solid {t['border']};
                        border-radius: 8px;
                        margin-top: 14px;
                        padding: 14px 12px 12px 12px;
                        font-weight: 700;
                        font-size: 11px;
                        color: {t['text_secondary']};
                    }}
                    QGroupBox::title {{
                        subcontrol-origin: margin;
                        subcontrol-position: top left;
                        left: 10px;
                        padding: 0 6px;
                        background-color: {t['bg_card']};
                        color: {t['text_accent']};
                    }}
                """)
                self.lbl_app_ver.setStyleSheet(f"color: {t['text_primary']}; font-size: 11px; background: transparent;")
                self.chk_auto_update.setStyleSheet(f"color: {t['text_secondary']}; font-size: 11px; font-weight: 600; background: transparent;")
                self.btn_check_update.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {t['bg_input']};
                        color: {t['text_primary']};
                        border: 1px solid {t['border']};
                        border-radius: 6px;
                        font-size: 11px;
                        font-weight: 700;
                        padding: 4px 12px;
                    }}
                    QPushButton:hover {{
                        border-color: {t['border_accent']};
                        color: #ffffff;
                    }}
                """)
                self.lbl_update_status.setStyleSheet(f"color: {t['text_muted']}; font-size: 10px; background: transparent;")
                if hasattr(self, "lic_separator"):
                    self.lic_separator.setStyleSheet(f"color: {t['border']}; background-color: {t['border']}; max-height: 1px;")
                if hasattr(self, "btn_manage_license"):
                    self.btn_manage_license.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {t['bg_input']};
                            color: {t['text_primary']};
                            border: 1px solid {t['border']};
                            border-radius: 6px;
                            font-size: 11px;
                            font-weight: 700;
                            padding: 4px 12px;
                        }}
                        QPushButton:hover {{
                            border-color: {t['border_accent']};
                            color: #ffffff;
                        }}
                    """)
            self.lbl_key_title.setStyleSheet(f"color: {t['text_secondary']}; font-weight: 700; font-size: 11px; background: transparent;")
            self.key_input.setStyleSheet(f"""
                QLineEdit {{
                    background-color: {t['bg_input']};
                    border: 1px solid {t['border']};
                    border-radius: 6px;
                    padding: 6px 10px;
                    color: {t['text_primary']};
                    font-family: Consolas, 'Fira Code', monospace;
                    font-size: 11px;
                }}
                QLineEdit:focus {{
                    border-color: {t['border_accent']};
                }}
            """)
            self.btn_toggle_key.setStyleSheet(f"""
                QPushButton {{
                    background-color: {t['bg_card_alt']};
                    color: {t['text_secondary']};
                    border: 1px solid {t['border']};
                    border-radius: 5px;
                    font-size: 13px;
                }}
                QPushButton:hover {{
                    background-color: {t['border']};
                    color: #ffffff;
                    border-color: {t['border_accent']};
                }}
                QPushButton:checked {{
                    background-color: {t['subtle_pill_bg']};
                    color: {t['text_accent']};
                    border-color: {t['border_accent']};
                }}
            """)
            self.btn_pool.setStyleSheet(f"""
                QPushButton {{
                    background-color: {t['subtle_pill_bg']};
                    color: {t['text_accent']};
                    border: 1px solid {t['border_accent']};
                    border-radius: 5px;
                    font-weight: 700;
                    font-size: 11px;
                    padding: 4px 6px;
                }}
                QPushButton:hover {{
                    background-color: {t['accent']};
                    color: #ffffff;
                }}
            """)
            self.link_btn.setStyleSheet(f"""
                QPushButton {{
                    color: {t['text_accent']};
                    text-decoration: underline;
                    background: transparent;
                    border: none;
                    text-align: left;
                    padding: 1px 0;
                    font-size: 11px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    color: #ffffff;
                }}
            """)
            self.lbl_model_title.setStyleSheet(f"color: {t['text_secondary']}; font-weight: 700; font-size: 11px; background: transparent;")
            self.model_combo.setStyleSheet(f"""
                QComboBox {{
                    background-color: {t['bg_input']};
                    border: 1px solid {t['border']};
                    border-radius: 6px;
                    padding: 6px 10px;
                    color: {t['text_primary']};
                    font-size: 11px;
                    font-weight: 600;
                }}
                QComboBox:hover {{
                    border-color: {t['border_accent']};
                }}
                QComboBox:focus {{
                    border-color: {t['border_accent']};
                }}
                QComboBox::drop-down {{
                    subcontrol-origin: padding;
                    subcontrol-position: top right;
                    width: 26px;
                    border: none;
                }}
                QComboBox::down-arrow {{
                    image: url("{chevron_dark}");
                    width: 12px;
                    height: 12px;
                    margin-right: 8px;
                }}
                QComboBox QAbstractItemView {{
                    background-color: {t['bg_card']};
                    border: 1px solid {t['border']};
                    color: {t['text_primary']};
                    selection-background-color: {t['subtle_pill_bg']};
                    selection-color: {t['text_accent']};
                    padding: 4px;
                }}
            """)
            self.tip_lbl.setStyleSheet(f"""
                background-color: {t['bg_card_alt']};
                color: {t['text_accent']};
                border: 1px solid {t['border']};
                border-radius: 6px;
                padding: 7px 10px;
                font-size: 9.5pt;
                line-height: 1.35;
            """)
            self.btn_test.setStyleSheet(f"""
                QPushButton {{
                    background: {t['accent_gradient']};
                    color: #ffffff;
                    border: 1px solid {t['border_accent']};
                    border-radius: 6px;
                    font-weight: 700;
                    font-size: 11px;
                    padding: 5px 14px;
                }}
                QPushButton:hover {{
                    background: {t['accent_hover']};
                }}
                QPushButton:disabled {{
                    background-color: {t['bg_card_alt']};
                    color: {t['text_muted']};
                    border-color: {t['border']};
                }}
            """)
            self.lbl_test_status.setStyleSheet(f"color: {t['text_muted']}; font-size: 10.5px; background: transparent;")
            self.btn_cancel.setStyleSheet(f"""
                QPushButton {{
                    background-color: {t['bg_card_alt']};
                    color: {t['text_secondary']};
                    border: 1px solid {t['border']};
                    border-radius: 6px;
                    padding: 6px 16px;
                    font-weight: 600;
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    background-color: {t['border']};
                    color: #ffffff;
                }}
            """)
            self.btn_save.setStyleSheet(f"""
                QPushButton {{
                    background: {t['accent_gradient']};
                    color: #ffffff;
                    border: 1px solid {t['border_accent']};
                    border-radius: 6px;
                    padding: 6px 20px;
                    font-weight: 700;
                    font-size: 11.5px;
                }}
                QPushButton:hover {{
                    background: {t['accent_hover']};
                }}
            """)
        else:
            # Modern Pristine Light Theme
            self.setStyleSheet("""
                QDialog {
                    background-color: #f8fafc;
                    color: #0f172a;
                }
            """)
            self.title_lbl.setStyleSheet("font-size: 15px; font-weight: 800; color: #0f172a; background: transparent;")
            self.api_group.setStyleSheet("""
                QGroupBox {
                    background-color: #ffffff;
                    border: 1px solid #cbd5e1;
                    border-radius: 8px;
                    margin-top: 14px;
                    padding: 16px 14px 14px 14px;
                    font-weight: 700;
                    font-size: 11px;
                    color: #0f172a;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    left: 10px;
                    padding: 0 6px;
                    background-color: #ffffff;
                    color: #1d4ed8;
                }
            """)
            if hasattr(self, "theme_group"):
                self.theme_group.setStyleSheet("""
                    QGroupBox {
                        background-color: #ffffff;
                        border: 1px solid #cbd5e1;
                        border-radius: 8px;
                        margin-top: 14px;
                        padding: 14px 12px 12px 12px;
                        font-weight: 700;
                        font-size: 11px;
                        color: #0f172a;
                    }
                    QGroupBox::title {
                        subcontrol-origin: margin;
                        subcontrol-position: top left;
                        left: 10px;
                        padding: 0 6px;
                        background-color: #ffffff;
                        color: #1d4ed8;
                    }
                """)
            if hasattr(self, "update_group"):
                self.update_group.setStyleSheet("""
                    QGroupBox {
                        background-color: #ffffff;
                        border: 1px solid #cbd5e1;
                        border-radius: 8px;
                        margin-top: 14px;
                        padding: 14px 12px 12px 12px;
                        font-weight: 700;
                        font-size: 11px;
                        color: #0f172a;
                    }
                    QGroupBox::title {
                        subcontrol-origin: margin;
                        subcontrol-position: top left;
                        left: 10px;
                        padding: 0 6px;
                        background-color: #ffffff;
                        color: #1d4ed8;
                    }
                """)
                self.lbl_app_ver.setStyleSheet("color: #0f172a; font-size: 11px; background: transparent;")
                self.chk_auto_update.setStyleSheet("color: #475569; font-size: 11px; font-weight: 600; background: transparent;")
                self.btn_check_update.setStyleSheet("""
                    QPushButton {
                        background-color: #ffffff;
                        color: #0f172a;
                        border: 1px solid #cbd5e1;
                        border-radius: 6px;
                        font-size: 11px;
                        font-weight: 700;
                        padding: 4px 12px;
                    }
                    QPushButton:hover {
                        border-color: #2563eb;
                        color: #2563eb;
                        background-color: #f1f5f9;
                    }
                """)
                self.lbl_update_status.setStyleSheet("color: #64748b; font-size: 10px; background: transparent;")
                if hasattr(self, "lic_separator"):
                    self.lic_separator.setStyleSheet("color: #e2e8f0; background-color: #e2e8f0; max-height: 1px;")
                if hasattr(self, "btn_manage_license"):
                    self.btn_manage_license.setStyleSheet("""
                        QPushButton {
                            background-color: #ffffff;
                            color: #0f172a;
                            border: 1px solid #cbd5e1;
                            border-radius: 6px;
                            font-size: 11px;
                            font-weight: 700;
                            padding: 4px 12px;
                        }
                        QPushButton:hover {
                            border-color: #2563eb;
                            color: #2563eb;
                            background-color: #f1f5f9;
                        }
                    """)
            self.lbl_key_title.setStyleSheet("color: #1e293b; font-weight: 700; font-size: 11px; background: transparent;")
            self.key_input.setStyleSheet("""
                QLineEdit {
                    background-color: #ffffff;
                    border: 1px solid #cbd5e1;
                    border-radius: 6px;
                    padding: 6px 10px;
                    color: #0f172a;
                    font-family: Consolas, 'Fira Code', monospace;
                    font-size: 11px;
                }
                QLineEdit:focus {
                    border-color: #2563eb;
                }
            """)
            self.btn_toggle_key.setStyleSheet("""
                QPushButton {
                    background-color: #ffffff;
                    color: #475569;
                    border: 1px solid #cbd5e1;
                    border-radius: 5px;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #f1f5f9;
                    color: #0f172a;
                    border-color: #94a3b8;
                }
                QPushButton:checked {
                    background-color: #eff6ff;
                    color: #1d4ed8;
                    border-color: #3b82f6;
                }
            """)
            self.btn_pool.setStyleSheet("""
                QPushButton {
                    background-color: #eff6ff;
                    color: #1d4ed8;
                    border: 1px solid #bfdbfe;
                    border-radius: 5px;
                    font-weight: 700;
                    font-size: 11px;
                    padding: 4px 6px;
                }
                QPushButton:hover {
                    background-color: #dbeafe;
                    border-color: #3b82f6;
                }
            """)
            self.link_btn.setStyleSheet("""
                QPushButton {
                    color: #0284c7;
                    text-decoration: underline;
                    background: transparent;
                    border: none;
                    text-align: left;
                    padding: 1px 0;
                    font-size: 11px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    color: #0369a1;
                }
            """)
            self.lbl_model_title.setStyleSheet("color: #1e293b; font-weight: 700; font-size: 11px; background: transparent;")
            self.model_combo.setStyleSheet(f"""
                QComboBox {{
                    background-color: #ffffff;
                    border: 1px solid #cbd5e1;
                    border-radius: 6px;
                    padding: 6px 10px;
                    color: #0f172a;
                    font-size: 11px;
                    font-weight: 600;
                }}
                QComboBox:hover {{
                    border-color: #94a3b8;
                }}
                QComboBox:focus {{
                    border-color: #2563eb;
                }}
                QComboBox::drop-down {{
                    subcontrol-origin: padding;
                    subcontrol-position: top right;
                    width: 26px;
                    border: none;
                }}
                QComboBox::down-arrow {{
                    image: url("{chevron_light}");
                    width: 12px;
                    height: 12px;
                    margin-right: 8px;
                }}
                QComboBox QAbstractItemView {{
                    background-color: #ffffff;
                    border: 1px solid #cbd5e1;
                    color: #0f172a;
                    selection-background-color: #eff6ff;
                    selection-color: #1d4ed8;
                    padding: 4px;
                }}
            """)
            self.tip_lbl.setStyleSheet("""
                background-color: #eff6ff;
                color: #1d4ed8;
                border: 1px solid #bfdbfe;
                border-radius: 6px;
                padding: 7px 10px;
                font-size: 9.5pt;
                line-height: 1.35;
            """)
            self.btn_test.setStyleSheet(f"""
                QPushButton {{
                    background: {t['accent_gradient']};
                    color: #ffffff;
                    border: 1px solid {t['border_accent']};
                    border-radius: 6px;
                    font-weight: 700;
                    font-size: 11px;
                    padding: 5px 14px;
                }}
                QPushButton:hover {{
                    background: {t['accent_hover']};
                }}
                QPushButton:disabled {{
                    background: #e2e8f0;
                    color: #94a3b8;
                    border-color: #cbd5e1;
                }}
            """)
            self.lbl_test_status.setStyleSheet("color: #475569; font-size: 10.5px; background: transparent;")
            self.btn_cancel.setStyleSheet("""
                QPushButton {
                    background-color: #ffffff;
                    color: #334155;
                    border: 1px solid #cbd5e1;
                    border-radius: 6px;
                    padding: 6px 16px;
                    font-weight: 600;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #f1f5f9;
                    color: #0f172a;
                }
            """)
            self.btn_save.setStyleSheet(f"""
                QPushButton {{
                    background: {t['accent_gradient']};
                    color: #ffffff;
                    border: 1px solid {t['border_accent']};
                    border-radius: 6px;
                    padding: 6px 20px;
                    font-weight: 700;
                    font-size: 11.5px;
                }}
                QPushButton:hover {{
                    background: {t['accent_hover']};
                }}
            """)

        self._update_badge_style()
        self._update_theme_cards_ui()
        self._refresh_license_status_label()


    def _on_key_text_changed(self, text: str):
        self._update_badge_style()

    def _open_key_pool(self):
        try:
            from app.ui.multi_key_dialog import MultiKeyDialog
            dlg = MultiKeyDialog(self.key_input.text(), parent=self, is_dark=self.is_dark)
            if dlg.exec():
                keys = dlg.get_keys()
                self.key_input.setText("\n".join(keys) if len(keys) > 1 else (keys[0] if keys else ""))
                self._update_badge_style()
        except Exception:
            pass

    def _update_badge_style(self):
        raw = self.key_input.text().strip()
        from app.config import parse_api_keys
        keys = parse_api_keys(raw)
        count = len(keys)
        t = getattr(self, "theme", get_theme(self.is_dark))
        if count > 0:
            self.lbl_key_badge.setText(f"✓ Key ត្រឹមត្រូវ — {count} គ្រាប់សកម្ម (Active Key Pool)")
            if self.is_dark:
                self.lbl_key_badge.setStyleSheet(f"""
                    background-color: {t['subtle_pill_bg']};
                    color: {t['text_accent']};
                    border: 1px solid {t['border_accent']};
                    border-radius: 5px;
                    padding: 3px 8px;
                    font-size: 11px;
                    font-weight: 700;
                """)
            else:
                self.lbl_key_badge.setStyleSheet("""
                    background-color: #ecfdf5;
                    color: #047857;
                    border: 1px solid #a7f3d0;
                    border-radius: 5px;
                    padding: 3px 8px;
                    font-size: 11px;
                    font-weight: 700;
                """)
        else:
            self.lbl_key_badge.setText("🟡 Demo Mode (Add Key for Unlimited Live Generation)")
            if self.is_dark:
                self.lbl_key_badge.setStyleSheet(f"""
                    background-color: {t['bg_card_alt']};
                    color: {t['text_muted']};
                    border: 1px solid {t['border']};
                    border-radius: 5px;
                    padding: 3px 8px;
                    font-size: 11px;
                    font-weight: 700;
                """)
            else:
                self.lbl_key_badge.setStyleSheet("""
                    background-color: #fef3c7;
                    color: #92400e;
                    border: 1px solid #fde68a;
                    border-radius: 5px;
                    padding: 3px 8px;
                    font-size: 11px;
                    font-weight: 700;
                """)

    def _toggle_key_visibility(self, checked: bool):
        if checked:
            self.key_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.key_input.setEchoMode(QLineEdit.EchoMode.Password)

    def _test_connection(self):
        from app.gemini_client import ConnectionTestWorker
        key = self.key_input.text().strip()
        if not key:
            QMessageBox.warning(self, "Missing Key", "Please enter an API key before testing.")
            return

        self.btn_test.setText("⏳ Testing...")
        self.btn_test.setEnabled(False)
        self.lbl_test_status.setText("⏳ Connecting to Google Gemini API (timeout 10s)...")
        self.lbl_test_status.setStyleSheet("color: #0284c7; font-weight: 600; font-size: 10.5px; background: transparent;" if not self.is_dark else "color: #38bdf8; font-weight: 600; font-size: 10.5px; background: transparent;")

        model = self.model_combo.currentText()
        self.test_worker = ConnectionTestWorker(key=key, model=model, parent=self)
        self.test_worker.status_update.connect(self._on_test_status_update)
        self.test_worker.finished_success.connect(self._on_test_success)
        self.test_worker.finished_error.connect(self._on_test_error)
        self.test_worker.start()

    def _on_test_status_update(self, msg: str):
        self.lbl_test_status.setText(f"⏳ {msg}")

    def _on_test_success(self, resp_text: str, active_model: str, latency: float, pool_count: int):
        self.btn_test.setText("✓ Connected")
        self.btn_test.setEnabled(True)
        self.btn_test.setStyleSheet("""
            QPushButton {
                background: #064e3b;
                color: #34d399;
                border: 1px solid #059669;
                border-radius: 6px;
                font-weight: 700;
                font-size: 11px;
                padding: 5px 14px;
            }
            QPushButton:hover {
                background: #047857;
            }
        """)

        if active_model != self.model_combo.currentText():
            idx = self.model_combo.findText(active_model)
            if idx >= 0:
                self.model_combo.setCurrentIndex(idx)
            else:
                self.model_combo.addItem(active_model)
                self.model_combo.setCurrentText(active_model)
            config_manager.set("gemini_model", active_model)
            model_switched_note = f"\n\n⚡ Notice: Model auto-switched to active endpoint '{active_model}'."
        else:
            model_switched_note = ""

        pool_info = f"\n• Configured Pool: {pool_count} API key(s)" if pool_count > 1 else ""
        self.lbl_test_status.setText(f"✅ Connected! Latency: {latency}s • {active_model}")
        self.lbl_test_status.setStyleSheet("color: #059669; font-weight: 700; font-size: 10.5px; background: transparent;" if not self.is_dark else "color: #34d399; font-weight: 700; font-size: 10.5px; background: transparent;")

        QMessageBox.information(
            self,
            "Connection Verified",
            f"Connection Verified Successfully! 🚀\n\n"
            f"• Active Engine: {active_model}\n"
            f"• Response Time: {latency} seconds{pool_info}\n"
            f"• Gemini Response: \"{resp_text}\"{model_switched_note}\n\n"
            f"All systems are ready for high-speed AI songwriting!"
        )

    def _on_test_error(self, err_msg: str, category: str):
        self.btn_test.setText("⚡ Test Connection")
        self.btn_test.setEnabled(True)
        self.apply_theme(self.is_dark)
        self.lbl_test_status.setText("❌ Connection Failed (Click to recheck)")
        self.lbl_test_status.setStyleSheet("color: #dc2626; font-weight: 700; font-size: 10.5px; background: transparent;" if not self.is_dark else "color: #f87171; font-weight: 700; font-size: 10.5px; background: transparent;")
        QMessageBox.critical(self, "Connection Test Result", err_msg)

    def closeEvent(self, event):
        if hasattr(self, "test_worker") and self.test_worker and self.test_worker.isRunning():
            self.test_worker.terminate()
            self.test_worker.wait(500)
        if hasattr(self, "update_worker") and self.update_worker and self.update_worker.isRunning():
            self.update_worker.quit()
            self.update_worker.wait(500)
        super().closeEvent(event)

    def _check_for_updates(self):
        self.btn_check_update.setEnabled(False)
        self.btn_check_update.setText("⏳ Checking...")
        self.lbl_update_status.setText("⏳ Connecting to update server...")
        self.lbl_update_status.setStyleSheet("color: #38bdf8; font-size: 10.5px; font-weight: 600;" if self.is_dark else "color: #0284c7; font-size: 10.5px; font-weight: 600;")

        from app.updater import UpdateCheckWorker
        url = config_manager.get("update_url", DEFAULT_UPDATE_URL)
        self.update_worker = UpdateCheckWorker(update_url=url, current_version=APP_VERSION, parent=self)
        self.update_worker.update_available.connect(self._on_update_available)
        self.update_worker.up_to_date.connect(self._on_up_to_date)
        self.update_worker.check_failed.connect(self._on_check_failed)
        self.update_worker.start()

    def _on_update_available(self, manifest: dict):
        self.btn_check_update.setEnabled(True)
        self.btn_check_update.setText("🚀 Update Ready!")
        new_v = manifest.get("version", "")
        self.lbl_update_status.setText(f"🚀 New version v{new_v} is available! Click to inspect and install.")
        self.lbl_update_status.setStyleSheet("color: #34d399; font-weight: 700; font-size: 10.5px;" if self.is_dark else "color: #059669; font-weight: 700; font-size: 10.5px;")

        from app.ui.update_dialog import StudioUpdateDialog
        dlg = StudioUpdateDialog(self, manifest=manifest, theme_key=self.selected_theme)
        dlg.exec()

    def _on_up_to_date(self, remote_ver: str):
        self.btn_check_update.setEnabled(True)
        self.btn_check_update.setText("🔄 Check for Updates")
        self.lbl_update_status.setText(f"✓ កម្មវិធីស្ថិតក្នុងកំណែថ្មីបំផុតហើយ (v{APP_VERSION} is the latest version)")
        self.lbl_update_status.setStyleSheet("color: #34d399; font-weight: 700; font-size: 10.5px;" if self.is_dark else "color: #059669; font-weight: 700; font-size: 10.5px;")

    def _on_check_failed(self, error_msg: str):
        self.btn_check_update.setEnabled(True)
        self.btn_check_update.setText("🔄 Check for Updates")
        self.lbl_update_status.setText(f"⚠️ Check failed: {error_msg}")
        self.lbl_update_status.setStyleSheet("color: #f87171; font-weight: 600; font-size: 10.5px;" if self.is_dark else "color: #dc2626; font-weight: 600; font-size: 10.5px;")

    def _open_license_dialog(self):
        from app.ui.activation_dialog import LicenseActivationDialog
        dlg = LicenseActivationDialog(self, theme_key=self.selected_theme)
        dlg.exec()
        self._refresh_license_status_label()
        if self.parent():
            if hasattr(self.parent(), "_update_license_btn_style"):
                self.parent()._update_license_btn_style()
            if hasattr(self.parent(), "_update_status_bar"):
                self.parent()._update_status_bar()

    def _refresh_license_status_label(self):
        if not hasattr(self, "lbl_license_status"):
            return
        info = license_manager.get_license_info()
        machine_id = license_manager.get_machine_id()
        if info["is_active"]:
            self.lbl_license_status.setText(f"💎 <b>{info['plan_name']}</b> — Active (ID: <code>{machine_id}</code>)")
            if self.is_dark:
                self.lbl_license_status.setStyleSheet("color: #34d399; font-size: 11px; background: transparent;")
            else:
                self.lbl_license_status.setStyleSheet("color: #059669; font-size: 11px; background: transparent;")
            self.btn_manage_license.setText("💎 License Info")
        else:
            self.lbl_license_status.setText(f"🔒 <b>Demo Mode</b> (ID: <code>{machine_id}</code>)")
            if self.is_dark:
                self.lbl_license_status.setStyleSheet("color: #fbbf24; font-size: 11px; background: transparent;")
            else:
                self.lbl_license_status.setStyleSheet("color: #d97706; font-size: 11px; background: transparent;")
            self.btn_manage_license.setText("🔑 Activate Pro")

    def _save_settings(self):
        key = self.key_input.text().strip()
        model = self.model_combo.currentText()
        config_manager.set_api_keys(key)
        config_manager.set("gemini_model", model)
        config_manager.set("studio_theme", getattr(self, "selected_theme", "obsidian"))
        if hasattr(self, "chk_auto_update"):
            config_manager.set("auto_check_updates", self.chk_auto_update.isChecked())
        self.accept()
