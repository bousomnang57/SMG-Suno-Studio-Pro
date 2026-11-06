@echo off
setlocal enabledelayedexpansion

echo =====================================================================
echo    SMG Suno Studio Pro - Production Release Builder
echo    Builds Standalone Executable and Inno Setup Windows Installer
echo =====================================================================
echo.

:: 1. Clean previous builds
echo [*] Cleaning previous build artifacts...
if exist "dist\SMG Suno Studio Pro" rmdir /s /q "dist\SMG Suno Studio Pro"
if exist "build" rmdir /s /q "build"
if not exist "dist_installer" mkdir "dist_installer"

:: 2. Run PyInstaller
echo [*] Compiling Application with PyInstaller...
python -m PyInstaller --clean SMG_Suno_Studio_Pro.spec
if %ERRORLEVEL% NEQ 0 (
    echo [!] PyInstaller build failed with error code %ERRORLEVEL%.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [*] PyInstaller build successful! Application bundled in:
echo     dist\SMG Suno Studio Pro\SMG Suno Studio Pro.exe
echo.

:: Ensure assets directory is also at root of dist bundle for direct shortcut/stylesheet resolution
if not exist "dist\SMG Suno Studio Pro\assets" (
    echo [*] Mirroring assets directory to dist bundle root...
    xcopy /E /I /Y "assets" "dist\SMG Suno Studio Pro\assets" >nul
)


:: 3. Detect Inno Setup Compiler
set "ISCC_PATH="
if exist "C:\Program Files\Inno Setup 7\ISCC.exe" set "ISCC_PATH=C:\Program Files\Inno Setup 7\ISCC.exe"
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "ISCC_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set "ISCC_PATH=C:\Program Files\Inno Setup 6\ISCC.exe"

if "%ISCC_PATH%"=="" (
    where ISCC.exe >nul 2>&1
    if %ERRORLEVEL% EQU 0 set "ISCC_PATH=ISCC.exe"
)

if "%ISCC_PATH%"=="" (
    echo [!] Inno Setup compiler (ISCC.exe) not found in standard paths.
    echo     Please compile 'installer.iss' manually via Inno Setup Compiler GUI.
    pause
    exit /b 0
)

:: 4. Compile Installer
echo [*] Compiling Inno Setup Windows Installer using:
echo     "%ISCC_PATH%"
"%ISCC_PATH%" installer.iss

if %ERRORLEVEL% NEQ 0 (
    echo [!] Inno Setup compilation failed with error code %ERRORLEVEL%.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo =====================================================================
echo    BUILD COMPLETE!
echo    Windows Installer created at:
echo    dist_installer\SMG_Suno_Studio_Pro_v2.0_Setup.exe
echo =====================================================================
echo.
pause

