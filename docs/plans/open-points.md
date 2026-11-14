# Atlas: open points

Topics raised in the design session of 13–14 Nov 2026 that are **not decided**. Nothing here should be built until it is discussed. Each point gives the context, the current leaning, and what is left to decide.

The Habits redesign (including checking habits automatically from device data) is being discussed next and is not listed here.

## 1. Reaching Atlas from the phone and the internet

- **Context.** The long-term wish is to use Atlas mostly from an iPhone, first as a web page and later as a native app that works alongside the desktop app. Today Atlas runs locally with no sign-in. One idea was to keep the app on the laptop with a cloud database, then move to cheap hosting.
- **Leaning.** Finish version 1 of the features first. Then: private web access from the phone, later a small native app for widgets and wearable data.
- **To decide.** Where the data lives (laptop, cloud database, hosted server); how the phone reaches it; the sign-in (one account with a passcode is the minimum once Atlas is reachable from outside); backups; cost.

## 2. Google Calendar

- **Context.** A full calendar inside Atlas is not wanted. Sessions should appear in Google Calendar.
- **Leaning.** Atlas owns sessions (only Atlas knows "done", "didn't happen", "to confirm") and pushes them one way to a dedicated "Atlas" Google calendar. Atlas reads other Google events only to show busy time. Sessions are added through Atlas, or later through an agent talking to Atlas.
- **To decide.** What happens when a pushed event is moved or deleted in Google Calendar; whether Plan shows busy time; how planned time compares with a task's estimate when extra sessions are added.

## 3. Quest experience

- **Context.** The model is kept. Goal, Milestone and Task are the core path; Ambition, Chapter and weights are optional. Rough time horizons: a goal is long, a milestone lasts a week to a month, a chapter is an extra layer to tidy a large milestone (for example the chapters of a book). Planning can start from either end: from a vague goal refined over time, or from a mid-size piece of work that later joins something bigger.
- **Leaning.** Take Chapter and weights off the default path: offer "Group into a chapter" only inside a milestone or side quest that has grown long, and put weights behind "Adjust weights". Let a side quest be moved into a goal, where it becomes a milestone with its chapters and tasks intact.
- **To decide.** The exact rules for when chapters are offered; the "Move into a goal…" flow; whether the quest names (Ambition, Goal, Milestone, Chapter, Task, Side quest, Session) all stay; insights for quests.

## 4. Health, and where device data comes from

- **Context.** Health is a tab in Stats and shows device data only. Nothing should be typed by hand. Sleep and Screen Time also wait for a device pipeline.
- **Leaning.** Start from what a wearable gives for free (workouts, steps, heart rate, weight from a smart scale).
- **To decide.** Which device and which integration; what Health shows first; how sleep and screen-time data are imported.

## 5. Manual metrics

- **Context.** Area pages are gone, so manual metrics (weight, pushups, mood) are managed in Settings → Metrics and their values are visible only through habits and All entries.
- **To decide.** Whether manual metrics get a place in Stats, or fade out as device data replaces them. Whether setup should use plain presets (Yes/no, Count per day, Measurement, Time spent, Rating, Note) with an Advanced option.

## 6. Names

- **Context.** Metric and Entry were kept in this pass. Tracker and Record were suggested as friendlier names; a rename must change the UI and the API together.
- **Leaning.** Library is the working name for the former Entertainment. Alternatives considered: Collection, Codex, Shelf, Media.
- **To decide.** Metric → Tracker and Entry → Record, yes or no; the final name for Library.

## 7. Visual identity

- **Context.** The current design feels dated and not catchy. The target is a video-game menu (a character screen, a quest log) with Apple-level polish, without cartoonish gamification and without stripping features.
- **Leaning.** This pass only unifies colour (one accent plus meaning colours) and replaces the sidebar with a rail.
- **To decide.** The look of the rail and cards, typography, motion, how much game flavour, and whether Home should read more like a character screen.

## 8. Journal

- **Context.** Writing a diary is not appealing. Journal is now a note field on Home, kept to find out whether it gets used.
- **Leaning.** Replace free writing with a guided conversation with an agent that asks about the day and stores a summary.
- **To decide.** Keep or remove the note after a trial period; the shape of the guided conversation.

## 9. Agent access

- **Context.** Wish to give Atlas data to an AI agent (for example through an MCP server) to interpret the week, suggest what to improve, and add sessions or tasks.
- **To decide.** What the agent may read and change; where suggestions appear; how this relates to Stats → This week.

## 10. Faster capture and search

- **Context.** Logging a value means opening a dialog and choosing from every metric. Ideas raised: voice, a phone widget, logging from a screenshot, links to other apps (for example a reading app).
- **Leaning.** The header "Add" button with "Task" and "Entry" is a stopgap.
- **To decide.** A quick-add model, keyboard shortcuts, search across the app.

## 11. Stats → This week

- **Context.** Built as a first version: five blocks compared with the previous week.
- **To decide.** A month view; which comparisons are useful; whether sleep and screen time should be shown against quest follow-through to explain good and bad weeks.

## 12. Library

- **Context.** Wanted as something much simpler than dedicated apps, kept so that everything is in one place.
- **To decide.** What to simplify (categories, filters, Insights).

## 13. Settings extras

- **To decide.** Managing archived items; anything else that needs a home (backup and restore stay in the command-line tool for now).

## 14. A wider release

- **Context.** Atlas is built for its owner first. If it matures, it might be opened to others.
- **To decide.** Nothing now. Avoid choices that only work for one person where an equally simple general choice exists.
