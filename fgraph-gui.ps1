<#
.SYNOPSIS
    Launches fgraph-gui -- the living, physics-based 3D file graph desktop app.

.DESCRIPTION
    First run creates a virtual environment and installs dependencies; every
    run after that is instant. Opens straight to the account picker -- no
    arguments needed.

.EXAMPLE
    .\fgraph-gui.ps1
#>

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$app = Join-Path $root "fgraph-gui"
$venv = Join-Path $app ".venv"
$venvPython = Join-Path $venv "Scripts\python.exe"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python isn't installed or isn't on PATH." -ForegroundColor Red
    Write-Host "Install Python 3.10+ from https://python.org, then re-run this script." -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Path $venvPython)) {
    Write-Host "First run: setting up a virtual environment and installing dependencies..." -ForegroundColor DarkGray
    python -m venv $venv
    & $venvPython -m pip install --upgrade pip --quiet
    & $venvPython -m pip install -r (Join-Path $app "requirements.txt") --quiet
}

Push-Location $app
try {
    & $venvPython webapp.py @args
} finally {
    Pop-Location
}
