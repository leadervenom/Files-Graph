<#
.SYNOPSIS
    Launches fgraph -- the terminal (braille-rendered 3D) file graph viewer.

.DESCRIPTION
    First run compiles the Rust binary (needs cargo/rustup); every run after
    that is instant since cargo no-ops when nothing changed. Any arguments you
    pass are forwarded straight to the binary: a folder path and optionally a
    max scan depth.

.EXAMPLE
    .\fgraph-terminal.ps1
    .\fgraph-terminal.ps1 "C:\Users\me\Documents" 6
#>

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$crate = Join-Path $root "fgraph"

if (-not (Get-Command cargo -ErrorAction SilentlyContinue)) {
    Write-Host "Rust's cargo isn't installed or isn't on PATH." -ForegroundColor Red
    Write-Host "Install it from https://rustup.rs, then re-run this script." -ForegroundColor Yellow
    exit 1
}

Push-Location $crate
try {
    Write-Host "Building fgraph (first run only -- cached after)..." -ForegroundColor DarkGray
    cargo build --release --quiet
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Build failed -- see errors above." -ForegroundColor Red
        exit $LASTEXITCODE
    }
} finally {
    Pop-Location
}

& (Join-Path $crate "target\release\fgraph.exe") @args
