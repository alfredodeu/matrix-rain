@echo off
rem Matrix Rain - Start unter Windows (legt beim ersten Start .venv an)
cd /d "%~dp0"

set PYCMD=
where py >nul 2>nul && set PYCMD=py
if not defined PYCMD (
    where python >nul 2>nul && set PYCMD=python
)
if not defined PYCMD (
    echo Python wurde nicht gefunden. Bitte von https://www.python.org/downloads/ installieren
    echo und dabei "Add python.exe to PATH" aktivieren.
    pause
    exit /b 1
)

if not exist .venv\Scripts\python.exe (
    echo Lege virtuelle Umgebung an ...
    %PYCMD% -m venv .venv || goto :fehler
)
.venv\Scripts\python.exe -m pip install --quiet --disable-pip-version-check -r requirements.txt || goto :fehler

.venv\Scripts\python.exe matrix_rain.py %*
exit /b %errorlevel%

:fehler
echo Einrichtung fehlgeschlagen.
pause
exit /b 1
