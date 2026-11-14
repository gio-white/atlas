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
| `seed_demo` | Demo dataset. Builds a payload in the export shape dated relative to `as_of` (default `Settings.today()`) and loads it through `import_all`. Metrics covering every `value_type` and every origin (hand-made ones, one made for a habit, one per screen app, and the journal's), daily/weekly/monthly habits of every kind (check, count, duration, and a `no-doomscrolling` quit habit with two slips) with times of day, a one-day skip, `at_most`, and a weekday mask, screen taxonomy (entertainment / social / productivity / learning), devices, a waste cap, ~28 days of mostly interval sessions, an entertainment library (topics plus films/series/books/podcasts/videos/anime/music in mixed statuses, most finished titles rated, a few with links), and ~4 weeks of staged sleep nights (a few skipped, later wake on weekends), and quests from `src/atlas/services/seed_quests.py` covering every shape in brief Part 4 (an ambition with two goals and direct tasks; an ambition with nothing under it; an independent goal with a milestone; a milestone with two chapters — one of them empty — and direct tasks; a goal completed by hand with an open task; a side quest with a chapter and a direct task, and one with a single task; two standalone tasks; three Inbox items; and time blocks yesterday, today, and tomorrow at local times in `ATLAS_TZ`, including one left unconfirmed and one cancelled) so habit statuses / `screen_dashboard` / `entertainment_dashboard` / `sleep_view` are non-empty. `SeedSummary` counts metrics, habits, entries, screen categories, apps, devices, sessions, entertainment topics, titles, sleep sessions, ambitions, goals, milestones, side quests, chapters, tasks, and time blocks. Refuses when the database already holds data (any metric, quest item, library title, sleep night, or screen category) unless `replace=True`. Entries and sessions are sourced as `import`. |
