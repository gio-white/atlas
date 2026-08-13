# Atlas

Personal life-tracking backend. Records what you did, layers habits and goals on top of that record, and computes all progress on read.

This README is how to install and run it. The data model, layering, derived computations, API and CLI surface, and configuration live in [docs/architecture.md](docs/architecture.md).

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Node.js 20+ (only when working on the web UI)

## Install

```bash
uv sync
```

That creates the virtualenv, installs runtime and dev dependencies from `uv.lock`, and exposes the `atlas` CLI.

Optional environment variables, documented under [configuration](docs/architecture.md#configuration):

- `ATLAS_DB` — SQLite file (default `~/.local/share/atlas/atlas.db`)
- `ATLAS_TZ` — IANA timezone used to resolve "today" (default: the system zone)

## CLI

Every command goes through `uv run`. The schema is created on first use; `init` is the explicit version of that.

```bash
uv run atlas init
uv run atlas seed
```

`seed` loads a demo dataset dated relative to today so review commands have something to show. It refuses if the database already has areas; pass `--replace` to wipe user data and load it again. `--on YYYY-MM-DD` pins the "today" the demo is built around.

Capture (the hot path):

```bash
uv run atlas log pushups 40
uv run atlas log meditated
uv run atlas log weight 78.4 --on 2026-08-10 --note "post-travel"
```

Review:

```bash
uv run atlas today
uv run atlas week
uv run atlas area health
uv run atlas habit pushups-daily
uv run atlas goals
```

Define, correct, and port (`export` / `import`) are listed in the [CLI](docs/architecture.md#cli) section of the architecture doc. `uv run atlas --help` prints the same surface.

## API and web UI

The HTTP API is the only consumer path. It binds to localhost only (`127.0.0.1`); there is no authentication. `atlas serve` runs that API and, after `web/` is built, the React SPA from `web/dist`.

```bash
uv run atlas serve
```

Equivalent: `uv run uvicorn atlas.api.app:app --reload --host 127.0.0.1` or `uv run python -m atlas.api`. OpenAPI UI is at <http://127.0.0.1:8000/docs>. During UI development the Vite app on port 5173 is allowed by CORS; see [frontend](docs/architecture.md#frontend).

```bash
curl -s http://127.0.0.1:8000/views/today
curl -s -X POST http://127.0.0.1:8000/entries \
  -H 'content-type: application/json' \
  -d '{"metric":"pushups","value":40}'
```

Endpoints are listed in the [HTTP API](docs/architecture.md#http-api) section of the architecture doc.

## Develop

```bash
uv run ruff check
uv run pytest
```

Both must pass before a commit. See [docs/architecture.md](docs/architecture.md) for layering rules and how streaks, adherence, and goal progress are defined.
