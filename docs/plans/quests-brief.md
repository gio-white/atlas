# Quests: product brief (source)

The product specification for the quest model, as given on 8 Nov 2026, kept here unchanged in
substance so every session can read it. How it lands in Atlas — what is removed, the schema, the
API, the screens, and the decisions that resolve its open points — is in
[quests-plan.md](quests-plan.md). Where they differ, **the plan wins** (for example: Atlas is
single-user, so the brief's `user_id` and ownership checks do not apply).

## Part 1 — Product vision

The application helps users transform ambitions into concrete goals, organize goals into
manageable milestones, break work down into chapters and tasks, and schedule tasks into calendar
time blocks. It is inspired by video game quest systems but keeps a sophisticated, minimal,
modern productivity-app aesthetic.

It answers five questions: What do I want to achieve? Why am I pursuing it? What intermediate
outcomes do I need? What should I work on next? Am I actually following through?

It combines personal goal management, hierarchical planning, task management, calendar-based
execution, progress tracking, and accountability. Workflow: **CAPTURE → ORGANIZE → STRUCTURE →
SCHEDULE → EXECUTE → REVIEW**.

**Progressive planning** is a core principle: a user can capture "I want to become a better
software engineer" as an Ambition with no Goals, and later add a Goal, Milestones, optional
Chapters, Tasks, and finally Time Blocks.

Philosophy: encourage structure without enforcing complexity; allow missing intermediate levels;
keep organization, execution, and scheduling separate; preserve relationships and history; make
progress tangible; show how small actions contribute to larger outcomes. Never force a planning
questionnaire before creating something.

## Part 2 — Domain model

Entities: Ambition, Goal, Milestone, Chapter, Task, plus Side Quest, Inbox state, and Time Block.
Main Quest and Side Quest are organizational concepts, not separate execution systems.

- **Ambition** — a broad direction ("Achieve financial independence"). Title, description,
  optional target date. Can exist without Goals; contains Goals and direct Tasks; weighted
  progress from children; no measurable success criteria; may never be fully completed.
  Answers "Where do I want to go?"
- **Goal** — a concrete desired outcome ("Save €20,000", "Move to Copenhagen"). Optional
  Ambition; contains Milestones and direct Tasks; optional deadline; success description; weighted
  progress; manually completed or eligible for completion from its children. Answers "What do I
  want to achieve?"
- **Milestone** — an intermediate achievement within a Goal ("Secure a Data Engineering position
  in Copenhagen"). Belongs to a Goal; contains Chapters and/or direct Tasks simultaneously;
  optional deadline; weighted progress; manually completed or completed when all children are.
  Chapters are optional. Answers "What important intermediate result do I need?"
- **Chapter** — a coherent collection of work ("Rust fundamentals", "Housing research"). Belongs
  to a Milestone **or** a Side Quest, never both; contains Tasks; no own success criteria in V1;
  completion determined by its Tasks; about a week of work (recommendation). **A Chapter with zero
  Tasks is empty / not started and never automatically completed.**
- **Task** — an individual **outcome** ("Understand Rust ownership"), never a time commitment
  ("Study Rust for 30 minutes" is an activity, i.e. a Time Block). Title, optional description,
  status (TODO, IN_PROGRESS, COMPLETED), priority, estimated effort, optional due date, multiple
  Time Blocks, any supported hierarchy level, may start with no association. Suggested 30 min–3 h
  of effort, not enforced. Completed when the outcome is achieved, not when its time elapses.

## Part 3 — Main Quests and Side Quests

- **Main Quest** — activity associated with a Goal; the Goal is the anchor, even with no
  Milestones or Tasks yet. An Ambition alone, without a Goal, is not a Main Quest.
- **Side Quest** — independent activity not associated with a Goal ("Complete tax declaration").
  Can be a single Task, a larger activity with Chapters, or Chapters plus direct Tasks — the same
  shape as a Milestone. **No separate execution implementation**: the distinction is
  organizational. A Task with no Goal association is eligible to appear as an independent Side
  Quest. A Task directly under an Ambition is not automatically a Main Quest.

## Part 4 — Optional hierarchy

Supported: Ambition → Goal → Milestone → Chapter → Task; Ambition → Goal → Milestone → Task;
Ambition → Goal → Task; Ambition → Task; Goal → Milestone → Chapter → Task; Goal → Task; Side
Quest → Chapter → Task; Side Quest → Task; standalone Task. Start at any level. Never generate
empty intermediate entities; never force Chapters, Milestones, or Goals. Mixed children are
supported: a Milestone with Chapters and direct Tasks; an Ambition with Goals and direct Tasks.

## Part 5 — Inbox

Quick capture of unorganized items without deciding where they belong. A captured item enters the
Inbox; can be organized later; assigned to an existing entity or used to create a new one; leaves
the Inbox once organized. An organized but unscheduled Task is not in the Inbox. The Inbox is not a
calendar backlog; it represents organizational incompleteness. States to distinguish: unorganized,
organized but unscheduled, scheduled, completed. **The original Task identity is preserved — no
duplicates during organization.** Minimal required fields.

## Part 6 — Time Blocks and execution

Task = what I want to achieve; Time Block = when I intend to work towards it. One Task can have
many Time Blocks. Time Block attributes: id, task_id, start_at, end_at, status (SCHEDULED,
COMPLETED, CANCELLED), provider, external_event_id, created_at, updated_at. Missed/expired
handling is designed separately from Task completion. **Completing a Time Block does not complete
the Task** (after a session: block COMPLETED, task IN_PROGRESS). V1 supports estimated effort on
Tasks, planned duration on Time Blocks, and aggregated planned effort = sum of block durations. No
timer in V1; never claim planned time equals actual effort.

## Part 7 — Progress and completion

Hierarchical, weighted progress: parent progress = Σ(child progress × child weight), weights
normalized per parent, equal-weight defaults, calculation kept in a dedicated domain/service
layer, partially decomposed structures handled consistently and documented.

Completion: a Chapter is completed only when all its Tasks are (zero Tasks → not completed). A
Milestone is eligible when all direct Tasks and all Chapters are completed; a Goal when all direct
Tasks and all Milestones are; an Ambition when its Goals and direct Tasks are, if the user chooses
to complete it. Users may manually override completion of Goals and Milestones as an explicit
action; never silently complete at a progress threshold; a manual completion with unfinished
children preserves those children, and the UI makes the override clear.

## Part 8 — UX/UI direction

Inspired by quest systems, RPG quest journals, skill trees, modern productivity apps, and
Apple-like simplicity. Avoid excessive gamification, cartoonish looks, too many colours,
excessive metrics, and dense tables as the main experience. Motivating, structured,
sophisticated.

- **Navigation:** Main Quests, Side Quests, Inbox, Today / Execution, Calendar (insights and
  reviews later).
- **Main Quest overview:** Goals, optionally grouped under Ambitions, as cards (title,
  description, progress, target date, status, number of Milestones and Tasks, next actionable
  item). Ambitions without Goals and independent Goals stay visible. Not the full hierarchy.
- **Quest detail:** a Goal's hierarchy as a graphical tree or quest map, expandable/collapsible,
  clear distinction between levels, visible progress, direct access to Tasks, add children, parent
  relationships visible; obvious how Tasks contribute to the Goal.
- **Side Quest overview:** a separate area with standalone Tasks and structured Side Quests; same
  execution interface.
- **Inbox:** quick add; edit title and description; assign to an existing entity; create a new
  structural entity from it; convert into a standalone Side Quest; dismiss or archive; identity
  preserved.
- **Today / Execution:** today's Time Blocks, task names, parent context, times, completion
  controls, optionally unscheduled organized Tasks. Marking a session completed must not
  accidentally complete the Task.

## Part 9 — Data model guidance

Separate tables (ambitions, goals, milestones, side_quests, chapters, tasks, time_blocks); no
generic recursive table or graph database; explicit, domain-specific relationships with foreign
keys and constraints; prevent invalid parent combinations; avoid cycles. A Task has one canonical
organizational parent, is never duplicated when moved, and keeps its identity, completion history,
and Time Blocks.

## Parts 10–12 — Phases, tests, working rules

Phases: inspection and proposal; domain model; core UI; execution system (statuses, effort, Time
Blocks, multiple sessions, internal scheduling, progress aggregation, completion rules). Later and
out of scope: accountability (notifications, end-of-day and weekly reviews, completion history,
planned vs actual effort, logbook) and Google Calendar integration; internal scheduling must work
without it.

Acceptance criteria: (1) Ambition without Goals; (2) Ambition with direct Tasks; (3) Goal without
Ambition; (4) Goal with direct Tasks; (5) Goal with Milestones; (6) Milestone with Chapters and
direct Tasks; (7) Chapter with multiple Tasks; (8) Side Quest with Chapters and direct Tasks; (9)
standalone Task as Side Quest; (10) Inbox capture; (11) move Inbox Task into a Chapter without
duplication; (12) move a Task between parents preserving history; (13) multiple Time Blocks per
Task; (14) completing a Time Block leaves the Task In Progress; (15) all Chapter Tasks completed →
Chapter completed; (16) empty Chapter not completed; (17) Milestone completion considers Chapters
and direct Tasks; (18) Goal completion considers Milestones and direct Tasks; (19) manual Goal
completion with unfinished children preserves them; (20) weighted progress; (21) missing levels
cause no errors; (22) ownership boundaries (not applicable: single-user).

Working rules: think about the domain model before coding; don't add unjustified concepts; don't
overengineer the future; keep domain logic out of UI; keep scheduling separate from execution;
preserve identity and history; keep levels optional; reusable UI components; meaningful domain
tests; document architectural decisions; on ambiguity, explain options, recommend one, avoid
irreversible assumptions; never silently change the agreed model.
