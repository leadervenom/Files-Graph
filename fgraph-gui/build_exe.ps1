<#
.SYNOPSIS
    Builds fgraph-gui.exe -- a single standalone executable for end users who
    just want to double-click and go, with no Python or git required on their
    machine.

.DESCRIPTION
    For developers only. Uses the same .venv as fgraph-gui.ps1, adds PyInstaller
    to it, and bundles webapp.py + the web/ assets into one exe under dist/.
    The WebView2 Runtime is still handled automatically at first launch by the
    exe itself (see _ensure_webview2 in webapp.py) -- nothing else to bundle.

.EXAMPLE
    .\build_exe.ps1
#>

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$venv = Join-Path $root ".venv"
$venvPython = Join-Path $venv "Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "Setting up virtual environment and installing dependencies..." -ForegroundColor DarkGray
    python -m venv $venv
    & $venvPython -m pip install --upgrade pip --quiet
    & $venvPython -m pip install -r (Join-Path $root "requirements.txt") --quiet
}

& $venvPython -m pip install --upgrade pyinstaller --quiet

Push-Location $root
try {
    & $venvPython -m PyInstaller `
        --name fgraph-gui `
        --onefile `
        --windowed `
        --icon "$(Join-Path $root 'icon.ico')" `
        --version-file "$(Join-Path $root 'version_info.txt')" `
        --add-data "$(Join-Path $root 'web');web" `
        --distpath dist `
        --workpath build `
        --specpath build `
        --noconfirm `
        webapp.py

    if ($LASTEXITCODE -ne 0) {
        Write-Host "Build failed -- see errors above." -ForegroundColor Red
        exit $LASTEXITCODE
    }

    $repoRoot = Split-Path -Parent $root
    Copy-Item (Join-Path $root "dist\fgraph-gui.exe") (Join-Path $repoRoot "fgraph-gui.exe") -Force

    Write-Host ""
    Write-Host "Built and copied to repo root: fgraph-gui.exe -- committed there so a plain clone can just double-click it, no build step needed." -ForegroundColor Green
} finally {
    Pop-Location
}
