# Workflow

One topic per branch, one PR per branch, checks green before every commit. When several
branches run at once, follow [parallel work](parallel-work.md). Docs change in the same commit
as the code ([docs-sync](docs-sync.md)).

## Python tooling

Python 3.12, managed entirely with `uv`. Every command goes through it: `uv add`, `uv sync`, `uv run pytest`, `uv run ruff check`, `uv run ruff format`. Never bare `pip`, `python`, `pytest`, or `ruff`. For Claude Code this is enforced, not advised: `.claude/settings.json` runs the PreToolUse hook `.claude/hooks/enforce_toolchain.py` on every Bash call, which denies non-uv Python tooling and non-pnpm JS tooling (`npm`, `npx`, `yarn`, `bun`) with the replacement command, backed by plain permission `deny` rules; the gate commands are pre-approved. `tests/test_toolchain_hook.py` pins what is blocked and what is allowed. A second PreToolUse hook, `.claude/hooks/docs_gate.py`, blocks `git commit` when code is staged without docs ([docs-sync](docs-sync.md)); `tests/test_docs_gate.py` pins it.

## Web tooling

The SPA in `web/` is managed entirely with pnpm and Biome. Every install and script goes through `pnpm`. Biome is the linter and the formatter; do not add ESLint, Prettier, or oxlint. Claude Code loads this rule from `.claude/rules/frontend.md` whenever it works under `web/`.

## Checks before every commit

Before a commit, `uv run ruff check`, `uv run ruff format --check`, and `uv run pytest` must be clean (and `pnpm lint`, `pnpm test`, `pnpm build` when `web/` changes). A diagnostic is work in this cycle: apply `ruff check --fix` / `ruff format` / `pnpm format` when the tool can, then inspect the rest and edit to match nearby code — do not `# noqa` or leave a known failure. Claude Code enforces this through `.claude/rules/checks.md` and the `fix-checks` skill (`.claude/skills/fix-checks/SKILL.md`). Update the docs in the same cycle as the behavior they describe ([docs-sync](docs-sync.md)).

## Agent guidance

Agent guidance is Claude Code's project memory. `CLAUDE.md` at the repo root orients a session and points to `docs/README.md`. `.claude/rules/` holds the rules: `architecture.md`, `checks.md`, `documentation.md`, and `tooling.md` load in every session; `frontend.md` (`paths: web/**`) and `python-conventions.md` (`paths: **/*.py`) load when Claude works on matching files. `.claude/skills/` holds project skills (`fix-checks`, `docs-sync`, plus the UI skills `ui-styling` and `ui-ux-pro-max`); their script commands run from the repo root as `.claude/skills/<skill>/scripts/...`.
