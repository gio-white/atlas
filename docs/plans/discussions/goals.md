# Discussion: what goals should be in Atlas

> **How to use this file.** Paste it into a chat (or say "let's go through
> `docs/plans/discussions/goals.md`") and we work through the questions in §6, one at a time.
> The goal is a short list of decisions (§8), not code. When we agree, the decisions become
> Track T5 in `docs/plans/2026-11-restructure.md`. Where goals sit in the sidebar is decided in
> `navigation-and-organization.md`, not here.

## 1. What we are deciding

What a goal is for you, how its progress is measured and shown, and how goals connect to habits,
tasks, and life areas, so that the Goals pages are easy to read and every status means something.

## 2. Fixed points

- Single user, local.
- Progress is always computed from recorded facts when the page loads (backfilling an old entry
  corrects every goal that depends on it).

## 3. How goals work today

### 3.1 The model

- **Two kinds of goal:**
  - **Metric target** — tied to one metric with a target: "weigh 75 kg" (uses the latest value),
    "read 12 books by April" (adds up values since the start date).
  - **Milestone goal** — a list of steps you tick off manually; progress = steps done / total.
  - Both kinds can carry milestones.
- **Three horizons:** long (1+ year "north star"), medium (months), short (about a week). Chosen
  by you, or inferred from the dates.
- **A tree:** a medium goal can sit under a long one, a short goal under a medium one. A parent's
  progress is **not** computed from its children.
- **Optional area tag** (Health, Career…).
- **Status:** active / achieved / paused / abandoned.
- **Tasks** can link to a goal. Completing a task does **not** change goal progress.
- **Habits** can link to a goal (for display only).

### 3.2 "On track" (pace)

Compares progress with how much time has passed between start and due date:

| Status | Meaning |
| ------ | ------- |
| Ahead / On track / Behind | progress is above / within 5% of / below elapsed time |
| No data | progress can't be computed (no entries yet, or a milestone goal with no steps) |
| Overdue | past the due date and not met |
| Achieved | target met |

### 3.3 The Goals page

Four columns: **Long term · Medium term · Short term · Weekly Action Plan** (this week's tasks
linked to goals). Each column header shows "N / M goals on track · X%". Arrows between columns
suggest the flow from vision to action. Below: an "Everything is connected" note and a quote.

## 4. What is confusing (seen with the demo data)

1. **"Durable health" says *Behind* with an empty bar.** It is a milestone goal with no steps
   done, so 0% progress against elapsed time reads as "Behind" — even though nothing about it is
   really measurable.
2. **"Financial freedom" says *No data*.** A milestone goal with no steps at all.
3. **Column headers say "0 / 3 goals on track · 0%"** while one goal in the column (Read 12
   books) is visibly about 40% done. The header counts *on-track goals*, not progress; it reads
   like progress.
4. **Long-term goals are almost never "on track"**, because a 2-year vision with no metric can't
   be measured by elapsed time.
5. **The Weekly Action Plan does not move anything.** Ticking off tasks there never changes any
   goal, so the arrows promise a connection that doesn't exist.
6. **Odd links:** "Meditate for 10 minutes" and "Evening walk" are tasks under "Workout four
   times" (demo data, but it shows that nothing checks whether a task actually serves its goal).
7. **Layout:** on a normal laptop screen the fourth column is cut off.
8. **Two goal kinds plus milestones plus horizons plus a tree plus pace** is a lot to understand
   before creating a first goal.

## 5. Options to react to

### Measuring goals that have no metric

- **a. Milestones only:** such goals show "3 of 5 steps"; no pace, no "Behind".
- **b. From children:** a long-term goal shows how its medium goals are doing (for example
  "2 of 3 on track"), without its own percentage.
- **c. Your own assessment:** a periodic check-in ("How confident are you? 1–5"), stored and
  charted.
- **d. Not measured:** north-star goals are a statement of direction; they only show their
  children.

### Linking action to goals

- **a. Tasks count:** a short-term goal's progress = its linked tasks done / total.
- **b. Habits count:** a goal shows the adherence of its linked habits.
- **c. Both, as "contributions"** listed under the goal, without changing its percentage.
- **d. No link** (simpler), and the Weekly Action Plan column goes away.

### The page layout

- **a. Columns** (today), made to fit the screen.
- **b. A tree / outline:** north star → medium → short, expandable, with progress next to each.
- **c. One focus view:** pick a long-term goal and see its whole branch, its tasks, and habits.
- **d. A list grouped by area or by status** (active, achieved, paused).

## 6. Questions to answer, in order

1. **What do you want goals to do for you?** Keep a long-term direction in view? Plan each week?
   Track measurable targets? All three?
2. **Do you want the three horizons and the tree, or is it too much?** Would two levels (vision →
   goals) be enough?
3. **How should a goal without a number show progress?** (§5, measuring options.)
4. **Should tasks and/or habits move goal progress?** (§5, linking options.)
5. **What should "on track" mean**, and should it exist for every goal or only for measurable
   ones?
6. **What should the column / section headers summarise?** Progress, counts, or nothing?
7. **Do you review goals regularly** (weekly, monthly)? Should Atlas support a review ritual
   (for example "weekly review: what moved, what's stuck")?
8. **What happens when a goal is achieved, paused, or abandoned?** Where do finished goals go?
9. **Which layout?** (§5, layout options.)
10. **Areas:** must every goal have an area, or is the tag optional (as today)?

## 7. Out of scope here

Where Goals sits in the sidebar, and naming (both in the navigation discussion).

## 8. Output of the discussion

A short decision list, which becomes T5's brief:

```text
G1 Purpose: …
G2 Horizons and tree: …
G3 Progress without a metric: …
G4 Tasks / habits and progress: …
G5 Meaning of "on track": …
G6 Header summaries: …
G7 Review ritual: …
G8 Finished goals: …
G9 Layout: …
G10 Area tag: …
```
