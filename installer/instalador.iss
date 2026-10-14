; Script de Inno Setup (https://jrsoftware.org/isinfo.php) - genera DeliciousFoodCostos_Setup.exe
; Requiere haber ejecutado antes installer\build_exe.bat
[Setup]
AppName=Delicious Food - Sistema de Costos
AppVersion=1.0
DefaultDirName={autopf}\DeliciousFoodCostos
DefaultGroupName=Delicious Food
OutputDir=..\dist
OutputBaseFilename=DeliciousFoodCostos_Setup
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest

[Files]
Source: "..\dist\DeliciousFoodCostos\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Dirs]
Name: "{app}\data"; Permissions: users-modify

[Icons]
Name: "{group}\Sistema de Costos"; Filename: "{app}\DeliciousFoodCostos.exe"
Name: "{autodesktop}\Sistema de Costos"; Filename: "{app}\DeliciousFoodCostos.exe"

[Run]
Filename: "{app}\DeliciousFoodCostos.exe"; Description: "Iniciar el sistema ahora"; Flags: postinstall nowait skipifsilent
