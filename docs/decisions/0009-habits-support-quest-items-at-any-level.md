# 0009 — Habits support quest items at any level

Status: accepted (2026-11-14, [redesign brief](../plans/redesign-brief.md) D16 and phase 6,
widened by the owner when the work started).

## Context

The brief asks for an optional, backend-only link between a habit and quest items: "A supported
item is an ambition, a goal or a side quest." Quests are deeper than that. A daily habit such as
"Deep work on weekdays" usually serves a concrete milestone, chapter, or even one long task, not
only the ambition at the top. The owner asked that every level be linkable, and that a link made
low in the tree still be visible from the levels above it.

## Decision

- A habit can support any quest item: an ambition, goal, milestone, side quest, chapter, or task.
  The same `QuestKind` values name the level everywhere (`kind` + `id`).
- One table, `habit_support`, with one nullable foreign key per level and a CHECK that exactly one
  is set, rather than a generic `kind` + `id` pair. Every link is a real reference (RESTRICT,
  indexed), like the quest tables themselves ([decision 0006](0006-quest-model-replaces-goals-and-tasks.md)).
- Reading from an item includes the links under it at any depth (`direct: false`, with
  `linked_to`), so a goal shows the habits on its milestones, chapters, and tasks. Reading from a
  habit gives each item with its path, so the chain above it is visible too. Inheritance is
  computed on read; only the direct link is stored ([decision 0002](0002-progress-computed-on-read.md)).
- The link is informational. No quest rule reads it: progress, completion and eligibility,
  weights, chapter state, and Next action never change because of it.
- Backend only for now: schema, service, and API (read, add, remove), plus export and the demo
  seed. No screen shows or edits links yet.

## Consequences

- Deleting a habit or an (empty) quest item deletes its links; archiving keeps them. Promoting an
  Inbox task moves its links to the item it becomes.
- Exports carry `habit_supports` from schema 14 ([migrations](../architecture/migrations.md));
  older exports import without links.
- A screen for links is future work and is not decided here.

See [habits](../domain/habits.md#quest-links).
