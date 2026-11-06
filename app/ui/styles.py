"""
Modern Professional Music Production Studio Themes for PyQt6.
Includes 5 Pristine Modern Themes:
1. Obsidian Violet (Flagship Cyberpunk Studio Dark)
2. Midnight Cyber Blue (Deep Ocean Sapphire & Sky Blue)
3. Emerald Forest (Nordic Slate Pine & Mint Green)
4. Sunset Amber (Analog Console & Warm Titanium)
5. Pure Canvas Light (Modern Cupertino / Notion Clean)

Engineered for zero Qt font warnings, ultra-high readability, and seamless 1-click theme switching.
"""

DARK_STUDIO_QSS = '''/* ==========================================================================
   SMG SUNO AI LYRIC WRITER - OBSIDIAN VIOLET THEME
   Flagship Ableton / Cyberpunk Studio Dark
   ========================================================================== */

QWidget {
    background-color: #08090f;
    color: #cbd5e1;
    font-family: "Segoe UI", "Khmer OS Battambang", "Noto Sans Khmer", "Khmer UI", "Leelawadee UI", sans-serif;
    font-size: 10pt;
    selection-background-color: #8b5cf6;
    selection-color: #ffffff;
}

QMainWindow {
    background-color: #08090f;
}

QToolBar {
    background-color: #111526;
    border-bottom: 1px solid #1e2540;
    padding: 6px;
    spacing: 8px;
}

QGroupBox {
    background-color: #111526;
    border: 1px solid #1e2540;
    border-radius: 8px;
    margin-top: 18px;
    padding: 14px 10px 10px 10px;
    font-weight: 700;
    color: #c4b5fd;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    background-color: #111526;
    color: #c4b5fd;
}

QLabel {
    color: #cbd5e1;
}

QLabel#headingLabel {
    font-size: 12pt;
    font-weight: 800;
    color: #ffffff;
}

QLabel#badgeLabel {
    background-color: #1e1b4b;
    color: #a78bfa;
    border: 1px solid #4338ca;
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 9pt;
    font-weight: 700;
}

QLabel#genreDescription {
    color: #94a3b8;
    font-size: 9pt;
    line-height: 1.4;
}

QLineEdit, QComboBox, QSpinBox {
    background-color: #090b14;
    border: 1px solid #283256;
    border-radius: 6px;
    padding: 6px 10px;
    color: #ffffff;
    font-size: 10pt;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border: 1px solid #8b5cf6;
    background-color: #0e1222;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    border: none;
    width: 24px;
}

QComboBox::down-arrow {
    image: url("assets/chevron_down_dark.svg");
    width: 12px;
    height: 12px;
    margin-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #111526;
    border: 1px solid #283256;
    selection-background-color: #7c3aed;
    selection-color: #ffffff;
    color: #cbd5e1;
    padding: 4px;
}

QPushButton {
    background-color: #161b2e;
    border: 1px solid #283256;
    border-radius: 6px;
    padding: 7px 14px;
    color: #ffffff;
    font-weight: 600;
    font-size: 10pt;
}

QPushButton:hover {
    background-color: #222944;
    border-color: #8b5cf6;
    color: #ffffff;
}

QPushButton:pressed {
    background-color: #08090f;
}

QPushButton:disabled {
    background-color: #08090f;
    border-color: #1e2540;
    color: #94a3b8;
}

QPushButton:checked {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7c3aed, stop:1 #4f46e5);
    border-color: #8b5cf6;
    color: #ffffff;
}

QMenu {
    background-color: #111526;
    color: #ffffff;
    border: 1px solid #283256;
    border-radius: 6px;
    padding: 4px;
}

QMenu::item {
    padding: 6px 14px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #7c3aed;
    color: #ffffff;
}

QMenu::separator {
    height: 1px;
    background: #1e2540;
    margin: 4px 8px;
}

QToolTip {
    background-color: #111526;
    color: #ffffff;
    border: 1px solid #8b5cf6;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 9pt;
}

QPushButton#primaryGenerateButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7c3aed, stop:1 #4f46e5);
    border: 1px solid #8b5cf6;
    color: #ffffff;
    font-weight: 800;
    font-size: 10pt;
    padding: 10px 18px;
    border-radius: 8px;
}

QPushButton#primaryGenerateButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #9333ea, stop:1 #8b5cf6);
    border-color: #9333ea;
}

QPushButton#primaryGenerateButton:pressed {
    background: #7c3aed;
}

QPushButton#accentButton {
    background-color: #1e1b4b;
    border: 1px solid #7c3aed;
    color: #9333ea;
    font-weight: 700;
    font-size: 10pt;
}

QPushButton#accentButton:hover {
    background-color: #7c3aed;
    color: #ffffff;
}

QPushButton#sectionButton {
    background-color: #111526;
    border: 1px dashed #283256;
    color: #94a3b8;
    border-radius: 5px;
    padding: 4px 8px;
    font-size: 9pt;
}

QPushButton#sectionButton:hover {
    background-color: #161b2e;
    border-color: #8b5cf6;
    color: #c4b5fd;
}

QTextEdit, QPlainTextEdit {
    background-color: #090b14;
    border: 1px solid #1e2540;
    border-radius: 8px;
    color: #ffffff;
    font-family: "Cascadia Code", "Consolas", "Khmer OS Battambang", monospace;
    font-size: 10pt;
    line-height: 1.6;
    padding: 10px;
}

QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #8b5cf6;
}

QTabWidget::pane {
    border: 1px solid #1e2540;
    background-color: #111526;
    border-radius: 8px;
    top: -1px;
}

QTabBar::tab {
    background-color: #08090f;
    border: 1px solid #1e2540;
    border-bottom: none;
    color: #94a3b8;
    padding: 8px 16px;
    margin-right: 4px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: 600;
    font-size: 9pt;
}

QTabBar::tab:selected {
    background-color: #111526;
    border-color: #1e2540;
    border-bottom: 2px solid #8b5cf6;
    color: #c4b5fd;
}

QTabBar::tab:hover:!selected {
    background-color: #161b2e;
    color: #cbd5e1;
}

QSlider::groove:horizontal {
    height: 6px;
    background: #1e2540;
    border-radius: 3px;
}

QSlider::sub-page:horizontal {
    background: #8b5cf6;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #c4b5fd;
    border: 2px solid #8b5cf6;
    width: 16px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 8px;
}

QScrollBar:vertical {
    background: #08090f;
    width: 8px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #283256;
    min-height: 25px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #8b5cf6;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QStatusBar {
    background-color: #08090f;
    border-top: 1px solid #1e2540;
    color: #94a3b8;
    font-size: 9pt;
}

QSplitter::handle {
    background-color: #1e2540;
}

QDialog {
    background-color: #08090f;
    color: #ffffff;
}

QTableWidget {
    background-color: #0b0f1f;
    color: #f8fafc;
    border: 1px solid #1e2540;
    gridline-color: #1e2540;
    selection-background-color: #2e1065;
    selection-color: #ffffff;
}

QHeaderView::section {
    background-color: #111526;
    color: #c4b5fd;
    padding: 6px 10px;
    border: 1px solid #1e2540;
    font-weight: 800;
}

QScrollBar:horizontal {
    background: #08090f;
    height: 8px;
    margin: 0px;
}

QScrollBar::handle:horizontal {
    background: #283256;
    min-width: 25px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal:hover {
    background: #8b5cf6;
}

QCheckBox, QRadioButton {
    color: #f1f5f9;
    font-weight: 600;
    spacing: 8px;
}

QProgressBar {
    background-color: #0b0f1f;
    border: 1px solid #1e2540;
    border-radius: 5px;
    text-align: center;
    color: #ffffff;
    font-weight: 700;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7c3aed, stop:1 #8b5cf6);
    border-radius: 4px;
}
'''

CYBER_BLUE_STUDIO_QSS = '''/* ==========================================================================
   SMG SUNO AI LYRIC WRITER - MIDNIGHT CYBER BLUE THEME
   Logic Pro X / Deep Ocean Sapphire & Sky Blue
   ========================================================================== */

QWidget {
    background-color: #050a14;
    color: #bae6fd;
    font-family: "Segoe UI", "Khmer OS Battambang", "Noto Sans Khmer", "Khmer UI", "Leelawadee UI", sans-serif;
    font-size: 10pt;
    selection-background-color: #0ea5e9;
    selection-color: #ffffff;
}

QMainWindow {
    background-color: #050a14;
}

QToolBar {
    background-color: #0a1424;
    border-bottom: 1px solid #152642;
    padding: 6px;
    spacing: 8px;
}

QGroupBox {
    background-color: #0a1424;
    border: 1px solid #152642;
    border-radius: 8px;
    margin-top: 18px;
    padding: 14px 10px 10px 10px;
    font-weight: 700;
    color: #7dd3fc;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    background-color: #0a1424;
    color: #7dd3fc;
}

QLabel {
    color: #bae6fd;
}

QLabel#headingLabel {
    font-size: 12pt;
    font-weight: 800;
    color: #ffffff;
}

QLabel#badgeLabel {
    background-color: #082f49;
    color: #38bdf8;
    border: 1px solid #0369a1;
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 9pt;
    font-weight: 700;
}

QLabel#genreDescription {
    color: #7dd3fc;
    font-size: 9pt;
    line-height: 1.4;
}

QLineEdit, QComboBox, QSpinBox {
    background-color: #070e1c;
    border: 1px solid #1d3862;
    border-radius: 6px;
    padding: 6px 10px;
    color: #ffffff;
    font-size: 10pt;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border: 1px solid #0ea5e9;
    background-color: #0b1a32;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    border: none;
    width: 24px;
}

QComboBox::down-arrow {
    image: url("assets/chevron_down_dark.svg");
    width: 12px;
    height: 12px;
    margin-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #0a1424;
    border: 1px solid #1d3862;
    selection-background-color: #0284c7;
    selection-color: #ffffff;
    color: #bae6fd;
    padding: 4px;
}

QPushButton {
    background-color: #0f1f38;
    border: 1px solid #1d3862;
    border-radius: 6px;
    padding: 7px 14px;
    color: #ffffff;
    font-weight: 600;
    font-size: 10pt;
}

QPushButton:hover {
    background-color: #162c4e;
    border-color: #0ea5e9;
    color: #ffffff;
}

QPushButton:pressed {
    background-color: #050a14;
}

QPushButton:disabled {
    background-color: #050a14;
    border-color: #152642;
    color: #7dd3fc;
}

QPushButton:checked {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #2563eb);
    border-color: #0ea5e9;
    color: #ffffff;
}

QMenu {
    background-color: #0a1424;
    color: #ffffff;
    border: 1px solid #1d3862;
    border-radius: 6px;
    padding: 4px;
}

QMenu::item {
    padding: 6px 14px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #0284c7;
    color: #ffffff;
}

QMenu::separator {
    height: 1px;
    background: #152642;
    margin: 4px 8px;
}

QToolTip {
    background-color: #0a1424;
    color: #ffffff;
    border: 1px solid #0ea5e9;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 9pt;
}

QPushButton#primaryGenerateButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #2563eb);
    border: 1px solid #0ea5e9;
    color: #ffffff;
    font-weight: 800;
    font-size: 10pt;
    padding: 10px 18px;
    border-radius: 8px;
}

QPushButton#primaryGenerateButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #38bdf8, stop:1 #0ea5e9);
    border-color: #38bdf8;
}

QPushButton#primaryGenerateButton:pressed {
    background: #0284c7;
}

QPushButton#accentButton {
    background-color: #082f49;
    border: 1px solid #0284c7;
    color: #38bdf8;
    font-weight: 700;
    font-size: 10pt;
}

QPushButton#accentButton:hover {
    background-color: #0284c7;
    color: #ffffff;
}

QPushButton#sectionButton {
    background-color: #0a1424;
    border: 1px dashed #1d3862;
    color: #7dd3fc;
    border-radius: 5px;
    padding: 4px 8px;
    font-size: 9pt;
}

QPushButton#sectionButton:hover {
    background-color: #0f1f38;
    border-color: #0ea5e9;
    color: #7dd3fc;
}

QTextEdit, QPlainTextEdit {
    background-color: #070e1c;
    border: 1px solid #152642;
    border-radius: 8px;
    color: #ffffff;
    font-family: "Cascadia Code", "Consolas", "Khmer OS Battambang", monospace;
    font-size: 10pt;
    line-height: 1.6;
    padding: 10px;
}

QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #0ea5e9;
}

QTabWidget::pane {
    border: 1px solid #152642;
    background-color: #0a1424;
    border-radius: 8px;
    top: -1px;
}

QTabBar::tab {
    background-color: #050a14;
    border: 1px solid #152642;
    border-bottom: none;
    color: #7dd3fc;
    padding: 8px 16px;
    margin-right: 4px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: 600;
    font-size: 9pt;
}

QTabBar::tab:selected {
    background-color: #0a1424;
    border-color: #152642;
    border-bottom: 2px solid #0ea5e9;
    color: #7dd3fc;
}

QTabBar::tab:hover:!selected {
    background-color: #0f1f38;
    color: #bae6fd;
}

QSlider::groove:horizontal {
    height: 6px;
    background: #152642;
    border-radius: 3px;
}

QSlider::sub-page:horizontal {
    background: #0ea5e9;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #7dd3fc;
    border: 2px solid #0ea5e9;
    width: 16px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 8px;
}

QScrollBar:vertical {
    background: #050a14;
    width: 8px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #1d3862;
    min-height: 25px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #0ea5e9;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QStatusBar {
    background-color: #050a14;
    border-top: 1px solid #152642;
    color: #7dd3fc;
    font-size: 9pt;
}

QSplitter::handle {
    background-color: #152642;
}

QDialog {
    background-color: #050a14;
    color: #ffffff;
}

QTableWidget {
    background-color: #08101d;
    color: #f0f9ff;
    border: 1px solid #152642;
    gridline-color: #152642;
    selection-background-color: #0c4a6e;
    selection-color: #ffffff;
}

QHeaderView::section {
    background-color: #0a1424;
    color: #7dd3fc;
    padding: 6px 10px;
    border: 1px solid #152642;
    font-weight: 800;
}

QScrollBar:horizontal {
    background: #050a14;
    height: 8px;
    margin: 0px;
}

QScrollBar::handle:horizontal {
    background: #1d3862;
    min-width: 25px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal:hover {
    background: #0ea5e9;
}

QCheckBox, QRadioButton {
    color: #f0f9ff;
    font-weight: 600;
    spacing: 8px;
}

QProgressBar {
    background-color: #08101d;
    border: 1px solid #152642;
    border-radius: 5px;
    text-align: center;
    color: #ffffff;
    font-weight: 700;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #0ea5e9);
    border-radius: 4px;
}
'''

EMERALD_STUDIO_QSS = '''/* ==========================================================================
   SMG SUNO AI LYRIC WRITER - EMERALD FOREST THEME
   Nordic Slate Pine & Radiant Mint Green
   ========================================================================== */

QWidget {
    background-color: #050f0c;
    color: #a7f3d0;
    font-family: "Segoe UI", "Khmer OS Battambang", "Noto Sans Khmer", "Khmer UI", "Leelawadee UI", sans-serif;
    font-size: 10pt;
    selection-background-color: #10b981;
    selection-color: #ffffff;
}

QMainWindow {
    background-color: #050f0c;
}

QToolBar {
    background-color: #0a1c17;
    border-bottom: 1px solid #16382e;
    padding: 6px;
    spacing: 8px;
}

QGroupBox {
    background-color: #0a1c17;
    border: 1px solid #16382e;
    border-radius: 8px;
    margin-top: 18px;
    padding: 14px 10px 10px 10px;
    font-weight: 700;
    color: #a7f3d0;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    background-color: #0a1c17;
    color: #a7f3d0;
}

QLabel {
    color: #a7f3d0;
}

QLabel#headingLabel {
    font-size: 12pt;
    font-weight: 800;
    color: #ffffff;
}

QLabel#badgeLabel {
    background-color: #064e3b;
    color: #34d399;
    border: 1px solid #059669;
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 9pt;
    font-weight: 700;
}

QLabel#genreDescription {
    color: #6ee7b7;
    font-size: 9pt;
    line-height: 1.4;
}

QLineEdit, QComboBox, QSpinBox {
    background-color: #061410;
    border: 1px solid #1f4f41;
    border-radius: 6px;
    padding: 6px 10px;
    color: #ffffff;
    font-size: 10pt;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border: 1px solid #10b981;
    background-color: #0d2821;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    border: none;
    width: 24px;
}

QComboBox::down-arrow {
    image: url("assets/chevron_down_dark.svg");
    width: 12px;
    height: 12px;
    margin-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #0a1c17;
    border: 1px solid #1f4f41;
    selection-background-color: #059669;
    selection-color: #ffffff;
    color: #a7f3d0;
    padding: 4px;
}

QPushButton {
    background-color: #0f2922;
    border: 1px solid #1f4f41;
    border-radius: 6px;
    padding: 7px 14px;
    color: #ffffff;
    font-weight: 600;
    font-size: 10pt;
}

QPushButton:hover {
    background-color: #153b31;
    border-color: #10b981;
    color: #ffffff;
}

QPushButton:pressed {
    background-color: #050f0c;
}

QPushButton:disabled {
    background-color: #050f0c;
    border-color: #16382e;
    color: #6ee7b7;
}

QPushButton:checked {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #0d9488);
    border-color: #10b981;
    color: #ffffff;
}

QMenu {
    background-color: #0a1c17;
    color: #ffffff;
    border: 1px solid #1f4f41;
    border-radius: 6px;
    padding: 4px;
}

QMenu::item {
    padding: 6px 14px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #059669;
    color: #ffffff;
}

QMenu::separator {
    height: 1px;
    background: #16382e;
    margin: 4px 8px;
}

QToolTip {
    background-color: #0a1c17;
    color: #ffffff;
    border: 1px solid #10b981;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 9pt;
}

QPushButton#primaryGenerateButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #0d9488);
    border: 1px solid #10b981;
    color: #ffffff;
    font-weight: 800;
    font-size: 10pt;
    padding: 10px 18px;
    border-radius: 8px;
}

QPushButton#primaryGenerateButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #34d399, stop:1 #10b981);
    border-color: #34d399;
}

QPushButton#primaryGenerateButton:pressed {
    background: #059669;
}

QPushButton#accentButton {
    background-color: #064e3b;
    border: 1px solid #059669;
    color: #34d399;
    font-weight: 700;
    font-size: 10pt;
}

QPushButton#accentButton:hover {
    background-color: #059669;
    color: #ffffff;
}

QPushButton#sectionButton {
    background-color: #0a1c17;
    border: 1px dashed #1f4f41;
    color: #6ee7b7;
    border-radius: 5px;
    padding: 4px 8px;
    font-size: 9pt;
}

QPushButton#sectionButton:hover {
    background-color: #0f2922;
    border-color: #10b981;
    color: #a7f3d0;
}

QTextEdit, QPlainTextEdit {
    background-color: #061410;
    border: 1px solid #16382e;
    border-radius: 8px;
    color: #ffffff;
    font-family: "Cascadia Code", "Consolas", "Khmer OS Battambang", monospace;
    font-size: 10pt;
    line-height: 1.6;
    padding: 10px;
}

QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #10b981;
}

QTabWidget::pane {
    border: 1px solid #16382e;
    background-color: #0a1c17;
    border-radius: 8px;
    top: -1px;
}

QTabBar::tab {
    background-color: #050f0c;
    border: 1px solid #16382e;
    border-bottom: none;
    color: #6ee7b7;
    padding: 8px 16px;
    margin-right: 4px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: 600;
    font-size: 9pt;
}

QTabBar::tab:selected {
    background-color: #0a1c17;
    border-color: #16382e;
    border-bottom: 2px solid #10b981;
    color: #a7f3d0;
}

QTabBar::tab:hover:!selected {
    background-color: #0f2922;
    color: #a7f3d0;
}

QSlider::groove:horizontal {
    height: 6px;
    background: #16382e;
    border-radius: 3px;
}

QSlider::sub-page:horizontal {
    background: #10b981;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #a7f3d0;
    border: 2px solid #10b981;
    width: 16px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 8px;
}

QScrollBar:vertical {
    background: #050f0c;
    width: 8px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #1f4f41;
    min-height: 25px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #10b981;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QStatusBar {
    background-color: #050f0c;
    border-top: 1px solid #16382e;
    color: #6ee7b7;
    font-size: 9pt;
}

QSplitter::handle {
    background-color: #16382e;
}

QDialog {
    background-color: #050f0c;
    color: #ffffff;
}

QTableWidget {
    background-color: #06120e;
    color: #f0fdf4;
    border: 1px solid #16382e;
    gridline-color: #16382e;
    selection-background-color: #064e3b;
    selection-color: #ffffff;
}

QHeaderView::section {
    background-color: #0a1c17;
    color: #6ee7b7;
    padding: 6px 10px;
    border: 1px solid #16382e;
    font-weight: 800;
}

QScrollBar:horizontal {
    background: #050f0c;
    height: 8px;
    margin: 0px;
}

QScrollBar::handle:horizontal {
    background: #1f4f41;
    min-width: 25px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal:hover {
    background: #10b981;
}

QCheckBox, QRadioButton {
    color: #f0fdf4;
    font-weight: 600;
    spacing: 8px;
}

QProgressBar {
    background-color: #06120e;
    border: 1px solid #16382e;
    border-radius: 5px;
    text-align: center;
    color: #ffffff;
    font-weight: 700;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #10b981);
    border-radius: 4px;
}
'''

SUNSET_AMBER_STUDIO_QSS = '''/* ==========================================================================
   SMG SUNO AI LYRIC WRITER - SUNSET AMBER THEME
   Analog Console / Warm Gold & Titanium
   ========================================================================== */

QWidget {
    background-color: #100b08;
    color: #fde68a;
    font-family: "Segoe UI", "Khmer OS Battambang", "Noto Sans Khmer", "Khmer UI", "Leelawadee UI", sans-serif;
    font-size: 10pt;
    selection-background-color: #f59e0b;
    selection-color: #ffffff;
}

QMainWindow {
    background-color: #100b08;
}

QToolBar {
    background-color: #1a130f;
    border-bottom: 1px solid #36241b;
    padding: 6px;
    spacing: 8px;
}

QGroupBox {
    background-color: #1a130f;
    border: 1px solid #36241b;
    border-radius: 8px;
    margin-top: 18px;
    padding: 14px 10px 10px 10px;
    font-weight: 700;
    color: #fde68a;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    background-color: #1a130f;
    color: #fde68a;
}

QLabel {
    color: #fde68a;
}

QLabel#headingLabel {
    font-size: 12pt;
    font-weight: 800;
    color: #ffffff;
}

QLabel#badgeLabel {
    background-color: #451a03;
    color: #fbbf24;
    border: 1px solid #92400e;
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 9pt;
    font-weight: 700;
}

QLabel#genreDescription {
    color: #fcd34d;
    font-size: 9pt;
    line-height: 1.4;
}

QLineEdit, QComboBox, QSpinBox {
    background-color: #140e0a;
    border: 1px solid #4d3427;
    border-radius: 6px;
    padding: 6px 10px;
    color: #ffffff;
    font-size: 10pt;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border: 1px solid #f59e0b;
    background-color: #241812;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    border: none;
    width: 24px;
}

QComboBox::down-arrow {
    image: url("assets/chevron_down_dark.svg");
    width: 12px;
    height: 12px;
    margin-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #1a130f;
    border: 1px solid #4d3427;
    selection-background-color: #d97706;
    selection-color: #ffffff;
    color: #fde68a;
    padding: 4px;
}

QPushButton {
    background-color: #241b16;
    border: 1px solid #4d3427;
    border-radius: 6px;
    padding: 7px 14px;
    color: #ffffff;
    font-weight: 600;
    font-size: 10pt;
}

QPushButton:hover {
    background-color: #362820;
    border-color: #f59e0b;
    color: #ffffff;
}

QPushButton:pressed {
    background-color: #100b08;
}

QPushButton:disabled {
    background-color: #100b08;
    border-color: #36241b;
    color: #fcd34d;
}

QPushButton:checked {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #d97706, stop:1 #ea580c);
    border-color: #f59e0b;
    color: #ffffff;
}

QMenu {
    background-color: #1a130f;
    color: #ffffff;
    border: 1px solid #4d3427;
    border-radius: 6px;
    padding: 4px;
}

QMenu::item {
    padding: 6px 14px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #d97706;
    color: #ffffff;
}

QMenu::separator {
    height: 1px;
    background: #36241b;
    margin: 4px 8px;
}

QToolTip {
    background-color: #1a130f;
    color: #ffffff;
    border: 1px solid #f59e0b;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 9pt;
}

QPushButton#primaryGenerateButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #d97706, stop:1 #ea580c);
    border: 1px solid #f59e0b;
    color: #ffffff;
    font-weight: 800;
    font-size: 10pt;
    padding: 10px 18px;
    border-radius: 8px;
}

QPushButton#primaryGenerateButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #fbbf24, stop:1 #f59e0b);
    border-color: #fbbf24;
}

QPushButton#primaryGenerateButton:pressed {
    background: #d97706;
}

QPushButton#accentButton {
    background-color: #451a03;
    border: 1px solid #d97706;
    color: #fbbf24;
    font-weight: 700;
    font-size: 10pt;
}

QPushButton#accentButton:hover {
    background-color: #d97706;
    color: #ffffff;
}

QPushButton#sectionButton {
    background-color: #1a130f;
    border: 1px dashed #4d3427;
    color: #fcd34d;
    border-radius: 5px;
    padding: 4px 8px;
    font-size: 9pt;
}

QPushButton#sectionButton:hover {
    background-color: #241b16;
    border-color: #f59e0b;
    color: #fde68a;
}

QTextEdit, QPlainTextEdit {
    background-color: #140e0a;
    border: 1px solid #36241b;
    border-radius: 8px;
    color: #ffffff;
    font-family: "Cascadia Code", "Consolas", "Khmer OS Battambang", monospace;
    font-size: 10pt;
    line-height: 1.6;
    padding: 10px;
}

QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #f59e0b;
}

QTabWidget::pane {
    border: 1px solid #36241b;
    background-color: #1a130f;
    border-radius: 8px;
    top: -1px;
}

QTabBar::tab {
    background-color: #100b08;
    border: 1px solid #36241b;
    border-bottom: none;
    color: #fcd34d;
    padding: 8px 16px;
    margin-right: 4px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: 600;
    font-size: 9pt;
}

QTabBar::tab:selected {
    background-color: #1a130f;
    border-color: #36241b;
    border-bottom: 2px solid #f59e0b;
    color: #fde68a;
}

QTabBar::tab:hover:!selected {
    background-color: #241b16;
    color: #fde68a;
}

QSlider::groove:horizontal {
    height: 6px;
    background: #36241b;
    border-radius: 3px;
}

QSlider::sub-page:horizontal {
    background: #f59e0b;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #fde68a;
    border: 2px solid #f59e0b;
    width: 16px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 8px;
}

QScrollBar:vertical {
    background: #100b08;
    width: 8px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #4d3427;
    min-height: 25px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #f59e0b;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QStatusBar {
    background-color: #100b08;
    border-top: 1px solid #36241b;
    color: #fcd34d;
    font-size: 9pt;
}

QSplitter::handle {
    background-color: #36241b;
}

QDialog {
    background-color: #100b08;
    color: #ffffff;
}

QTableWidget {
    background-color: #140e0b;
    color: #fffbeb;
    border: 1px solid #36241b;
    gridline-color: #36241b;
    selection-background-color: #78350f;
    selection-color: #ffffff;
}

QHeaderView::section {
    background-color: #1a130f;
    color: #fde68a;
    padding: 6px 10px;
    border: 1px solid #36241b;
    font-weight: 800;
}

QScrollBar:horizontal {
    background: #100b08;
    height: 8px;
    margin: 0px;
}

QScrollBar::handle:horizontal {
    background: #4d3427;
    min-width: 25px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal:hover {
    background: #f59e0b;
}

QCheckBox, QRadioButton {
    color: #fffbeb;
    font-weight: 600;
    spacing: 8px;
}

QProgressBar {
    background-color: #140e0b;
    border: 1px solid #36241b;
    border-radius: 5px;
    text-align: center;
    color: #ffffff;
    font-weight: 700;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #d97706, stop:1 #f59e0b);
    border-radius: 4px;
}
'''

LIGHT_STUDIO_QSS = '''/* ==========================================================================
   SMG SUNO AI LYRIC WRITER - PURE CANVAS LIGHT THEME
   Modern Cupertino / Notion Studio Canvas
   ========================================================================== */

QWidget {
    background-color: #f8fafc;
    color: #1e293b;
    font-family: "Segoe UI", "Khmer OS Battambang", "Noto Sans Khmer", "Khmer UI", "Leelawadee UI", sans-serif;
    font-size: 10pt;
    selection-background-color: #3b82f6;
    selection-color: #ffffff;
}

QMainWindow {
    background-color: #f8fafc;
}

QToolBar {
    background-color: #ffffff;
    border-bottom: 1px solid #e2e8f0;
    padding: 6px;
    spacing: 8px;
}

QGroupBox {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    margin-top: 18px;
    padding: 14px 10px 10px 10px;
    font-weight: 700;
    color: #1e293b;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    background-color: #ffffff;
    color: #2563eb;
}

QLabel {
    color: #334155;
}

QLabel#headingLabel {
    font-size: 12pt;
    font-weight: 800;
    color: #0f172a;
}

QLabel#badgeLabel {
    background-color: #eff6ff;
    color: #2563eb;
    border: 1px solid #bfdbfe;
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 9pt;
    font-weight: 700;
}

QLabel#genreDescription {
    color: #64748b;
    font-size: 9pt;
    line-height: 1.4;
}

QLineEdit, QComboBox, QSpinBox {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 6px 10px;
    color: #1e293b;
    font-size: 10pt;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border: 1px solid #3b82f6;
    background-color: #f8fafc;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    border: none;
    width: 24px;
}

QComboBox::down-arrow {
    image: url("assets/chevron_down_light.svg");
    width: 12px;
    height: 12px;
    margin-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    selection-background-color: #3b82f6;
    selection-color: #ffffff;
    color: #1e293b;
    padding: 4px;
}

QPushButton {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 7px 14px;
    color: #334155;
    font-weight: 600;
    font-size: 10pt;
}

QPushButton:hover {
    background-color: #f1f5f9;
    border-color: #94a3b8;
    color: #0f172a;
}

QPushButton:pressed {
    background-color: #e2e8f0;
}

QPushButton:disabled {
    background-color: #f8fafc;
    border-color: #e2e8f0;
    color: #94a3b8;
}

QPushButton:checked {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563eb, stop:1 #4f46e5);
    border-color: #2563eb;
    color: #ffffff;
}

QMenu {
    background-color: #ffffff;
    color: #1e293b;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 4px;
}

QMenu::item {
    padding: 6px 14px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #3b82f6;
    color: #ffffff;
}

QMenu::separator {
    height: 1px;
    background: #e2e8f0;
    margin: 4px 8px;
}

QToolTip {
    background-color: #ffffff;
    color: #0f172a;
    border: 1px solid #3b82f6;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 9pt;
}

QPushButton#primaryGenerateButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563eb, stop:1 #4f46e5);
    border: 1px solid #2563eb;
    color: #ffffff;
    font-weight: 800;
    font-size: 10pt;
    padding: 10px 18px;
    border-radius: 8px;
}

QPushButton#primaryGenerateButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3b82f6, stop:1 #6366f1);
    border-color: #3b82f6;
}

QPushButton#accentButton {
    background-color: #eff6ff;
    border: 1px solid #bfdbfe;
    color: #2563eb;
    font-weight: 700;
    font-size: 10pt;
}

QPushButton#accentButton:hover {
    background-color: #2563eb;
    color: #ffffff;
}

QPushButton#sectionButton {
    background-color: #f8fafc;
    border: 1px dashed #cbd5e1;
    color: #64748b;
    border-radius: 5px;
    padding: 4px 8px;
    font-size: 9pt;
}

QPushButton#sectionButton:hover {
    background-color: #eff6ff;
    border-color: #3b82f6;
    color: #2563eb;
}

QTextEdit, QPlainTextEdit {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    color: #0f172a;
    font-family: "Cascadia Code", "Consolas", "Khmer OS Battambang", monospace;
    font-size: 10pt;
    line-height: 1.6;
    padding: 10px;
}

QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #3b82f6;
}

QTabWidget::pane {
    border: 1px solid #e2e8f0;
    background-color: #ffffff;
    border-radius: 8px;
    top: -1px;
}

QTabBar::tab {
    background-color: #f1f5f9;
    border: 1px solid #e2e8f0;
    border-bottom: none;
    color: #64748b;
    padding: 8px 16px;
    margin-right: 4px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: 600;
    font-size: 9pt;
}

QTabBar::tab:selected {
    background-color: #ffffff;
    border-color: #e2e8f0;
    border-bottom: 2px solid #2563eb;
    color: #2563eb;
}

QTabBar::tab:hover:!selected {
    background-color: #e2e8f0;
    color: #1e293b;
}

QSlider::groove:horizontal {
    height: 6px;
    background: #e2e8f0;
    border-radius: 3px;
}

QSlider::sub-page:horizontal {
    background: #3b82f6;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #ffffff;
    border: 2px solid #3b82f6;
    width: 16px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 8px;
}

QScrollBar:vertical {
    background: #f8fafc;
    width: 8px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #cbd5e1;
    min-height: 25px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #94a3b8;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QStatusBar {
    background-color: #f8fafc;
    border-top: 1px solid #cbd5e1;
    color: #334155;
    font-size: 9pt;
    font-weight: 600;
}

QSplitter::handle {
    background-color: #cbd5e1;
}

QDialog {
    background-color: #f8fafc;
    color: #0f172a;
}

QTableWidget {
    background-color: #ffffff;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    gridline-color: #e2e8f0;
    selection-background-color: #eff6ff;
    selection-color: #1d4ed8;
}

QHeaderView::section {
    background-color: #f1f5f9;
    color: #0f172a;
    padding: 6px 10px;
    border: 1px solid #cbd5e1;
    font-weight: 800;
}

QScrollBar:horizontal {
    background: #f8fafc;
    height: 8px;
    margin: 0px;
}

QScrollBar::handle:horizontal {
    background: #cbd5e1;
    min-width: 25px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal:hover {
    background: #94a3b8;
}

QCheckBox, QRadioButton {
    color: #0f172a;
    font-weight: 600;
    spacing: 8px;
}

QProgressBar {
    background-color: #e2e8f0;
    border: 1px solid #cbd5e1;
    border-radius: 5px;
    text-align: center;
    color: #0f172a;
    font-weight: 700;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1d4ed8, stop:1 #2563eb);
    border-radius: 4px;
}
'''

STUDIO_THEMES = {
    "obsidian": {
        "id": "obsidian",
        "name": "Obsidian Violet",
        "icon": "🌌",
        "tagline": "Flagship Ableton / Cyberpunk Studio Dark",
        "is_dark": True,
        "accent": "#8b5cf6",
        "accent_secondary": "#7c3aed",
        "accent_hover": "#a78bfa",
        "accent_gradient": "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7c3aed, stop:1 #4f46e5)",
        "bg_window": "#08090f",
        "bg_card": "#111526",
        "bg_card_alt": "#0d1120",
        "bg_input": "#090b14",
        "bg_btn": "#161b2e",
        "bg_btn_hover": "#222944",
        "bg_btn_secondary": "#1e1b4b",
        "border": "#1e2540",
        "border_subtle": "#283256",
        "border_accent": "#8b5cf6",
        "text_primary": "#ffffff",
        "text_secondary": "#cbd5e1",
        "text_muted": "#94a3b8",
        "text_accent": "#c4b5fd",
        "active_pill_bg": "#7c3aed",
        "active_pill_color": "#ffffff",
        "subtle_pill_bg": "#161b2e",
        "subtle_pill_text": "#cbd5e1",
        "subtle_pill_border": "#283256",
        "header_start": "#111424",
        "header_end": "#0a0c16",
        "header_sub_text": "#38bdf8",
    },
    "cyber_blue": {
        "id": "cyber_blue",
        "name": "Midnight Cyber Blue",
        "icon": "🌊",
        "tagline": "Logic Pro X / Deep Ocean Sapphire & Sky Blue",
        "is_dark": True,
        "accent": "#0ea5e9",
        "accent_secondary": "#0284c7",
        "accent_hover": "#38bdf8",
        "accent_gradient": "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #0ea5e9)",
        "bg_window": "#050a14",
        "bg_card": "#0a1424",
        "bg_card_alt": "#08101d",
        "bg_input": "#060d1a",
        "bg_btn": "#0f1f38",
        "bg_btn_hover": "#162c4e",
        "bg_btn_secondary": "#0c4a6e",
        "border": "#152642",
        "border_subtle": "#1d3862",
        "border_accent": "#0ea5e9",
        "text_primary": "#ffffff",
        "text_secondary": "#bae6fd",
        "text_muted": "#7dd3fc",
        "text_accent": "#38bdf8",
        "active_pill_bg": "#0284c7",
        "active_pill_color": "#ffffff",
        "subtle_pill_bg": "#0f1f38",
        "subtle_pill_text": "#bae6fd",
        "subtle_pill_border": "#1d3862",
        "header_start": "#0c182c",
        "header_end": "#060d1a",
        "header_sub_text": "#38bdf8",
    },
    "emerald": {
        "id": "emerald",
        "name": "Emerald Forest",
        "icon": "🌲",
        "tagline": "Nordic Slate Pine & Radiant Mint Green",
        "is_dark": True,
        "accent": "#10b981",
        "accent_secondary": "#059669",
        "accent_hover": "#34d399",
        "accent_gradient": "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #10b981)",
        "bg_window": "#050f0c",
        "bg_card": "#0a1c17",
        "bg_card_alt": "#071612",
        "bg_input": "#06120e",
        "bg_btn": "#0f2922",
        "bg_btn_hover": "#153b31",
        "bg_btn_secondary": "#064e3b",
        "border": "#16382e",
        "border_subtle": "#1f4f41",
        "border_accent": "#10b981",
        "text_primary": "#ffffff",
        "text_secondary": "#a7f3d0",
        "text_muted": "#6ee7b7",
        "text_accent": "#34d399",
        "active_pill_bg": "#059669",
        "active_pill_color": "#ffffff",
        "subtle_pill_bg": "#0f2922",
        "subtle_pill_text": "#a7f3d0",
        "subtle_pill_border": "#1f4f41",
        "header_start": "#0c221c",
        "header_end": "#05120f",
        "header_sub_text": "#34d399",
    },
    "sunset_amber": {
        "id": "sunset_amber",
        "name": "Sunset Amber",
        "icon": "🌅",
        "tagline": "Analog Console / Warm Gold & Titanium",
        "is_dark": True,
        "accent": "#f59e0b",
        "accent_secondary": "#d97706",
        "accent_hover": "#fbbf24",
        "accent_gradient": "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #d97706, stop:1 #f59e0b)",
        "bg_window": "#100b08",
        "bg_card": "#1a130f",
        "bg_card_alt": "#140e0b",
        "bg_input": "#0d0906",
        "bg_btn": "#241b16",
        "bg_btn_hover": "#362820",
        "bg_btn_secondary": "#451a03",
        "border": "#36241b",
        "border_subtle": "#4d3427",
        "border_accent": "#f59e0b",
        "text_primary": "#ffffff",
        "text_secondary": "#fde68a",
        "text_muted": "#fbbf24",
        "text_accent": "#fde68a",
        "active_pill_bg": "#d97706",
        "active_pill_color": "#ffffff",
        "subtle_pill_bg": "#241b16",
        "subtle_pill_text": "#fde68a",
        "subtle_pill_border": "#4d3427",
        "header_start": "#211712",
        "header_end": "#120c09",
        "header_sub_text": "#fbbf24",
    },
    "canvas_light": {
        "id": "canvas_light",
        "name": "Pure Canvas Light",
        "icon": "☀️",
        "tagline": "Modern Cupertino / Notion Studio Canvas",
        "is_dark": False,
        "accent": "#2563eb",
        "accent_secondary": "#1d4ed8",
        "accent_hover": "#3b82f6",
        "accent_gradient": "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1d4ed8, stop:1 #2563eb)",
        "bg_window": "#f8fafc",
        "bg_card": "#ffffff",
        "bg_card_alt": "#f1f5f9",
        "bg_input": "#ffffff",
        "bg_btn": "#ffffff",
        "bg_btn_hover": "#f1f5f9",
        "bg_btn_secondary": "#eff6ff",
        "border": "#cbd5e1",
        "border_subtle": "#e2e8f0",
        "border_accent": "#2563eb",
        "text_primary": "#0f172a",
        "text_secondary": "#1e293b",
        "text_muted": "#475569",
        "text_accent": "#2563eb",
        "active_pill_bg": "#2563eb",
        "active_pill_color": "#ffffff",
        "subtle_pill_bg": "#f1f5f9",
        "subtle_pill_text": "#1e293b",
        "subtle_pill_border": "#cbd5e1",
        "header_start": "#ffffff",
        "header_end": "#f8fafc",
        "header_sub_text": "#334155",
    },
}

# Map QSS strings to theme dict
STUDIO_THEMES["obsidian"]["qss"] = DARK_STUDIO_QSS
STUDIO_THEMES["cyber_blue"]["qss"] = CYBER_BLUE_STUDIO_QSS
STUDIO_THEMES["emerald"]["qss"] = EMERALD_STUDIO_QSS
STUDIO_THEMES["sunset_amber"]["qss"] = SUNSET_AMBER_STUDIO_QSS
STUDIO_THEMES["canvas_light"]["qss"] = LIGHT_STUDIO_QSS

def get_theme(theme_id_or_dark=None) -> dict:
    """Resolves theme dictionary with backward-compatible aliases and bool/dict support."""
    if isinstance(theme_id_or_dark, dict):
        return theme_id_or_dark
    if isinstance(theme_id_or_dark, bool):
        return STUDIO_THEMES["obsidian"] if theme_id_or_dark else STUDIO_THEMES["canvas_light"]
    if not theme_id_or_dark:
        return STUDIO_THEMES["obsidian"]
    t = str(theme_id_or_dark).lower().strip()
    if t in ["dark", "dark_modern", "obsidian_violet", "default"]:
        t = "obsidian"
    elif t in ["light", "canvas", "modern_light", "canvas_light"]:
        t = "canvas_light"
    elif t in ["blue", "cyber", "midnight", "cyber_blue"]:
        t = "cyber_blue"
    elif t in ["green", "mint", "forest", "emerald"]:
        t = "emerald"
    elif t in ["amber", "sunset", "warm", "gold", "sunset_amber"]:
        t = "sunset_amber"
    return STUDIO_THEMES.get(t, STUDIO_THEMES["obsidian"])

def get_theme_qss(theme_id: str) -> str:
    """Retrieves the compiled QSS stylesheet for the specified theme."""
    return get_theme(theme_id)["qss"]
