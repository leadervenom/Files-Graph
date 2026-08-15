# Installation guide

fgraph ships two apps — `fgraph-gui` (desktop) and `fgraph-terminal` (terminal). Pick whichever you want; they're independent and you don't need both.

## Option 1: Installer (recommended for most people)

1. Go to the [Releases page](https://github.com/leadervenom/Files-Graph/releases).
2. Download `fgraph-gui-setup.exe` from the latest release.
3. Double-click it and click through the wizard (Next → Next → Install).
4. Launch fgraph from the Start Menu or the desktop shortcut it creates.

This installs a proper Start Menu entry and an uninstaller listed in Windows Settings → Apps. On first launch, if the Microsoft Edge WebView2 Runtime isn't already on your machine, it installs silently in the background — no extra prompts, no action needed from you.

To uninstall: Windows Settings → Apps → fgraph → Uninstall.

## Option 2: Portable exe (no installation)

1. Go to the [Releases page](https://github.com/leadervenom/Files-Graph/releases) and download `fgraph-gui.exe`, **or** clone the repo — it's committed at the root:
   ```powershell
   git clone https://github.com/leadervenom/Files-Graph.git
   ```
2. Double-click `fgraph-gui.exe`.

Nothing is written to your system outside the app's own data — no registry entries, no Start Menu shortcut. Delete the exe to remove it completely.

## Option 3: Run from source (developers)

Requires [Python 3.10+](https://python.org) for `fgraph-gui`, or the [Rust toolchain](https://rustup.rs) for `fgraph-terminal`.

```powershell
git clone https://github.com/leadervenom/Files-Graph.git
cd Files-Graph

# Terminal version — compiles the Rust binary on first run
.\fgraph-terminal.ps1

# Desktop version — sets up a Python venv and installs deps on first run
.\fgraph-gui.ps1
```

Both launchers set themselves up automatically the first time; every run after is instant. They're plain PowerShell scripts — if double-clicking doesn't launch them, open PowerShell in the repo folder and run `.\fgraph-terminal.ps1` or `.\fgraph-gui.ps1` directly.

## Requirements

- Windows 10 or 11 (fgraph is Windows-only)
- `fgraph-gui` needs the Microsoft Edge WebView2 Runtime — present by default on Windows 11 and most up-to-date Windows 10 machines; installed automatically and silently if missing, regardless of which distribution above you use
- Building from source additionally needs Python 3.10+ (`fgraph-gui`) or the Rust toolchain (`fgraph-terminal`) — the installer and portable exe need neither

## Troubleshooting

**"Windows protected your PC" SmartScreen prompt** — this shows up for installers/exes without an expensive code-signing certificate. Click "More info" → "Run anyway". This is expected for an independently published tool and doesn't indicate a problem with the download.

**Double-clicking a `.ps1` launcher does nothing / opens a text editor** — PowerShell scripts don't always have a default double-click action. Open PowerShell in the repo folder and run it directly, e.g. `.\fgraph-gui.ps1`.

**PowerShell refuses to run the script (execution policy error)** — run PowerShell as your normal user (not elevated) and try:
```powershell
powershell -ExecutionPolicy Bypass -File .\fgraph-gui.ps1
```

**The app can't see a WebView2 install / GUI window is blank** — make sure you're online for the first launch so the WebView2 Runtime can install; after that, `fgraph-gui` runs fully offline.

**Building `fgraph-terminal` fails** — confirm `rustup show` reports a working stable toolchain; reinstall via [rustup.rs](https://rustup.rs) if not.

For anything else, please [open an issue](https://github.com/leadervenom/Files-Graph/issues) — see [CONTRIBUTING.md](CONTRIBUTING.md) for what to include.

## Building the distributables yourself

See the "Building the distributables" section of [README.md](README.md#building-the-distributables) — you only need this if you're packaging a release, not to just run the app.
