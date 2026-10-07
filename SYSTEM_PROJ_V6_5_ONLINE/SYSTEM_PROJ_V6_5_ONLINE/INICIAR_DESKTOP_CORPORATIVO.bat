@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv_corporativo\Scripts\python.exe" (
    echo Execute PREPARAR_PC_CORPORATIVO.bat primeiro.
    pause
    exit /b 1
)

start "SYSTEM PROJ SERVER" /min ".venv_corporativo\Scripts\python.exe" "modo_corporativo.py" server
timeout /t 3 /nobreak >nul

".venv_corporativo\Scripts\python.exe" "desktop\main.py"
