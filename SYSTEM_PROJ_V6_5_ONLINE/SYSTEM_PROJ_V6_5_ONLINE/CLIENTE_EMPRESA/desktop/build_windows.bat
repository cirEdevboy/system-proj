@echo off
setlocal
cd /d "%~dp0"
python -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm --clean --windowed --name "SYSTEM_PROJ" --collect-all PySide6 main.py
if errorlevel 1 pause & exit /b 1
echo EXE gerado em dist\SYSTEM_PROJ\SYSTEM_PROJ.exe
pause
