# Tooling

Python 3.12. Stack: uv, FastAPI, uvicorn, SQLModel, Typer, Rich, pytest, ruff, SQLite.

## uv only

Every Python, install, and test command goes through `uv`. Never `pip`, never bare `python` / `pytest` / `ruff`.

```bash
# ❌ BAD
pip install fastapi
python -m pytest
ruff check .

# ✅ GOOD
uv add fastapi
uv add --dev pytest ruff
uv run pytest
uv run ruff check
uv run ruff format --check
uv run uvicorn atlas.api.app:app --reload
```

Use `uv add` / `uv add --dev` / `uv sync`. The lockfile is `uv.lock`; do not invent a `requirements.txt`.

## Pre-commit gates

Before every commit, all must pass:

1. `uv run ruff check`
2. `uv run ruff format --check`
3. `uv run pytest`

A finding is work: apply `ruff check --fix` / `ruff format` when the tool can, then inspect the rest. See `.claude/rules/checks.md`. Do not commit with a known failure.

## Frontend (`web/`)

pnpm and Biome only. See `.claude/rules/frontend.md`. Never `npm` / `yarn` / ESLint / Prettier / oxlint in `web/`.

## Enforced

This rule is not advisory. `.claude/settings.json` runs `.claude/hooks/enforce_toolchain.py` before every Bash call and denies any command that runs `pip`, `pip3`, `pipx`, a bare `python` / `python3` (including `.venv/bin/python`), `pytest`, `ruff`, `uvicorn`, `atlas`, `poetry`, `pipenv`, `conda`, `virtualenv`, `uv pip`, or `pip` inside `uv run` — and on the web side `npm`, `npx`, `yarn`, `bun`, `bunx`. It reads chained commands, `VAR=x` and `sudo` prefixes, `bash -c` strings, and skips heredoc bodies and quoted text. Plain `deny` permission rules back it up. The gate commands (`uv run ruff`, `uv run pytest`, `uv sync`, `pnpm install|lint|format|test|build`) are pre-approved. Tests: `tests/test_toolchain_hook.py`.
