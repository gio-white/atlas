# 0006 — The quest model replaces goals and tasks

Status: accepted (2026-11-08, [quests plan](../plans/quests-plan.md)).

## Context

Atlas had metric-target and milestone goals in a long / medium / short horizon tree, with pace,
checkpoint milestones, area tags, habit links, and a separate today / upcoming / someday task
queue. The [quests brief](../plans/quests-brief.md) asks for something different: ambitions,
goals, milestones, chapters, and tasks with optional levels, side quests, an Inbox, and time
blocks, with progress that comes only from the work under an item. Running both models side by
side would have meant two goal concepts, two task lists, and a migration between shapes that do
not map onto each other. The existing goal and task data was demo data.

## Decision

- The quest model **replaces** goals, milestones, and tasks outright. Schema 11 drops the old
  `goal`, `milestone`, and `task` tables and `habit.goal_id`, then creates `ambition`, `goal`,
  `milestone`, `side_quest`, `chapter`, `task`, and `time_block`. There is no data migration,
  no parallel period, and no backwards-compatible endpoint for the old shapes.
- One explicit table per level with typed foreign keys (`RESTRICT`, indexed) and CHECK
  constraints — no generic node table and no self-reference, so cycles cannot exist.
- Only explicit decisions are stored (statuses, completion, weights, order). Progress,
  completion eligibility, chapter state, next action, planned effort, and unconfirmed sessions
  are computed on read ([decision 0002](0002-progress-computed-on-read.md)).
- Quest entities use **integer ids** on the wire; they have no slug.
- Quests have no area tag and no link to metrics or habits; there is no pace and no
  metric-target goal. Progress comes only from children.
- Exports before version 11 still import; their `goals`, `milestones`, and `tasks` sections are
  ignored and the import summary says so.

## Consequences

- The Goals board, goal detail, Tasks page, Home Tasks card, habit ↔ goal link, and goal parts
  of the Area and Catalog pages are gone. The sidebar gets a Quests group (Today, Inbox, Main
  quests, Side quests, Calendar).
- Habit progress stays separate from quest progress.
- The remaining open points are settled in the plan's decisions D1–D17.

See [quests](../domain/quests.md) and [time blocks](../domain/time-blocks.md).
