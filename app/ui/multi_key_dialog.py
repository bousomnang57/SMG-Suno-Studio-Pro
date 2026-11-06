"""
Gemini Multi-API Key Pool Dialog.
Enables pasting, validating, and rotating multiple Gemini API keys
to prevent 429 quota exhaustion during high-volume batch generations.
Engineered for clean UI fit, high contrast, zero background artifacts, and full theme synchronization.
"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPlainTextEdit, QPushButton, QMessageBox, QFrame, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from app.config import config_manager, parse_api_keys, get_asset_path
from app.gemini_client import ConnectionTestWorker

class MultiKeyDialog(QDialog):
    """Sleek modal dialog for managing the Gemini API key rotation pool."""
    keys_updated = pyqtSignal(int)

    def __init__(self, parent=None, is_dark: bool = None):
        super().__init__(parent)
        if is_dark is None:
            if parent and hasattr(parent, "is_dark"):
                is_dark = parent.is_dark
            elif parent and hasattr(parent, "is_dark_theme"):
                is_dark = parent.is_dark_theme
            else:
                is_dark = (config_manager.get("theme", "light") == "dark")
        self.is_dark = is_dark

        self.setWindowTitle("SMG Suno AI — Gemini API Key Pool")
        self.setFixedSize(540, 480)
        self.setModal(True)

        logo_path = get_asset_path("logo.png")
        if logo_path.exists():
            self.setWindowIcon(QIcon(str(logo_path)))

        self._init_ui()
        self.apply_theme(self.is_dark)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        # Header Title
        title = QLabel("🔑 Gemini API Key Pool")
        title.setObjectName("headingLabel")
        self.title_lbl = title
        layout.addWidget(title)

        desc = QLabel(
            "បញ្ចូល ឬ Paste API Key ច្រើនគ្រាប់ (បំបែកដោយបន្ទាត់ថ្មី ឬក្បៀស)។\n"
            "ប្រព័ន្ធនឹងធ្វើការបង្វិល (Auto-Rotate) ឆ្លាស់គ្នាដោយស្វ័យប្រវត្តិកុំឱ្យជាប់ 429 Quota Exhaustion។"
        )
        desc.setWordWrap(True)
        self.desc_lbl = desc
        layout.addWidget(desc)

        # Live Status Badge Card
        self.status_card = QFrame()
        sc_layout = QHBoxLayout(self.status_card)
        sc_layout.setContentsMargins(10, 7, 10, 7)

        self.lbl_badge = QLabel()
        sc_layout.addWidget(self.lbl_badge)
        sc_layout.addStretch()

        self.lbl_counter = QLabel("0 keys detected")
        sc_layout.addWidget(self.lbl_counter)

        layout.addWidget(self.status_card)

        # Multiline Text Editor for Keys
        self.txt_keys = QPlainTextEdit()
        self.txt_keys.setPlaceholderText(
            "AIzaSyExampleKey1...\n"
            "AIzaSyExampleKey2...\n"
            "AIzaSyExampleKey3...\n"
            "(Paste 1 to 50+ Gemini API keys here, 1 per line or comma-separated)"
        )
        self.txt_keys.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.txt_keys, stretch=1)

        # Quick Helper Buttons
        h_tools = QHBoxLayout()
        h_tools.setSpacing(8)

        self.btn_paste = QPushButton("📋 Paste Clipboard")
        self.btn_paste.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_paste.clicked.connect(self._paste_clipboard)
        h_tools.addWidget(self.btn_paste)

        self.btn_clear = QPushButton("🗑️ Clear")
        self.btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear.clicked.connect(self._clear_text)
        h_tools.addWidget(self.btn_clear)

        self.btn_test_pool = QPushButton("⚡ Test Pool")
        self.btn_test_pool.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_test_pool.setToolTip("Test connectivity of the entered API key(s)")
        self.btn_test_pool.clicked.connect(self._test_pool)
        h_tools.addWidget(self.btn_test_pool)

        h_tools.addStretch()
        layout.addLayout(h_tools)

        # Bottom Action Buttons
        h_actions = QHBoxLayout()
        h_actions.setSpacing(10)
        h_actions.addStretch()

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.clicked.connect(self.reject)
        h_actions.addWidget(self.btn_cancel)

        self.btn_save = QPushButton("💾 Save Key Pool")
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.clicked.connect(self._save_pool)
        h_actions.addWidget(self.btn_save)

        layout.addLayout(h_actions)

        # Load existing keys
        existing = config_manager.get_api_keys()
        if existing:
            self.txt_keys.setPlainText("\n".join(existing))
        self._on_text_changed()

    def _on_text_changed(self):
        text = self.txt_keys.toPlainText().strip()
        keys = parse_api_keys(text)
        count = len(keys)
        if count > 0:
            self.lbl_badge.setText(f"✓ Key ត្រឹមត្រូវ — {count} គ្រាប់")
            if self.is_dark:
                self.lbl_badge.setStyleSheet("font-size: 12px; font-weight: 800; color: #34d399; background: transparent;")
                self.lbl_counter.setStyleSheet("font-size: 11px; font-weight: 700; color: #a78bfa; background: transparent;")
            else:
                self.lbl_badge.setStyleSheet("font-size: 12px; font-weight: 800; color: #059669; background: transparent;")
                self.lbl_counter.setStyleSheet("font-size: 11px; font-weight: 700; color: #6d28d9; background: transparent;")
            self.lbl_counter.setText(f"{count} active keys in pool")
        else:
            self.lbl_badge.setText("🟡 No Keys Configured (Demo Mode)")
            if self.is_dark:
                self.lbl_badge.setStyleSheet("font-size: 12px; font-weight: 800; color: #fbbf24; background: transparent;")
                self.lbl_counter.setStyleSheet("font-size: 11px; font-weight: 700; color: #94a3b8; background: transparent;")
            else:
                self.lbl_badge.setStyleSheet("font-size: 12px; font-weight: 800; color: #b45309; background: transparent;")
                self.lbl_counter.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748b; background: transparent;")
            self.lbl_counter.setText("0 keys detected")

    def _paste_clipboard(self):
        clipboard = QApplication.clipboard()
        text = clipboard.text().strip()
        if text:
            cur = self.txt_keys.toPlainText().strip()
            if cur:
                self.txt_keys.setPlainText(cur + "\n" + text)
            else:
                self.txt_keys.setPlainText(text)

    def _clear_text(self):
        self.txt_keys.clear()

    def _test_pool(self):
        text = self.txt_keys.toPlainText().strip()
        keys = parse_api_keys(text)
        if not keys:
            QMessageBox.warning(self, "No Keys", "Please enter or paste at least one valid Gemini API key to test.")
            return

        self.btn_test_pool.setText("⏳ Testing...")
        self.btn_test_pool.setEnabled(False)
        self.lbl_counter.setText("⏳ Verifying with Google API (timeout 10s)...")
        self.lbl_counter.setStyleSheet("font-size: 11px; font-weight: 700; color: #38bdf8; background: transparent;")

        model = config_manager.get("gemini_model", "gemini-3.5-flash")
        self.test_worker = ConnectionTestWorker(key=text, model=model, parent=self)
        self.test_worker.status_update.connect(lambda msg: self.lbl_counter.setText(f"⏳ {msg}"))
        self.test_worker.finished_success.connect(self._on_pool_test_success)
        self.test_worker.finished_error.connect(self._on_pool_test_error)
        self.test_worker.start()

    def _on_pool_test_success(self, resp_text: str, active_model: str, latency: float, pool_count: int):
        self.btn_test_pool.setText("✓ Verified")
        self.btn_test_pool.setEnabled(True)
        self.lbl_counter.setText(f"✅ Verified! {pool_count} key(s) • {latency}s")
        self.lbl_counter.setStyleSheet("font-size: 11px; font-weight: 800; color: #34d399; background: transparent;")

        QMessageBox.information(
            self,
            "Key Pool Verified",
            f"API Key Pool Verified Successfully! 🚀\n\n"
            f"• Verified Keys: {pool_count} active\n"
            f"• Active Model: {active_model}\n"
            f"• Response Time: {latency}s\n"
            f"• Echo Response: \"{resp_text}\"\n\n"
            f"Your key rotation pool is active and ready for batch generation."
        )

    def _on_pool_test_error(self, err_msg: str, category: str):
        self.btn_test_pool.setText("⚡ Test Pool")
        self.btn_test_pool.setEnabled(True)
        self.lbl_counter.setText("❌ Verification Failed")
        self.lbl_counter.setStyleSheet("font-size: 11px; font-weight: 700; color: #f87171; background: transparent;")

        QMessageBox.critical(self, "Verification Failed", err_msg)

    def closeEvent(self, event):
        if hasattr(self, "test_worker") and self.test_worker and self.test_worker.isRunning():
            self.test_worker.terminate()
            self.test_worker.wait(500)
        super().closeEvent(event)

    def _save_pool(self):
        text = self.txt_keys.toPlainText().strip()
        keys = parse_api_keys(text)
        config_manager.set_api_keys(keys)
        self.keys_updated.emit(len(keys))
        self.accept()

    def apply_theme(self, is_dark: bool):
        self.is_dark = is_dark
        if is_dark:
            self.setStyleSheet("""
                QDialog {
                    background-color: #0b0f19;
                    color: #f1f5f9;
                }
            """)
            self.title_lbl.setStyleSheet("font-size: 15px; font-weight: 800; color: #f8fafc; background: transparent;")
            self.desc_lbl.setStyleSheet("font-size: 11px; color: #94a3b8; background: transparent; line-height: 1.4;")
            self.status_card.setStyleSheet("""
                background-color: #111827;
                border: 1px solid #1f2937;
                border-radius: 6px;
            """)
            self.txt_keys.setStyleSheet("""
                QPlainTextEdit {
                    background-color: #0d1117;
                    color: #e2e8f0;
                    border: 1px solid #1f2845;
                    border-radius: 6px;
                    padding: 8px;
                    font-family: Consolas, 'Fira Code', monospace;
                    font-size: 11px;
                }
                QPlainTextEdit:focus {
                    border: 1px solid #6366f1;
                }
            """)
            btn_tool_style = """
                QPushButton {
                    background-color: #1e1b4b;
                    color: #a78bfa;
                    border: 1px solid #4338ca;
                    border-radius: 5px;
                    padding: 5px 12px;
                    font-size: 11px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #312e81;
                    color: #ffffff;
                }
            """
            self.btn_paste.setStyleSheet(btn_tool_style)
            self.btn_clear.setStyleSheet(btn_tool_style)
            self.btn_test_pool.setStyleSheet("""
                QPushButton {
                    background-color: #1e1b4b;
                    color: #c084fc;
                    border: 1px solid #6366f1;
                    border-radius: 5px;
                    padding: 5px 12px;
                    font-size: 11px;
                    font-weight: 700;
                }
                QPushButton:hover {
                    background-color: #312e81;
                    color: #ffffff;
                    border-color: #818cf8;
                }
            """)
            self.btn_cancel.setStyleSheet("""
                QPushButton {
                    background-color: #1f2937;
                    color: #94a3b8;
                    border: 1px solid #374151;
                    border-radius: 6px;
                    padding: 6px 14px;
                    font-size: 11.5px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #374151;
                    color: #ffffff;
                }
            """)
            self.btn_save.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366f1, stop:1 #8b5cf6);
                    color: #ffffff;
                    border: none;
                    border-radius: 6px;
                    padding: 6px 18px;
                    font-size: 11.5px;
                    font-weight: 700;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4f46e5, stop:1 #7c3aed);
                }
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
            self.desc_lbl.setStyleSheet("font-size: 11px; color: #64748b; background: transparent; line-height: 1.4;")
            self.status_card.setStyleSheet("""
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
            """)
            self.txt_keys.setStyleSheet("""
                QPlainTextEdit {
                    background-color: #ffffff;
                    color: #0f172a;
                    border: 1px solid #cbd5e1;
                    border-radius: 6px;
                    padding: 8px;
                    font-family: Consolas, 'Fira Code', monospace;
                    font-size: 11px;
                }
                QPlainTextEdit:focus {
                    border: 1px solid #6366f1;
                }
            """)
            btn_tool_style = """
                QPushButton {
                    background-color: #f1f5f9;
                    color: #334155;
                    border: 1px solid #cbd5e1;
                    border-radius: 5px;
                    padding: 5px 12px;
                    font-size: 11px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #e2e8f0;
                    color: #0f172a;
                }
            """
            self.btn_paste.setStyleSheet(btn_tool_style)
            self.btn_clear.setStyleSheet(btn_tool_style)
            self.btn_test_pool.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4f46e5, stop:1 #6366f1);
                    color: #ffffff;
                    border: 1px solid #4338ca;
                    border-radius: 5px;
                    padding: 5px 12px;
                    font-size: 11px;
                    font-weight: 700;
                }
                QPushButton:hover {
                    background: #4338ca;
                }
            """)
            self.btn_cancel.setStyleSheet("""
                QPushButton {
                    background-color: #f1f5f9;
                    color: #475569;
                    border: 1px solid #cbd5e1;
                    border-radius: 6px;
                    padding: 6px 14px;
                    font-size: 11.5px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #e2e8f0;
                    color: #0f172a;
                }
            """)
            self.btn_save.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563eb, stop:1 #3b82f6);
                    color: #ffffff;
                    border: 1px solid #1d4ed8;
                    border-radius: 6px;
                    padding: 6px 18px;
                    font-size: 11.5px;
                    font-weight: 700;
                }
                QPushButton:hover {
                    background: #1d4ed8;
                }
            """)

        self._on_text_changed()
