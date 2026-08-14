---
name: fix-checks
description: >-
  Apply ruff, Biome, pytest, and pnpm build failures in the same cycle.
  Auto-fixable suggestions are applied; remaining diagnostics are inspected
  and edited for codebase coherence. Use when a check fails, reports FIXABLE
  or [*], would reformat files, or when the user mentions ruff, biome, lint,
  format drift, or leaving a known failure.
---

# Fix checks

A check finding is work. Do not report it and continue. Do not `# noqa`, disable a rule, or skip hooks to get a green run.

## Commands (uv / pnpm only)

```bash
uv run ruff check --fix src tests
uv run ruff format src tests
uv run ruff check src tests && uv run ruff format --check src tests
uv run pytest
cd web && pnpm format && pnpm lint && pnpm test && pnpm build
```

Never bare `ruff` / `pytest` / `npm`.

## Auto-fixable

If the tool marks the finding (`[*]`, `FIXABLE`, `--fix`, Biome `--write`), apply that suggestion, then re-run the **same** check.

Typical: import order (`I001`), unused imports (`F401`), format drift (`ruff format`, `pnpm format`).

## Not auto-fixable

Inspect the diagnostic against nearby code and fix it the same way the rest of the tree would:

| Finding | What to do |
| ------- | ---------- |
| `E501` line too long | Wrap; keep wording. Do not disable. |
| Test failure | Change the code or the assertion so both match intended behavior. |
| Type / Biome lint | Edit to the existing pattern (explicit keys, no assign-in-expression). |

## Done

The cycle ends only when the gates that failed are green. See `.cursor/rules/checks.mdc` and `.cursor/rules/tooling.mdc`.
