"""
SMG Suno Studio Pro — Global Music Studio
Main Desktop Application Launcher (PyQt6 + Gemini AI)
Hardened for portable zero-error execution across all Windows 10/11 PCs.
"""

import sys
import os
import traceback
from pathlib import Path

# Ensure the project root is in sys.path (dev & frozen PyInstaller)
_BOOT_DIR = os.path.dirname(os.path.abspath(__file__))
if _BOOT_DIR not in sys.path:
    sys.path.insert(0, _BOOT_DIR)

# Force UTF-8 I/O & configure bundled SSL CA certificates before any network/AI imports
os.environ.setdefault("PYTHONUTF8", "1")
try:
    import certifi
    _CA_PATH = certifi.where()
    if _CA_PATH and os.path.exists(_CA_PATH):
        os.environ.setdefault("SSL_CERT_FILE", _CA_PATH)
        os.environ.setdefault("REQUESTS_CA_BUNDLE", _CA_PATH)
except Exception:
    pass


def _install_crash_logger():
    """Log unhandled exceptions to ~/.lyric_ai_writer/crash.log so frozen builds never fail silently."""
    log_dir = Path.home() / ".lyric_ai_writer"

    def _handle_exception(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        trace_txt = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            with open(log_dir / "crash.log", "a", encoding="utf-8") as f:
                f.write("\n" + "=" * 60 + "\n")
                f.write(trace_txt)
        except Exception:
            pass
        try:
            from PyQt6.QtWidgets import QApplication, QMessageBox
            if QApplication.instance():
                QMessageBox.critical(
                    None,
                    "SMG Suno Studio Pro — Unexpected Error",
                    f"An unexpected error occurred and was logged to:\n{log_dir / 'crash.log'}\n\n{exc_value}"
                )
        except Exception:
            pass

    sys.excepthook = _handle_exception


from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon, QFontDatabase

from app.config import config_manager, get_asset_path, get_resource_dir, APP_NAME, APP_VERSION
from app.ui.styles import get_theme
from app.ui.main_window import MainWindow


def setup_application_fonts():
    """Load bundled Khmer and UI fonts into memory so the app renders perfectly on all PCs."""
    fonts_dir = get_asset_path("fonts")
    if fonts_dir.exists():
        for font_file in sorted(fonts_dir.glob("*.ttf")):
            try:
                QFontDatabase.addApplicationFont(str(font_file))
            except Exception:
                pass


def _extract_cli_project_file(argv: list[str]) -> Path | None:
    """Resolve an optional .smgsong / .json / .txt / .lrc / .cho path before changing cwd."""
    supported = {".smgsong", ".json", ".txt", ".lrc", ".cho"}
    for arg in argv[1:]:
        if arg.startswith("-"):
            continue
        try:
            p = Path(arg).expanduser().resolve()
            if p.is_file() and p.suffix.lower() in supported:
                return p
        except Exception:
            continue
    return None


def main():
    _install_crash_logger()

    smoke_test = "--smoke-test" in sys.argv
    initial_project_file = _extract_cli_project_file(sys.argv)

    # If running frozen executable, ensure current working directory is the app bundle folder
    try:
        os.chdir(get_resource_dir())
    except Exception:
        pass

    # Enable High DPI and Modern Scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
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

    # If launched by double-clicking a .smgsong or lyric file, open it directly into the studio
    if initial_project_file is not None:
        try:
            from app.project_manager import ProjectManager
            proj = ProjectManager.load_project(str(initial_project_file))
            window._apply_project(proj)
            if initial_project_file.suffix.lower() == ".smgsong":
                window.current_project_path = str(initial_project_file)
                window._update_window_title()
            window._set_studio_mode(3)
        except Exception:
            pass

    if smoke_test:
        # Automated frozen-EXE health verification for release builds
        for idx in range(5):
            window._set_studio_mode(idx)
        window.close()
        app.quit()
        sys.exit(0)

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
