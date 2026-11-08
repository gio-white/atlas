# Navigation

The sidebar, every SPA route, and the page inventory. Each route path in
`web/src/App.tsx` must appear in the table below; `web/src/docs-drift.test.ts` fails otherwise.
Page behaviour is described in each feature's doc under [domain/](../domain/) (section
**Screens**).

## Routes

| Path            | Page                                      | Status      |
| --------------- | ----------------------------------------- | ----------- |
| `/`               | Home: Sleep and Screen Time summary cards, then the weekly Habits confirm grid | implemented |
| `/week`           | Redirects to `/habit?period=week` (preserves `?on=`) | implemented |
| `/sleep`          | Display-only: Week / Month / 90 days range, time asleep trend, bedtime and wake consistency, stage split, read-only nights list with No data gaps | implemented |
| `/health`         | Placeholder ("Coming soon"); its design waits on the navigation discussion | implemented |
| `/adventure`      | Placeholder ("Coming soon"); its design waits on the navigation discussion | implemented |
| `/entertainment`  | Category icons, add from link, Everything / Insights dock | implemented |
| `/entertainment/:category` | Library table for one category (or `all`) with filter/sort, add/edit dialog | implemented |
| `/entertainment/insights` | Period dashboard: finished by kind and tag, recently finished | implemented |
| `/screen`         | Display-only period dashboard: totals, score, charts, heatmap, insights, cap status; collapsed Configure section for category judgment, app category, caps, and devices | implemented |
| `/journal`        | Today's journal (write / edit), earlier entries | implemented |
| `/history`        | Every entry by day with metric and date filters and Hide automatic data (on by default); edit value, day, note; delete | implemented |
| `/area/:slug`   | Area dashboard (linked from Catalog)      | implemented |
| `/habit`        | Today checklist by time of day with one-tap check-ins, this week / this month progress, 7/30-day completion, week/month overview grid | implemented |
| `/habit/:slug`  | Habit detail: check-in, streaks, adherence, this week, recent check-ins (slips for quit habits), pauses & skips; edit, archive, delete | implemented |
| `/catalog`      | Create and edit areas, metrics, and habits; slugs link to review pages | implemented |
| `/today`        | Quests: today's time blocks, unconfirmed sessions, due today, up next ([time blocks](../domain/time-blocks.md#screens)) | placeholder (Q3) |
| `/inbox`        | Quests: always-focused capture (Enter adds a title); each item can be edited, organized into any ambition, goal, milestone, chapter, or side quest (search picker), made standalone, turned into a new item, or archived ([quests](../domain/quests.md#screens)) | implemented |
| `/quests`       | Quests: Main quests — each ambition with its goal cards (ring, status, date, counts, next action) and direct tasks, ambitions without goals included, then independent goals; new ambition and new goal | implemented |
| `/quests/ambitions/:id` | Quests: one ambition — edit, complete or reopen, its goal cards (reorder, add) and direct tasks | implemented |
| `/quests/goals/:id` | Quests: one goal's quest map — breadcrumb, success description, completion (with override), a path of expandable milestones with chapters and tasks, direct tasks, add and reorder at every level | implemented |
| `/side-quests`  | Quests: side quest cards with progress and standalone tasks; new side quest | implemented |
| `/side-quests/:id` | Quests: one side quest — edit, completion, its chapters and direct tasks (the same tree as a milestone) | implemented |
| `/calendar`     | Quests: week view of time blocks | placeholder (Q3) |

## Sidebar and review pages

The sidebar lists Home, the life sections, Screen Time, Habits, Journal, and History, then a **Quests** group: Today, Inbox, Main quests, Side quests, and Calendar (labels in sentence case per [ux-writing](ux-writing.md)). Inbox shows the number of items still to sort from `GET /views/inbox`, refreshed on every navigation and whenever a quest screen changes something (the `atlas:inbox-changed` window event), and hidden at zero. Today and Calendar are placeholders ("Coming soon" with a one-line hint of what will show) until Q3 of the [quest plan](../plans/quests-plan.md) builds them; the other quest pages are described in [quests](../domain/quests.md#screens). Any task row on them opens the task drawer. Health and Adventure are placeholder pages in the sidebar ("Coming soon / There is nothing to show on this page yet."); what they become is decided in the navigation discussion (`docs/plans/discussions/navigation-and-organization.md`). The header shows a menu button (narrow screens), the date, and a Settings button; there is no notifications bell. Review pages (Catalog, Area, Habit, Habits, Screen, Entertainment, life sections) link back to Home.

## Catalog

Catalog creates and edits areas, metrics, and habits. Catalog slugs link to `/area/:slug` and `/habit/:slug`, preserving `?on=`. Quests are not in Catalog; they are created on the quest pages.
