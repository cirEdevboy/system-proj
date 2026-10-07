@echo off
cd /d "%~dp0"
if not exist "DIST_FINAL\SYSTEM_PROJ_SERVIDOR.exe" (
  echo Execute GERAR_EXECUTAVEIS_WINDOWS.bat primeiro.
  pause
  exit /b 1
)
"DIST_FINAL\SYSTEM_PROJ_SERVIDOR.exe"
