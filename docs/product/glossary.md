# Glossary

Every user-facing concept, the word the UI shows, and its name in the code. Decision 3 of the
[November plan](../plans/2026-11-restructure.md#7-decisions-8-nov-2026) applies: until the
navigation discussion picks final names, the UI uses the same words as the API. When a name
changes, change it here, in the UI, and in the API together.

| Concept | Shown in the UI as | In the code / API | Doc |
| ------- | ------------------ | ----------------- | --- |
| A part of life that groups what you measure | Area | `Area`, `/areas` | [life areas](../domain/life-areas.md) |
| Something you measure | Metric | `Metric`, `/metrics` | [trackers and entries](../domain/trackers-and-entries.md) |
| One logged value | Entry | `Entry`, `/entries` | [trackers and entries](../domain/trackers-and-entries.md) |
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
| A planned session on the calendar | Session (time block) | `TimeBlock`, `/time-blocks` | [time blocks](../domain/time-blocks.md) |
| A session whose time passed without an answer | Not confirmed yet | derived: `scheduled` after `end_at` | [time blocks](../domain/time-blocks.md) |
| Total time planned in sessions | Planned time | `planned_minutes` (never "actual effort") | [time blocks](../domain/time-blocks.md) |
| A free-text daily note | Journal | `journal` metric in the `life` area, `/journal` | [journal](../domain/journal.md) |
| One night of sleep | Night | `SleepSession`, `/sleep/sessions` | [sleep](../domain/sleep.md) |
| Deep / Light / REM / Awake | same | `SleepSessionStage.stage` | [sleep](../domain/sleep.md) |
| Time spent in an app | Session | `ScreenSession`, `/screen/sessions` | [screen time](../domain/screen-time.md) |
| A group of apps | Category | `ScreenCategory` | [screen time](../domain/screen-time.md) |
| Good / Bad / Neutral | same | `judgment`: `useful`, `waste`, `neutral` | [screen time](../domain/screen-time.md) |
| A daily limit | Cap | `ScreenBudget`, `/screen/budgets` | [screen time](../domain/screen-time.md) |
| A phone or computer | Device | `ScreenDevice` | [screen time](../domain/screen-time.md) |
| A work in the library | Title | `EntertainmentTitle` | [entertainment](../domain/entertainment.md) |
| A label on a title | Tag | `EntertainmentTopic` | [entertainment](../domain/entertainment.md) |
| Everything ever recorded | History | `GET /entries` | [history](../domain/history.md) |
| Viewing the app on a past date | As of | `as_of` / `?on=` | [api conventions](../architecture/api-conventions.md) |

Words that never reach the UI are listed in [ux-writing](ux-writing.md).
