# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# Base directory
base_dir = Path(os.path.abspath('.'))

# Collect data files (including assets, Khmer fonts, and version manifest)
datas = [
    (str(base_dir / 'assets'), 'assets'),
    (str(base_dir / 'version.json'), '.'),
]

# Collect certifi SSL certificate bundle for resilient Gemini API calls on all PCs
try:
    certifi_datas = collect_data_files('certifi')
    datas.extend(certifi_datas)
except Exception:
    pass

# Explicit hidden imports required for rock-solid runtime on any Windows PC
hiddenimports = [
    'PyQt6',
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'PyQt6.QtSvg',
    'google',
    'google.genai',
    'google.genai.types',
    'google.genai.client',
    'google.genai.models',
    'pydantic',
    'pydantic_core',
    'anyio',
    'httpx',
    'httpcore',
    'certifi',
    'fpdf',
    'edge_tts',
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
    're',
]

# Exclude heavy unrelated machine-learning packages to keep app fast, light, and reliable
excludes = [
    'tkinter', 'matplotlib', 'torch', 'torchaudio', 'scipy', 'IPython', 'notebook',
    'transformers', 'onnxruntime', 'funasr', 'librosa', 'mediapipe',
    'modelscope', 'kaldiio', 'sentencepiece', 'cv2', 'opencv_python',
    'sounddevice', 'soundfile', 'webrtcvad', 'openai_whisper', 'yt_dlp'
]

a = Analysis(
    ['main.py'],
    pathex=[str(base_dir)],
    binaries=[],
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

# Build Directory Bundle for Inno Setup (Instant startup, zero false-positives)
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
