"""Color and size rules shared by the 3D view and the legend.

Kept identical in spirit to the terminal version's category_color/size_radius
so both tools "mean" the same thing when they show the same colors.
"""
from __future__ import annotations

DEPTH_COLORS = [
    (80, 220, 220),   # cyan
    (100, 220, 120),  # green
    (230, 210, 90),   # yellow
    (210, 110, 220),  # magenta
    (110, 150, 230),  # blue
    (230, 230, 230),  # white
]

CATEGORY_COLORS = {
    "code": (90, 220, 130),
    "docs": (230, 220, 130),
    "image": (230, 120, 220),
    "video": (120, 180, 230),
    "audio": (230, 160, 90),
    "archive": (190, 90, 90),
    "executable": (255, 90, 90),
    "data": (120, 220, 220),
    "other": (150, 150, 150),
}

_EXT_TO_CATEGORY = {
    **{e: "code" for e in (
        "rs", "py", "js", "ts", "tsx", "jsx", "c", "cpp", "h", "hpp",
        "java", "go", "rb", "php", "cs", "swift", "kt", "sh", "ps1",
    )},
    **{e: "docs" for e in ("md", "txt", "pdf", "doc", "docx", "rtf", "odt")},
    **{e: "image" for e in ("png", "jpg", "jpeg", "gif", "svg", "bmp", "webp", "ico")},
    **{e: "video" for e in ("mp4", "mov", "avi", "mkv", "webm")},
    **{e: "audio" for e in ("mp3", "wav", "flac", "ogg", "m4a")},
    **{e: "archive" for e in ("zip", "rar", "7z", "tar", "gz", "bz2")},
    **{e: "executable" for e in ("exe", "dll", "msi", "bat", "sys")},
    **{e: "data" for e in ("json", "yaml", "yml", "toml", "xml", "csv", "ini", "cfg")},
}

SELECTED_COLOR = (255, 60, 60)
EDGE_COLOR = (90, 90, 100)


def category_of(name: str) -> str:
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    return _EXT_TO_CATEGORY.get(ext, "other")


def node_color(is_dir: bool, depth: int, name: str) -> tuple[int, int, int]:
    if is_dir:
        return DEPTH_COLORS[depth % len(DEPTH_COLORS)]
    return CATEGORY_COLORS[category_of(name)]


def node_radius(is_dir: bool, size: int, leaf_count: int) -> float:
    if is_dir:
        if leaf_count <= 1:
            return 0.35
        if leaf_count <= 10:
            return 0.55
        if leaf_count <= 50:
            return 0.8
        return 1.1
    if size <= 10_240:
        return 0.25
    if size <= 102_400:
        return 0.4
    if size <= 1_048_576:
        return 0.6
    return 0.9


def rgb_hex(rgb: tuple[int, int, int]) -> str:
    return "#%02x%02x%02x" % rgb


def human_size(num: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if num < 1024.0:
            return f"{num:.1f} {unit}"
        num /= 1024.0
    return f"{num:.1f} PB"
