# Atlas docs

The knowledge base for Atlas, maintained alongside the code. A change in behavior and the
matching doc edit belong to the same commit: code and docs disagreeing is a bug, not a stale
doc. Commits that touch `src/` or `web/src/` without touching `docs/` are blocked
([docs-sync](development/docs-sync.md)).

How to install and run Atlas is in the root [README](../README.md).

## How to navigate

| Folder | Holds | Start with |
| ------ | ----- | ---------- |
| [product/](product/) | What Atlas is, how it is organised, how it should read and look | [vision](product/vision.md), [navigation](product/navigation.md) |
| [architecture/](architecture/) | How it is built: layers, tables, schema versions, API rules, frontend, CLI, config | [overview](architecture/overview.md) |
| [domain/](domain/) | One file per feature, all with the same headings | the feature you are changing |
| [data-sources/](data-sources/) | Data that arrives from devices, not from typing | [overview](data-sources/overview.md) |
| [development/](development/) | Setup, workflow, parallel branches, testing, the docs gate | [workflow](development/workflow.md) |
| [decisions/](decisions/) | Short records of choices that should not be re-argued | [0001](decisions/0001-local-first-single-user.md) |
| [changelog/](changelog/) | What landed, per cycle | [how fragments work](changelog/README.md) |
| [plans/](plans/) | Active plans and discussion briefs | — |

Every `domain/*.md` file uses the same headings: **Purpose · Concepts · Data model · Rules and
calculations · API · Screens · Tests · Status**. For any feature you know where to look, and a
reviewer can check each heading against the code.

## Code → doc map

When you change a file on the left, re-read the docs on the right against your change and
update them in the same commit. The first matching row wins; patterns are shell globs relative
to the repository root. `.claude/hooks/docs_gate.py` reads this table to name the docs a
blocked commit should review, so keep it a plain two-column table.

| Code | Docs |
| ---- | ---- |
| `src/atlas/domain/buckets.py` | `docs/domain/trackers-and-entries.md` |
| `src/atlas/domain/rollup.py` | `docs/domain/trackers-and-entries.md` |
| `src/atlas/domain/habits.py` | `docs/domain/habits.md` |
| `src/atlas/domain/goals.py` | `docs/domain/goals.md` |
| `src/atlas/domain/horizons.py` | `docs/domain/goals.md` |
| `src/atlas/domain/screen.py` | `docs/domain/screen-time.md` |
| `src/atlas/domain/sleep.py` | `docs/domain/sleep.md` |
| `src/atlas/domain/entertainment*.py` | `docs/domain/entertainment.md` |
| `src/atlas/domain/*` | `docs/architecture/overview.md` |
| `src/atlas/db/models.py` | `docs/architecture/data-model.md`, the feature's `docs/domain/*.md` (Data model) |
| `src/atlas/db/engine.py` | `docs/architecture/migrations.md` |
| `src/atlas/db/*` | `docs/architecture/overview.md` |
| `src/atlas/services/areas.py` | `docs/domain/life-areas.md` |
| `src/atlas/services/metrics.py` | `docs/domain/trackers-and-entries.md` |
| `src/atlas/services/entries.py` | `docs/domain/trackers-and-entries.md`, `docs/domain/history.md` |
| `src/atlas/services/habits.py` | `docs/domain/habits.md` |
| `src/atlas/services/goals.py` | `docs/domain/goals.md` |
| `src/atlas/services/tasks.py` | `docs/domain/tasks.md` |
| `src/atlas/services/journal.py` | `docs/domain/journal.md` |
| `src/atlas/services/life.py` | `docs/domain/journal.md` |
| `src/atlas/services/screen.py` | `docs/domain/screen-time.md`, `docs/data-sources/screen-time.md` |
| `src/atlas/services/sleep.py` | `docs/domain/sleep.md`, `docs/data-sources/sleep.md` |
| `src/atlas/services/entertainment*.py` | `docs/domain/entertainment.md` |
| `src/atlas/services/views.py` | `docs/domain/habits.md`, `docs/domain/goals.md`, `docs/domain/life-areas.md` |
| `src/atlas/services/port.py` | `docs/architecture/migrations.md` |
| `src/atlas/services/seed.py` | `docs/architecture/cli.md` |
| `src/atlas/services/*` | `docs/architecture/overview.md` |
| `src/atlas/api/routers/entries.py` | `docs/domain/trackers-and-entries.md` |
| `src/atlas/api/routers/metrics.py` | `docs/domain/trackers-and-entries.md` |
| `src/atlas/api/routers/areas.py` | `docs/domain/life-areas.md` |
| `src/atlas/api/routers/habits.py` | `docs/domain/habits.md` |
| `src/atlas/api/routers/goals.py` | `docs/domain/goals.md` |
| `src/atlas/api/routers/views.py` | `docs/domain/habits.md`, `docs/domain/goals.md`, `docs/domain/life-areas.md` |
| `src/atlas/api/routers/screen.py` | `docs/domain/screen-time.md`, `docs/data-sources/screen-time.md` |
| `src/atlas/api/routers/sleep.py` | `docs/domain/sleep.md`, `docs/data-sources/sleep.md` |
| `src/atlas/api/routers/tasks.py` | `docs/domain/tasks.md` |
| `src/atlas/api/routers/journal.py` | `docs/domain/journal.md` |
| `src/atlas/api/routers/entertainment.py` | `docs/domain/entertainment.md` |
| `src/atlas/api/routers/port.py` | `docs/architecture/cli.md`, `docs/architecture/migrations.md` |
| `src/atlas/api/spa.py` | `docs/architecture/frontend.md` |
| `src/atlas/api/*` | `docs/architecture/api-conventions.md` |
| `src/atlas/cli/*` | `docs/architecture/cli.md` |
| `src/atlas/settings.py` | `docs/architecture/configuration.md` |
| `web/src/App.tsx` | `docs/product/navigation.md` |
| `web/src/components/Layout.tsx` | `docs/product/navigation.md` |
| `web/src/lib/sections.ts` | `docs/product/navigation.md` |
| `web/src/pages/HomePage.tsx` | `docs/domain/home.md` |
| `web/src/components/home/*` | `docs/domain/home.md` |
| `web/src/pages/Habit*.tsx` | `docs/domain/habits.md` |
| `web/src/components/habits/*` | `docs/domain/habits.md` |
| `web/src/pages/Goal*.tsx` | `docs/domain/goals.md` |
| `web/src/components/goals/*` | `docs/domain/goals.md` |
| `web/src/pages/TasksPage.tsx` | `docs/domain/tasks.md` |
| `web/src/components/tasks/*` | `docs/domain/tasks.md` |
| `web/src/pages/JournalPage.tsx` | `docs/domain/journal.md` |
| `web/src/pages/SleepPage.tsx` | `docs/domain/sleep.md` |
| `web/src/pages/ScreenPage.tsx` | `docs/domain/screen-time.md` |
| `web/src/components/screen/*` | `docs/domain/screen-time.md` |
| `web/src/pages/Entertainment*.tsx` | `docs/domain/entertainment.md` |
| `web/src/components/entertainment/*` | `docs/domain/entertainment.md` |
| `web/src/pages/EntriesPage.tsx` | `docs/domain/history.md` |
| `web/src/pages/AreaPage.tsx` | `docs/domain/life-areas.md` |
| `web/src/pages/CatalogPage.tsx` | `docs/product/navigation.md` |
| `web/src/components/LogDialog.tsx` | `docs/domain/trackers-and-entries.md` |
| `web/src/components/LogForm.tsx` | `docs/domain/trackers-and-entries.md` |
| `web/src/components/ui/*` | `docs/product/design-system.md` |
| `web/src/index.css` | `docs/product/design-system.md` |
| `web/src/lib/theme.ts` | `docs/product/design-system.md` |
| `web/src/lib/api.ts` | `docs/architecture/frontend.md` |
| `web/src/*` | `docs/architecture/frontend.md`, `docs/product/ux-writing.md` (any user-facing text) |
| `src/*` | `docs/architecture/overview.md` |

Every commit that changes behaviour also adds or edits its branch's changelog fragment in
[changelog/unreleased/](changelog/unreleased/).
