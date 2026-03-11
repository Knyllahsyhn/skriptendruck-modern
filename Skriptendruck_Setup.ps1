#Requires -Version 5.1
<#
.SYNOPSIS
    Skriptendruck - Ersteinrichtung
.DESCRIPTION
    Richtet das Skriptendruck-Programm auf einem neuen Rechner ein.
    Einmalig als Admin ausführen. Installiert Abhängigkeiten, erstellt
    Ordnerstruktur und richtet verschlüsselte LDAP-Credentials ein.
#>

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Set-Location -Path $PSScriptRoot

Write-Host ""
Write-Host "  ╔══════════════════════════════════════════╗" -ForegroundColor Blue
Write-Host "  ║   Skriptendruck - Ersteinrichtung         ║" -ForegroundColor Blue
Write-Host "  ╚══════════════════════════════════════════╝" -ForegroundColor Blue
Write-Host ""

$step = 0
$totalSteps = 5

# --- 1. Python ---
$step++
Write-Host "[$step/$totalSteps] Prüfe Python..." -ForegroundColor Cyan
try {
    $pyVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) { throw }
    Write-Host "  $pyVersion" -ForegroundColor Green
} catch {
    Write-Host "  [FEHLER] Python nicht gefunden!" -ForegroundColor Red
    Write-Host "  Bitte Python 3.11+ installieren: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "  WICHTIG: Bei der Installation 'Add to PATH' ankreuzen!" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Enter zum Beenden"
    exit 1
}

# --- 2. Poetry ---
$step++
Write-Host "[$step/$totalSteps] Prüfe Poetry..." -ForegroundColor Cyan

# Hilfsfunktion um Poetry in User-Verzeichnissen zu finden, falls PATH nicht gesetzt ist
function Get-PoetryPath {
    $pythonVersion = (python -c "import sys; print(f'{sys.version_info.major}{sys.version_info.minor}')")
    $paths = @(
        "$env:APPDATA\Python\Scripts\poetry.exe",
        "$env:APPDATA\Python\Python$pythonVersion\Scripts\poetry.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python$pythonVersion\Scripts\poetry.exe",
        "$env:USERPROFILE\.local\bin\poetry.exe"
    )
    foreach ($p in $paths) { if (Test-Path $p) { return $p } }
    return $null
}

$poetryCmd = "poetry"
$poetryFound = $false

try {
    $null = poetry --version 2>&1
    if ($LASTEXITCODE -eq 0) { $poetryFound = $true }
} catch {}

if (-not $poetryFound) {
    $pPath = Get-PoetryPath
    if ($pPath) {
        $poetryCmd = "& '$pPath'"
        $poetryFound = $true
        Write-Host "  Poetry über absoluten Pfad gefunden: $pPath" -ForegroundColor Gray
    } else {
        Write-Host "  Poetry nicht gefunden, installiere via pip..." -ForegroundColor Yellow
        python -m pip install --user poetry
        $pPath = Get-PoetryPath
        if ($pPath) {
            $poetryCmd = "& '$pPath'"
            $poetryFound = $true
        }
    }
}

if (-not $poetryFound) {
    Write-Host "  [FEHLER] Poetry konnte nicht gefunden oder installiert werden!" -ForegroundColor Red
    Read-Host "Enter zum Beenden"
    exit 1
}

$poetryVersion = Invoke-Expression "$poetryCmd --version 2>&1"
Write-Host "  $poetryVersion" -ForegroundColor Green

# --- 3. Dependencies ---
$step++
Write-Host "[$step/$totalSteps] Installiere Abhängigkeiten..." -ForegroundColor Cyan
Write-Host "  (Dies kann auf Netzlaufwerken einen Moment dauern...)" -ForegroundColor Gray

Invoke-Expression "$poetryCmd install --without dev" | ForEach-Object {
    if ($_ -match "Installing|Already") { Write-Host "  $_" -ForegroundColor DarkGray }
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "  [FEHLER] Abhängigkeiten konnten nicht installiert werden!" -ForegroundColor Red
    Read-Host "Enter zum Beenden"
    exit 1
}
Write-Host "  OK" -ForegroundColor Green

# --- 4. .env und Ordnerstruktur ---
$step++
Write-Host "[$step/$totalSteps] Initialisiere Konfiguration und Ordnerstruktur" -ForegroundColor Cyan

if (-not (Test-Path ".env")) {
    if (Test-Path "_env") {
        Copy-Item "_env" ".env"
        Write-Host "  .env aus Vorlage erstellt" -ForegroundColor Green
    } else {
        Write-Host "  [WARNUNG] Keine _env Vorlage gefunden!" -ForegroundColor Yellow
    }
}

Invoke-Expression "$poetryCmd run skriptendruck init"
Write-Host "  OK" -ForegroundColor Green

# --- 5. Credentials ---
$step++
Write-Host "[$step/$totalSteps] LDAP-Credentials einrichten..." -ForegroundColor Cyan
Write-Host ""

$setupCreds = Read-Host "  LDAP-Credentials jetzt einrichten? (j/n)"
if ($setupCreds -eq "j" -or $setupCreds -eq "J" -or $setupCreds -eq "y") {
    Invoke-Expression "$poetryCmd run skriptendruck credentials setup"
} else {
    Write-Host "  Übersprungen. Später einrichten mit:" -ForegroundColor Yellow
    Write-Host "  poetry run skriptendruck credentials setup" -ForegroundColor Yellow
}

# --- Fertig ---
Write-Host ""
Write-Host "  ══════════════════════════════════════════" -ForegroundColor Green
Write-Host "  Einrichtung abgeschlossen!" -ForegroundColor Green
Write-Host ""
Write-Host "  Nächste Schritte:" -ForegroundColor Cyan
Write-Host "    1. .env Datei prüfen (BASE_PATH, LDAP-Einstellungen)"
Write-Host "    2. Skriptendruck.ps1 zum Verarbeiten starten"
Write-Host "  ══════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Read-Host "Enter zum Beenden"
