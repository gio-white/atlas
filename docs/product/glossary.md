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
| An outcome by a date | Goal | `Goal`, `/goals` | [goals](../domain/goals.md) |
| A manual step of a goal | Milestone | `Milestone` | [goals](../domain/goals.md) |
| How far ahead a goal looks | Long / Medium / Short term | `horizon`: `long`, `medium`, `short` | [goals](../domain/goals.md) |
| Whether a goal is on track | Ahead / On track / Behind / Overdue / Achieved / No data | `pace_status` | [goals](../domain/goals.md) |
| A one-off to-do | Task | `Task`, `/tasks` | [tasks](../domain/tasks.md) |
| Today / Upcoming / Someday | same | `bucket`: `today`, `upcoming`, `someday` | [tasks](../domain/tasks.md) |
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
