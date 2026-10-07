@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ============================================================
echo SYSTEM PROJ V6.3 - PREPARAR SERVIDOR NO PC DE CASA
echo ============================================================
echo.

set "PYTHON_CMD="

py -3.11 -c "import sys; exit(0 if sys.version_info >= (3,11) else 1)" >nul 2>nul
if not errorlevel 1 set "PYTHON_CMD=py -3.11"

if not defined PYTHON_CMD (
    python -c "import sys; exit(0 if sys.version_info >= (3,11) else 1)" >nul 2>nul
    if not errorlevel 1 set "PYTHON_CMD=python"
)

if not defined PYTHON_CMD (
    echo [ERRO] Python 3.11 ou superior nao foi encontrado.
    echo Instale Python no seu PC de casa e tente novamente.
    pause
    exit /b 1
)

%PYTHON_CMD% --version

if not exist ".venv_casa\Scripts\python.exe" (
    echo.
    echo Criando ambiente Python da V6.3...
    %PYTHON_CMD% -m venv ".venv_casa"
)

echo.
echo Instalando dependencias...
".venv_casa\Scripts\python.exe" -m pip install --upgrade pip
".venv_casa\Scripts\python.exe" -m pip install -r "requirements_casa.txt"

if errorlevel 1 (
    echo.
    echo [ERRO] Nao foi possivel instalar as dependencias.
    pause
    exit /b 1
)

echo.
echo Baixando componente de acesso externo Cloudflare Tunnel...
".venv_casa\Scripts\python.exe" "modo_casa.py" download-cloudflared

echo.
echo Executando diagnostico...
".venv_casa\Scripts\python.exe" "modo_casa.py" doctor

if errorlevel 1 (
    echo.
    echo O diagnostico encontrou um problema.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo SERVIDOR PREPARADO
echo ============================================================
echo.
echo Para usar apenas em casa:
echo INICIAR_SERVIDOR_CASA.bat
echo.
echo Para abrir acesso ao PC da empresa:
echo INICIAR_CASA_COM_ACESSO_EMPRESA.bat
echo.
pause
