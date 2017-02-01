@echo off
setlocal

set VERAViewDir=%~dp0

rem ---------------------------------------------------------------------
rem - If you changed the path for your per-user Canopy environment setup,
rem - set the value of the CanopyUserDir variable to point to the User subdir
rem - under that path.
rem ---------------------------------------------------------------------
if not exist "%userprofile%\AppData\Local\Continuum\Miniconda2" goto not_found
set CondaBinDir=%userprofile%\AppData\Local\Continuum\Miniconda2


if exist "%CondaBinDir%\pythonw.exe" goto found
echo msgbox "Anaconda2 installation not found.  Edit this script to set the CondaBinDir variable." > %temp%\msg.vbs
call "%temp%\msg.vbs"
goto finished


:found
set PYTHONPATH=%VERAViewDir%;%PYTHONPATH%
"%CondaBinDir%\pythonw" "%VERAViewDir%veraview.py" %1 %2 %3 %4 %5 %6 %7 %8 %9


:finished
endlocal
