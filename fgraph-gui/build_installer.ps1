<#
.SYNOPSIS
    Builds fgraph-gui-setup.exe -- a traditional Windows installer wizard
    (Next > Next > Install, Start Menu/Desktop shortcuts, an "Apps & features"
    entry with a real uninstaller) wrapping the portable fgraph-gui.exe.

.DESCRIPTION
    For developers only. Requires Inno Setup 6 (https://jrsoftware.org/isinfo.php,
    or `winget install JRSoftware.InnoSetup`). Rebuilds fgraph-gui.exe first via
    build_exe.ps1 so the installer always packages the current code, then
    compiles installer.iss with ISCC.

.EXAMPLE
    .\build_installer.ps1
#>

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

& (Join-Path $root "build_exe.ps1")

$iscc = Get-Command ISCC.exe -ErrorAction SilentlyContinue
if (-not $iscc) {
    $candidates = @(
        "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
    )
    $found = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
    if (-not $found) {
        Write-Host "Inno Setup isn't installed." -ForegroundColor Red
        Write-Host "Install it with: winget install JRSoftware.InnoSetup" -ForegroundColor Yellow
        exit 1
    }
    $iscc = $found
} else {
    $iscc = $iscc.Source
}

& $iscc (Join-Path $root "installer.iss")
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installer build failed -- see errors above." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Built fgraph-gui\installer_output\fgraph-gui-setup.exe -- attach this to a GitHub Release for a traditional install experience." -ForegroundColor Green
