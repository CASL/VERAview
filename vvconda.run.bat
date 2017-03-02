@echo off
setlocal

set VERAViewDir=%~dp0

:try_0
rem ---------------------------------------------------------------------
rem - If you changed the path for your per-user Anaconda/Miniconda environment
rem - setup, set the value of the CondaDir variable to point to that path.
rem ---------------------------------------------------------------------
set CondaDir=%userprofile%\AppData\Local\Continuum\Miniconda2
if not exist "%CondaDir%\pythonw.exe" goto try_2
set PythonCommand=%CondaDir%\pythonw.exe
goto found

:try_2
set CondaDir=%userprofile%\Miniconda2
if not exist "%CondaDir%\pythonw.exe" goto try_3
set PythonCommand=%CondaDir%\pythonw.exe
goto found

:try_3
set CondaDir=%userprofile%\AppData\Local\Continuum\Anaconda2
if not exist "%CondaDir%\pythonw.exe" goto try_4
set PythonCommand=%CondaDir%\pythonw.exe
goto found

:try_4
set CondaDir=%userprofile%\Anaconda2
if not exist "%CondaDir%\pythonw.exe" goto not_found
set PythonCommand=%CondaDir%\pythonw.exe
goto found

:not_found
echo msgbox "Anaconda2/Miniconda2 installation not found.  Edit this script to set the CondaDir variable." > %temp%\msg.vbs
call "%temp%\msg.vbs"
goto finished

:use_default
set PythonCommand=python

:found
set PYTHONPATH=%VERAViewDir%;%PYTHONPATH%
"%PythonCommand%" "%VERAViewDir%veraview.py" %1 %2 %3 %4 %5 %6 %7 %8 %9

:finished
endlocal
