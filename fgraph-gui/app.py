"""fgraph-gui: a friendlier, mouse-driven 3D file-system graph viewer.

Desktop window (PySide6 + PyVista/VTK) that scans a real folder and shows it
as a 3D graph: drag to orbit, scroll to zoom, click a node to inspect it,
double-click (or the Open button) to open it in Explorer. No keyboard-only
controls, no terminal required -- built for people who aren't going to
memorize shortcuts.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pyvista as pv
from pyvistaqt import QtInteractor
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from colors import CATEGORY_COLORS, EDGE_COLOR, SELECTED_COLOR, human_size, node_color, node_radius
from layout import layout as layout_graph
from scan import scan

DEFAULT_DEPTH = 6
DEFAULT_ENTRIES_CAP = 8000


class LegendSwatch(QWidget):
    def __init__(self, rgb: tuple[int, int, int], label: str):
        super().__init__()
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)
        swatch = QFrame()
        swatch.setFixedSize(12, 12)
        swatch.setStyleSheet(
            f"background-color: rgb({rgb[0]},{rgb[1]},{rgb[2]}); border-radius: 3px;"
        )
        row.addWidget(swatch)
        row.addWidget(QLabel(label))
        row.addStretch(1)


class MainWindow(QMainWindow):
    def __init__(self, start_path: Path):
        super().__init__()
        self.setWindowTitle("fgraph — 3D file explorer")
        self.resize(1280, 800)

        self.graph = None
        self.positions: np.ndarray | None = None
        self.selected_idx: int | None = None
        self.glyph_actor = None
        self.edge_actor = None

        splitter = QSplitter(Qt.Horizontal)
        self.setCentralWidget(splitter)

        splitter.addWidget(self._build_sidebar(start_path))

        self.plotter = QtInteractor(splitter)
        self.plotter.set_background("black")
        splitter.addWidget(self.plotter)
        splitter.setSizes([320, 960])

        self.plotter.enable_point_picking(
            callback=self._on_pick,
            show_message=False,
            left_clicking=True,
            show_point=False,
        )

        self._rescan()

    # ---------------------------------------------------------- sidebar --

    def _build_sidebar(self, start_path: Path) -> QWidget:
        panel = QWidget()
        panel.setMinimumWidth(300)
        panel.setMaximumWidth(420)
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)

        layout.addWidget(QLabel("<b>Folder</b>"))
        path_row = QHBoxLayout()
        self.path_edit = QLineEdit(str(start_path))
        browse_btn = QPushButton("Browse…")
        browse_btn.clicked.connect(self._browse)
        path_row.addWidget(self.path_edit)
        path_row.addWidget(browse_btn)
        layout.addLayout(path_row)

        depth_row = QHBoxLayout()
        depth_row.addWidget(QLabel("Max depth"))
        self.depth_spin = QSpinBox()
        self.depth_spin.setRange(1, 12)
        self.depth_spin.setValue(DEFAULT_DEPTH)
        depth_row.addWidget(self.depth_spin)
        depth_row.addStretch(1)
        layout.addLayout(depth_row)

        scan_btn = QPushButton("Scan && Visualize")
        scan_btn.clicked.connect(self._rescan)
        layout.addWidget(scan_btn)

        layout.addSpacing(6)
        layout.addWidget(QLabel("<b>Search</b>"))
        search_row = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("file or folder name…")
        self.search_edit.returnPressed.connect(self._search)
        search_btn = QPushButton("Find")
        search_btn.clicked.connect(self._search)
        search_row.addWidget(self.search_edit)
        search_row.addWidget(search_btn)
        layout.addLayout(search_row)
        self.search_status = QLabel("")
        self.search_status.setWordWrap(True)
        layout.addWidget(self.search_status)

        layout.addSpacing(6)
        layout.addWidget(QLabel("<b>Selected item</b>"))
        self.info_name = QLabel("—")
        self.info_name.setWordWrap(True)
        self.info_name.setStyleSheet("font-weight: bold;")
        self.info_path = QLabel("Click a node in the 3D view to inspect it.")
        self.info_path.setWordWrap(True)
        self.info_meta = QLabel("")
        self.info_meta.setWordWrap(True)
        layout.addWidget(self.info_name)
        layout.addWidget(self.info_path)
        layout.addWidget(self.info_meta)

        open_btn = QPushButton("Open in Explorer")
        open_btn.clicked.connect(self._open_selected)
        layout.addWidget(open_btn)

        layout.addSpacing(10)
        reset_btn = QPushButton("Reset View")
        reset_btn.clicked.connect(lambda: self.plotter.reset_camera())
        layout.addWidget(reset_btn)

        layout.addSpacing(10)
        layout.addWidget(QLabel("<b>Legend</b>"))
        for label, rgb in CATEGORY_COLORS.items():
            layout.addWidget(LegendSwatch(rgb, label))
        layout.addWidget(LegendSwatch(SELECTED_COLOR, "selected"))
        layout.addWidget(
            QLabel("Bigger dot = bigger file or fuller folder. Folders are colored by depth.")
        )
        hint = QLabel(
            "Drag = orbit · Scroll = zoom · Right-drag = pan · Click a node = select it"
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: gray;")
        layout.addWidget(hint)

        layout.addStretch(1)
        return panel

    # -------------------------------------------------------- scanning --

    def _browse(self):
        chosen = QFileDialog.getExistingDirectory(self, "Choose a folder", self.path_edit.text())
        if chosen:
            self.path_edit.setText(chosen)
            self._rescan()

    def _rescan(self):
        root = Path(self.path_edit.text()).expanduser()
        if not root.exists():
            self.info_path.setText(f"Path not found: {root}")
            return

        self.graph = scan(root, max_depth=self.depth_spin.value(), max_entries=DEFAULT_ENTRIES_CAP)
        layout_graph(self.graph)
        self.selected_idx = None
        self._render_graph()
        self.info_name.setText(root.name or str(root))
        self.info_path.setText(str(root))
        self.info_meta.setText(f"{len(self.graph.nodes)} items scanned")

    # -------------------------------------------------------- rendering --

    def _render_graph(self):
        graph = self.graph
        positions = np.array([node.pos for node in graph.nodes], dtype=np.float32)
        colors = np.array(
            [node_color(node.is_dir, node.depth, node.name) for node in graph.nodes],
            dtype=np.uint8,
        )
        radii = np.array(
            [node_radius(node.is_dir, node.size, node.leaf_count) for node in graph.nodes],
            dtype=np.float32,
        )
        self.positions = positions

        self.plotter.clear_actors()

        # Edges: one polyline segment per parent-child relationship.
        edge_pairs = [(node.parent, i) for i, node in enumerate(graph.nodes) if node.parent is not None]
        if edge_pairs:
            lines_arr = np.hstack([[2, a, b] for a, b in edge_pairs])
            edge_mesh = pv.PolyData(positions, lines=lines_arr)
            self.edge_actor = self.plotter.add_mesh(
                edge_mesh, color=EDGE_COLOR, opacity=0.35, line_width=1, pickable=False
            )

        # Visible + pickable nodes: sphere glyphs scaled per-node so size communicates weight.
        # Picking snaps to a point on a sphere's surface; since node spacing is much larger
        # than sphere radius, "nearest original node position" still resolves unambiguously.
        cloud = pv.PolyData(positions)
        cloud["radius"] = radii
        cloud["rgb"] = colors
        sphere = pv.Sphere(theta_resolution=10, phi_resolution=10)
        glyphs = cloud.glyph(scale="radius", geom=sphere, orient=False)
        self.glyph_actor = self.plotter.add_mesh(
            glyphs, scalars="rgb", rgb=True, pickable=True, smooth_shading=True
        )

        self.plotter.reset_camera()
        self._refresh_selection_visual()

    def _refresh_selection_visual(self):
        """Recolors the glyph mesh so the selected node is highlighted, without a full rebuild."""
        if self.glyph_actor is None or self.graph is None:
            return
        n = len(self.graph.nodes)
        colors = np.array(
            [node_color(node.is_dir, node.depth, node.name) for node in self.graph.nodes],
            dtype=np.uint8,
        )
        if self.selected_idx is not None:
            colors[self.selected_idx] = SELECTED_COLOR
        radii = np.array(
            [node_radius(node.is_dir, node.size, node.leaf_count) for node in self.graph.nodes],
            dtype=np.float32,
        )
        if self.selected_idx is not None:
            radii[self.selected_idx] *= 1.6

        cloud = pv.PolyData(self.positions)
        cloud["radius"] = radii
        cloud["rgb"] = colors
        sphere = pv.Sphere(theta_resolution=10, phi_resolution=10)
        glyphs = cloud.glyph(scale="radius", geom=sphere, orient=False)
        self.plotter.remove_actor(self.glyph_actor)
        self.glyph_actor = self.plotter.add_mesh(
            glyphs, scalars="rgb", rgb=True, pickable=True, smooth_shading=True
        )
        self.plotter.render()

    # ----------------------------------------------------------- picking --

    def _on_pick(self, point):
        if point is None or self.positions is None:
            return
        deltas = self.positions - np.asarray(point, dtype=np.float32)
        nearest = int(np.argmin(np.einsum("ij,ij->i", deltas, deltas)))
        self._select(nearest)

    def _select(self, idx: int):
        self.selected_idx = idx
        node = self.graph.nodes[idx]
        kind = "Folder" if node.is_dir else "File"
        self.info_name.setText(f"[{kind}] {node.name}")
        self.info_path.setText(str(node.path))
        if node.is_dir:
            self.info_meta.setText(f"{node.leaf_count} items inside")
        else:
            self.info_meta.setText(human_size(node.size))
        self._refresh_selection_visual()

    def _open_selected(self):
        if self.selected_idx is None:
            return
        path = self.graph.nodes[self.selected_idx].path
        try:
            os.startfile(path)  # noqa: S606 - intentional, user-triggered, Windows only
        except OSError as exc:
            self.info_meta.setText(f"Couldn't open: {exc}")

    # ------------------------------------------------------------ search --

    def _search(self):
        if self.graph is None:
            return
        query = self.search_edit.text().strip().lower()
        if not query:
            return
        matches = [i for i, node in enumerate(self.graph.nodes) if query in node.name.lower()]
        if not matches:
            self.search_status.setText("No matches.")
            return
        self.search_status.setText(f"{len(matches)} match(es). Showing first.")
        self._select(matches[0])
        target = self.positions[matches[0]]
        cam = self.plotter.camera
        cam.focal_point = tuple(target)
        self.plotter.render()


def main():
    start_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home()
    self_test = "--self-test" in sys.argv

    app = QApplication(sys.argv)
    window = MainWindow(start_path)
    window.show()

    if self_test:
        QTimer.singleShot(1500, app.quit)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
