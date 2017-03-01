@echo off
setlocal

set VERAViewDir=%~dp0

rem ---------------------------------------------------------------------
rem - If you changed the path for your per-user Anaconda environment setup,
rem - set the value of the CondaDir variable to point to that path.
rem ---------------------------------------------------------------------
if not exist "%userprofile%\AppData\Local\Continuum\Miniconda2" goto not_found
set CondaDir=%userprofile%\AppData\Local\Continuum\Miniconda2
set PythonCommand=%CondaDir%\pythonw

if exist "%CondaDir%\pythonw.exe" goto found
echo msgbox "Miniconda2 installation not found.  Edit this script to set the CondaDir variable." > %temp%\msg.vbs
call "%temp%\msg.vbs"
goto finished

:not_found
set PythonCommand=python

:found
set PYTHONPATH=%VERAViewDir%;%PYTHONPATH%
"%PythonCommand%" "%VERAViewDir%veraview.py" %1 %2 %3 %4 %5 %6 %7 %8 %9


:finished
endlocal
