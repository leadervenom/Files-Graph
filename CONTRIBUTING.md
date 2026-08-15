# Contributing to fgraph

Thanks for taking the time to contribute. fgraph is a small, mostly solo-maintained project, so keeping changes focused and well-scoped makes them much easier to review.

## Before you start

For anything beyond a small fix (typo, obvious bug), please open an issue first to discuss the change. This avoids spending time on a PR that doesn't fit the project's direction — see `PRODUCT.md` for the current scope: `fgraph-gui` is the actively maintained surface, while `fgraph-terminal` and the older PyVista/Qt viewer are prior work, not areas under active design.

## Reporting bugs

Open an [issue](https://github.com/leadervenom/Files-Graph/issues) with:

- What you did, what you expected, what actually happened
- Windows version (10 or 11) and which app (`fgraph-gui` or `fgraph-terminal`)
- Whether you're on the installer, portable exe, or running from source
- Screenshots or a screen recording if it's a visual/graph issue
- Console/terminal output if there's an error message

## Suggesting features

Open an issue describing the use case, not just the feature — what are you trying to do, and how does fgraph currently fall short? Check `PRODUCT.md`'s "Product Principles" first (alive not static, mouse-first, read-only and safe, offline-first) — proposals that cut against those will need a stronger justification.

## Development setup

See [INSTALL.md](INSTALL.md#option-3-run-from-source-developers) for getting either app running from source. Project layout is documented in `README.md`'s "Project structure" section.

For UI iteration on `fgraph-gui`'s frontend without the desktop shell, there's a `?mock=1` dev harness — see the "Development" section of `README.md`.

## Making changes

1. Fork the repo and create a branch off `main` for your change.
2. Keep the change scoped to one thing — separate unrelated fixes into separate PRs.
3. Match the existing code style in the file you're editing rather than introducing a new convention.
4. Test manually against a real folder (or several — try a small one and a large one) for any change touching scanning or the graph rendering. There's no automated test suite yet, so manual verification matters.
5. Update `README.md` if you change setup steps, controls, or project structure.
6. Don't commit build output (`fgraph-gui/build/`, `fgraph-gui/dist/`, `fgraph-gui/installer_output/`, `fgraph/target/`) — these are gitignored for a reason; the root `fgraph-gui.exe` is the one intentional exception, rebuilt and committed deliberately per release.

## Submitting a pull request

- Give the PR a clear title and describe *why* the change is needed, not just what changed.
- Reference the issue it addresses, if any (`Fixes #123`).
- Keep the diff focused — avoid reformatting or refactoring unrelated code in the same PR.
- Be responsive to review feedback; if a PR goes stale without updates, it may be closed and can be reopened later.

## Code of conduct

Participation in this project is covered by [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
