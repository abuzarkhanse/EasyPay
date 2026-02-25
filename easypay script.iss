#define MyAppName "EasyPay"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "EasyPay Solutions"

[Setup]
AppId={{EASYPAY-APP-2026}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={pf}\EasyPay
DefaultGroupName=EasyPay
OutputDir=.
OutputBaseFilename=EasyPay_Setup_v1.0.0
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin

[Files]
Source: "dist\EasyPay\*"; DestDir: "{app}"; Flags: recursesubdirs

[Icons]
Name: "{group}\EasyPay"; Filename: "{app}\EasyPay.exe"
Name: "{commondesktop}\EasyPay"; Filename: "{app}\EasyPay.exe"

[Dirs]
Name: "{commonappdata}\EasyPay"; Permissions: users-full

[Run]
Filename: "{app}\EasyPay.exe"; Description: "Launch EasyPay"; Flags: nowait postinstall skipifsilent
