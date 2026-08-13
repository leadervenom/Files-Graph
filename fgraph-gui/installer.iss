; Inno Setup script for fgraph-gui -- produces a traditional Windows installer
; (Next > Next > Install wizard, Start Menu/Desktop shortcuts, an entry in
; "Apps & features" with a real uninstaller) around the portable fgraph-gui.exe
; built by build_exe.ps1. Build with: fgraph-gui\build_installer.ps1

#define MyAppName "fgraph"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "leadervenom"
#define MyAppURL "https://github.com/leadervenom/Files-Graph"
#define MyAppExeName "fgraph-gui.exe"

[Setup]
AppId={{B3C1D9A2-5E4E-4C2B-9C6C-6B7B4A7C6C1D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
; Per-user by default so it never needs an admin prompt; the checkbox below
; still offers an all-users install for anyone who wants that instead.
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=installer_output
OutputBaseFilename=fgraph-gui-setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Files]
Source: "..\fgraph-gui.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName} now"; Flags: nowait postinstall skipifsilent
