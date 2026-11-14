# CLI

Code: `src/atlas/cli/`.

The CLI is admin only: run the app, create the database, load demo data, and back it up. Capture, setup, correction, and review all live in the web SPA over the HTTP API, so there is one place to add a feature. Confirmations are one line.

| Command               | Purpose                                                                                                                            | Status      |
| --------------------- | ---------------------------------------------------------------------------------------------------------------------------------- | ----------- |
| `atlas init`          | Create the SQLite file and schema at `ATLAS_DB`                                                                                    | implemented |
| `atlas seed`          | Load a demo dataset dated relative to today (or `--on`). Refuses if the database already has data unless `--replace`. Prints counts of every seeded collection. | implemented |
| `atlas export`        | Write a JSON export to stdout                                                                                                      | implemented |
| `atlas import <file>` | Load a JSON export. `--replace` clears user rows first. Prints a note when old goal, milestone, or task sections, or the areas of an export from before schema 12, were skipped.  | implemented |
| `atlas serve`         | Serve the HTTP API and, when `web/dist` exists, the SPA on `127.0.0.1:8000`.                                                       | implemented |

## API

The HTTP side of backup and restore:

| Method   | Path                     | Purpose                                       | Status      |
| -------- | ------------------------ | --------------------------------------------- | ----------- |
| `GET`    | `/export`                | Full JSON export                              | implemented |
| `POST`   | `/import`                | Full JSON import; returns `{schema_version, ignored_sections, notes}` | implemented |

## Demo data

| Function | Role |
| -------- | ---- |
| `seed_demo` | Demo dataset. Builds a payload in the export shape dated relative to `as_of` (default `Settings.today()`) and loads it through `import_all`. Metrics covering every `value_type` and every origin (hand-made ones, an archived one once made for a habit, one per screen app, and the journal's), twelve habits in the schema-15 shape ([habits](../domain/habits.md#screens)): ticked by you and from your data, every frequency (every day, specific days, times a week with a rule change eleven days ago, times a month), every data source family (wake time, sessions planned, Bad apps, one app), every time of day, one archived habit, a three-day holiday freeze for all habits and a one-day freeze on one habit, screen taxonomy (entertainment / social / productivity / learning), devices (each with its "complete up to" time), a waste cap, ~28 days of mostly interval sessions, a library (topics plus films/series/books/podcasts/videos/anime/music in mixed statuses, most finished titles rated, a few with links), and ~4 weeks of staged sleep nights (a few skipped, later wake on weekends), and quests from `src/atlas/services/seed_quests.py` covering every shape in brief Part 4 (an ambition with two goals and direct tasks; an ambition with nothing under it; an independent goal with a milestone; a milestone with two chapters — one of them empty — and direct tasks; a goal completed by hand with an open task; a side quest with a chapter and a direct task, and one with a single task; two standalone tasks; three Inbox items; and time blocks yesterday, today, and tomorrow at local times in `ATLAS_TZ`, including one left unconfirmed and one cancelled, plus two weeks of weekday sessions, some planned before noon and some after, for the sessions-planned habit), habits that support quest items at several levels (an ambition, a goal and its milestone, a chapter, and a task) so the habits list / `screen_dashboard` / `library_dashboard` / `sleep_view` are non-empty. `SeedSummary` counts metrics, habits, entries, screen categories, apps, devices, sessions, library topics, titles, sleep sessions, ambitions, goals, milestones, side quests, chapters, tasks, and time blocks. Refuses when the database already holds data (any metric, quest item, library title, sleep night, or screen category) unless `replace=True`. Entries and sessions are sourced as `import`. |
