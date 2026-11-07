# CLI

Code: `src/atlas/cli/`.

The CLI is admin only: run the app, create the database, load demo data, and back it up. Capture, catalog definition, correction, and review all live in the web SPA over the HTTP API, so there is one place to add a feature. Confirmations are one line.

| Command               | Purpose                                                                                                                            | Status      |
| --------------------- | ---------------------------------------------------------------------------------------------------------------------------------- | ----------- |
| `atlas init`          | Create the SQLite file and schema at `ATLAS_DB`                                                                                    | implemented |
| `atlas seed`          | Load a demo dataset dated relative to today (or `--on`). Refuses if the database already has areas unless `--replace`. Prints counts of every seeded collection. | implemented |
| `atlas export`        | Write a JSON export to stdout                                                                                                      | implemented |
| `atlas import <file>` | Load a JSON export. `--replace` clears user rows first.                                                                            | implemented |
| `atlas serve`         | Serve the HTTP API and, when `web/dist` exists, the SPA on `127.0.0.1:8000`.                                                       | implemented |

## API

The HTTP side of backup and restore:

| Method   | Path                     | Purpose                                       | Status      |
| -------- | ------------------------ | --------------------------------------------- | ----------- |
| `GET`    | `/export`                | Full JSON export                              | implemented |
| `POST`   | `/import`                | Full JSON import                              | implemented |

## Demo data

| Function | Role |
| -------- | ---- |
| `seed_demo` | Demo dataset. Builds a payload in the export shape dated relative to `as_of` (default `Settings.today()`) and loads it through `import_all`. Six areas (health, career, finance, relationships, screen, habits), metrics covering every `value_type`, daily/weekly/monthly habits of every kind (check, count, duration, and a `no-doomscrolling` quit habit with two slips) with times of day, a one-day skip, `at_most`, and a weekday mask, both goal kinds in a long→medium→short tree, linked weekly tasks, screen taxonomy (entertainment / social / productivity / learning), devices, a waste cap, ~28 days of mostly interval sessions, an entertainment library (topics plus films/series/books/podcasts/videos/anime/music in mixed statuses, most finished titles rated, a few with links), and ~4 weeks of staged sleep nights (a few skipped, later wake on weekends) so `habit statuses / goal progress / `screen_dashboard` / `entertainment_dashboard` / `sleep_view` are non-empty. `SeedSummary` counts areas, metrics, habits, goals, milestones, entries, tasks, screen categories, apps, devices, sessions, entertainment topics, titles, and sleep sessions. Refuses when areas already exist unless `replace=True`. Entries and sessions are sourced as `import`. |
