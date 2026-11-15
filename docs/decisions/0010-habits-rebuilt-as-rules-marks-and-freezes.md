# 0010 — Habits rebuilt as rules, marks, and freezes

Status: accepted (2026-11-14, [habits brief](../plans/habits-brief.md) D21–D40, with the owner's
answers in [habits-plan.md](../plans/habits-plan.md#decisions-so-far)). Replaces section 7 and the
Home habits block of the [redesign brief](../plans/redesign-brief.md).

## Context

A habit used to be a target on a metric: a period, a comparator, a number, and a kind (check,
count, duration, quit). Every habit needed a metric and entries, so "Morning pushups" meant
logging a number, and a habit about sleep or screen time could not read the data Atlas already
had. Skips and pauses were a separate table, and editing a target silently re-judged every past
day.

## Decision

- **A habit is self-contained** (D21). It no longer has a metric. Its rule says how often (every
  day, specific days, times a week, times a month) and how it is checked.
- **Two checks only** (D28). *You tick it*: your answer for a day is a mark. *From your data*: a
  source from a fixed registry (`src/atlas/domain/habit_sources.py`) reads sleep, screen
  sessions, or sessions, with a threshold and a value ("Wake time before 07:00"). Anything Atlas
  or a device cannot measure is ticked (owner, 2026-11-14); count, duration, quit, and "exactly"
  leave the create flow. There is no "your entries" source.
- **One rule record per change** (D24). A rule edit applies from today by default and creates a
  new version starting today; "to all past days too" replaces every version. Name and time of day
  are not versioned. Each day is judged by the rule in force that day (owner: compare only from
  the day the rule changed, and keep both data results and manual answers in the backend).
- **Marks are the only stored answers.** A mark is Done or Not done for one habit and day; for a
  data habit it is "Set by you" and wins over the data (D23). Data results are computed on read
  ([decision 0002](0002-progress-computed-on-read.md)), never stored.
- **Freezes replace skips and pauses** (D26, D37): a date range for one habit or all habits; frozen
  days neither break a streak nor count.
- **Archive and Restore, plus Delete** (owner). Archive hides a habit and keeps its history;
  Restore brings it back. Delete removes it with its rules, marks, own freezes, and quest links.
- **A weekly or monthly habit's day without a tick is blank, never a cross** (owner); the
  period's figure carries the judgment.
- **Screen devices carry "complete up to"** (`complete_through`), set by whatever brings data in
  (imports, the API, the demo seed), so a data habit can tell final minutes from missing ones. No
  new CLI command (owner).
- **Addresses** (owner): Day `/habits`, Week `/habits/week`, a habit `/habit/:slug`; the old
  `/habit` and `/week` redirect.
- **Migration** (schema 15): each old habit becomes its first rule version plus one Done mark per
  day the old rule met; breaks become freezes; the metrics habits read are archived, entries kept
  ([migrations](../architecture/migrations.md)). Real data is not migrated by hand; the demo data
  is generated (owner).

## Consequences

- The app runs between phases: phase 1 replaces the old Habits screens and the Home block with a
  read-only list, and nothing writes the old shape.
- Until brief phase 2, nothing judges a day: Habits kept reads "—" on Home and This week.
- Screen caps keep the old period helpers in `domain/habits.py` until the habit side is rewritten.
- Partial logging, swipe to complete, forcing a data request, end-of-day retrieval, and a day
  boundary from sleep or set by you are open points, not decided here
  ([open points](../plans/open-points.md)).

See [habits](../domain/habits.md).
