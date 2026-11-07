# UX writing

How Atlas talks to you. It applies to every string a person can see: labels, buttons, empty
states, errors, tooltips, dialog titles, and seed data names.

## The rule: no developer wording reaches the UI

The UI speaks about your life, not about the database. Nothing below may appear on screen:

- **Slugs.** Show the name ("Morning run"), never `morning-run`. Slugs are generated from names
  and stay in URLs and the API.
- **Enum values.** Map each value to a plain label. Never render `higher_is_better`,
  `at_least`, `metric_target`, `in_progress`, `sum`, or `last` as text.
- **Internal jargon.** No "capture path", "rollup", "bucket", "dual-write", "domain cycle",
  "clipped range", "backing metric", "as_of", or "UI labels …". No explanations of how a number
  is computed in code terms.
- **Generated names.** Names are written by people. "Coffee Daily" built from an id is not a
  name; "At most one coffee" is.
- **Raw counts of implementation details.** "22 stages" is a storage fact; "7 h 10 m asleep" is
  what a person wants.

| ❌ Developer wording | ✅ Plain wording |
| -------------------- | ---------------- |
| `higher_is_better` | More is better |
| `at_most 1` | At most 1 |
| `sum` / `last` | Add up the day / Keep the latest |
| One capture path. Counts for 2026-11-07. | Log a value for today |
| This section ships with the matching domain cycle. | Nothing here yet |
| Good + half of Neutral, over total. | How much of your screen time went to good apps |
| Zeros included across the clipped range. | Daily average, counting days with no use |
| · 22 stages | (omit, or show time asleep) |
| `morning-run` | Morning run |
| Meditated Daily | Meditate |

## Voice and tone

- Short, direct, friendly. Write as if talking to one person: you.
- Sentence case for labels and titles ("New habit", not "New Habit").
- Say what happens, not how: "Saved" rather than "PATCH succeeded".
- Errors say what went wrong and what to do: "Couldn't reach Atlas. Is it running?"
- Empty states say what will appear and how to get it there.

## Labelling options

- Every enum shown in a select, chip, or badge goes through one label map in the web app
  (planned: `web/src/lib/labels.ts`, Track T2). Do not inline raw values.
- Dates read as "7 Nov 2026"; times as "07:05".
- Units sit next to the value ("40 reps", "75 kg"), not in a separate column header only.

## Checking a change

Before committing UI text, read each new or changed string aloud. If it contains a word from
the list above, or would confuse someone who has never seen the code, rewrite it. Record new
user-facing names in the [glossary](glossary.md).
