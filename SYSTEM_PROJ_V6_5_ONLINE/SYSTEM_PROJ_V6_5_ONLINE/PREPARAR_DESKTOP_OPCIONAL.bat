@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv_corporativo\Scripts\python.exe" (
    echo Execute PREPARAR_PC_CORPORATIVO.bat primeiro.
    pause
    exit /b 1
)

echo.
echo Instalando interface Desktop PySide6 apenas neste ambiente local...
".venv_corporativo\Scripts\python.exe" -m pip install -r "desktop\requirements.txt"

if errorlevel 1 (
    echo.
    echo Nao foi possivel instalar o Desktop.
    echo Voce ainda pode testar normalmente pelo navegador.
    pause
    exit /b 1
)

echo Desktop preparado.
pause
