# Navigation

The sidebar, every SPA route, and the page inventory. Each route path in
`web/src/App.tsx` must appear in the table below; `web/src/docs-drift.test.ts` fails otherwise.
Page behaviour is described in each feature's doc under [domain/](../domain/) (section
**Screens**).

## Routes

| Path            | Page                                      | Status      |
| --------------- | ----------------------------------------- | ----------- |
| `/`               | Home: Sleep and Screen Time summary cards, then Today’s quests and the weekly Habits confirm grid | implemented |
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
| `/today`        | Quests: timeline of today’s sessions with Session done and, separately, Outcome achieved; unconfirmed sessions to resolve; due today; up next; Plan a session ([time blocks](../domain/time-blocks.md#screens)) | implemented |
| `/inbox`        | Quests: captured tasks not yet organized ([quests](../domain/quests.md#screens)) | placeholder (Q2) |
| `/quests`       | Quests: Main quests — ambitions with their goal cards and direct tasks, then independent goals | placeholder (Q2) |
| `/quests/ambitions/:id` | Quests: one ambition's goals and direct tasks | placeholder (Q2) |
| `/quests/goals/:id` | Quests: one goal's quest map (milestones, chapters, tasks) | placeholder (Q2) |
| `/side-quests`  | Quests: side quests and standalone tasks | placeholder (Q2) |
| `/side-quests/:id` | Quests: one side quest's chapters and tasks | placeholder (Q2) |
| `/calendar`     | Quests: Monday–Sunday week of sessions by hour (`?on=` picks the week); click an empty hour to plan a session, click a session to edit, complete, cancel, or delete ([time blocks](../domain/time-blocks.md#screens)) | implemented |

## Sidebar and review pages

The sidebar lists Home, the life sections, Screen Time, Habits, Journal, and History, then a **Quests** group: Today, Inbox, Main quests, Side quests, and Calendar (labels in sentence case per [ux-writing](ux-writing.md)). Inbox shows the number of items still to sort from `GET /views/inbox`, refreshed on every navigation and hidden at zero. Today and Calendar are built ([time blocks](../domain/time-blocks.md#screens)); the other quest pages are placeholders ("Coming soon" with a one-line hint of what will show) until Q2 of the [quest plan](../plans/quests-plan.md) builds them. Health and Adventure are placeholder pages in the sidebar ("Coming soon / There is nothing to show on this page yet."); what they become is decided in the navigation discussion (`docs/plans/discussions/navigation-and-organization.md`). The header shows a menu button (narrow screens), the date, and a Settings button; there is no notifications bell. Review pages (Catalog, Area, Habit, Habits, Screen, Entertainment, life sections) link back to Home.

## Catalog

Catalog creates and edits areas, metrics, and habits. Catalog slugs link to `/area/:slug` and `/habit/:slug`, preserving `?on=`. Quests are not in Catalog; they are created on the quest pages.
