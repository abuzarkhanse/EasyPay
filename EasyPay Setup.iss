[Setup]
AppId={{A1B7E6F2-9D2A-4F52-9C1D-EPAY1100}}
AppName=EasyPay
AppVersion=1.1.0
AppVerName=EasyPay 1.1.0
AppPublisher=EasyPay
DefaultDirName={autopf}\EasyPay
DefaultGroupName=EasyPay
DisableProgramGroupPage=yes
OutputDir=installer_output
OutputBaseFilename=EasyPay_v1.1.0_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
SetupIconFile=assets\EasyPay.ico
UninstallDisplayIcon={app}\EasyPay.exe

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"

[Files]
Source: "dist\EasyPay\EasyPay.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\EasyPay\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\EasyPay"; Filename: "{app}\EasyPay.exe"
Name: "{autodesktop}\EasyPay"; Filename: "{app}\EasyPay.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\EasyPay.exe"; Description: "Launch EasyPay"; Flags: nowait postinstall skipifsilent