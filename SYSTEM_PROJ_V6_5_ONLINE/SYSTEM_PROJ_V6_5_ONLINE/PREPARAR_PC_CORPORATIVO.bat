@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ============================================================
echo SYSTEM PROJ V6.2 - PREPARAR PC CORPORATIVO SEM ADMIN
echo ============================================================
echo.
echo Este processo instala pacotes SOMENTE dentro desta pasta.
echo Nao cria servicos do Windows e nao requer Docker.
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
    echo.
    echo Neste PC corporativo voce precisara de uma destas opcoes:
    echo 1. Python ja disponibilizado pela TI;
    echo 2. Instalacao Python por usuario, se a politica permitir;
    echo 3. Mais tarde gerar o pacote portatil no seu PC de casa.
    echo.
    pause
    exit /b 1
)

echo Python localizado.
%PYTHON_CMD% --version
echo.

if not exist ".venv_corporativo\Scripts\python.exe" (
    echo Criando ambiente virtual local...
    %PYTHON_CMD% -m venv ".venv_corporativo"
    if errorlevel 1 (
        echo [ERRO] Nao foi possivel criar o ambiente virtual.
        pause
        exit /b 1
    )
)

echo.
echo Atualizando pip dentro do ambiente local...
".venv_corporativo\Scripts\python.exe" -m pip install --upgrade pip

echo.
echo Instalando dependencias do teste...
echo Nenhum pacote sera instalado para todos os usuarios do Windows.
".venv_corporativo\Scripts\python.exe" -m pip install -r "requirements_corporativo.txt"

if errorlevel 1 (
    echo.
    echo [ERRO] A instalacao das dependencias falhou.
    echo Em rede corporativa isso pode ser bloqueio de internet/proxy.
    echo Tire um print desta tela e envie para diagnostico.
    pause
    exit /b 1
)

echo.
echo Executando diagnostico...
".venv_corporativo\Scripts\python.exe" "modo_corporativo.py" doctor

if errorlevel 1 (
    echo.
    echo O diagnostico encontrou um problema.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo PC PREPARADO COM SUCESSO
echo ============================================================
echo.
echo Agora execute:
echo INICIAR_TESTE_CORPORATIVO.bat
echo.
pause
