"""3D radial tree layout: same scheme as the terminal version's layout.rs.

Each node gets an angular slice proportional to its subtree size, radius
grows with depth, and elevation is nudged per-node (stable hash of the path)
so the tree blooms into a dome instead of sitting flat on one plane.
"""
from __future__ import annotations

import hashlib
import math

from scan import Graph

RADIUS_PER_DEPTH = 3.0


def _stable_unit(path) -> float:
    digest = hashlib.md5(str(path).encode("utf-8", "ignore")).digest()
    return int.from_bytes(digest[:4], "big") / 0xFFFFFFFF


def layout(graph: Graph) -> None:
    _assign(graph, graph.root, 0.0, math.tau, 0.0)


def _assign(graph: Graph, idx: int, angle_start: float, angle_end: float, elevation_bias: float):
    node = graph.nodes[idx]
    angle_mid = (angle_start + angle_end) * 0.5
    radius = node.depth * RADIUS_PER_DEPTH

    jitter = (_stable_unit(node.path) - 0.5) * 0.6
    elevation = max(-1.4, min(1.4, elevation_bias + jitter))
    polar = math.pi / 2 - elevation

    x = radius * math.sin(polar) * math.cos(angle_mid)
    y = radius * math.cos(polar)
    z = radius * math.sin(polar) * math.sin(angle_mid)
    node.pos = (x, y, z)

    children = node.children
    if not children:
        return

    total_leaves = sum(graph.nodes[c].leaf_count for c in children) or 1
    cursor = angle_start
    span = angle_end - angle_start
    for c in children:
        share = graph.nodes[c].leaf_count / total_leaves
        child_start = cursor
        child_end = cursor + span * share
        child_bias = elevation_bias + (_stable_unit(graph.nodes[c].path) - 0.5) * 0.5
        _assign(graph, c, child_start, child_end, child_bias)
        cursor = child_end
