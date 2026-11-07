# Navigation

The sidebar, every SPA route, and the page inventory. Each route path in
`web/src/App.tsx` must appear in the table below; `web/src/docs-drift.test.ts` fails otherwise.
Page behaviour is described in each feature's doc under [domain/](../domain/) (section
**Screens**).

## Routes

| Path            | Page                                      | Status      |
| --------------- | ----------------------------------------- | ----------- |
| `/`               | Home: Sleep and Screen Time summary cards, then Tasks and the weekly Habits confirm grid | implemented |
| `/week`           | Redirects to `/habit?period=week` (preserves `?on=`) | implemented |
| `/sleep`          | Display-only: Week / Month / 90 days range, time asleep trend, bedtime and wake consistency, stage split, read-only nights list with No data gaps | implemented |
| `/health`         | Placeholder ("Coming soon"); its design waits on the navigation discussion | implemented |
| `/adventure`      | Placeholder ("Coming soon"); its design waits on the navigation discussion | implemented |
| `/entertainment`  | Category icons, add from link, Everything / Insights dock | implemented |
| `/entertainment/:category` | Library table for one category (or `all`) with filter/sort, add/edit dialog | implemented |
| `/entertainment/insights` | Period dashboard: finished by kind and tag, recently finished | implemented |
| `/screen`         | Display-only period dashboard: totals, score, charts, heatmap, insights, cap status; collapsed Configure section for category judgment, app category, caps, and devices | implemented |
| `/tasks`          | Three-column work queue (today / upcoming / someday): create, complete, "Move to…" menu, optional goal link, `?goal=` filter | implemented |
| `/journal`        | Today's journal (write / edit), earlier entries | implemented |
| `/history`        | Every entry by day with metric and date filters and Hide automatic data (on by default); edit value, day, note; delete | implemented |
| `/area/:slug`   | Area dashboard (linked from Catalog)      | implemented |
| `/habit`        | Today checklist by time of day with one-tap check-ins, this week / this month progress, 7/30-day completion, week/month overview grid | implemented |
| `/habit/:slug`  | Habit detail: check-in, streaks, adherence, this week, recent check-ins (slips for quit habits), pauses & skips; edit, archive, delete | implemented |
| `/goal`         | Four-column north-star board (long / medium / short / this week's linked tasks) | implemented |
| `/goal/:slug`   | Goal detail: parent, children, linked tasks (add + view on `/tasks?goal=`), progress, pace, milestone toggles (linked from Catalog) | implemented |
| `/catalog`      | Create and edit areas, metrics, habits, goals (goal area is optional); slugs link to review pages | implemented |

## Sidebar and review pages

Health and Adventure are placeholder pages in the sidebar ("Coming soon / There is nothing to show on this page yet."); what they become is decided in the navigation discussion (`docs/plans/discussions/navigation-and-organization.md`). The header shows a menu button (narrow screens), the date, and a Settings button; there is no notifications bell. Review pages (Catalog, Area, Habit, Habits, Goal, Screen, Goals, Tasks, Entertainment, life sections) link back to Home.

## Catalog

Catalog and the create dialog accept optional area (None), horizon, parent, and description; the Home task form can link an optional goal. Catalog slugs link to `/area/:slug`, `/habit/:slug`, and `/goal/:slug`, preserving `?on=`.
