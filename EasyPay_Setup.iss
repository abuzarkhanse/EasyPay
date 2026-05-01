#define MyAppName "EasyPay"
#define MyAppVersion "2.0"
#define MyAppPublisher "EasyPay"
#define MyAppExeName "EasyPay.exe"

[Setup]
AppId={{EASYPAY-2026}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}

DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}

OutputDir=installer_output
OutputBaseFilename=EasyPay_Setup_v2

Compression=lzma
SolidCompression=yes

SetupIconFile=assets\icon.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create Desktop Shortcut"; GroupDescription: "Additional Icons"; Flags: unchecked

[Files]
Source: "dist\EasyPay\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\EasyPay"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\EasyPay"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch EasyPay"; Flags: nowait postinstall skipifsilent