# Discussion: how Atlas is organized

> **How to use this file.** Paste it into a chat (or say "let's go through
> `docs/plans/discussions/navigation-and-organization.md`") and we work through the questions
> in §6, one at a time. The goal is a short list of decisions (§8), not code. When we agree,
> the decisions become Track T2 in `docs/plans/2026-11-restructure.md`.

## 1. What we are deciding

How the app's pages, sidebar, and concepts fit together, so that:

- every idea in Atlas has **one home and one name**, and that name is the same in the UI and the
  API;
- you can tell from the sidebar alone where something lives;
- the app stays **comprehensive** (you prefer depth over minimalism), without feeling like a
  database admin tool.

## 2. Fixed points (already decided, not up for discussion here)

- Single user, runs on this computer only, no accounts.
- Everything shown (streaks, progress, pace, totals) is computed from recorded facts when the
  page loads; nothing is stored twice.
- **Sleep and Screen Time are display-only.** Their data will come from devices through a
  future pipeline. Their configuration (good/bad apps, categories, caps, device names) lives in
  Settings.
- The web app is the only screen; the command-line tool is admin only.
- Goals get their own discussion (`goals.md`). Here we only decide *where* goals sit.
- Your preference so far: **Health should be a section of its own.**

## 3. What exists today

### 3.1 The sidebar

Home · Sleep · Health *(empty)* · Adventure *(empty)* · Entertainment · Screen Time · Goals ·
Habits · Tasks · Journal · History. Two more pages are reachable only indirectly:
**Catalog** (via the settings gear) and **Area pages** `/area/<name>` (via links in Catalog).

### 3.2 The building blocks, as the code names them

| Code name | What it is | Where you see it today |
| --------- | ---------- | ---------------------- |
| **Area** | A part of life that groups metrics: Health, Career, Finance, Relationships. Goals can be tagged with one. | Catalog, Area pages |
| **Metric** | A definition of something measured: pushups (count, summed per day), weight (kg, latest value), mood (rating, averaged). Stores no values. | Catalog, New Entry dropdown, History filter |
| **Entry** | One recorded value of a metric on a day. | History, New Entry |
| **Habit** | A recurring commitment on a metric: "≥ 40 pushups every day". Creating a habit can create its metric automatically. | Habits pages, Home grid |
| **Goal** | An outcome by a date, long / medium / short term, optionally nested. | Goals pages |
| **Task** | A one-off to-do, optionally linked to a goal. | Tasks page, Home |
| **Journal** | A daily text note (stored as entries of a `journal` metric). | Journal page |
| **Sleep night / Screen session** | Device data with its own tables. | Sleep, Screen Time |
| **Entertainment title** | A library of films, books, podcasts, music. Own tables. | Entertainment |

There are also internal areas the user never chose: `habits` (where habit-created metrics go),
`screen` (one metric per app), and `life` (the journal metric).

### 3.3 What "Catalog" is

One long admin page with raw forms to create and edit areas, metrics, habits, and goals. It shows
internal fields (IDs like `deep-work-weekdays`, `higher_is_better`, `at_least`, `sum` / `last`).
Habits and goals can also be created on their own pages, so Catalog mostly duplicates them.

## 4. What is confusing

1. **Two unrelated groupings share names.** The sidebar's *Health* page is a hard-coded empty
   section. The *Health area* (with weight, pushups, the bodyweight goal) is something else, and
   is only reachable through Catalog.
2. **Three different kinds of thing are mixed in one flat sidebar:**
   - *parts of life* (Health, Adventure),
   - *tools you act with* (Goals, Habits, Tasks, Journal),
   - *data that is recorded for you* (Sleep, Screen Time), plus a *library* (Entertainment).
3. **Too many concepts with technical names**: area, metric, entry, habit, goal, milestone, task,
   screen category, judgment, cap, device, topic.
4. **Catalog** exposes internals and duplicates create/edit flows.
5. **Sections vs areas are not defined.** Sleep, Screen Time, and Entertainment have their own
   data models and dashboards. Areas are user-defined groups of metrics. Health and Adventure are
   currently neither.

## 5. Options for the overall structure

### Option A — Tools first, areas as a filter

```text
Today
Goals · Habits · Tasks · Journal
Sleep · Screen Time · Health · Entertainment
History · Settings
```

Areas are not in the sidebar; every tool page has an area filter ("Show: All / Health / Career…").

- **For:** closest to today; few top-level items; tools are what you open daily.
- **Against:** areas stay second-class; there is no single page that shows "everything about my
  Finance".

### Option B — Life areas first, tools inside each area

```text
Today
Health · Career · Finance · Relationships · Adventure   (your areas)
Sleep · Screen Time · Entertainment
History · Settings
```

Each area page has tabs: Overview · Goals · Habits · Tasks · Trackers. There are also global
Goals / Habits / Tasks views, but they are secondary.

- **For:** matches how people think about their life; very comprehensive per area.
- **Against:** daily habit check-ins and the goals tree get split across pages; anything without
  an area needs a home.

### Option C — Grouped sidebar (proposal from the plan)

```text
Today
PLAN & ACT        Goals · Habits · Tasks · Journal
LIFE AREAS        your own list (Career, Finance, …)
SECTIONS          Health · Sleep · Screen Time · Entertainment   (dedicated dashboards)
History · Settings
```

- **For:** every kind of thing gets its own visible group; areas get full dashboards; tools stay
  one click away.
- **Against:** the longest sidebar; the difference between a *life area* and a *section* has to
  be crisp (see question 2).

### Option D — Hubs

```text
Today
Plan     (Goals, Habits, Tasks as tabs)
Life     (areas as tabs or cards)
Data     (Sleep, Screen Time, Health as tabs)
Library  (Entertainment, Journal)
History · Settings
```

- **For:** the shortest sidebar; very structured.
- **Against:** two clicks to anything; tabs inside tabs.

## 6. Questions to answer, in order

1. **What do you open Atlas for, day to day?** (Check habits? Review the week? Look at sleep?)
   This decides what is one click away.
2. **Section vs life area.** Proposed definition: a *section* has its own kind of data and a
   purpose-built dashboard (Sleep, Screen Time, Entertainment, Health); a *life area* is your own
   label to group goals, habits, and trackers (Career, Finance, Relationships). Does that match how
   you see it? Is Adventure a section (trips, places, with its own data) or a life area?
3. **What is Health, concretely?** Which data would its page show (weight, workouts, steps,
   heart rate, nutrition, medical)? Is any of it device data, like Sleep (display-only)? Should
   Sleep be *inside* Health?
4. **Can something belong to several areas, or exactly one?** (Today: a metric belongs to exactly
   one area; a goal has at most one area tag; habits and tasks have none of their own.)
5. **Which structure (A–D, or a mix)?**
6. **Names, consistent in the UI *and* the API.** Keep the code names everywhere (Area, Metric,
   Entry), or rename everywhere (for example Life area / Tracker / Record, with the API
   following: `/trackers`, `/records`)? Renaming the API is a large but mechanical change.
7. **What replaces Catalog?** Proposed: create and edit things where they live (habits on
   Habits, areas on their area page), with a Settings page for lists, ordering, and archiving.
   Do you want a single "manage everything" page anyway?
8. **Metric setup.** Replace the three technical choices (type, how values combine, whether
   higher is better) with plain presets (Yes/no, Count per day, Measurement, Time spent, Rating,
   Note), keeping an "Advanced" option?
9. **Home ("Today").** Today it has Sleep, Screen Time, Tasks, and a weekly Habits grid. Once the
   structure is chosen, what belongs there?
10. **Journal**: a tool next to Goals and Habits, or part of Today?

## 7. Out of scope here

The design of the Goals pages (separate discussion), data pipelines, running Atlas on other
devices, New Entry improvements.

## 8. Output of the discussion

A short decision list, which becomes T2's brief:

```text
D1 Structure: …
D2 Section vs area: …
D3 Health: …
D4 Area membership: …
D5 Names (UI + API): …
D6 Catalog replacement: …
D7 Metric setup: …
D8 Home contents: …
D9 Journal placement: …
```
