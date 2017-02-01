[Setup]
AppId=VERAView
AppName=VERAView
;AppCopyright=Copyright (C) 2007 UT-Battelle, LLC
;AppVerName=HPAC Data 6.0
AppVersion=1.0.80
AppPublisher=Oak Ridge National Laboratory
AppPublisherURL=http://www.ornl.gov/
;AppSupportURL=http://newton.ornl.gov/FPTool
;AppUpdatesURL=http://newton.ornl.gov/FPTool
ArchitecturesAllowed=x64 ia64
ArchitecturesInstallIn64BitMode=x64 ia64
BackColor=$ffc8c8
BackColor2=$ffffff
BackColorDirection=toptobottom
;DefaultDirName={pf}\Fallout Planning Tool
;DefaultDirName={code:GetHpacRootDir}
DefaultDirName={%userprofile}\VERAView
;DefaultGroupName=DELFIC Fallout Planning Tool
DirExistsWarning=yes
;InfoAfterFile=postinstall.txt
InfoBeforeFile=preinstall.rtf
OutputBaseFilename=veraview-1.0.80-setup.exe
PrivilegesRequired=lowest
;PrivilegesRequired=admin, poweruser, lowest
SetupLogging=yes
UsePreviousAppDir=yes
;UsePreviousAppDir=no


[Types]
Name: "full"; Description: "Full installation";
Name: "custom"; Description: "Select individual components"; Flags: iscustom
;Name: "nojava"; Description: "Install without Java Runtime";


[Components]
;Name: "firefox"; Description: "Firefox"; Types: custom all; Flags: fixed
Name: "anaconda2"; Description: "Anaconda2 Python Runtime Environment"; Types: full;
Name: "veraview"; Description: "VERAView Application"; Types: full; Flags: fixed;


[Tasks]
;Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; MinVersion: 4,4; Flags: unchecked
;Name: "quicklaunchicon"; Description: "Create a &Quick Launch icon"; GroupDescription: "Additional icons:"; MinVersion: 4,4; Flags: unchecked


[Dirs]
Name: "{app}\bean"; Components: veraview; Permissions: users-modify;
Name: "{app}\bin"; Components: veraview; Permissions: users-modify;
Name: "{app}\bin\win64"; Components: veraview; Permissions: users-modify;
Name: "{app}\data"; Components: veraview; Permissions: users-modify;
Name: "{app}\event"; Components: veraview; Permissions: users-modify;
Name: "{app}\res"; Components: veraview; Permissions: users-modify;
Name: "{app}\view3d"; Components: veraview; Permissions: users-modify;
Name: "{app}\widget"; Components: veraview; Permissions: users-modify;
Name: "{app}\widget\bean"; Components: veraview; Permissions: users-modify;
Name: "{localappdata}\Continuum\Anaconda2"; Components: anaconda2; Permissions: users-modify;


[Files]
Source: "..\..\*.py"; DestDir: "{app}"; Components: veraview; Permissions: users-modify; Flags: ignoreversion
Source: "..\..\vvconda.run.bat"; DestDir: "{app}"; Components: veraview; Permissions: users-modify; Flags: ignoreversion
Source: "..\..\bin\win64\*.*"; DestDir: "{app}\bin\win64"; Components: veraview; Permissions: users-modify; Flags: createallsubdirs ignoreversion recursesubdirs
Source: "..\..\data\*.py"; DestDir: "{app}\data"; Components: veraview; Permissions: users-modify; Flags: ignoreversion
Source: "..\..\event\*.py"; DestDir: "{app}\event"; Components: veraview; Permissions: users-modify; Flags: ignoreversion
Source: "..\..\res\*.*"; DestDir: "{app}\res"; Components: veraview; Permissions: users-modify; Flags: ignoreversion
Source: "..\..\view3d\*.py"; DestDir: "{app}\view3d"; Components: veraview; Permissions: users-modify; Flags: ignoreversion
Source: "..\..\view3d\*.py"; DestDir: "{app}\view3d"; Components: veraview; Permissions: users-modify; Flags: ignoreversion
Source: "..\..\widget\*.py"; DestDir: "{app}\widget"; Components: veraview; Permissions: users-modify; Flags: createallsubdirs ignoreversion recursesubdirs

Source: "bin\*.*"; DestDir: "${tmp}"; Components: anaconda2;


[Messages]
BeveledLabel=VERAView 1.0.80 Install


[Run]
Filename: "cmd.exe"; Parameters: "/c curl -O https://repo.continuum.io/miniconda/Miniconda2-latest-Windows-x86_64.exe"; Components: anaconda2; Description: "Download Miniconda2"; Flags: runascurrentuser waituntilterminated; StatusMsg: "Downloading Miniconda2 Installer"; WorkingDir: "{tmp}"

Filename: "Miniconda2-latest-Windows-x86_64.exe"; Parameters: "/AddToPath=0 /RegisterPython=0 /NoRegistry=1 /D={localappdata}\Continuum\Miniconda2"; Components: anaconda2; Description: "Install Miniconda2"; Flags: runascurrentuser waituntilterminated; StatusMsg: "Installing Miniconda2"; WorkingDir: "{tmp}"

Filename: "{localappdata}\Continuum\Miniconda2\scripts\conda.exe"; Parameters: "install -y numpy=1.9.3 h5py=2.5.0 matplotlib wxpython-3.0 mayavi=4.4.0" Components: anaconda2; Description: "Install Required Packages"; Flags: runascurrentuser waituntilterminated; StatusMsg: "Installing Required Packages"; WorkingDir: "{app}"


[UninstallRun]
Filename: "{localappdata}\Continuum\Miniconda2\Uninstall-Anaconda.exe"; Components: anaconda2; Description: "Uninstall Miniconda2"; Flags: runascurrentuser waituntilterminated; StatusMsg: "Uninstalling Miniconda2";
