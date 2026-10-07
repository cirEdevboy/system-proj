@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv_corporativo\Scripts\python.exe" (
    echo Execute PREPARAR_PC_CORPORATIVO.bat primeiro.
    pause
    exit /b 1
)

".venv_corporativo\Scripts\python.exe" "modo_corporativo.py" migrate
echo.
pause
