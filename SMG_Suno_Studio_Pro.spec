# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Production Spec for SMG Suno Studio Pro v2.3.0
Hardened for zero-error standalone execution on ANY Windows 10/11 (x64) PC:
- Bundles all app.*, google.genai, and mutagen submodules
- Bundles PyQt6 QtWidgets, QtGui, QtCore, QtSvg, QtMultimedia + QtWebEngine (Chromium runtime, pak, locales)
- Bundles Pillow (PIL), NumPy, fpdf2, edge_tts/aiohttp, soundfile (libsndfile DLLs), pywin32
- Bundles certifi CA certificates for resilient HTTPS/Gemini/Auto-Updater calls
- Bundles VC++ 2015-2022 runtime DLLs (vcruntime140, vcruntime140_1, msvcp140)
- Bundles assets/ (icons, SVGs, Khmer fonts) and version.json
"""

import os
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_dynamic_libs
from PyInstaller.utils.hooks.qt import pyqt6_library_info

block_cipher = None
base_dir = Path(os.path.abspath('.'))

# ── 1. Data Files (Assets, Khmer Fonts, Version Manifest, SSL Certs, FPDF, SoundFile, WebEngine) ──
datas = [
    (str(base_dir / 'assets'), 'assets'),
    (str(base_dir / 'version.json'), '.'),
]

for pkg in ('certifi', 'fpdf', 'imageio_ffmpeg', '_soundfile_data'):
    try:
        datas.extend(collect_data_files(pkg))
    except Exception:
        pass

# ── 2. Portable Windows VC++ Runtime & Native Binaries ──
binaries = []
_dll_names = ('vcruntime140.dll', 'vcruntime140_1.dll', 'msvcp140.dll')
_search_dirs = [
    Path(sys.base_prefix),
    Path(sys.prefix),
    Path(sys.executable).parent,
    Path(os.environ.get('SystemRoot', r'C:\Windows')) / 'System32',
]
_added_dlls = set()
for dll_name in _dll_names:
    for sdir in _search_dirs:
        cand = sdir / dll_name
        if cand.exists() and dll_name.lower() not in _added_dlls:
            binaries.append((str(cand), '.'))
            _added_dlls.add(dll_name.lower())
            break

for dyn_pkg in ('PIL', 'numpy', '_soundfile_data'):
    try:
        binaries.extend(collect_dynamic_libs(dyn_pkg))
    except Exception:
        pass

# ── 2b. Explicit Chromium WebEngine Process & Resources (Prevents Blank WebEngine on Other PCs) ──
if pyqt6_library_info.version is not None:
    try:
        web_bins, web_datas = pyqt6_library_info.collect_qtwebengine_files()
        binaries.extend(web_bins)
        datas.extend(web_datas)
    except Exception as e:
        print(f"Notice: WebEngine collection via hook info: {e}")

# ── 3. Explicit Hidden Imports (Zero ModuleNotFoundError on Clean PCs) ──
hiddenimports = [
    # PyQt6 GUI, SVG Icons, Multimedia & Embedded Suno WebEngine Browser
    'PyQt6',
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'PyQt6.QtSvg',
    'PyQt6.QtMultimedia',
    'PyQt6.QtMultimediaWidgets',
    'PyQt6.QtWebEngineWidgets',
    'PyQt6.QtWebEngineCore',
    'PyQt6.QtWebChannel',
    'PyQt6.QtNetwork',
    'PyQt6.QtPrintSupport',
    'PyQt6.sip',

    # Google Gemini SDK & Async HTTP/SSL Stack
    'google',
    'google.genai',
    'google.genai.types',
    'google.genai.client',
    'google.genai.models',
    'pydantic',
    'pydantic_core',
    'anyio',
    'anyio._backends._asyncio',
    'sniffio',
    'httpx',
    'httpcore',
    'h11',
    'certifi',
    'ssl',

    # Audio, Imaging, PDF & TTS Engines
    'PIL',
    'PIL.Image',
    'PIL.ImageDraw',
    'PIL.ImageFont',
    'PIL.ImageFilter',
    'numpy',
    'fpdf',
    'edge_tts',
    'aiohttp',
    'imageio_ffmpeg',
    'soundfile',
    'charset_normalizer',
    'multidict',
    'yarl',
    'win32com',
    'win32com.client',
    'pythoncom',
    'pywintypes',
    'winsound',

    # Standard Library Modules Used Dynamically
    'json',
    'wave',
    'struct',
    'math',
    'threading',
    'pathlib',
    'hashlib',
    'hmac',
    'winreg',
    'platform',
    'uuid',
    'zipfile',
    'csv',
    'html',
    're',
    'dataclasses',
    'xml.etree.ElementTree',
]

# Auto-collect all internal app modules + google.genai + edge_tts + mutagen submodules
for sub_pkg in ('app', 'google.genai', 'edge_tts', 'mutagen'):
    try:
        hiddenimports.extend(collect_submodules(sub_pkg))
    except Exception:
        pass

# Deduplicate while preserving order
hiddenimports = list(dict.fromkeys(hiddenimports))

# Exclude heavy unrelated ML/data-science packages to keep installer lean and fast
excludes = [
    'tkinter', 'matplotlib', 'torch', 'torchaudio', 'scipy', 'IPython', 'notebook',
    'transformers', 'onnxruntime', 'funasr', 'librosa', 'mediapipe',
    'modelscope', 'kaldiio', 'sentencepiece', 'cv2', 'opencv_python',
    'sounddevice', 'webrtcvad', 'openai_whisper', 'yt_dlp',
    'pytest', 'setuptools', 'pip', 'wheel',
]

a = Analysis(
    ['main.py'],
    pathex=[str(base_dir)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Directory Bundle for Inno Setup (Instant startup, zero antivirus UPX false-positives)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SMG Suno Studio Pro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(base_dir / 'assets' / 'logo.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='SMG Suno Studio Pro',
)
