@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv_cliente\Scripts\python.exe" (
    echo Execute PREPARAR_CLIENTE_EMPRESA.bat primeiro.
    pause
    exit /b 1
)
".venv_cliente\Scripts\python.exe" "configurar_servidor.py"
echo.
pause
