# Data model

All tables at a glance. Field-level tables live in each feature's doc:

| Table | Doc |
| ----- | --- |
| `Area` | [life areas](../domain/life-areas.md#data-model) |
| `Metric`, `Entry` | [trackers and entries](../domain/trackers-and-entries.md#data-model) |
| `Goal`, `Milestone` | [goals](../domain/goals.md#data-model) |
| `Habit`, `HabitBreak` | [habits](../domain/habits.md#data-model) |
| `ScreenCategory`, `ScreenApp`, `ScreenBudget`, `ScreenDevice`, `ScreenSession` | [screen time](../domain/screen-time.md#data-model) |
| `SleepSession`, `SleepSessionStage` | [sleep](../domain/sleep.md#data-model) |
| Life catalog (journal rows) | [journal](../domain/journal.md#data-model) |
| `Task` | [tasks](../domain/tasks.md#data-model) |
| `EntertainmentTopic`, `EntertainmentTitle`, `EntertainmentTitleTopic` | [entertainment](../domain/entertainment.md#data-model) |
| `SchemaVersion` | [migrations](migrations.md) |

## Overview

Integer primary keys are internal. Slugs are the human key and are what the API accepts: unique per entity type, lowercase, `[a-z0-9-]`.

```mermaid
flowchart TD
  Area[Area: life aspect] -->|groups| Metric[Metric: what is measured]
  Metric -->|has many| Entry[Entry: one observation]
  Habit[Habit: recurring commitment] -->|measured by| Metric
  Goal[Goal: outcome by a date] -->|optional tag| Area
  Goal -->|measured by| Metric
  Goal -->|has many| Milestone[Milestone: manual checkpoint]
  Goal -->|optional parent| Goal
  Goal -->|optional| Task[Task: one-off work item]
  ScreenCategory[ScreenCategory] -->|judgment| ScreenJudgment[useful waste or neutral]
  ScreenApp[ScreenApp] -->|classified as| ScreenCategory
  ScreenApp -->|backing| Metric
  ScreenApp -->|has many| ScreenSession[ScreenSession]
  ScreenSession -->|optional| ScreenDevice[ScreenDevice]
  ScreenBudget[ScreenBudget] -->|caps| ScreenJudgment
  ScreenBudget -->|or caps| ScreenCategory
  EntertainmentTopic[EntertainmentTopic]
  EntertainmentTitle[EntertainmentTitle]
  EntertainmentTopic -->|M2M tags| EntertainmentTitle
  SleepSession[SleepSession: one night] -->|has many| SleepSessionStage[SleepSessionStage: deep light rem awake]
```
