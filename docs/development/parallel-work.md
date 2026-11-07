# Parallel work

How several feature branches run at the same time without colliding. Taken from §1.3–1.4 of
the [November restructure plan](../plans/2026-11-restructure.md); the plan's track names (T1–T6)
are the owners below. When a new plan defines new tracks, update the ownership table here.

## Rules that keep branches from colliding
1. **File ownership.** Each track edits only the files it owns (table below). If a track needs a
   change in a file it does not own, it writes it down under "Handoffs" in its PR, and the
   owner (or T6) makes it.
2. **Shared files are edited only in your own feature's lines.** These are touched by several
   tracks: `web/src/lib/api.ts`, `src/atlas/api/schemas.py`, `src/atlas/services/__init__.py`,
   `src/atlas/api/app.py`, `tests/api/test_app.py`. Add or remove only the lines for your
   feature, never reorder or reformat others', and rebase on `main` before merging.
3. **One schema change per wave.** Only T2 bumps the database schema in wave 1 (to version 11).
   T5 takes version 12 in wave 2. T3 makes no schema change (the pipeline comes later).
4. **Docs per feature.** After T1, each feature has its own doc file. A track edits its own
   domain docs and adds a changelog fragment (`docs/changelog/unreleased/<branch>.md`) instead
   of appending to a shared log, so changelog entries never conflict.
5. **Seed data by function.** In `src/atlas/services/seed.py`, T2 edits only `_areas()`, and T4
   only `_habits()`.

## File ownership

| Files | Owner |
| ----- | ----- |
| `docs/**` structure, `CLAUDE.md`, `.claude/rules/**`, `.claude/hooks/**`, `.claude/skills/docs-sync/**` | T1 |
| `web/src/components/Layout.tsx`, `web/src/App.tsx`, `web/src/lib/sections.ts`, `web/src/pages/{AreaPage,CatalogPage,SectionPage}.tsx`, new `web/src/pages/SettingsPage.tsx`, `web/src/components/ProfileDialog.tsx`, `web/src/components/habits/HabitFormDialog.tsx` (area picker only), new `web/src/lib/labels.ts`, `src/atlas/services/areas.py`, `src/atlas/services/metrics.py`, `src/atlas/db/models.py` + `engine.py` (wave 1), `docs/product/navigation.md`, `docs/domain/life-areas.md` | T2 |
| `web/src/pages/{SleepPage,ScreenPage,EntriesPage}.tsx`, `web/src/components/home/{SleepCard,ScreenTimeCard,Charts}.tsx`, `web/src/components/screen/**`, new `web/src/components/settings/{ScreenTimeSettings,DataSourcesSettings}.tsx`, `src/atlas/services/{sleep,screen,entries}.py` (filters only), `docs/domain/{sleep,screen-time,history}.md`, `docs/data-sources/**` | T3 |
| `web/src/components/{LogDialog,LogForm}.tsx`, `web/src/components/home/HomeCards.tsx`, `web/src/pages/TasksPage.tsx`, `web/src/components/habits/HabitCard.tsx`, `web/src/pages/{HabitsPage,HabitPage}.tsx`, `src/atlas/services/habits.py` (labels only), `docs/domain/{tasks,habits,home}.md` | T4 |
| `web/src/pages/{GoalsPage,GoalPage}.tsx`, `web/src/components/goals/**`, `src/atlas/services/goals.py`, `src/atlas/domain/goals.py`, `docs/domain/goals.md` | T5 |
| Everything still unowned, plus cross-cutting sweeps | T6 |

Ownership changes from the plan's decisions (§7):

- T4 also owns: `web/src/components/habits/HabitFormDialog.tsx` (area picker),
  `src/atlas/services/habits.py` (`create_habit` area), the header bell in
  `web/src/components/Layout.tsx` (removal only), and the wording in
  `web/src/pages/SectionPage.tsx`.
- T2 keeps the rest of `Layout.tsx`, `App.tsx`, `sections.ts`, Area, Catalog, and Settings for
  later.

## Changelog fragments

Each branch writes `docs/changelog/unreleased/<branch>.md` instead of editing the year file.
See [changelog](../changelog/README.md).
