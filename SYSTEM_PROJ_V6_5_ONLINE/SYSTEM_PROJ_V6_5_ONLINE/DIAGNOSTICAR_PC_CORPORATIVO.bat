@echo off
setlocal
cd /d "%~dp0"

if exist ".venv_corporativo\Scripts\python.exe" (
    ".venv_corporativo\Scripts\python.exe" "modo_corporativo.py" doctor
) else (
    py -3.11 "modo_corporativo.py" doctor 2>nul
    if errorlevel 1 python "modo_corporativo.py" doctor
)

echo.
pause
