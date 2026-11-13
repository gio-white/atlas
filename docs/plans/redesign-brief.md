# Atlas redesign brief: navigation, Home, Stats and Settings

This brief comes out of a product design session. It restructures where things live in Atlas and how the app is navigated. It does **not** change the quest model, how habits work, or how sleep and screen-time data arrive.

Things still undecided are listed in `open-points.md`. Do not design or build those yet.

## Before you change any code

1. Read the current navigation, routes, page components, API routes and database schema.
2. Write a short plan that maps each section of this brief to the files you will touch.
3. List anything in this brief that conflicts with how the code really works, and anything ambiguous.
4. Wait for my go-ahead.

Then work phase by phase (section 13). After each phase the app must run, tests must pass, and you commit. Back up the database with the admin command-line tool before any schema change.

## 1. Rules that stay fixed

- Single user. Runs locally for now.
- Only facts and explicit decisions are stored. Everything shown (streaks, adherence, progress, totals, averages, the new weekly numbers) is computed when the page loads. Add no stored statistics.
- The web app is the only interface.
- Sleep and Screen Time are display-only. Only their configuration is editable.
- No developer wording on screen: no IDs or slugs, no raw enum values, no jargon. Sentence case, short, friendly, speaking to "you". Dates read "7 Nov 2026", times "07:05".
- A concept has the same name in the UI and in the API. Every rename in this brief applies to both, and to routes and code.
- The global "As of" date keeps working on every page, including the new ones.

## 2. Why this change

Atlas today is three apps sharing one long sidebar: a planner (quests), a tracker (sleep, screen time, habits) and a library. Twelve-plus links sit at the same level, two pages both act as "today", and some pages are empty placeholders or admin screens. The new structure follows a video-game menu: a few destinations, each answering one question, and a Home that shows the day and the state of the "character" at a glance.

## 3. Target structure

Five destinations plus Settings.

| Destination | Question it answers | Tabs inside |
|---|---|---|
| Home | What now, and am I on track? | none |
| Quests | What am I working toward? | Main quests · Side quests · Inbox · Plan |
| Habits | What do I keep doing? | none (board, plus habit pages) |
| Stats | What does the data say? | This week · Sleep · Screen time · Health |
| Library | What have I watched, read, heard? | as today's Entertainment |
| Settings | (gear) | Appearance · Screen time setup · Devices · Metrics · All entries |

Where each current page goes:

| Today | After |
|---|---|
| Home (four cards and a quote) | New Home (section 5). The quote is removed. |
| Quests → Today | Merged into Home. Page removed. |
| Quests → Inbox, Main quests, Side quests | Tabs inside Quests. Unchanged. |
| Quests → Calendar | Renamed **Plan**, a tab inside Quests (section 6). |
| Habits | Its own destination. Unchanged apart from section 7. |
| Sleep | Stats → Sleep. Unchanged. |
| Screen Time | Stats → Screen time. Its Configure section moves to Settings. |
| Health (placeholder) | Stats → Health, with a real empty state (section 8). |
| Adventure (placeholder) | Removed entirely. |
| Entertainment | Renamed **Library**. Otherwise unchanged. |
| Journal | A "Note for today" field on Home, plus an "Earlier notes" page reached from it. No navigation entry. |
| History | Settings → All entries. |
| Catalog | Removed. Metric management moves to Settings → Metrics; habits are created and edited in Habits only. |
| Area pages | Removed, with areas (section 10). |

Old addresses redirect to the new location so nothing breaks.

## 4. Navigation shell

Replace the long sidebar with a narrow rail.

**Desktop**

- A fixed left rail, about 76px wide. Each item is an icon with its label underneath.
- Top to bottom: Home, Quests, Habits, Stats, Library. Settings (gear) sits at the bottom of the rail.
- The active item uses the accent colour on icon and label, with a subtle raised surface.
- The Inbox count of unsorted items shows as a badge on the Quests rail item and on the Inbox tab.
- Suggested icons: house (Home), map (Quests), repeat arrows (Habits), bar chart (Stats), books (Library). Use the existing icon set; do not reuse the icons that already mean a quest level (compass, flag, diamond, bookmark, scroll).

**Section tabs**

- A destination with sub-pages shows them as a row of text tabs under the page title. The active tab is underlined in the accent colour.
- Each tab has its own address, so links and the back button work.

**Header**

- Shows the date, the "As of" control, and an **Add** button. The Settings button leaves the header on desktop (it is in the rail).
- **Add** opens a small menu with two items that reuse existing flows: "Task" (adds to the Inbox) and "Entry" (the existing New entry dialog). A faster capture model is an open point; keep this minimal.

**Narrow screens (below about 768px)**

- The rail becomes a bottom tab bar with the same five destinations.
- Settings is reached from a gear in the header.
- Section tabs scroll sideways if they do not fit.
- Every page must remain usable, but only Home, Habits and the Stats pages need to be comfortable on a phone. Editing a quest's structure is a desktop job; it must not break on a phone, but it need not be optimised.

## 5. Home

Home is the single daily entry point. It merges the old Home and the quest Today page. Each block loads independently, as cards do today.

**Desktop: two columns.** Left is what to do today. Right is where you stand; every block there is a doorway into its section.

```
 TODAY                           │ THIS WEEK SO FAR
                                 │ Sessions kept      5 of 7
 2 sessions to confirm           │ Habits kept           82%
                                 │ Sleep, average     6h 50m
 09:00  Rust ownership           │ Screen score           61
        Session done · Edit      │
 ── Now 11:20 ───────────────────│ MAIN QUESTS
 14:30  Tax forms                │ ◔ Move to Copenhagen   40%
                                 │   Next: Book a viewing trip
 Due today                       │ ◑ Handstand push-up    55%
 ○ Book flights                  │   Next: Hold a wall handstand
                                 │
 Habits                          │ LAST NIGHT
 ☐ Read 30 minutes               │ 6h 12m · 00:40 → 07:05
 ☑ Up before 07:00               │
 ☐ Gym · 2 of 4 this week        │ SCREEN TIME TODAY
                                 │ 2h 05m of 3h cap
 Note for today…                 │ IN PROGRESS
```

**Left column, in order**

1. **To confirm.** Shown only when unconfirmed sessions exist: "2 sessions to confirm", each with Session done / Didn't happen. Same behaviour as on the old Today page.
2. **Today.** Today's sessions as a timeline with the "Now" line. Each session keeps Session done / Cancel / Edit and, separately, Outcome achieved. A "Plan a session" button. Empty state: "No sessions today."
3. **Due today.** Tasks due today, with overdue ones marked "Overdue". Empty state: "Nothing due today."
4. **Up next.** The existing Up next list.
5. **Habits.** The habits scheduled for today, each with the existing one-tap Mark done or Log value. Habits with a weekly or monthly frequency show their progress, for example "2 of 4 this week". A link "All habits". This replaces the Monday–Sunday grid on Home; the grid stays on the Habits page. Empty state: "No habits yet."
6. **Note for today.** A one-line field that grows when focused. It saves today's journal note. A link "Earlier notes" opens the list of past notes (the current Journal page content).

**Right column, in order**

1. **This week so far.** Four numbers (definitions below), with a link "This week" to Stats → This week.
2. **Main quests.** Active goals, up to five, each with its progress ring, title and "Next: …" (its Next action). Same order as on Main quests. A link "All quests". Empty state: "No goals yet." with "Add a goal".
3. **Last night.** Time asleep and bed → wake. Links to Stats → Sleep. Empty state: "No sleep data for last night."
4. **Screen time today.** Today's total, followed by "of 3h cap" only if a daily cap on the total exists. Links to Stats → Screen time. Empty state: "No screen time data yet today."
5. **In progress.** Library titles in progress: a count and up to three titles. Links to Library. Empty state: "Nothing in progress."

**Definitions for "This week so far"** (Monday to now, computed at load, never stored)

- **Sessions kept:** sessions marked done, out of sessions whose end time has passed and that were not cancelled (done, didn't happen, and unconfirmed all count in the total).
- **Habits kept:** the existing adherence calculation, for this week to date, across habits that are not archived or paused. Reuse the existing calculation; do not write a second formula.
- **Sleep, average:** average time asleep over this week's nights that have data.
- **Screen score:** the existing score, for this week to date.

**Narrow screens: one column**, in this order: To confirm, Today, Due today, Habits, Up next, Note for today, This week so far, Main quests, Last night, Screen time today, In progress.

## 6. Quests

- Tabs: Main quests · Side quests · Inbox · Plan.
- Main quests, Side quests, Inbox, the Ambition page, the Goal page and the task drawer are **unchanged**. Do not alter levels, completion, weights or chapters in this pass.
- The Today page is removed; its content lives on Home.
- **Plan** is the Calendar page renamed (label, address, and any API or code that names the page "calendar"). The concept "session" keeps its name. The week-by-hour grid stays as it is.
- One addition to Plan: beside the week grid, a list titled "Not scheduled yet" showing each active goal's and side quest's Next action that has no upcoming session. Choosing one opens the existing plan-a-session flow with that task filled in. Empty state: "Everything next has a session."
- Google Calendar is not part of this pass.

## 7. Habits

- Habits is a destination of its own. The board, the overview grid and the habit pages are unchanged in this pass; a redesign is being discussed separately.
- Habits are created, edited, archived and deleted here only (Catalog no longer does this).
- Remove the optional Area field from the habit form.
- **Backend only: an optional link between a habit and quest items.**
  - A habit can support zero or more quest items. A supported item is an ambition, a goal or a side quest.
  - The link is informational. It must never affect progress, completion, weights or Next action.
  - Add it to the schema and the API (read, add, remove). Build no UI for it yet.
- Screen Time's daily caps stay a Screen Time feature. They are **not** converted into habits. Automatic checking of habits from device data is not part of this pass.

## 8. Stats

Tabs: This week · Sleep · Screen time · Health.

**This week (new page)**

- One Monday–Sunday week, with previous and next controls. Title: "This week", or "Week of 9 Nov 2026" for other weeks.
- Five blocks. Each shows its numbers and, where it makes sense, the change from the previous week ("+35m vs last week"). Each block's heading links to its section.
  - **Quests:** sessions kept, tasks completed, milestones completed.
  - **Habits:** habits kept, then one row per habit with its progress for the week.
  - **Sleep:** average time asleep, average bedtime, average wake time, missing nights.
  - **Screen time:** total, daily average, score, and the Good / Neutral / Bad split.
  - **Library:** titles finished.
- Everything is computed at load from existing data, reusing each section's existing calculations.

**Sleep and Screen time**

- The existing pages, moved under Stats, unchanged.
- Remove the Configure section from the Screen time page; it now lives in Settings → Screen time setup. Leave a link: "Set up apps, categories and caps".

**Health**

- Shows device data only. Nothing is typed by hand here.
- No device data exists yet, so the page shows an empty state rather than "Coming soon": heading "No health data yet", text "This fills in once a device is connected."
- What Health will contain is an open point. Build nothing more.

## 9. Library

- Entertainment is renamed **Library** everywhere: label, address, API, code. "Entertainment title" becomes a Library title.
- Behaviour and layout are unchanged in this pass.

## 10. Settings, and what is removed

**Settings** is a page with these sections:

- **Appearance:** theme (dark or cream light) and display name.
- **Screen time setup:** the former Configure section (Good / Bad / Neutral per category, each app's category, daily caps).
- **Devices:** device names.
- **Metrics:** list, create, edit and archive metrics. These flows move here from Catalog. The setup questions are unchanged for now.
- **All entries:** the former History page, unchanged, including the "Hide automatic data" switch and inline edit.

Show only sections that work. No placeholders.

**Removed**

- **Catalog.** Delete the page once Metrics lives in Settings.
- **Areas.** Remove areas as a concept the user sees: Area pages, the Area field on habits and metrics, and area management. Existing metrics and habits keep working without an area. Hidden system areas exist internally: check what depends on them and propose in your plan whether to keep an internal-only grouping or drop the table. Do not expose areas in the UI or the public API either way.
- **Adventure**, the **Health placeholder**, the **Journal page as a navigation entry**, the **quest Today page**, and the **static quote** on Home.

## 11. Visual direction

The current look uses a different accent colour per section, which makes the app feel busy. Move to one system.

- **One accent colour:** the iris purple used by quests today, across the whole app. Remove the per-section accents (indigo, blue, rose, teal, fuchsia).
- **Colours that carry meaning:** green for done or kept, amber for needs attention (to confirm, due today), red for overdue or over a cap. Never rely on colour alone; pair it with an icon or a label.
- **Charts** may use a small fixed set of muted data colours (sleep stages, Good / Neutral / Bad). Define them once as shared tokens.
- **Sections are told apart by icon and layout**, not colour.
- Keep the dark navy default and the cream light mode, Inter, and raised cards. Use the quest screens as the reference for surfaces, spacing and type across all pages.
- A deeper visual identity pass is an open point. Do not add game-style decoration now.

## 12. Wording

Use these labels exactly.

- Rail: Home · Quests · Habits · Stats · Library · Settings
- Quests tabs: Main quests · Side quests · Inbox · Plan
- Stats tabs: This week · Sleep · Screen time · Health
- Settings sections: Appearance · Screen time setup · Devices · Metrics · All entries
- Home headings: To confirm · Today · Due today · Up next · Habits · Note for today · This week so far · Main quests · Last night · Screen time today · In progress
- Home numbers: "Sessions kept", "Habits kept", "Sleep, average", "Screen score"
- Home links: "All habits", "Earlier notes", "This week", "All quests"
- Add menu: "Task", "Entry"
- Plan list: "Not scheduled yet"

Empty states are given in each section above.

## 13. Phases

1. **Shell.** Rail, section tabs, bottom tab bar, header, new addresses and redirects. Pages keep their current content.
2. **Settings.** Build Settings; move Screen time setup, Devices, Metrics and All entries into it. Remove Catalog and areas.
3. **Home.** Build the new Home; remove the quest Today page, the Journal navigation entry and the quote.
4. **Stats.** Add This week and the Health empty state.
5. **Renames.** Entertainment → Library and Calendar → Plan, in UI, addresses, API and code. Add the "Not scheduled yet" list to Plan.
6. **Habit links.** Schema and API for the optional habit-to-quest link.
7. **Visual pass.** One accent, meaning colours, shared chart colours.

## 14. Out of scope

Sign-in and internet access; a native phone app or widgets; Google Calendar; any change to the quest model or quest screens; the Habits redesign and automatic habit checking; Health content and device integrations; renaming Metric or Entry; metric setup presets; faster capture or search; the guided journal conversation; agent or MCP access. See `open-points.md`.

## 15. Done when

- The rail shows exactly five destinations plus Settings; narrow screens show a five-item bottom bar.
- No link leads to a placeholder, to Catalog, or to an Area page. Old addresses redirect.
- Home shows today's sessions, due tasks, habits and note on the left, and the week, quests, sleep, screen time and library on the right, each with a working empty state.
- Stats → This week shows all five blocks with a comparison to the previous week, and nothing new is stored.
- Screen time setup is reachable only in Settings (and by the link on the Screen time page).
- "Entertainment" and "Calendar" no longer appear in the UI, addresses or API.
- A habit can be linked to an ambition, goal or side quest through the API, and no progress number changes when it is.
- Only one accent colour is in use outside charts.
- The "As of" date works on Home and on Stats → This week.
- No screen shows an ID, a raw enum value or technical wording.

## Appendix: decisions behind this brief

- **D1** Atlas has three linked pillars: Quests (the largest), Stats and Library. *The owner's game-menu model.*
- **D2** Desktop is for overview, planning and input; the phone is for checking and small edits. *Different jobs on different screens.*
- **D3** Automatic data first, minimal manual logging. *Logging by hand does not last.*
- **D4** Google Calendar will be integrated instead of building a full calendar. *Later.*
- **D5** No review ritual; a This week view instead. *The structure does the reviewing.*
- **D6** Journal becomes a note on Home. *It is not used as a diary.*
- **D7** The quest model stays. Goal, Milestone and Task are the core; Ambition, Chapter and weights are optional. *It works for the first user.*
- **D8** Atlas owns sessions and will push them one way to a dedicated Google calendar. *Later.*
- **D9** Internet access, sign-in and hosting wait until after version 1. *Features mature first.*
- **D10** The owner is the first user; a wider release is possible later. *No onboarding yet.*
- **D11** Five destinations on a rail (desktop) and a tab bar (phone). *One question per destination.*
- **D12** Today is merged into Home. *One daily entry point.*
- **D13** Stats holds This week, Sleep, Screen time and Health; Health shows device data only. *Nothing typed by hand.*
- **D14** Habits is its own destination. *Keeps Quests uncluttered.*
- **D15** Screen Time and its caps stay separate from habits. *Screen Time is a data view in its own right; a limit can be a habit later.*
- **D16** A habit can optionally support quest items, in the backend only for now, never affecting progress. *Progress stays about outcomes.*
- **D17** Areas and Catalog are removed; Settings exists and holds All entries. *No admin pages.*
- **D18** Calendar becomes Plan inside Quests. *A planning view, not a calendar.*
- **D19** One accent colour plus colours that carry meaning. *Too many colours made the app feel busy.*
- **D20** Entertainment is renamed Library. *Plain, and covers every kind of title.*
