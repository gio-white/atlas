# Atlas habits brief: model, rules and screens

This brief rebuilds habits in Atlas. It replaces how habits work today: kinds, targets, skips, pauses, the board and the detail page. Rebuild or remove what exists so it matches this version. Do not keep both side by side.

It comes after `redesign-brief.md` and **replaces its section 7 (Habits) and the Habits block on Home (section 5, left column, item 5)**. Everything else in the redesign brief still applies. Undecided topics are in `open-points.md`; do not build those.

## Before you change any code

1. Read the current habit code: schema, API, calculations (streaks, adherence, period progress), skips, pauses, the board, the detail page, the Home habits block and the habit form.
2. List every existing habit in my database with its kind, schedule and target, and propose how each one migrates (section 11).
3. Write a plan that maps each section of this brief to the files you will touch.
4. List anything that conflicts with the code or is ambiguous. **When in doubt, ask me. Do not guess.**
5. Wait for my go-ahead. Then work phase by phase (section 13). Back up the database with the admin command-line tool before any schema change.

## 1. What a habit is

- A habit is something you **do again and again and never finish**. Anything that can be finished for good is a task.
- **Habits are a self-contained module.** They work on their own. A habit may *read* from Sleep, Screen time or Quests when that data exists. It never writes to, or changes, any other part of Atlas.
- **Each day ends as Done or Not done.** There is no partial credit. Progress ("5,200 of 8,000 steps") is shown only while the day is still running.
- Fixed rules still apply: only facts and explicit decisions are stored, and every result, streak and percentage is computed when the page loads.

## 2. Two ways a habit is checked

**You tick it.** A manual habit. Ticking a day stores a mark "Done" for that day; unticking removes the mark. A day without a mark is Not done.

**From your data.** A data habit has a **source** and a **threshold**, and Atlas works out the day's result.

Sources in this version:

| Source | Value for day D |
|---|---|
| Wake time | Wake time of the night that ends on D |
| Bedtime | Bedtime of the night that ends on D |
| Time asleep | Time asleep of the night that ends on D |
| Screen time in Bad apps | Total minutes on D in apps whose category is Bad, all devices |
| Screen time in a category | Total minutes on D in one category, all devices |
| Screen time in an app | Total minutes on D in one app, all devices |
| Screen time, total | Total minutes on D, all devices |
| Sessions planned | Whether at least one session scheduled on D was **created** before a set time on D (default 12:00) |

- **A night belongs to the day you wake up.** If a day has several sleeps, use the longest.
- **Sessions planned** needs the session's creation time. If sessions do not store it, add it; existing sessions count as created at their start time.
- The source list must be easy to extend later (workouts, steps, mindful minutes, a reading app).

**Thresholds:** At least · At most (for durations), Before · After (for times of day).

- Bedtime is compared on an evening-to-morning scale running from 18:00 to 17:59, so 00:40 counts as later than 23:30.
- Remove the "exactly" target.

**Manual override.** On any day, for any habit, I can set Done or Not done by hand. For a data habit this stores a mark that always wins over the data. It is labelled "Set by you", and "Use data again" deletes it.

## 3. Missing and incomplete data

The rule: **a data habit is Done only if the data was received, is complete for that day, and passes the threshold.** Missing data must never count as success.

- **Sleep sources:** if no night ends on D, the day is Not done, with the reason "No data received".
- **Screen time sources:** day D is complete only when every active device has sent data covering the whole of D. Store, per device, the time its data is complete up to (as a fact the import writes). If no such field exists, add it. Since there is no pipeline yet, the demo data and the admin tool should set it. If any device is behind, the day is incomplete.
- **Reason lines:** "No data received" when nothing arrived for D; "Data incomplete" when some arrived but not all.
- **Waiting period:** the day that has just ended (yesterday) shows "Waiting for data" instead of Not done until today ends. While it waits, it does not break the streak. After that it is Not done, unless data arrives later; data that arrives late re-judges the day automatically.

## 4. While the day is running (today only)

- **At least:** show progress ("20 of 30m"). Done as soon as the threshold is reached.
- **At most:** "On track · 40m of 1h 30m" while under the limit. As soon as the limit is passed, the day is Not done with "Over the limit". Otherwise it becomes Done only once the day's data is complete, so it shows "Waiting for data" after midnight.
- **Before / After a time:** judged when the value arrives (for example when the night arrives). Until then, nothing is shown for today.
- **Sessions planned:** Done as soon as a qualifying session exists. Not done once the cut-off time passes without one.
- **Manual habits:** open until ticked.

## 5. Schedules, rule history and freezes

**How often:** Every day · Specific days (weekdays) · N× a week · N× a month. Weeks run Monday to Sunday; months are calendar months.

**Rule history.** A habit's schedule and threshold are stored as rule versions, each with a start date. Every day is judged by the version that applied on that day.

- Editing the schedule or threshold asks "Apply this change": **From today** (adds a version starting today) or **To all past days too** (replaces all versions with one starting on the habit's first day).
- Name and time of day are not versioned.
- One record per edit; nothing else is stored.

**Freezes** replace skips and pauses.

- A freeze has a start date, an end date (the same day for a single day), an optional reason, and applies to one habit or to all habits.
- A frozen day is neither Done nor Not done. It does not break a streak and is left out of every percentage.
- **Weekly and monthly habits with frozen days:** the target becomes `ceil(N × open days ÷ days in the period)`, where open days are days not frozen. A period with no open days is left out entirely.
- The same formula applies to the first, partial period after a habit is created, counting its days before creation as not open.

**Days.** A day is the calendar day in local time and switches at midnight. Past days stay editable.

## 6. Calculations

All computed at load and unit-tested.

- **Day result** for a habit on day D: Not scheduled · Frozen · Done · Not done · In progress (today only) · Waiting for data (yesterday only), each with an optional reason line.
- **Period** of a habit: day for Every day and Specific days; week for N× a week; month for N× a month.
- **A period is kept** when its Done days reach the target (1 for daily periods).
- **Current streak:** consecutive kept periods counting back from the most recent finished period. Skip unscheduled days, fully frozen periods and periods still waiting for data. The current period adds 1 if it is already kept and never breaks the streak while it is running.
- **Best streak:** the longest run ever, by the same rules.
- **Kept, last 4 weeks** for one habit: kept periods divided by judged periods over the last 28 days. Frozen periods and periods still running are excluded.
- **Habits kept** across habits (used on Home, Stats → This week and the Week tab): sum over habits of min(Done, target) divided by the sum of targets, for the period shown. Each daily-habit day counts as a target of 1.
- **Unit tests** must cover at least: a manual tick and its removal; an override beating data both ways; no night; an incomplete screen-time day; going over the limit mid-day; yesterday waiting and then becoming Not done; late data re-judging a day; a rule change applied from today and to all past days; a single-day freeze and a holiday freeze; the proportional weekly target; a habit created mid-week; a bedtime after midnight; the Sessions planned cut-off.

## 7. Habits page: Day tab

```
Habits                                     New habit
Day   Week
──────────────────────────────────────────────────
   M     T     W     T     F    [S]    S
   9    10    11    12    13    14    15
   ●     ●     ◐     ●     ◐     ◔
──────────────────────────────────────────────────
Saturday 14 Nov 2026                    3 of 6 done

MORNING
 ✓  Wake up before 07:00            🔥 12 days
    06:48 · from sleep
 ✓  Plan the day                     🔥 4 days
    Session planned at 08:10
ANY TIME
 ○  Read 30 minutes                  🔥 2 days
 ○  Meditate
 ◔  Bad apps under 1h 30m            🔥 6 days
    On track · 40m of 1h 30m
 ✓  Physical activity          2 of 4 this week · 🔥 3 weeks
```

- **Week strip:** Monday to Sunday of the selected week. Each day shows a small ring with the share of that day's scheduled habits that are done. Future days are dimmed and cannot be selected. "‹ ›" moves between weeks. Today is selected by default.
- **Count:** "3 of 6 done" counts scheduled habits that are not frozen.
- **Groups:** habits are grouped by time of day (Morning, Afternoon, Evening, Any time). Empty groups are hidden. If no habit has a time of day, show no group headings.
- **Rows:** status icon, name, and on the right the streak (flame icon, number and unit). Weekly and monthly habits also show "2 of 4 this week" or "1 of 2 this month".
- **Reason line** under the name when there is one: "06:48 · from sleep", "No data received", "Data incomplete", "Waiting for data", "Over the limit", "Set by you", "Frozen".
- **Status icon:** tapping it toggles Done for manual habits. For data habits it does not toggle; it opens the row menu.
- **Row menu**, opened by tapping the row or "…": Mark done · Mark not done · Use data again (only if set by you) · Freeze this day / Unfreeze · Open habit. Show only the actions that apply.
- **Unscheduled habits** (for example a weekday-only habit on Saturday) are not listed for that day.
- **Empty state:** "No habits yet" with "New habit".

## 8. Habits page: Week tab and habit page

**Week tab**

```
Week of 9 Nov 2026                          ‹   ›
                        M  T  W  T  F  S  S
Wake up before 07:00    ✓  ✓  ✕  ✓  ✓  ✓  ·   🔥 12 days
Plan the day            ✓  ✓  ✓  ✕  ✓  ✓  ·   🔥 4 days
Read 30 minutes         ✕  ✓  ✓  ✓  ✕  ○  ·   🔥 2 days
Physical activity       ✓  ·  ✓  ·  ·  ✓  ·   2 of 4 · 🔥 3 weeks

Habits kept this week 81% · last week 74%
```

- One row per active habit, in the same order and groups as the Day tab.
- Cells: Done, Not done, In progress, Waiting, Frozen, Not scheduled (blank), future (dimmed dot).
- Tapping a manual habit's past or present cell toggles it; any other cell opens the row menu for that day. Tapping a habit name opens its page.
- Footer: "Habits kept this week" and the same figure for last week.

**Habit page**

- **Header:** name, then one line: how often · how it is checked · time of day. For example: "Every day · From your data: wake time before 07:00 · Morning".
- **Three figures:** Current streak, Best streak, Kept, last 4 weeks.
- **History:** the last 12 weeks as a grid of one square per day for daily habits, or one per week for weekly habits, coloured by result.
- **Recent days:** the last 14 days with result and reason. Each row opens the row menu.
- **Freezes:** upcoming and past freezes, each removable.
- **Actions:** Edit · Freeze… · Archive · Delete. Delete asks for confirmation and states that the history goes with it. Archive keeps the history and hides the habit everywhere except an "Archived" list at the bottom of the Week tab.

## 9. Creating, editing and freezing

**New habit** is one sheet with four questions:

1. **What do you want to do?** Name.
2. **How often?** Every day · Specific days · Times a week (a stepper, 1–7). "More options" reveals Times a month (1–31).
3. **How is it checked?** You tick it · From your data. Choosing "From your data" shows a source picker, then the threshold as one readable line with an editable value: "Wake time before 07:00", "Bad apps at most 1h 30m", "A session planned before 12:00".
4. **When?** (optional) Morning · Afternoon · Evening · Any time. The default is Any time.

The button is "Create habit".

- **Edit** uses the same sheet. If the schedule or threshold changed, it shows "Apply this change: From today / To all past days too", defaulting to From today.
- **Freeze…** opens a sheet with From and To dates (defaulting to today), an optional "Reason", and a switch "Freeze all habits". The button is "Freeze".

## 10. Habits on Home

This replaces the Habits block on Home.

- **Heading** "Habits", with "3 of 6 done" beside it. The heading opens Habits → Day.
- **Rows:** today's scheduled habits, in groups and order as on the Day tab, each with status icon, name, reason line and streak.
- **Behaviour** is the same as on the Day tab: the icon toggles manual habits, and tapping the name opens the row menu (including "Open habit").
- **Empty state:** "No habits yet" with "New habit".
- Swipe gestures come later; do not build them now.

## 11. Remove and migrate

**Remove from the UI and the API:**

- the habit kinds (check, count, duration, quit) and the "exactly" target
- skips and pauses (replaced by freezes)
- the "Log value" action on habits
- the old board, the overview grid and the old detail page, replaced by sections 7–8
- the Area field, if still present

**Migrate:**

- Existing skips become single-day freezes; existing pauses become freezes over the same range.
- **Check habits** become manual habits. Each past day whose result was Done becomes a manual Done mark.
- **Count and duration habits:** propose per habit in your plan. My default:
  - Keep the habit as a data habit whose source is its existing metric ("Your entries"), with its current target as the threshold, so history is preserved.
  - Do not offer this source in the New habit sheet.
- **Quit habits:** propose per habit. My default: a manual habit; a past day counts as Done when no slip was logged that day.
- The existing schedule and target become the first rule version, starting on the habit's first day.
- The optional habit-to-quest link from the redesign brief stays as specified there: backend only, no effect on progress.

## 12. Wording

Use these exactly.

- Tabs: Day · Week
- Buttons: New habit · Create habit · Edit · Freeze… · Freeze · Archive · Delete
- Row menu: Mark done · Mark not done · Use data again · Freeze this day · Unfreeze · Open habit
- Reasons: No data received · Data incomplete · Waiting for data · Over the limit · Set by you · Frozen
- Progress: "On track · 40m of 1h 30m" · "20 of 30m" · "2 of 4 this week" · "1 of 2 this month" · "3 of 6 done"
- Streaks: a flame icon, then "12 days" / "3 weeks" / "2 months" (singular "1 day", "1 week", "1 month")
- Figures: Current streak · Best streak · Kept, last 4 weeks · Habits kept this week
- New habit sheet: What do you want to do? · How often? · How is it checked? · When? · You tick it · From your data · More options · Apply this change · From today · To all past days too
- Times of day: Morning · Afternoon · Evening · Any time

## 13. Visual

| State | Look |
|---|---|
| Done | Filled check in the success green |
| Not done | Quiet grey cross. Never red: red stays for overdue tasks. |
| In progress | Partial ring in the accent colour |
| Waiting for data | Small clock, grey |
| Frozen | Snowflake, grey |
| Not scheduled | Blank |

- The flame is a small monochrome icon in the accent colour, not an illustration or emoji.
- Follow the single-accent rule from the redesign brief.
- On narrow screens, the week strip and the Day list must be comfortable to use with a thumb, with tap targets of at least 44px.

## 14. Phases

1. **Model and migration:** rule versions, marks, freezes, data sources, device "complete up to", session creation time; migrate existing habits.
2. **Calculations** with all unit tests from section 6.
3. **Day tab.**
4. **Week tab and habit page.**
5. **New habit, Edit and Freeze sheets.**
6. **Home Habits block.**
7. **Remove the old habit screens and API**, then check that nothing links to them.

After each phase: the app runs, tests pass, and you commit.

## 15. Done when

- A habit is either "You tick it" or "From your data". No kind, "exactly" target, skip, pause or Log value remains in the UI or the API.
- Every past day of a habit is Done, Not done, Frozen or Not scheduled. Yesterday may also be Waiting for data.
- A data habit with missing or incomplete data is never Done unless I set it by hand.
- Changing a threshold "From today" leaves every past result unchanged; "To all past days too" re-judges them.
- Freezing a week of holiday leaves every streak intact.
- "Plan the day" turns Done by itself when I plan a session before 12:00.
- Streaks show a flame, a number and the right unit for daily, weekly and monthly habits.
- Home, the Day tab and the Week tab agree on every habit's status for every day.
- The "As of" date works on all habit screens.
- No screen shows an ID, a raw value or technical wording.

## Appendix: decisions behind this brief

- **D21** A habit is a self-contained module; links to data are optional and read-only.
- **D22** Each day ends Done or Not done; progress shows only during the day.
- **D23** Missing or incomplete data means Not done, with a reason; a manual answer always wins.
- **D24** Changes apply from today by default, with an option to apply them to the past; one rule record per edit.
- **D25** Streaks count the habit's own period.
- **D26** Freeze replaces skips and pauses; frozen days neither break nor count.
- **D27** Today switches at midnight; past days stay editable.
- **D28** A habit is ticked by you or checked from data; count, duration, quit and "exactly" leave the create flow.
- **D29** A night counts for the day you wake up.
- **D30, D36** The Habits page has Day and Week tabs, plus a page per habit, with optional time-of-day groups.
- **D32** Plan the day is checked from Atlas: a session for today planned before 12:00.
- **D33** The phone-time habit limits only Bad apps, across all devices.
- **D35** No number typing in version 1; partly frozen periods use the proportional rule.
- **D37** A freeze can cover one habit or all habits.
- **D38** Not done is quiet grey, not red.
- **D39** Streaks show a flame icon, the number and the period unit.
- **D40** Home lists today's habits with their status; gestures come later.
