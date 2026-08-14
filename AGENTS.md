# AGENTS.md

Atlas is a single-user, local-first life-tracking backend. Architecture, data model, and the full CLI/API surface live in [docs/architecture.md](docs/architecture.md); install/run basics live in [README.md](README.md). Coding rules live under `.cursor/rules/`.

## Cursor Cloud specific instructions

- Toolchain: Python 3.12 managed entirely by `uv`. Every Python/install/test command goes through `uv` (`uv sync`, `uv run pytest`, `uv run ruff check`, `uv run atlas ...`, `uv run uvicorn ...`). Never use bare `pip`/`python`/`pytest`/`ruff`. `uv` is installed to `~/.local/bin` (already on `PATH`); the update script runs `uv sync`.
- Pre-commit gates (from `.cursor/rules/tooling.mdc`): `uv run ruff check` and `uv run pytest` must both pass before every commit. The whole suite (~153 tests) runs offline in a few seconds against in-memory SQLite; there are no external services, databases, or network dependencies to start.
- No standalone service processes are required for tests. The API tests use FastAPI `TestClient`, and CLI tests use a temp SQLite file — neither starts a live server.
- Running the app for manual/dev use: the CLI is `uv run atlas <cmd>` and the HTTP API is `uv run uvicorn atlas.api.app:app --reload --host 127.0.0.1`. Both share one SQLite database resolved from `ATLAS_DB`.
- `ATLAS_DB` gotcha: it defaults to `~/.local/share/atlas/atlas.db` (outside the repo). When you want the CLI and the API to operate on the same visible database during a session, export a repo-local path first, e.g. `export ATLAS_DB="$PWD/.atlas-dev.db"` — `*.db` is gitignored so it won't be committed. `atlas seed` refuses to run if areas already exist; use `atlas seed --replace` to reload the demo dataset.
- The API binds to `127.0.0.1` only with no auth by design; it is not reachable from outside the VM. Use `curl` from within the VM (or the Desktop browser at `http://127.0.0.1:8000/docs`) to exercise it.
