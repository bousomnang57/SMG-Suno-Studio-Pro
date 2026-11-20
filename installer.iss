; Script generated for Inno Setup 7
; SMG Suno Studio Pro v2.3.0 — Global Music Studio Windows Installer
; Optimized for all Windows 10/11 (x64) PCs with built-in Khmer Fonts, WebEngine & .smgsong Association

#define MyAppName "SMG Suno Studio Pro"
#define MyAppVersion "2.3.0"
#define MyAppPublisher "SMG Studio"
#define MyAppExeName "SMG Suno Studio Pro.exe"
#define MyAppId "{{C287895A-8E41-432D-8C56-9D3A4B8E17F0}"
#define MyAppAssocExt ".smgsong"
#define MyAppAssocKey "SMGSunoStudioProject"
#define MyAppAssocName "SMG Suno Studio Pro Project"

[Setup]
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} v{#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=dist_installer
OutputBaseFilename=SMG_Suno_Studio_Pro_v2.3.0_Setup
SetupIconFile=assets\logo.ico
UninstallDisplayIcon={app}\assets\logo.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=commandline dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
DisableProgramGroupPage=auto
ChangesAssociations=yes
CloseApplications=force
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce
Name: "installfonts"; Description: "Install Khmer & Modern Studio Typography (Khmer OS Battambang, Content, Siemreap, Noto Sans Khmer)"; GroupDescription: "Typography & Display Quality:"; Flags: checkedonce
Name: "associateproject"; Description: "Associate .smgsong Studio Project files with {#MyAppName}"; GroupDescription: "File Associations:"; Flags: checkedonce

[Files]
; Main Application Binary, Bundled Runtimes, VC++ DLLs, Assets & Fonts
Source: "dist\SMG Suno Studio Pro\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Bundled Khmer Fonts Registered System-Wide / Per-User
Source: "assets\fonts\KhmerOSBattambang-Regular.ttf"; DestDir: "{autofonts}"; FontInstall: "Khmer OS Battambang"; Tasks: installfonts; Flags: onlyifdoesntexist uninsneveruninstall
Source: "assets\fonts\KhmerOSBattambang-Bold.ttf"; DestDir: "{autofonts}"; FontInstall: "Khmer OS Battambang Bold"; Tasks: installfonts; Flags: onlyifdoesntexist uninsneveruninstall
Source: "assets\fonts\KhmerOSContent-Regular.ttf"; DestDir: "{autofonts}"; FontInstall: "Khmer OS Content"; Tasks: installfonts; Flags: onlyifdoesntexist uninsneveruninstall
Source: "assets\fonts\KhmerOSContent-Bold.ttf"; DestDir: "{autofonts}"; FontInstall: "Khmer OS Content Bold"; Tasks: installfonts; Flags: onlyifdoesntexist uninsneveruninstall
Source: "assets\fonts\KhmerOSsiemreap.ttf"; DestDir: "{autofonts}"; FontInstall: "Khmer OS Siemreap"; Tasks: installfonts; Flags: onlyifdoesntexist uninsneveruninstall
Source: "assets\fonts\NotoSansKhmer-Regular.ttf"; DestDir: "{autofonts}"; FontInstall: "Noto Sans Khmer"; Tasks: installfonts; Flags: onlyifdoesntexist uninsneveruninstall
Source: "assets\fonts\NotoSansKhmer-Bold.ttf"; DestDir: "{autofonts}"; FontInstall: "Noto Sans Khmer Bold"; Tasks: installfonts; Flags: onlyifdoesntexist uninsneveruninstall

[Registry]
; Register native .smgsong studio project file association (works for both per-user and admin installs via HKA)
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocExt}"; ValueType: string; ValueName: ""; ValueData: "{#MyAppAssocKey}"; Tasks: associateproject; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocKey}"; ValueType: string; ValueName: ""; ValueData: "{#MyAppAssocName}"; Tasks: associateproject; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocKey}\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\assets\logo.ico,0"; Tasks: associateproject
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocKey}\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Tasks: associateproject

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\assets\logo.ico"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"; IconFilename: "{app}\assets\logo.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\assets\logo.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
