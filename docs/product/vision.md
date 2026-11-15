# Vision

What Atlas is and is not. The decision records in [decisions/](../decisions/) hold the reasons
for the choices below.

## Purpose

Atlas is a single-user, local-first life-tracking backend. It records what actually happened, then layers commitments (habits) on top of that record, and plans what you want to achieve as quests (ambitions, goals, milestones, chapters, tasks, and time blocks). Everything a review screen wants to show — streaks, Habits kept, quest progress, completion eligibility — is computed on read from the stored facts.

Consequences of that stance:

- Data that arrives late (last night's sleep, a device's screen time) re-judges every habit day and streak that depends on it. There is no recalculation step and nothing to migrate.
- A habit stores only what you tell it: its rule versions, your ticks (marks), and freezes. A data habit reads sleep, screen sessions, or planned sessions on read; habits never read metrics or entries ([habits](../domain/habits.md)).
- The React SPA in `web/` is the only frontend. It is an HTTP client of the API: it has no privileged access and no streaks, Habits kept, or progress of its own to reimplement. The CLI is an in-process admin adapter (`init`, `seed`, `serve`, export/import). Capture, definition, and review all go through the SPA.
