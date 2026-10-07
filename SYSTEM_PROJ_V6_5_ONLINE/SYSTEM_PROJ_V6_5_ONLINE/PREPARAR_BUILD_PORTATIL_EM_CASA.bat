@echo off
setlocal
cd /d "%~dp0"

echo ============================================================
echo GERAR PACOTE PORTATIL - EXECUTAR NO PC DE CASA
echo ============================================================
echo.
echo Este script e para o seu PC pessoal, onde voce tem liberdade
echo para instalar ferramentas de desenvolvimento.
echo.

if not exist ".venv_portatil\Scripts\python.exe" (
    py -3.11 -m venv ".venv_portatil"
)

".venv_portatil\Scripts\python.exe" -m pip install --upgrade pip
".venv_portatil\Scripts\python.exe" -m pip install -r "requirements_corporativo.txt" pyinstaller

echo.
echo Validando ambiente...
".venv_portatil\Scripts\python.exe" "modo_corporativo.py" doctor

echo.
echo Observacao:
echo A geracao de um EXE unico para FastAPI + templates sera finalizada
echo numa etapa de empacotamento Windows depois dos testes funcionais.
echo Por enquanto este script deixa todo o ambiente de build preparado.
echo.
pause
