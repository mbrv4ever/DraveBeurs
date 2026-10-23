@echo off
rem === bouw-exe.bat - bouwt DraveBeurs naar dist\DraveBeurs\DraveBeurs.exe ===
setlocal
cd /d "%~dp0"

set "PY="
for %%V in (3.11 3.12 3.10 3.13) do (
  if not defined PY ( py -%%V -c "import sys" >nul 2>&1 && set "PY=py -%%V" )
)
if not defined PY ( py -3 -c "import sys" >nul 2>&1 && set "PY=py -3" )
if not defined PY ( python -c "import sys" >nul 2>&1 && set "PY=python" )
if not defined PY ( echo Geen Python gevonden. Installeer Python 3.11 of 3.12. & pause & exit /b 1 )

if not exist ".venv" ( %PY% -m venv .venv )
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
python -m pip install PyQt6 pyinstaller pillow
if errorlevel 1 ( echo. & echo FOUT: installeren mislukt ^(internet?^). & pause & exit /b 1 )

echo.
echo === Bouwen met PyInstaller... ===
python -m PyInstaller --noconfirm --clean dravebeurs.spec
if errorlevel 1 ( echo. & echo FOUT: bouwen mislukt - lees de melding hierboven. & pause & exit /b 1 )

if exist "dist\DraveBeurs\DraveBeurs.exe" (
  echo.
  echo Klaar! Start:  dist\DraveBeurs\DraveBeurs.exe
) else (
  echo.
  echo LET OP: geen exe gevonden in dist\DraveBeurs - er ging iets mis hierboven.
)
echo.
pause
endlocal
