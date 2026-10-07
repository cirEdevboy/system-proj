@echo off
setlocal
cd /d "%~dp0"

docker compose up -d postgres minio api >nul
echo.
echo Crie o ADMIN com o MESMO username que voce usava na V5
echo se quiser manter automaticamente seus projetos vinculados a sua conta.
echo.
docker compose exec api python /app/scripts/bootstrap_admin.py
echo.
pause
