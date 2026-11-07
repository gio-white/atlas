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
| `/sleep`          | Last night and 7-night card, Log night with optional stages, last 60 nights with delete | implemented |
| `/health`         | Empty Health section until the health domain cycle | implemented |
| `/adventure`      | Empty Adventure section until the adventure domain cycle | implemented |
| `/entertainment`  | Category icons, add from link, Everything / Insights dock | implemented |
| `/entertainment/:category` | Library table for one category (or `all`) with filter/sort, add/edit dialog | implemented |
| `/entertainment/insights` | Period dashboard: finished by kind and tag, recently finished | implemented |
| `/screen`         | Period dashboard: totals, score, charts, heatmap, insights, capture; session edit / delete, caps, category judgment and app category | implemented |
| `/tasks`          | Three-column work queue (today / upcoming / someday): create, complete, move bucket, optional goal link, `?goal=` filter | implemented |
| `/journal`        | Today's journal (write / edit), earlier entries | implemented |
| `/history`        | Every entry by day with metric and date filters; edit value, day, note; delete | implemented |
| `/area/:slug`   | Area dashboard (linked from Catalog)      | implemented |
| `/habit`        | Today checklist by time of day with one-tap check-ins, this week / this month progress, 7/30-day completion, week/month overview grid | implemented |
| `/habit/:slug`  | Habit detail: check-in, streaks, adherence, this week, recent check-ins (slips for quit habits), pauses & skips; edit, archive, delete | implemented |
| `/goal`         | Four-column north-star board (long / medium / short / this week's linked tasks) | implemented |
| `/goal/:slug`   | Goal detail: parent, children, linked tasks (add + view on `/tasks?goal=`), progress, pace, milestone toggles (linked from Catalog) | implemented |
| `/catalog`      | Create and edit areas, metrics, habits, goals (goal area is optional); slugs link to review pages | implemented |

## Sidebar and review pages

Health and Adventure are empty section shells in the sidebar until those domain cycles land. Review pages (Catalog, Area, Habit, Habits, Goal, Screen, Goals, Tasks, Entertainment, life sections) link back to Home.

## Catalog

Catalog and the create dialog accept optional area (None), horizon, parent, and description; the Home task form can link an optional goal. Catalog slugs link to `/area/:slug`, `/habit/:slug`, and `/goal/:slug`, preserving `?on=`.
