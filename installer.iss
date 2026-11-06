; Script generated for Inno Setup 7
; SMG Suno AI Lyric Writer — Global Music Studio Installer
; Optimized for all Windows PCs with built-in Khmer & Modern UI Font Registration

#define MyAppName "SMG Suno Studio Pro"
#define MyAppVersion "2.0"
#define MyAppPublisher "SMG Studio"
#define MyAppExeName "SMG Suno Studio Pro.exe"
#define MyAppId "{{C287895A-8E41-432D-8C56-9D3A4B8E17F0}"

[Setup]
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=dist_installer
OutputBaseFilename=SMG_Suno_Studio_Pro_v2.0_Setup
SetupIconFile=assets\logo.ico
UninstallDisplayIcon={app}\assets\logo.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
WizardResizable=no
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=commandline dialog
ArchitecturesInstallIn64BitMode=x64compatible
DisableProgramGroupPage=auto
ChangesAssociations=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce
Name: "installfonts"; Description: "Install Khmer & Modern Studio Typography (Khmer OS Battambang, Content, Siemreap)"; GroupDescription: "Typography & Display Quality:"; Flags: checkedonce

[Files]
; Main Application Binary and Python Runtimes
Source: "dist\SMG Suno Studio Pro\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Bundled Khmer Fonts Registered System-Wide
Source: "assets\fonts\KhmerOSBattambang-Regular.ttf"; DestDir: "{autofonts}"; FontInstall: "Khmer OS Battambang"; Tasks: installfonts; Flags: onlyifdoesntexist uninsneveruninstall
Source: "assets\fonts\KhmerOSBattambang-Bold.ttf"; DestDir: "{autofonts}"; FontInstall: "Khmer OS Battambang Bold"; Tasks: installfonts; Flags: onlyifdoesntexist uninsneveruninstall
Source: "assets\fonts\KhmerOSContent-Regular.ttf"; DestDir: "{autofonts}"; FontInstall: "Khmer OS Content"; Tasks: installfonts; Flags: onlyifdoesntexist uninsneveruninstall
Source: "assets\fonts\KhmerOSContent-Bold.ttf"; DestDir: "{autofonts}"; FontInstall: "Khmer OS Content Bold"; Tasks: installfonts; Flags: onlyifdoesntexist uninsneveruninstall
Source: "assets\fonts\KhmerOSsiemreap.ttf"; DestDir: "{autofonts}"; FontInstall: "Khmer OS Siemreap"; Tasks: installfonts; Flags: onlyifdoesntexist uninsneveruninstall
Source: "assets\fonts\NotoSansKhmer-Regular.ttf"; DestDir: "{autofonts}"; FontInstall: "Noto Sans Khmer"; Tasks: installfonts; Flags: onlyifdoesntexist uninsneveruninstall
Source: "assets\fonts\NotoSansKhmer-Bold.ttf"; DestDir: "{autofonts}"; FontInstall: "Noto Sans Khmer Bold"; Tasks: installfonts; Flags: onlyifdoesntexist uninsneveruninstall

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\logo.ico"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"; IconFilename: "{app}\assets\logo.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\logo.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
