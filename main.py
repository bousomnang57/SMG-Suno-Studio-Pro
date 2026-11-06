"""
SMG Suno AI Lyric Writer — Global Music Studio
Main Desktop Application Launcher (PyQt6 + Gemini AI)
"""

import sys
import os

# Ensure the project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon, QFontDatabase

from app.config import config_manager, get_asset_path, get_resource_dir
from app.ui.styles import get_theme
from app.ui.main_window import MainWindow

def setup_application_fonts():
    """Load bundled Khmer and UI fonts into memory so the app renders perfectly on all PCs."""
    fonts_dir = get_asset_path("fonts")
    if fonts_dir.exists():
        for font_file in fonts_dir.glob("*.ttf"):
            try:
                QFontDatabase.addApplicationFont(str(font_file))
            except Exception:
                pass

def main():
    # If running frozen executable, ensure current working directory is the app folder
    try:
        os.chdir(get_resource_dir())
    except Exception:
        pass

    # Enable High DPI and Modern Scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("SMG Suno AI Lyric Writer")
    app.setOrganizationName("SMG Studio")

    # Set Application Window Icon
    logo_path = get_asset_path("logo.png")
    if logo_path.exists():
        app.setWindowIcon(QIcon(str(logo_path)))

    # Load Bundled Khmer & Latin Fonts
    setup_application_fonts()

    # Set default modern font with robust Khmer fallback
    font = QFont()
    font.setFamilies([
        "Segoe UI",
        "Khmer OS Battambang",
        "Noto Sans Khmer",
        "Khmer OS Content",
        "Khmer UI",
        "Leelawadee UI",
        "Arial",
        "sans-serif"
    ])
    font.setPointSize(10)
    app.setFont(font)

    # Apply saved or default modern studio stylesheet
    saved_theme = config_manager.get("theme", "obsidian")
    t_data = get_theme(saved_theme)
    app.setStyleSheet(t_data["qss"])

    window = MainWindow()
    if logo_path.exists():
        window.setWindowIcon(QIcon(str(logo_path)))
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
