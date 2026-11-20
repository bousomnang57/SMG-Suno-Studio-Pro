@echo off
setlocal enabledelayedexpansion

set "APP_VERSION=2.3.0"

echo =====================================================================
echo    SMG Suno Studio Pro v%APP_VERSION% - Production Release Builder
echo    Builds Portable Standalone EXE + Inno Setup Windows Installer
echo =====================================================================
echo.

:: 1. Clean previous builds
echo [*] Cleaning previous build artifacts...
if exist "dist\SMG Suno Studio Pro" rmdir /s /q "dist\SMG Suno Studio Pro"
if exist "build" rmdir /s /q "build"
if not exist "dist_installer" mkdir "dist_installer"

:: 2. Run PyInstaller
echo [*] Compiling Application with PyInstaller...
python -m PyInstaller --noconfirm --clean SMG_Suno_Studio_Pro.spec
if %ERRORLEVEL% NEQ 0 (
    echo [!] PyInstaller build failed with error code %ERRORLEVEL%.
    exit /b %ERRORLEVEL%
)

:: 3. Mirror assets, version.json & qt.conf at root of dist bundle for icon/shortcut/fallback resolution
if not exist "dist\SMG Suno Studio Pro\assets" (
    echo [*] Mirroring assets directory to dist bundle root...
    xcopy /E /I /Y "assets" "dist\SMG Suno Studio Pro\assets" >nul
)
copy /Y "version.json" "dist\SMG Suno Studio Pro\version.json" >nul

if not exist "dist\SMG Suno Studio Pro\qt.conf" (
    (
        echo [Paths]
        echo Prefix = PyQt6/Qt6
    ) > "dist\SMG Suno Studio Pro\qt.conf"
)

:: 4. Smoke-Test the compiled frozen EXE (verifies zero missing DLLs/imports on clean startup)
echo [*] Running frozen EXE smoke test...
set "QT_QPA_PLATFORM=offscreen"
"dist\SMG Suno Studio Pro\SMG Suno Studio Pro.exe" --smoke-test
if %ERRORLEVEL% NEQ 0 (
    echo [!] Frozen EXE smoke test failed with error code %ERRORLEVEL%!
    exit /b %ERRORLEVEL%
)
echo [OK] Frozen EXE booted cleanly across all 5 Studio Modes!
echo.

:: 5. Detect Inno Setup Compiler
set "ISCC_PATH="
if exist "C:\Program Files\Inno Setup 7\ISCC.exe" set "ISCC_PATH=C:\Program Files\Inno Setup 7\ISCC.exe"
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "ISCC_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set "ISCC_PATH=C:\Program Files\Inno Setup 6\ISCC.exe"

if "%ISCC_PATH%"=="" (
    where ISCC.exe >nul 2>&1
    if %ERRORLEVEL% EQU 0 set "ISCC_PATH=ISCC.exe"
)

if "%ISCC_PATH%"=="" (
    echo [!] Inno Setup compiler ISCC.exe not found in standard paths.
    echo     Please compile 'installer.iss' manually via Inno Setup Compiler GUI.
    exit /b 0
)

:: 6. Compile Installer
echo [*] Compiling Inno Setup Windows Installer using:
echo     "%ISCC_PATH%"
"%ISCC_PATH%" installer.iss
if %ERRORLEVEL% NEQ 0 (
    echo [!] Inno Setup compilation failed with error code %ERRORLEVEL%.
    exit /b %ERRORLEVEL%
)

echo.
echo =====================================================================
echo    BUILD COMPLETE!
echo    Portable EXE : dist\SMG Suno Studio Pro\SMG Suno Studio Pro.exe
echo    Setup File   : dist_installer\SMG_Suno_Studio_Pro_v%APP_VERSION%_Setup.exe
echo =====================================================================
echo.
exit /b 0
