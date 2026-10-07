@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv_casa\Scripts\python.exe" (
    echo Execute PREPARAR_SERVIDOR_CASA.bat primeiro.
    pause
    exit /b 1
)
".venv_casa\Scripts\python.exe" "modo_casa.py" server
