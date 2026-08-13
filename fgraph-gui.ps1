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

function Test-WebView2Installed {
    $clientId = "{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
    $paths = @(
        "HKLM:\SOFTWARE\Microsoft\EdgeUpdate\Clients\$clientId",
        "HKLM:\SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\$clientId",
        "HKCU:\SOFTWARE\Microsoft\EdgeUpdate\Clients\$clientId"
    )
    foreach ($path in $paths) {
        if (Test-Path $path) {
            $pv = (Get-ItemProperty -Path $path -Name "pv" -ErrorAction SilentlyContinue).pv
            if ($pv -and $pv -ne "0.0.0.0") { return $true }
        }
    }
    return $false
}

function Install-WebView2Runtime {
    Write-Host "Microsoft Edge WebView2 Runtime not found -- installing it silently (needed once, ~2MB downloader)..." -ForegroundColor DarkGray
    $bootstrapper = Join-Path $env:TEMP "MicrosoftEdgeWebview2Setup.exe"
    try {
        Invoke-WebRequest -Uri "https://go.microsoft.com/fwlink/p/?LinkId=2124703" -OutFile $bootstrapper -UseBasicParsing
        Start-Process -FilePath $bootstrapper -ArgumentList "/silent", "/install" -Wait
    } finally {
        Remove-Item $bootstrapper -ErrorAction SilentlyContinue
    }
    if (-not (Test-WebView2Installed)) {
        Write-Host "Automatic WebView2 install didn't complete. Install it manually from https://developer.microsoft.com/microsoft-edge/webview2/ and re-run this script." -ForegroundColor Red
        exit 1
    }
}

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

if (-not (Test-WebView2Installed)) {
    Install-WebView2Runtime
}

Push-Location $app
try {
    & $venvPython webapp.py @args
} finally {
    Pop-Location
}
