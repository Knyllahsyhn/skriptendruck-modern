<#
.SYNOPSIS
    Startet das Skriptendruck Web-Dashboard.
.DESCRIPTION
    Startet den FastAPI/Uvicorn-Server fuer das Web-Dashboard.
    Konfiguration erfolgt ueber Umgebungsvariablen oder .env-Datei.
#>

$Host_Addr = if ($env:DASHBOARD_HOST) { $env:DASHBOARD_HOST } else { "0.0.0.0" }
$Port = if ($env:DASHBOARD_PORT) { $env:DASHBOARD_PORT } else { "8080" }

Write-Host ""
Write-Host "  ====================================" -ForegroundColor Cyan
Write-Host "   Skriptendruck Web-Dashboard" -ForegroundColor Cyan
Write-Host "  ====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Starte auf http://${Host_Addr}:${Port}" -ForegroundColor Green
Write-Host "  Stoppen mit Ctrl+C" -ForegroundColor Yellow
Write-Host ""

# Virtual Environment aktivieren falls vorhanden
if (Test-Path ".venv\Scripts\Activate.ps1") {
    & ".venv\Scripts\Activate.ps1"
}

python -m uvicorn skriptendruck.web.app:app --host $Host_Addr --port $Port --reload --app-dir src
