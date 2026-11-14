# Documentation

`docs/` is the knowledge base and the source of truth alongside the code. Start at
`docs/README.md`. Update docs in the **same commit** as the change that alters behavior — never
as a follow-up chore. Code and docs disagreeing is a bug, not a stale doc.

## The code → doc map decides which docs

`docs/README.md` has a **Code → doc map** table: each code path (glob) → the docs that describe
it. Before committing, look up every staged file under `src/` and `web/src/`, re-read those
docs against the code, and update them. Use the `docs-sync` skill for this.

| You changed | Update |
| ----------- | ------ |
| `src/atlas/services/habits.py`, `api/routers/habits.py`, `domain/habits.py` | `docs/domain/habits.md` |
| `src/atlas/db/models.py` | the feature's `docs/domain/*.md` (Data model) and `docs/architecture/data-model.md` |
| `src/atlas/db/engine.py` (schema version) | `docs/architecture/migrations.md` |
| A route in a router | the feature doc's API table |
| `web/src/App.tsx` | `docs/product/navigation.md` |
| Any user-facing string | check it against `docs/product/ux-writing.md` |
| A new code file | add a row to the map |

The full map is in `docs/README.md`; the rows above are examples.

## What to keep current

- Each feature's `docs/domain/*.md`, under its fixed headings: Purpose · Concepts · Data model ·
  Rules and calculations (precise definitions, not summaries) · API · Screens · Tests · Status.
- Layering and import rules: `docs/architecture/overview.md`.
- Configuration (`ATLAS_DB`, `ATLAS_TZ`, bind address): `docs/architecture/configuration.md`.
- A choice that should not be re-argued: a new record in `docs/decisions/`.
- Changelog: one fragment per branch, `docs/changelog/unreleased/<branch>.md`, one bullet per
  cycle (date, todo id, what landed). Never edit `docs/changelog/2026.md` on a branch.

Do not duplicate docs into the README. Link to them instead.

## Enforced

A hook blocks `git commit` when files under `src/` or `web/src/` are staged and nothing under
`docs/` is (`.claude/hooks/docs_gate.py`, wired in `.claude/settings.json` and in
`.githooks/commit-msg`). If you re-read the mapped docs and they genuinely need no change, add
the line `Docs-Reviewed: no change needed` to the commit message. Drift tests fail when an API
route or SPA route is missing from the docs (`tests/test_docs_drift.py`,
`web/src/docs-drift.test.ts`). A failing check is work in this cycle (`.claude/rules/checks.md`).

```markdown
# ❌ BAD — commit the feature, "docs later"
# (docs/domain/habits.md still lacks the new PATCH field)

# ✅ GOOD — same commit updates the API table and adds the changelog fragment
# docs/domain/habits.md: PATCH /habits/{slug} row lists `target`
# docs/changelog/unreleased/feature-ui-copy-and-fixes.md: - **2026-11-08 —** `habit-target` — …
```
