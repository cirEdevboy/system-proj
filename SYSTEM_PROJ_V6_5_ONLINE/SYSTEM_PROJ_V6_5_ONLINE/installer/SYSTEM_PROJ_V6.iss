#define MyAppName "SYSTEM PROJ"
#define MyAppVersion "6.0.0"
#define MyAppExeName "SYSTEM_PROJ.exe"
[Setup]
AppId={{B86D6D62-2447-4B31-92C7-5ED1FE27A606}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\SYSTEM PROJ
DefaultGroupName=SYSTEM PROJ
OutputDir=output
OutputBaseFilename=SYSTEM_PROJ_V6_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
[Files]
Source: "..\desktop\dist\SYSTEM_PROJ\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{autodesktop}\SYSTEM PROJ"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\SYSTEM PROJ"; Filename: "{app}\{#MyAppExeName}"
[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir SYSTEM PROJ"; Flags: nowait postinstall skipifsilent
