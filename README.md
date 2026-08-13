# fgraph

Turn your real Windows file system into an explorable 3D graph. Instead of a nested list of folders, see your files as a living, spatial map — colored by type, sized by weight, navigable with just a mouse.

Two ways to run it, same idea, different feel:

| | `fgraph-terminal` | `fgraph-gui` |
|---|---|---|
| **Runs in** | your terminal | a native desktop window |
| **Look** | braille-rendered 3D wireframe | physics-driven, glowing, "living" graph |
| **Controls** | keyboard | mouse — drag to orbit, drag a node to pull it |
| **Best for** | terminal/power users, SSH sessions | everyone else |

No filesystem driver, no virtual drive, no writes — both just read your real folders and draw what's there.

## Quick start (just want to use it, not develop it)

```powershell
git clone https://github.com/leadervenom/Files-Graph.git
```

Then open the `Files-Graph` folder and double-click `fgraph-gui.exe`. That's it — no Python, no PowerShell, no build step. The exe is committed straight in the repo root, so cloning already gives you the finished app. First launch may take a couple seconds longer if it needs to silently install the Microsoft Edge WebView2 Runtime in the background (only on machines that don't already have it) — nothing to click through either way.

## Quick start (developers)

Clone the repo, then run one of the two launchers. Each one sets itself up automatically the first time (compiles the Rust binary / creates a Python virtual environment and installs dependencies) — nothing to configure by hand.

```powershell
git clone https://github.com/leadervenom/Files-Graph.git
cd Files-Graph

# Terminal version
.\fgraph-terminal.ps1

# Desktop version
.\fgraph-gui.ps1
```

That's it. First run takes a little longer (building/installing); every run after is instant.

> Both launchers are plain PowerShell scripts — if double-clicking doesn't work, open PowerShell in the repo folder and run `.\fgraph-terminal.ps1` or `.\fgraph-gui.ps1` directly.

### Rebuilding the standalone .exe

If you change `fgraph-gui`'s Python code, rebuild the committed exe so clones stay up to date. `fgraph-gui/build_exe.ps1` bundles it via PyInstaller and copies the result to the repo root as `fgraph-gui.exe`:

```powershell
cd fgraph-gui
.\build_exe.ps1
```

Commit the updated root `fgraph-gui.exe` along with your code changes.

## Requirements

- **Windows 10/11**
- **`fgraph-terminal`** needs the Rust toolchain — install via [rustup.rs](https://rustup.rs)
- **`fgraph-gui`** needs **Python 3.10+** — install from [python.org](https://python.org)

You only need the toolchain for whichever version you're using — you don't need Rust to run the desktop app, or Python to run the terminal one.

`fgraph-gui` also needs the Microsoft Edge WebView2 Runtime (present by default on Windows 11 and most up-to-date Windows 10 machines). If it's missing, both `fgraph-gui.ps1` and the standalone `.exe` download and install it silently on first run — no prompts, nothing to click through.

## `fgraph-gui` — the desktop app

```
.\fgraph-gui.ps1
```

Opens straight to an account picker: pick a Windows user account on the machine, then a folder inside it (or the whole account). The graph loads progressively — like an open-world game, only the area you're actually looking at renders in detail. Unexplored folders show up as a single dimmed "aggregate" node; double-click one to load its contents in place.

**Controls**
- Drag = orbit the camera
- Scroll = zoom
- Drag a node = pull it — it springs back into place under the other nodes' pull
- Click a node = select it (see its name/path/size in the sidebar)
- Double-click a folder = open it in the graph (load its contents)
- Double-click a file = open it on disk

The sidebar also has search, a legend, an "Open in Explorer" button, and a folder browser for scanning anywhere else on disk.

## `fgraph-terminal` — the terminal app

```
.\fgraph-terminal.ps1 [path] [max-depth]
```

Renders the same idea directly in your terminal using Unicode braille characters — no GUI, works over SSH, nothing to install beyond Rust. Defaults to your home folder at depth 6 if no arguments are given.

**Controls**
- Arrow keys / WASD = rotate camera
- `+` / `-` = zoom
- Tab / N / P = cycle node selection
- Enter / O = open the selected file/folder
- Space = toggle auto-rotate
- R = reset camera
- Q / Esc = quit

## How it works

Both apps scan a folder with the same shared rules — file-type category colors (code/docs/image/video/audio/archive/executable/data) and size-weighted node radius — so a file means the same thing visually no matter which version you're looking at. Everything is read-only: no filesystem driver, no writes, no virtual drive. `fgraph-gui` runs entirely offline too — its 3D rendering library and fonts are vendored locally, no CDN calls at runtime.

## Project structure

```
fgraph/            Rust terminal app (crossterm + braille rendering)
  src/
  Cargo.toml

fgraph-gui/         Python desktop app (pywebview + physics-based 3D graph)
  webapp.py          entry point / native-dialog + filesystem bridge
  scan.py            filesystem scanning
  colors.py          shared color/size rules
  web/               the actual UI (HTML/CSS/JS + vendored 3d-force-graph)
  build_exe.ps1      rebuilds the standalone exe (developers only)

fgraph-terminal.ps1  launcher for the terminal app
fgraph-gui.ps1       launcher for the desktop app (dev mode, needs Python)
fgraph-gui.exe       committed, standalone build of fgraph-gui -- double-click, needs nothing installed
```

## Development

Both apps have a `?mock=1` dev harness for `fgraph-gui`'s frontend — open `fgraph-gui/web/index.html` via a local static server with `?mock=1` in the URL to iterate on the UI in a regular browser without needing the desktop shell, and `&mockbig=1` to stress-test against a synthetic large tree.

## License

MIT — see [LICENSE](LICENSE).
