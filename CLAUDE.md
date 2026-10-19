# Atlas

Single-user, local-first life tracker: a FastAPI + SQLModel backend over SQLite, a Typer CLI for capture and admin, and a React SPA in `web/` for review. Entries are the stored facts; streaks, adherence, goal progress, and pace are computed on read.

- How to install and run: [README.md](README.md).
- Data model, layering, API, CLI, web surface, and the development log: [docs/architecture.md](docs/architecture.md). It is the source of truth and changes in the same commit as the behavior it describes.

## Rules

Project rules live in `.claude/rules/` and load automatically:

| Rule | Loads | Covers |
| ---- | ----- | ------ |
| `architecture.md` | always | Layering, import bans, data principles |
| `tooling.md` | always | uv only, Python pre-commit gates |
| `checks.md` | always | A check finding is work in this cycle |
| `documentation.md` | always | Keep `docs/architecture.md` in lockstep |
| `frontend.md` | `web/**` | pnpm and Biome only, web gates |
| `python-conventions.md` | `**/*.py` | Types, explicit `Session`, domain purity, tests by layer |

## Gates

Before every commit (see `tooling.md` and `frontend.md`):

```bash
uv run ruff check && uv run ruff format --check && uv run pytest
cd web && pnpm lint && pnpm test && pnpm build   # when web/ changes
```

When a gate fails, use the `fix-checks` skill. Design and UI skills (`ui-ux-pro-max`, `ui-styling`, `design`, `design-system`, `brand`, `banner-design`, `slides`) live in `.claude/skills/`.
