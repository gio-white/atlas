# Glossary

Every user-facing concept, the word the UI shows, and its name in the code. Decision 3 of the
[November plan](../plans/2026-11-restructure.md#7-decisions-8-nov-2026) applies: until the
navigation discussion picks final names, the UI uses the same words as the API. When a name
changes, change it here, in the UI, and in the API together.

| Concept | Shown in the UI as | In the code / API | Doc |
| ------- | ------------------ | ----------------- | --- |
| Something you measure | Metric | `Metric`, `/metrics` | [trackers and entries](../domain/trackers-and-entries.md) |
| One logged value | Entry | `Entry`, `/entries` | [trackers and entries](../domain/trackers-and-entries.md) |
| How a metric came to exist (never shown as a word; it decides where the metric appears) | "Made for a habit" for habit-made ones | `Metric.origin`: `manual`, `habit`, `screen`, `journal` | [trackers and entries](../domain/trackers-and-entries.md#data-model) |
| What you record / Several values in one day / Which way is better | Yes / no, Count, … / Add up the day, … / More is better, … | `value_type`, `aggregation`, `direction`, labelled in `web/src/lib/labels.ts` | [trackers and entries](../domain/trackers-and-entries.md#screens) |
| Entries written by a device rather than typed | Automatic data | `include_automatic` on `GET /entries` | [history](../domain/history.md) |
| A recurring commitment | Habit | `Habit`, `/habits` | [habits](../domain/habits.md) |
| A skip or pause of a habit | Skip / Pause | `HabitBreak`, `/habits/{slug}/breaks` | [habits](../domain/habits.md) |
| Marking a habit done or logging toward it | Check in | check-in (an `Entry`), `/habits/{slug}/checkins` | [habits](../domain/habits.md) |
| A broad direction in life | Ambition | `Ambition`, `/ambitions` | [quests](../domain/quests.md) |
| A concrete outcome you want | Goal | `Goal`, `/goals` | [quests](../domain/quests.md) |
| An important step on the way to a goal | Milestone | `Milestone`, `/milestones` | [quests](../domain/quests.md) |
| A batch of related work, about a week | Chapter | `Chapter`, `/chapters` | [quests](../domain/quests.md) |
| One outcome to achieve | Task | `Task`, `/tasks` | [quests](../domain/quests.md) |
| A goal and everything under it | Main quest | derived: a `Goal` tree, `/views/main-quests` | [quests](../domain/quests.md) |
| Something to get done outside any goal | Side quest | `SideQuest`, `/side-quests`; a standalone `Task` also counts | [quests](../domain/quests.md) |
| A task not yet sorted into a quest | Inbox | derived: no parent and `organized_at` empty, `/views/inbox` | [quests](../domain/quests.md) |
| A task you file on its own, outside any quest | Standalone task | `Task` with no parent and `organized_at` set | [quests](../domain/quests.md) |
| To do / In progress / Done | same | task `status`: `todo`, `in_progress`, `completed` | [quests](../domain/quests.md) |
| Low / Normal / High | same | task `priority` | [quests](../domain/quests.md) |
| How much a part counts toward its parent | Weight (shown as a percentage) | `weight` | [quests](../domain/quests.md) |
| A quest with nothing under it yet | Not broken down yet | `progress: null` | [quests](../domain/quests.md) |
| Marked done while parts are still open | Completed with open items | `completed_with_open_items` | [quests](../domain/quests.md) |
| Sorting an Inbox task into a quest (same task, new place) | Organize… / Move… | `POST /tasks/{id}/organize` | [quests](../domain/quests.md) |
| Making an Inbox task into a new ambition, goal, side quest, milestone, or chapter | Turn into… | `POST /tasks/{id}/promote` | [quests](../domain/quests.md) |
| Empty / Not started / In progress / Completed | same | chapter `state`: `empty`, `not_started`, `in_progress`, `completed` | [quests](../domain/quests.md) |
| The task to work on next | Next | `next_action` | [quests](../domain/quests.md) |
| A planned session on Plan | Session (time block) | `TimeBlock`, `/time-blocks` | [time blocks](../domain/time-blocks.md) |
| Next tasks with no upcoming session | Not scheduled yet (on Plan) | `not_scheduled` on `GET /views/plan` | [time blocks](../domain/time-blocks.md) |
| Recording that a session happened (the task stays open) | Session done | `POST /time-blocks/{id}/complete` | [time blocks](../domain/time-blocks.md) |
| Completing the task itself from a session | Outcome achieved | task `status: completed` via `PATCH /tasks/{id}` | [time blocks](../domain/time-blocks.md) |
| A session whose time passed without an answer | To confirm (on Home), Unconfirmed (on Plan and in the task's sessions) | derived: `scheduled` after `end_at` | [time blocks](../domain/time-blocks.md) |
| A session whose time came and that was not held | Didn't happen | `TimeBlockStatus.missed`, `POST /time-blocks/{id}/miss` | [time blocks](../domain/time-blocks.md) |
| A session called off ahead of time | Cancel / Cancelled | `TimeBlockStatus.cancelled`, `POST /time-blocks/{id}/cancel` | [time blocks](../domain/time-blocks.md) |
| Done sessions out of those due an answer this week | Sessions kept | `sessions_kept`, `GET /views/week-so-far` | [home](../domain/home.md) |
| One week's numbers against the same days last week | This week | `this_week`, `GET /views/this-week`, `ThisWeekPage` | [this week](../domain/this-week.md) |
| Pooled habit adherence this week | Habits kept | `habits_kept_share` | [home](../domain/home.md) |
| A cap on all screen time | All screen time | `ScreenBudgetTargetKind.total`, `target_slug: all` | [screen time](../domain/screen-time.md) |
| Total time planned in sessions | Planned time | `planned_minutes` (never "actual effort") | [time blocks](../domain/time-blocks.md) |
| A free-text daily note | Note for today; the past ones are Earlier notes | `journal` metric (origin `journal`), `/journal` | [journal](../domain/journal.md) |
| One night of sleep | Night | `SleepSession`, `/sleep/sessions` | [sleep](../domain/sleep.md) |
| Deep / Light / REM / Awake | same | `SleepSessionStage.stage` | [sleep](../domain/sleep.md) |
| Time spent in an app | Session | `ScreenSession`, `/screen/sessions` | [screen time](../domain/screen-time.md) |
| A group of apps | Category | `ScreenCategory` | [screen time](../domain/screen-time.md) |
| Good / Bad / Neutral | same | `judgment`: `useful`, `waste`, `neutral` | [screen time](../domain/screen-time.md) |
| A daily limit | Cap | `ScreenBudget`, `/screen/budgets` | [screen time](../domain/screen-time.md) |
| A phone or computer | Device | `ScreenDevice` | [screen time](../domain/screen-time.md) |
| A work in the library | Title | `LibraryTitle` | [library](../domain/library.md) |
| A label on a title | Tag | `LibraryTopic` | [library](../domain/library.md) |
| Everything ever recorded | History | `GET /entries` | [history](../domain/history.md) |
| Viewing the app on a past date | As of | `as_of` / `?on=` | [api conventions](../architecture/api-conventions.md) |

Words that never reach the UI are listed in [ux-writing](ux-writing.md).

## Renamed by the redesign

The [redesign brief](../plans/redesign-brief.md) renamed two things. The labels and addresses
changed with the shell (phase 1), the API and code with phase 5, so the UI word and the API word
are the same again. The old addresses redirect.

| Concept | Name in the UI, API, and code | Was |
| ------- | ----------------------------- | --- |
| Everything watched, read, and heard | Library (`/library`, API `/library/…`, `Library*`, tables `library_*`) | Entertainment |
| The week of planned sessions | Plan (`/quests/plan`, `GET /views/plan`, `PlanPage`) | Calendar |
| A habit's day / week / month history grid | Grid (`GET /views/habits/grid`, `habit_grid`) | calendar |

History is shown as **All entries** (Settings → All entries); the API is `GET /entries` as before.

**Area** is no longer a concept: metrics are not grouped, and there is no `/areas` in the API
([decision 0008](../decisions/0008-areas-removed-metrics-carry-an-origin.md)). **Catalog** is gone
too; metrics are managed in Settings → Metrics and habits on the Habits pages.
