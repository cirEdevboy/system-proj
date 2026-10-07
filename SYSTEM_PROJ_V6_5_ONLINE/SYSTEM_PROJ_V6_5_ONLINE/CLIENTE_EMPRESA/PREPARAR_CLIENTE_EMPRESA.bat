@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ============================================================
echo SYSTEM PROJ V6.3 - CLIENTE DO PC DA EMPRESA
echo ============================================================
echo.
echo Este cliente conecta no servidor que esta rodando no PC de casa.
echo Para o Outlook automatico ele precisa do Outlook Desktop instalado.
echo.

set "PYTHON_CMD="

py -3.11 -c "import sys; exit(0 if sys.version_info >= (3,11) else 1)" >nul 2>nul
if not errorlevel 1 set "PYTHON_CMD=py -3.11"

if not defined PYTHON_CMD (
    python -c "import sys; exit(0 if sys.version_info >= (3,11) else 1)" >nul 2>nul
    if not errorlevel 1 set "PYTHON_CMD=python"
)

if not defined PYTHON_CMD (
    echo [ERRO] Python 3.11 ou superior nao encontrado.
    pause
    exit /b 1
)

if not exist ".venv_cliente\Scripts\python.exe" (
    %PYTHON_CMD% -m venv ".venv_cliente"
)

".venv_cliente\Scripts\python.exe" -m pip install --upgrade pip
".venv_cliente\Scripts\python.exe" -m pip install -r "desktop\requirements.txt"

if errorlevel 1 (
    echo.
    echo [ERRO] A rede corporativa pode ter bloqueado alguma dependencia.
    pause
    exit /b 1
)

echo.
echo Cliente preparado.
echo Agora execute CONFIGURAR_LINK_SERVIDOR.bat.
echo.
pause
