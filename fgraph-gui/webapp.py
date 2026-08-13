"""fgraph-web: a "living", Obsidian-style 3D file graph in a native desktop window.

Physics (force-directed layout, draggable/springy nodes, flowing link particles)
comes from the 3d-force-graph JS library rendered inside a pywebview window --
VTK/matplotlib-style static 3D can't produce that organic, self-organizing feel,
a real physics simulation can. Python only scans the filesystem and hands JSON
to the page; pywebview's js_api bridges JS calls back to Python for anything
that needs real OS access (folder picker, opening files).
"""
from __future__ import annotations

import ctypes
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import urllib.request
import winreg
from pathlib import Path

import webview

# The evergreen bootstrapper always resolves to the current WebView2 Runtime release.
WEBVIEW2_BOOTSTRAPPER_URL = "https://go.microsoft.com/fwlink/p/?LinkId=2124703"
WEBVIEW2_CLIENT_ID = "{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"


def _resource_dir() -> Path:
    """Directory to load bundled assets (web/) from -- a PyInstaller onefile exe
    unpacks everything into a temp dir exposed as sys._MEIPASS at runtime; running
    from source, it's just this file's own folder."""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS"))
    return Path(__file__).parent


def _webview2_installed() -> bool:
    for hive, subkey in (
        (winreg.HKEY_LOCAL_MACHINE, rf"SOFTWARE\Microsoft\EdgeUpdate\Clients\{WEBVIEW2_CLIENT_ID}"),
        (winreg.HKEY_LOCAL_MACHINE, rf"SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{WEBVIEW2_CLIENT_ID}"),
        (winreg.HKEY_CURRENT_USER, rf"SOFTWARE\Microsoft\EdgeUpdate\Clients\{WEBVIEW2_CLIENT_ID}"),
    ):
        try:
            with winreg.OpenKey(hive, subkey) as key:
                pv, _ = winreg.QueryValueEx(key, "pv")
                if pv and pv != "0.0.0.0":
                    return True
        except OSError:
            continue
    return False


def _ensure_webview2() -> None:
    """A non-developer double-clicking the exe has never heard of WebView2 and can't
    be handed a manual install step -- so on the (usually rare) machine that lacks it,
    fetch and silently run Microsoft's own bootstrapper before the window ever opens."""
    if _webview2_installed():
        return
    bootstrapper = Path(tempfile.gettempdir()) / "MicrosoftEdgeWebview2Setup.exe"
    try:
        urllib.request.urlretrieve(WEBVIEW2_BOOTSTRAPPER_URL, bootstrapper)
        subprocess.run([str(bootstrapper), "/silent", "/install"], check=False)
    finally:
        bootstrapper.unlink(missing_ok=True)
    if not _webview2_installed():
        ctypes.windll.user32.MessageBoxW(
            0,
            "fgraph needs the Microsoft Edge WebView2 Runtime, and the automatic "
            "install didn't complete (likely no internet access). Install it from "
            "https://developer.microsoft.com/microsoft-edge/webview2/ and try again.",
            "fgraph - setup required",
            0x10,  # MB_ICONERROR
        )
        sys.exit(1)

from colors import CATEGORY_COLORS, DEPTH_COLORS, human_size, node_color, node_radius, rgb_hex
from scan import list_children, scan as scan_dir

# Shallow by design: like an open-world game, only the area you're actually looking
# at loads in detail. Depth-truncated folders come back marked "expandable" and load
# their contents on demand (expand_folder) instead of everything scanning up front.
DEFAULT_DEPTH = 2
DEFAULT_ENTRIES_CAP = 8000

# Windows profile folders that show up under C:\Users but aren't a real person's
# account -- excluded from the account picker so the list stays short and calm.
NON_USER_PROFILES = {"default", "default user", "public", "all users", "wdagutilityaccount", "defaultuser0"}


def _force_dialog_foreground(titles: tuple[str, ...], timeout: float = 3.0) -> None:
    """Background watcher: polls for a top-level window matching one of `titles` and
    forces it to the foreground the instant it appears, so a modal dialog opened from
    a non-UI thread doesn't get silently stranded behind the main window."""
    user32 = ctypes.windll.user32
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    def watch():
        deadline = time.time() + timeout
        while time.time() < deadline:
            found = []

            def enum_cb(hwnd, _lparam):
                if user32.IsWindowVisible(hwnd):
                    length = user32.GetWindowTextLengthW(hwnd)
                    if length:
                        buf = ctypes.create_unicode_buffer(length + 1)
                        user32.GetWindowTextW(hwnd, buf, length + 1)
                        if buf.value in titles:
                            found.append(hwnd)
                return True

            user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
            if found:
                user32.SetForegroundWindow(found[0])
                user32.BringWindowToTop(found[0])
                return
            time.sleep(0.1)

    threading.Thread(target=watch, daemon=True).start()


class Api:
    def users_root(self) -> str:
        # Path("C:") / "Users" resolves to the unanchored "C:Users", not "C:\Users" --
        # a trailing separator on the drive is required to anchor it to the root.
        drive = os.environ.get("SystemDrive", "C:") + os.sep
        return str(Path(drive) / "Users")

    def list_users(self) -> dict:
        root = Path(self.users_root())
        current = Path.home().name
        users = []
        try:
            for entry in sorted(os.scandir(root), key=lambda e: e.name.lower()):
                if not entry.is_dir(follow_symlinks=False):
                    continue
                if entry.name.lower() in NON_USER_PROFILES or entry.name.startswith("."):
                    continue
                users.append({"name": entry.name, "path": str(Path(entry.path)), "isCurrentUser": entry.name == current})
        except OSError as exc:
            return {"root": str(root), "users": [], "error": str(exc)}
        return {"root": str(root), "users": users}

    def list_subfolders(self, path: str) -> dict:
        """Top-level folders inside a chosen user's account, for the picker's second step.

        Windows profiles carry legacy junctions (Application Data, Cookies, Local Settings,
        ...) that just alias real folders elsewhere -- is_junction() (Python 3.12+) filters
        those out so the list stays to real, distinct folders instead of a noisy duplicate-y one.
        """
        root = Path(str(path))
        folders = []
        try:
            for entry in sorted(os.scandir(root), key=lambda e: e.name.lower()):
                if not entry.is_dir(follow_symlinks=False) or entry.name.startswith("."):
                    continue
                try:
                    if entry.is_junction():
                        continue
                except OSError:
                    continue
                folders.append({"name": entry.name, "path": str(Path(entry.path))})
        except OSError as exc:
            return {"root": str(root), "folders": [], "error": str(exc)}
        return {"root": str(root), "folders": folders}

    def client_error(self, message: str) -> None:
        """JS-side errors get reported here (see index.html's window.onerror hook) so
        they show up in this process's console instead of vanishing silently in the window."""
        print(f"[JS ERROR] {message}", flush=True)

    def default_depth(self) -> int:
        return DEFAULT_DEPTH

    def legend(self) -> list[dict]:
        items = [{"label": label, "color": rgb_hex(rgb)} for label, rgb in CATEGORY_COLORS.items()]
        items.append({"label": "folder (color = depth)", "color": rgb_hex(DEPTH_COLORS[1])})
        return items

    def browse_folder(self) -> str | None:
        # The native folder dialog reliably opens (confirmed via window enumeration)
        # but Windows doesn't grant it foreground focus, so it silently sits behind
        # the app window -- indistinguishable from "nothing happened" to the user.
        # Poll for it by title and force it forward the moment it appears.
        _force_dialog_foreground(("Select Folder", "Browse For Folder"))
        window = webview.windows[0]
        result = window.create_file_dialog(webview.FOLDER_DIALOG)
        if not result:
            return None
        return result[0]

    def open_path(self, path: str) -> dict:
        try:
            os.startfile(path)  # noqa: S606 - intentional, user-triggered, Windows only
            return {"ok": True}
        except OSError as exc:
            return {"ok": False, "error": str(exc)}

    def scan(self, path: str, max_depth) -> dict:
        try:
            depth = max(1, int(max_depth))
        except (TypeError, ValueError):
            depth = DEFAULT_DEPTH

        window = webview.windows[0] if webview.windows else None

        def report_progress(count, cap, current_dir):
            if window is None:
                return
            try:
                window.evaluate_js(
                    f"window.__scanProgress && window.__scanProgress({count}, {cap}, {json.dumps(current_dir)})"
                )
            except Exception:
                pass  # progress UI is best-effort; never let it break the scan

        try:
            root = Path(str(path)).expanduser()
            if not root.exists():
                return {"error": f"Path not found: {root}", "nodes": [], "links": []}
            graph = scan_dir(
                root, max_depth=depth, max_entries=DEFAULT_ENTRIES_CAP, on_progress=report_progress
            )
        except Exception as exc:  # surface scan failures to the UI instead of crashing the window
            traceback.print_exc()
            return {"error": str(exc), "nodes": [], "links": []}

        nodes = []
        for node in graph.nodes:
            nodes.append(
                {
                    "id": str(node.path),
                    "name": node.name,
                    "path": str(node.path),
                    "isDir": node.is_dir,
                    "size": node.size,
                    "sizeHuman": human_size(node.size),
                    "depth": node.depth,
                    "leafCount": node.leaf_count,
                    "color": rgb_hex(node_color(node.is_dir, node.depth, node.name)),
                    "val": node_radius(node.is_dir, node.size, node.leaf_count),
                    "expandable": node.truncated,
                }
            )

        links = [
            {"source": str(graph.nodes[node.parent].path), "target": str(node.path)}
            for node in graph.nodes
            if node.parent is not None
        ]

        return {"nodes": nodes, "links": links, "root": str(root)}

    def expand_folder(self, path: str, depth) -> dict:
        """Single-level listing of `path`'s children, merged into the live graph by the
        JS side on double-click -- the open-world "load only what you drill into" step."""
        try:
            parent_depth = int(depth)
        except (TypeError, ValueError):
            parent_depth = 0

        try:
            dir_path = Path(str(path))
            if not dir_path.exists():
                return {"path": str(dir_path), "children": [], "error": f"Path not found: {dir_path}"}
            entries = list_children(dir_path)
        except Exception as exc:  # keep expansion failures from crashing the window
            traceback.print_exc()
            return {"path": str(path), "children": [], "error": str(exc)}

        child_depth = parent_depth + 1
        children = []
        for entry in entries:
            children.append(
                {
                    "id": str(entry["path"]),
                    "name": entry["name"],
                    "path": str(entry["path"]),
                    "isDir": entry["is_dir"],
                    "size": entry["size"],
                    "sizeHuman": human_size(entry["size"]),
                    "depth": child_depth,
                    "leafCount": entry["child_count"] if entry["is_dir"] else 0,
                    "color": rgb_hex(node_color(entry["is_dir"], child_depth, entry["name"])),
                    "val": node_radius(entry["is_dir"], entry["size"], entry["child_count"]),
                    # Any subdirectory returned here is presumptively expandable until
                    # proven empty -- cheap and honest enough without another syscall.
                    "expandable": entry["is_dir"] and entry["child_count"] > 0,
                }
            )

        return {"path": str(dir_path), "children": children, "error": None}


def main():
    _ensure_webview2()
    api = Api()
    web_dir = _resource_dir() / "web"
    webview.create_window(
        "fgraph — living file graph",
        str(web_dir / "index.html"),
        js_api=api,
        width=1440,
        height=900,
        min_size=(900, 600),
        background_color="#05070d",
    )
    webview.start()


if __name__ == "__main__":
    main()
