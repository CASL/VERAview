@echo off
setlocal

:try_mini
set CondaDir=%userprofile%\AppData\Local\Continuum\Miniconda2
if not exist "%CondaDir%\scripts\conda.exe" goto try_full
set CondaCommand=%CondaDir%\scripts\conda.exe
goto found

:try_full
set CondaDir=%userprofile%\AppData\Local\Continuum\Anaconda2
if not exist "%CondaDir%\scripts\conda.exe" goto not_found
set CondaCommand=%CondaDir%\scripts\conda.exe
goto found

:not_found
echo msgbox "Anaconda2/Miniconda2 installation not found.  Edit this script to set the CondaDir variable." > %temp%\msg.vbs
call "%temp%\msg.vbs"
goto finished

:found
"%CondaCommand%" install -y numpy=1.9.3 h5py=2.5.0 matplotlib pillow wxpython=3.0 mayavi=4.4.0

:finished
endlocal
