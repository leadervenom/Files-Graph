"""Scans a directory tree into a flat list of nodes with parent/child links.

Mirrors the layout of the terminal (Rust) version so both tools produce the
same shape of graph, just consumed differently.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Node:
    name: str
    path: Path
    is_dir: bool
    size: int
    depth: int
    parent: int | None
    children: list[int] = field(default_factory=list)
    leaf_count: int = 0
    pos: tuple[float, float, float] = (0.0, 0.0, 0.0)
    truncated: bool = False


class Graph:
    def __init__(self):
        self.nodes: list[Node] = []
        self.root: int = 0


def scan(root_path: Path, max_depth: int = 6, max_entries: int = 8000, on_progress=None) -> Graph:
    """Scans root_path into a Graph. If given, on_progress(count, cap, current_dir_path)
    is called once per directory visited, throttled to roughly every 20 items, so a caller
    (the desktop app) can show a live, honest percentage instead of an indefinite spinner.
    """
    graph = Graph()
    graph.nodes.append(
        Node(
            name=root_path.name or str(root_path),
            path=root_path,
            is_dir=True,
            size=0,
            depth=0,
            parent=None,
        )
    )
    last_reported = 0

    def report(current_dir_path):
        nonlocal last_reported
        count = len(graph.nodes)
        if on_progress and (count - last_reported >= 20 or count >= max_entries):
            last_reported = count
            on_progress(count, max_entries, current_dir_path)

    def walk(idx: int):
        if len(graph.nodes) >= max_entries:
            return
        node = graph.nodes[idx]
        if node.depth >= max_depth:
            # Depth cap cut this node's subtree off -- mark it so the UI can offer
            # click-to-expand instead of silently pretending it has no contents.
            try:
                with os.scandir(node.path) as it:
                    node.truncated = any(True for _ in it)
            except OSError:
                pass
            return
        try:
            entries = list(os.scandir(node.path))
        except (PermissionError, FileNotFoundError, NotADirectoryError, OSError):
            return
        report(str(node.path))

        for entry in entries:
            if len(graph.nodes) >= max_entries:
                break
            try:
                is_dir = entry.is_dir(follow_symlinks=False)
                size = 0 if is_dir else entry.stat(follow_symlinks=False).st_size
            except OSError:
                continue

            child_idx = len(graph.nodes)
            graph.nodes.append(
                Node(
                    name=entry.name,
                    path=Path(entry.path),
                    is_dir=is_dir,
                    size=size,
                    depth=node.depth + 1,
                    parent=idx,
                )
            )
            node.children.append(child_idx)
            if is_dir:
                walk(child_idx)

    walk(0)
    if on_progress:
        on_progress(len(graph.nodes), max_entries, None)
    _compute_leaf_counts(graph, 0)
    return graph


def list_children(dir_path: Path) -> list[dict]:
    """Single-level, non-recursive listing of dir_path's immediate children, used for
    on-demand graph expansion (open-world style: only the folder you click into loads).

    child_count for subdirectories is itself a cheap single-level count, not a
    recursive true count -- same cost class as listing one folder, not a subtree.
    """
    children: list[dict] = []
    try:
        entries = list(os.scandir(dir_path))
    except (PermissionError, FileNotFoundError, NotADirectoryError, OSError):
        return children

    for entry in entries:
        try:
            is_dir = entry.is_dir(follow_symlinks=False)
            size = 0 if is_dir else entry.stat(follow_symlinks=False).st_size
        except OSError:
            continue

        child_count = 0
        if is_dir:
            try:
                with os.scandir(entry.path) as sub:
                    child_count = sum(1 for _ in sub)
            except OSError:
                child_count = 0

        children.append(
            {
                "name": entry.name,
                "path": Path(entry.path),
                "is_dir": is_dir,
                "size": size,
                "child_count": child_count,
            }
        )
    return children


def _compute_leaf_counts(graph: Graph, idx: int) -> int:
    node = graph.nodes[idx]
    if not node.children:
        node.leaf_count = 1
        return 1
    total = sum(_compute_leaf_counts(graph, c) for c in node.children)
    node.leaf_count = total
    return total
