[Setup]
AppName=EasyPay
AppVersion=1.0.2
DefaultDirName={commonpf}\EasyPay
DefaultGroupName=EasyPay
OutputDir=installer_output
OutputBaseFilename=EasyPay_Setup_v1.0.2
Compression=lzma
SolidCompression=yes
SetupIconFile=assets\EasyPay.ico

[Files]
Source: "dist\EasyPay\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\EasyPay"; Filename: "{app}\EasyPay.exe"
Name: "{commondesktop}\EasyPay"; Filename: "{app}\EasyPay.exe"

[Run]
Filename: "{app}\EasyPay.exe"; Description: "Launch EasyPay"; Flags: nowait postinstall skipifsilent