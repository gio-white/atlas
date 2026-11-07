# Vision

What Atlas is and is not. The decision records in [decisions/](../decisions/) hold the reasons
for the choices below.

## Purpose

Atlas is a single-user, local-first life-tracking backend. It records what actually happened, then layers commitments (habits) and outcomes (goals) on top of that record. Everything a review screen wants to show — streaks, adherence, goal progress, whether a goal is on pace — is computed on read from the recorded facts.

Consequences of that stance:

- Backfilling an entry for last Tuesday automatically corrects every streak, adherence ratio, and goal percentage that depends on it. There is no recalculation step and nothing to migrate.
- There is exactly one capture path for habits and goals. They point at metrics; they never store their own observations. Screen time is the exception: sessions are stored in `screen_session` and dual-written onto the app's backing entry.
- The React SPA in `web/` is the only frontend. It is an HTTP client of the API: it has no privileged access and no streaks, adherence, or progress of its own to reimplement. The CLI is an in-process admin adapter (`init`, `seed`, `serve`, export/import). Capture, definition, and review all go through the SPA.
