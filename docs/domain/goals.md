# Goals

## Purpose

Outcomes to reach by a date, arranged in an optional long → medium → short tree, with progress and pace computed on read.

## Concepts

- **Goal** — `metric_target` (a value on a metric) or `milestone` (manual checkpoints).
- **Horizon** — `long`, `medium`, or `short`.
- **Milestone** — a manual checkpoint.
- **Progress** — a fraction from baseline to target.
- **Pace** — progress compared with elapsed time.

## Data model

### Goal

An outcome to reach by a date. Goals are a dedicated table, not a child of Area. Two kinds share one table because they share a lifecycle and a due date. Goals form an optional tree: long-term (1+ year north star) → medium-term (months) → short-term (about a week). Parent is optional. Child and parent need not share an area. Area is an optional tag; untagged goals still appear on the north-star board.

| Field            | Type            | Notes                                                                            |
| ---------------- | --------------- | -------------------------------------------------------------------------------- |
| `id`             | int             | primary key                                                                      |
| `area_id`        | int \| None     | optional FK to `Area`; a tag, not ownership                                      |
| `slug`           | str             | unique                                                                           |
| `name`           | str             |                                                                                  |
| `kind`           | enum            | `metric_target | milestone`                                                      |
| `metric_id`      | int | None      | required when `kind` is `metric_target`                                          |
| `target_value`   | float | None    | required when `kind` is `metric_target`                                          |
| `comparator`     | enum | None     | `at_least | at_most | exactly`; required when `kind` is `metric_target`          |
| `baseline_value` | float | None    | optional explicit starting point; see [goal progress](#goal-progress)            |
| `measure`        | enum | None     | `latest_value | cumulative_since_start`; required when `kind` is `metric_target` |
| `start_on`       | date            | inclusive                                                                        |
| `due_on`         | date            | inclusive                                                                        |
| `horizon`        | enum            | `long | medium | short` — stored, not re-derived on read                         |
| `parent_id`      | int | None      | FK to `Goal`; long has none; medium may parent under long; short under medium    |
| `description`    | str | None      | card copy                                                                        |
| `status`         | enum            | `active | achieved | paused | abandoned`                                         |
| `achieved_at`    | datetime | None | UTC                                                                              |

`horizon` is chosen by the user or inferred once on create/import from `due_on - start_on`: **≥365 days → long**, **≥28 days → medium**, else **short**. Changing `horizon` is rejected while the goal has children. A goal cannot parent itself.

A `metric_target` goal still requires a metric. The metric must belong to the tagged area only when both area and metric are set.

`measure` distinguishes the two shapes of numeric goal: `latest_value` for "weigh 75 kg" (the current reading is what matters), `cumulative_since_start` for "read 12 books this year" (the running total is what matters).

### Milestone

A manual checkpoint under a goal. Available to both goal kinds, so a `metric_target` goal can still carry qualitative steps.

| Field     | Type            | Notes                  |
| --------- | --------------- | ---------------------- |
| `id`      | int             | primary key            |
| `goal_id` | int             | FK to `Goal`           |
| `name`    | str             |                        |
| `due_on`  | date | None     |                        |
| `done_at` | datetime | None | UTC; `None` means open |

## Rules and calculations

### Goal progress

`goal_progress(goal, as_of)` returns the current value, the baseline, a fraction in `0.0 … 1.0`, and whether the target is met.

For `kind = metric_target`, the current value depends on `measure`:

- `latest_value` — the value of the most recent entry with `occurred_on <= as_of`. `None` if there is no such entry.
- `cumulative_since_start` — the sum of `value_num` over entries with `start_on <= occurred_on <= as_of`.

The baseline is `baseline_value` when set. Otherwise it is:

- for `latest_value`, the value of the most recent entry with `occurred_on <= start_on`, falling back to the current value (a goal with no history starts at 0 % rather than dividing by nothing),
- for `cumulative_since_start`, `0.0`.

The fraction is

```
fraction = clamp((current - baseline) / (target_value - baseline), 0.0, 1.0)
```

Signed arithmetic handles both directions with one formula: for "lose weight to 75 kg" the numerator and denominator are both negative, so shedding kilos moves the fraction up. When `target_value == baseline`, the fraction is `1.0` if the target is met and `0.0` otherwise. When the current value is `None`, the fraction is `None`.

The target is met when the comparator holds against `target_value`, using the same three comparisons as habit satisfaction. Reaching it does not by itself change `status`; a service marks the goal `achieved` and stamps `achieved_at`.

For `kind = milestone`, the fraction is `done_milestones / total_milestones`, `None` when the goal has no milestones, and the target is met when every milestone is done.

### Pace status

`pace_status(goal, as_of)` answers "is this on track" by comparing progress against elapsed time.

```
elapsed = clamp((as_of - start_on) / (due_on - start_on), 0.0, 1.0)   # inclusive day counts
```

| Status     | Condition                                  |
| ---------- | ------------------------------------------ |
| `achieved` | the target is met                          |
| `overdue`  | `as_of > due_on` and the target is not met |
| `no_data`  | the progress fraction is `None`            |
| `ahead`    | `fraction > elapsed + 0.05`                |
| `on_track` | `fraction` within `0.05` of `elapsed`      |
| `behind`   | `fraction < elapsed - 0.05`                |

The `0.05` tolerance keeps a goal from flickering between `ahead` and `behind` on consecutive days. When `due_on == start_on`, `elapsed` is `1.0` from the start date onward.

Parent progress is never a rollup of children. The goals board column “on track” count is view-level: among non-paused, non-abandoned goals in that horizon, pace in `{on_track, ahead, achieved}` over the column total.

## API

Conventions shared by every endpoint (slugs, `as_of`, errors): [api-conventions](../architecture/api-conventions.md).

| Method   | Path                     | Purpose                                       | Status      |
| -------- | ------------------------ | --------------------------------------------- | ----------- |
| `GET`    | `/goals`                 | List goals (`area`, `status`, `horizon`, `parent`) | implemented |
| `POST`   | `/goals`                 | Create a goal                                 | implemented |
| `GET`    | `/goals/{slug}`          | Get one goal including milestones             | implemented |
| `PATCH`  | `/goals/{slug}`          | Update name, due date, target, status, horizon, parent, description, or area | implemented |
| `GET`    | `/goals/{slug}/progress` | Progress and pace for a goal                  | implemented |
| `POST`   | `/goals/{slug}/milestones/{name}/toggle` | Toggle a milestone done | implemented |
| `GET`    | `/views/goals`           | Horizon columns plus this week's linked tasks | implemented |

Service functions (in `src/atlas/services/`, each taking an explicit `Session` first; see [overview](../architecture/overview.md#services)):

| Function | Role |
| -------- | ---- |
| `create_goal` / `list_goals` / `get_goal` / `get_goal_detail` / `update_goal` / `goal_progress` / `goals_board` / `toggle_milestone` | Goals. Area is an optional tag. `metric_target` requires metric, target, comparator, and measure; the metric must match the tagged area only when both are set. `milestone` kind forbids those fields. Optional `MilestoneInput` values can be created with the goal. `horizon` is stored (`long` / `medium` / `short`); omitted on create it is inferred from the date window. `parent` is an optional slug of the previous horizon. `list_goals` can filter by area, status, horizon, and parent slug (area filter is tagged goals only). `get_goal_detail` includes milestones. `update_goal` may change name, `due_on`, `target_value`, status (`active` / `paused` / `abandoned`; not `achieved`), horizon, parent, description, and area (including clear). Horizon cannot change while children exist. `goal_progress` returns current/baseline/fraction/`target_met` plus `pace_status`, horizon, parent slug, and description. `goals_board` groups non-paused, non-abandoned goals by horizon with column on-track counts and this week's linked tasks. When the target is met and `status` is still `active`, the service sets `status = achieved` and stamps `achieved_at`; it does not reopen an achieved, paused, or abandoned goal. |

## Screens

`/goal` is the four-column north-star board from `GET /views/goals` (long / medium / short plus this week's linked tasks). Goal detail shows parent, children, and linked tasks.

Route inventory with status: [navigation](../product/navigation.md).

## Tests

- `tests/domain/test_goals.py`, `tests/domain/test_horizons.py`
- `tests/services/test_goals.py`
- `tests/api/test_goals.py`
- `web/src/lib/horizons.test.ts`

## Status

Implemented. Review pending (`docs/plans/discussions/goals.md`).
