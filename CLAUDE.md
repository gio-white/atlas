# Atlas

Single-user, local-first life tracker: a FastAPI + SQLModel backend over SQLite, a small Typer admin CLI, and a React SPA in `web/` for review. Entries are the stored facts; streaks, adherence, goal progress, and pace are computed on read.

- How to install and run: [README.md](README.md).
- Product, architecture, one doc per feature, data sources, development workflow, decisions, and the changelog: [docs/README.md](docs/README.md). It is the source of truth and changes in the same commit as the behavior it describes. The **code → doc map** there says which doc covers which file.

## Rules

Project rules live in `.claude/rules/` and load automatically:

| Rule | Loads | Covers |
| ---- | ----- | ------ |
| `architecture.md` | always | Layering, import bans, data principles |
| `tooling.md` | always | uv only, Python pre-commit gates |
| `checks.md` | always | A check finding is work in this cycle |
| `documentation.md` | always | Docs change with code, via the code → doc map |
| `frontend.md` | `web/**` | pnpm and Biome only, web gates |
| `python-conventions.md` | `**/*.py` | Types, explicit `Session`, domain purity, tests by layer |

## Gates

Before every commit (see `tooling.md` and `frontend.md`):

```bash
uv run ruff check && uv run ruff format --check && uv run pytest
cd web && pnpm lint && pnpm test && pnpm build   # when web/ changes
```

Only `uv` (Python) and `pnpm` (web) are allowed: `.claude/settings.json` runs a hook that denies `pip`, bare `python` / `pytest` / `ruff`, `npm`, `npx`, `yarn`, and friends, and pre-approves the gate commands above.

Commits that stage `src/` or `web/src/` without `docs/` are blocked (`.claude/hooks/docs_gate.py`) unless the message has the line `Docs-Reviewed: no change needed`; use the `docs-sync` skill before committing. Each clone enables the same gate for git with `git config core.hooksPath .githooks` ([docs/development/docs-sync.md](docs/development/docs-sync.md)).

When a gate fails, use the `fix-checks` skill. UI skills (`ui-ux-pro-max`, `ui-styling`) live in `.claude/skills/`.
