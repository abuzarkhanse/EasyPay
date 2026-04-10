[Setup]
AppName=EasyPay
AppVersion=1.0.1
AppPublisher=Abuzar
AppPublisherURL=https://github.com/abuzarkhanse/EasyPay
DefaultDirName={autopf}\EasyPay
DefaultGroupName=EasyPay
OutputDir=installer_output
OutputBaseFilename=EasyPay_v1.0.1_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile=assets\EasyPay.ico

[Files]
Source: "dist\EasyPay\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\EasyPay"; Filename: "{app}\EasyPay.exe"
Name: "{autodesktop}\EasyPay"; Filename: "{app}\EasyPay.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create Desktop Shortcut"; GroupDescription: "Additional icons:"

[Run]
Filename: "{app}\EasyPay.exe"; Description: "Launch EasyPay"; Flags: nowait postinstall skipifsilent