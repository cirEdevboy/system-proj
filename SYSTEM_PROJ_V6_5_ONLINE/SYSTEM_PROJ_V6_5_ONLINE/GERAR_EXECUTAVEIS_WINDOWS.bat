@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ============================================================
echo PROJECT CENTER V6.5.1 - GERAR EXECUTAVEIS WINDOWS
echo ============================================================
echo.
echo Serao gerados:
echo   DIST_FINAL\PROJECT_CENTER.exe
echo   DIST_FINAL\SYSTEM_PROJ_SERVIDOR.exe
echo.
echo O build pode demorar varios minutos.
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

if not exist ".venv_build\Scripts\python.exe" (
    echo Criando ambiente de build...
    %PYTHON_CMD% -m venv ".venv_build"
    if errorlevel 1 goto :erro
)

set "PY=.venv_build\Scripts\python.exe"

echo.
echo Instalando dependencias de build...
"%PY%" -m pip install --upgrade pip
"%PY%" -m pip install -r "requirements_casa.txt"
"%PY%" -m pip install -r "desktop\requirements.txt"
"%PY%" -m pip install pyinstaller

if errorlevel 1 goto :erro

if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "DIST_FINAL" rmdir /s /q "DIST_FINAL"
mkdir "DIST_FINAL"

echo.
echo ============================================================
echo 1/2 - GERANDO CLIENTE PROJECT_CENTER.exe
echo ============================================================

"%PY%" -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --onefile ^
  --windowed ^
  --name "PROJECT_CENTER" ^
  --paths "desktop" ^
  --collect-all "PySide6" ^
  --hidden-import "win32com.client" ^
  --hidden-import "pythoncom" ^
  --hidden-import "pywintypes" ^
  "desktop\main.py"

if errorlevel 1 goto :erro

copy /Y "dist\PROJECT_CENTER.exe" "DIST_FINAL\PROJECT_CENTER.exe" >nul

echo.
echo ============================================================
echo 2/2 - GERANDO SERVIDOR SYSTEM_PROJ_SERVIDOR.exe
echo ============================================================

"%PY%" -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --onefile ^
  --console ^
  --name "SYSTEM_PROJ_SERVIDOR" ^
  --paths "server" ^
  --add-data "server\app\templates;app\templates" ^
  --add-data "server\app\static;app\static" ^
  --collect-submodules "app" ^
  --collect-all "uvicorn" ^
  --collect-all "reportlab" ^
  --collect-all "openpyxl" ^
  --hidden-import "email_validator" ^
  "servidor_exe.py"

if errorlevel 1 goto :erro

copy /Y "dist\SYSTEM_PROJ_SERVIDOR.exe" "DIST_FINAL\SYSTEM_PROJ_SERVIDOR.exe" >nul

echo.
echo ============================================================
echo EXECUTAVEIS GERADOS COM SUCESSO
echo ============================================================
echo.
echo Pasta:
echo %CD%\DIST_FINAL
echo.
echo PC DE CASA:
echo   SYSTEM_PROJ_SERVIDOR.exe
echo.
echo PC DA EMPRESA:
echo   PROJECT_CENTER.exe
echo.
echo No PC da empresa, na primeira execucao, clique em
echo "Configurar servidor" e cole o link HTTPS do servidor de casa.
echo.
pause
exit /b 0

:erro
echo.
echo ============================================================
echo O BUILD FALHOU
echo ============================================================
echo.
echo Tire um print desta janela e envie para diagnostico.
echo.
pause
exit /b 1
