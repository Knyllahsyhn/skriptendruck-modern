@echo off
REM ============================================
REM  Skriptendruck Web-Dashboard starten
REM ============================================
title Skriptendruck Dashboard

REM Host und Port aus Umgebungsvariablen oder Defaults
if not defined DASHBOARD_HOST set DASHBOARD_HOST=0.0.0.0
if not defined DASHBOARD_PORT set DASHBOARD_PORT=8080

echo.
echo  ====================================
echo   Skriptendruck Web-Dashboard
echo  ====================================
echo.
echo  Starte auf http://%DASHBOARD_HOST%:%DASHBOARD_PORT%
echo  Stoppen mit Ctrl+C
echo.

REM Aktiviere .venv falls vorhanden
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

python -m uvicorn skriptendruck.web.app:app --host %DASHBOARD_HOST% --port %DASHBOARD_PORT% --reload --app-dir src

pause
