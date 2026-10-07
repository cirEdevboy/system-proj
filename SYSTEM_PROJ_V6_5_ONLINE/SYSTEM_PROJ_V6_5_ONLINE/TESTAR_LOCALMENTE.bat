@echo off
setlocal
cd /d "%~dp0"

where docker >nul 2>nul
if errorlevel 1 (
    echo Docker Desktop nao foi encontrado.
    echo Instale/abra o Docker Desktop e tente novamente.
    pause
    exit /b 1
)

if not exist ".env" (
    copy /Y ".env.local.example" ".env" >nul
    echo Arquivo .env local criado.
)

echo.
echo Iniciando PostgreSQL, MinIO e API...
docker compose up -d --build postgres minio api
if errorlevel 1 (
    echo Falha ao iniciar os containers.
    pause
    exit /b 1
)

echo.
echo Aguardando o servidor...
timeout /t 8 /nobreak >nul

start "" "http://localhost:8000"

echo.
echo SYSTEM PROJ local iniciado.
echo Web: http://localhost:8000
echo.
echo Para criar o primeiro ADMIN execute:
echo CRIAR_ADMIN_LOCAL.bat
echo.
pause
