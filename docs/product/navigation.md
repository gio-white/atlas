# Navigation

The rail, the tabs inside each destination, every SPA route, and the redirects from old
addresses. Each route path in `web/src/App.tsx` must appear in a table below;
`web/src/docs-drift.test.ts` fails otherwise. Home, the Habits pages, and a few small pages are in the main
bundle; every other page is loaded on first visit (`React.lazy`), which keeps the main bundle
under Vite's 500 kB warning.
Page behaviour is described in each feature's doc under [domain/](../domain/) (section
**Screens**).

The structure comes from the [redesign brief](../plans/redesign-brief.md) and
[decision 0007](../decisions/0007-five-destinations-on-a-rail.md). The brief lands in phases;
this page describes what is built now. **Phases 1 (the shell), 2 (Settings), 3 (Home), 4 (Stats), 5 (Library and Plan names, Not scheduled yet), and 7 (the visual pass: one accent, [design system](design-system.md#colour)) are built; phase 6 (habit links) has its API but no screen yet.** Other
pages keep their earlier content; the notes marked *until phase N* say what is still temporary.

## Destinations

Five destinations plus Settings. Labels, order, and addresses live in `web/src/lib/nav.ts`.

| Destination | Address | Tabs inside | Marked active on |
| ----------- | ------- | ----------- | ---------------- |
| Home | `/` | none | `/`, and `/journal` (Earlier notes, reached from Home) |
| Quests | `/quests` | Main quests · Side quests · Inbox · Plan | everything under `/quests` |
| Habits | `/habit` | none | everything under `/habit` |
| Stats | `/stats` | This week · Sleep · Screen time · Health | everything under `/stats` |
| Library | `/library` | none | everything under `/library` |
| Settings | `/settings` | Appearance · Screen time setup · Devices · Metrics · All entries | everything under `/settings` |

Habits keeps the address `/habit`: `/habits` is the API's list of habits.

## Shell

`web/src/components/Layout.tsx` and `web/src/components/shell/`.

- **Rail** (screens 768px and wider): a fixed left rail, 76px wide. Each item is an icon with
  its label underneath: Home, Quests, Habits, Stats, Library from the top, Settings at the
  bottom. The active item has the accent colour on icon and label and a raised surface,
  and carries `aria-current="page"`. Icons are house, map, repeat arrows, bar chart, and books;
  none is a quest level icon (compass, flag, diamond, bookmark, scroll).
- **Bottom tab bar** (narrower screens): the same five destinations in a fixed bar at the bottom.
  Settings is a gear in the header instead.
- **Inbox count**: the number of tasks still to sort, from `GET /views/inbox`, shows as a badge
  on the Quests item (rail and bottom bar) and on the Inbox tab. It refreshes on every
  navigation and whenever a screen changes the Inbox (the `atlas:inbox-changed` window event),
  and is hidden at zero.
- **Section tabs** (`SectionLayout`): a destination with sub-pages shows its title (`Quests`,
  `Stats`, `Settings`) with a row of text tabs underneath; the active tab is underlined in the
  accent colour. Each tab has its own address, so links and the back button work. On narrow
  screens the row scrolls sideways. A tab page keeps its own name as a screen-reader heading
  (`PageHeader` with `tab`), since the tab already shows it. Detail pages (an ambition, a goal,
  a side quest, a habit, a Library category) show no tabs; the quest ones keep their breadcrumb.
- **Header**: the date, which is also the **As of** control, and **Add**.
  - Pressing the date opens the date picker. While another date is chosen it reads
    "As of 7 Nov 2026" in the attention colour, with **Back to today** ("Today" on narrow
    screens). The date is kept in the address as `?on=`.
  - **Add** opens a menu with **Task** (a one-field dialog that adds the title to the Inbox,
    like the Inbox's own capture field) and **Entry** (the New entry dialog,
    [trackers and entries](../domain/trackers-and-entries.md#screens)).
- **What follows you between destinations**: only the As of date (`?on=`). A page's own filters
  stay with that page.
- There is no profile dialog, avatar, or "Home" link above page titles: the rail is always
  there. The display name and theme are in Settings → Appearance.

## Routes

| Path | Page | Status |
| ---- | ---- | ------ |
| `/` | Home: left, To confirm, Today (sessions with a Now line), Due today, Up next, Habits (today's, one tap), Note for today; right, This week so far, Main quests, Last night, Screen time today, In progress ([home](../domain/home.md)) | implemented |
| `/journal` | Earlier notes: the journal notes before today, newest first, reached from Home's Note for today ([journal](../domain/journal.md#screens)) | implemented |
| `/quests` | Quests → Main quests: each ambition with its goal cards (ring, status, date, counts, next action) and direct tasks, ambitions without goals included, then independent goals; new ambition and new goal | implemented |
| `/quests/side-quests` | Quests → Side quests: side quest cards with progress and standalone tasks; new side quest | implemented |
| `/quests/inbox` | Quests → Inbox: always-focused capture (Enter adds a title); each item can be edited, organized into any ambition, goal, milestone, chapter, or side quest (search picker), made standalone, turned into a new item, or archived ([quests](../domain/quests.md#screens)) | implemented |
| `/quests/plan` | Quests → Plan: Monday–Sunday week of sessions by hour (`?on=` picks the week); click an empty hour to plan a session, click a session to edit, complete, cancel, or delete; Not scheduled yet lists each goal's and side quest's next action with no upcoming session, and Schedule plans one ([time blocks](../domain/time-blocks.md#screens)) | implemented |
| `/quests/ambitions/:id` | One ambition: edit, complete or reopen, its goal cards (reorder, add) and direct tasks | implemented |
| `/quests/goals/:id` | One goal's quest map: breadcrumb, success description, completion (with override), a path of expandable milestones with chapters and tasks, direct tasks, add and reorder at every level | implemented |
| `/quests/side-quests/:id` | One side quest: edit, completion, its chapters and direct tasks (the same tree as a milestone) | implemented |
| `/habit` | Today checklist by time of day with one-tap check-ins, this week / this month progress, 7/30-day completion, week/month overview grid | implemented |
| `/habit/:slug` | Habit detail: check-in, streaks, adherence, this week, recent check-ins (slips for quit habits), pauses & skips; edit, archive, delete | implemented |
| `/stats/week` | Stats → This week: one Monday–Sunday week (`?on=` picks it; previous and next move by whole weeks) in five blocks, Quests, Habits, Sleep, Screen time, and Library, each number with its change from the same days last week ([this week](../domain/this-week.md)) | implemented |
| `/stats/sleep` | Stats → Sleep, display-only: Week / Month / 90 days range, time asleep trend, bedtime and wake consistency, stage split, read-only nights list with No data gaps | implemented |
| `/stats/screen-time` | Stats → Screen time, display-only period dashboard: totals, score, charts, heatmap, insights, cap status; a link to its setup in Settings | implemented |
| `/stats/health` | Stats → Health: an empty state, "No health data yet / This fills in once a device is connected." Health only ever shows device data | implemented |
| `/library` | Library: category icons, add from link, Everything / Insights dock ([library](../domain/library.md#screens)) | implemented |
| `/library/:category` | Library table for one category (or `all`) with filter/sort, add/edit dialog | implemented |
| `/library/insights` | Period dashboard: finished by kind and tag, recently finished | implemented |
| `/settings/appearance` | Settings → Appearance: theme (dark or light) and your name, both kept on this device | implemented |
| `/settings/entries` | Settings → All entries: every entry by day with metric and date filters and Hide automatic data (on by default); edit value, day, note; delete ([history](../domain/history.md)) | implemented |
| `/settings/screen-time` | Settings → Screen time setup: Good / Bad / Neutral per category, each app's category, daily caps ([screen time](../domain/screen-time.md#screens)) | implemented |
| `/settings/devices` | Settings → Devices: device names | implemented |
| `/settings/metrics` | Settings → Metrics: list, create, edit, and archive the metrics you manage, in plain words ([trackers and entries](../domain/trackers-and-entries.md#screens)) | implemented |

## Redirects

Old addresses still work. `Redirect` (`web/src/components/shell/Redirect.tsx`) keeps ids, the
query string (so the As of date and filters survive), and the hash.

| Path | Goes to |
| ---- | ------- |
| `/stats` | `/stats/week` (the first Stats tab) |
| `/settings` | `/settings/appearance` |
| `/week` | `/habit?period=week` |
| `/side-quests` | `/quests/side-quests` |
| `/side-quests/:id` | `/quests/side-quests/:id` |
| `/inbox` | `/quests/inbox` |
| `/calendar` | `/quests/plan` |
| `/sleep` | `/stats/sleep` |
| `/screen` | `/stats/screen-time` |
| `/health` | `/stats/health` |
| `/adventure` | `/` (Adventure is removed) |
| `/entertainment/*` | `/library/*` (the home, a category, and Insights) |
| `/history` | `/settings/entries` |
| `/today` | `/` (the quest Today page merged into Home) |
| `/catalog` | `/settings/metrics` (Catalog is removed) |
| `/area/:slug` | `/settings/metrics` (areas are removed) |

Any other unknown address goes to Home.

## What was removed

Catalog and area pages are gone ([decision 0008](../decisions/0008-areas-removed-metrics-carry-an-origin.md)).
Metrics are managed in Settings → Metrics, habits are created and edited on the Habits pages, and
quests on the quest pages. Settings shows only sections that work; there are no placeholders.
