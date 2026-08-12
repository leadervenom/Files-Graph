# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

The active product surface is `fgraph-gui/webapp.py`: a native desktop window (pywebview) hosting a local, fully offline web page (`fgraph-gui/web/index.html` + `app.js`). Impeccable's web tooling (live mode, the bundled detector) targets this surface directly.

Earlier exploratory builds exist in the same repo — a terminal app (`fgraph/`, Rust) and a static PyVista/Qt desktop viewer (`fgraph-gui/app.py`) — but are out of active design scope per the author's direction; treat them as prior work, not surfaces to design, critique, or polish going forward.

## Users

Windows users who want to understand and navigate their own file system spatially instead of through a nested list view — the tool is being designed for a general, less-technical audience (not just the author), since it may eventually be shared/published.

Job: explore a real folder tree, get an intuitive sense of what's big, what type of content is where, and open or drill into the actual file/folder from the visualization — driven entirely by mouse (drag to orbit, scroll to zoom, drag a node to pull it), no keyboard shortcuts to learn.

## Product Purpose

Turns a user's real Windows file system into a living, explorable 3D graph — size and file-type are visible at a glance instead of hidden in list columns, and the graph behaves like it's alive (physics-driven layout, draggable/springy nodes, flowing particles on links, gentle idle motion) rather than a static rendering. Success is a user reaching and opening a real file or folder through the visualization and finding the experience genuinely more engaging than Explorer for that "get a feel for what's here" moment.

## Positioning

Unlike a conventional file manager or disk-usage tool (Explorer, WinDirStat, TreeSize) — and unlike a static 3D file-tree render — this behaves like Obsidian's graph view applied to a filesystem: a physics-simulated, touchable, self-organizing graph rather than a fixed layout the camera merely orbits.

## Operating Context

- Runs on Windows 10/11, against real local folders the user picks (e.g. Documents, home directory, a whole user profile).
- Strictly read-only: scans the existing NTFS filesystem via ordinary directory traversal. No virtual drive, no filesystem driver (WinFsp or otherwise) — explicitly deferred as future, additive scope, not current behavior.
- Rescans on launch and on-demand (Scan & Visualize button, folder browse); depth and total-entry caps keep large trees (e.g. an entire user profile) responsive rather than attempting a full unbounded index.
- Architecture: `webapp.py` (Python) scans the filesystem and exposes a `js_api` bridge (scan, browse folder, open path, legend) to the page; `web/index.html` + `web/app.js` render the graph via a locally vendored `3d-force-graph` bundle (`web/vendor/`) — no CDN, fully offline at runtime.

## Capabilities and Constraints

- Windows-only at present (`os.startfile` to open files/folders).
- Fully offline: the `3d-force-graph` JS bundle is vendored locally, no network dependency at runtime.
- Force-directed layout: nodes settle via physics rather than a fixed computed position; dragging a node un-pins it on release so it eases back under its neighbors' pull instead of freezing where dropped.
- Visual language: file-type category palette (code / docs / image / video / audio / archive / executable / data / other) and a size-weighting rule (bigger node = bigger file or fuller folder), both defined in `fgraph-gui/colors.py`.
- Sidebar (glass-panel over the 3D view): folder path + browse, max-depth control, search, selected-item info card, open-in-Explorer, legend.
- Undecided: final distribution/packaging (installer vs. plain zip/download), and whether the "fgraph" name is final for a public release.

## Brand Commitments

Working name "fgraph" — not yet confirmed as a final public-facing product name. No logo or established voice yet.

## Evidence on Hand

None yet: no real users, testimonials, usage data, or feedback beyond the author's own testing. Future work must not fabricate any of this.

## Product Principles

1. Alive, not static — the graph should always feel like it's responding: physics settle, particles flow on links, idle auto-rotate, nodes spring back after a drag instead of staying frozen.
2. Mouse-first, zero memorization — every interaction (orbit, zoom, select, drag, search, browse, open) is discoverable without reading a shortcut list, because the audience is explicitly wider than terminal-comfortable users.
3. Real data only, always — the app visualizes the user's actual filesystem; never fabricated or placeholder data in shipped behavior.
4. Read-only and safe by default — no virtual filesystem driver, no writes to the scanned tree; the visualization sits cleanly on top of the real filesystem.
5. Offline-first — no runtime dependency on a CDN or network connection; the visual library is vendored locally.

## Accessibility & Inclusion

None established yet.
