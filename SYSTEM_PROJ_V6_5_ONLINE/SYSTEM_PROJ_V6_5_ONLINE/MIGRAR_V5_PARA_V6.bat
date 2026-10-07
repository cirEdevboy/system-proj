@echo off
setlocal
cd /d "%~dp0"

if not exist "migration_data\gestao_projetos.db" (
    echo.
    echo ERRO: migration_data\gestao_projetos.db nao encontrado.
    echo Copie o banco REAL da V5 para essa pasta.
    echo.
    pause
    exit /b 1
)

if not exist ".env" (
    copy /Y ".env.local.example" ".env" >nul
)

docker compose up -d --build postgres minio api
if errorlevel 1 (
    echo Falha ao iniciar o ambiente local.
    pause
    exit /b 1
)

echo.
echo ================================================
echo 1/2 - ANALISE DO BANCO V5
echo ================================================
docker compose exec api python /app/scripts/migrate_v5_sqlite.py ^
  /data/migration/gestao_projetos.db ^
  --documents-root /data/migration/DOCUMENTOS_PROJETOS ^
  --transfers-root /data/migration/TRANSFERENCIAS_GERADAS ^
  --report /data/migration/relatorio_pre_migracao.json ^
  --dry-run

if errorlevel 1 (
    echo.
    echo A analise encontrou um erro. A migracao NAO foi executada.
    pause
    exit /b 1
)

echo.
echo O relatorio de analise foi criado em:
echo migration_data\relatorio_pre_migracao.json
echo.
choice /M "Deseja executar a migracao agora"
if errorlevel 2 exit /b 0

echo.
echo ================================================
echo 2/2 - MIGRANDO V5 PARA V6
echo ================================================
docker compose exec api python /app/scripts/migrate_v5_sqlite.py ^
  /data/migration/gestao_projetos.db ^
  --documents-root /data/migration/DOCUMENTOS_PROJETOS ^
  --transfers-root /data/migration/TRANSFERENCIAS_GERADAS ^
  --report /data/migration/relatorio_migracao.json ^
  --activation-csv /data/migration/codigos_ativacao_usuarios.csv

if errorlevel 1 (
    echo.
    echo A migracao falhou. Verifique a mensagem acima.
    pause
    exit /b 1
)

echo.
echo ================================================
echo MIGRACAO CONCLUIDA
echo ================================================
echo.
echo Relatorio:
echo migration_data\relatorio_migracao.json
echo.
echo Usuarios migrados que precisam completar cadastro:
echo migration_data\codigos_ativacao_usuarios.csv
echo.
echo Abra:
echo http://localhost:8000
echo.
pause
