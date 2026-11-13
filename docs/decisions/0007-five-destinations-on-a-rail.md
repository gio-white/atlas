# 0007 — Five destinations on a rail

Status: accepted (2026-11-13, [redesign brief](../plans/redesign-brief.md) D11–D14, D17, D18, D20).

## Context

Atlas had grown into three apps sharing one long sidebar: a planner (quests), a tracker (sleep,
screen time, habits), and a library. Twelve-plus links sat at one level, two pages both acted as
"today", and some pages were placeholders or admin screens. The earlier
[navigation discussion](../plans/discussions/navigation-and-organization.md) listed the options;
the design session of 13–14 Nov 2026 chose one.

## Decision

- Five destinations, each answering one question, plus Settings: **Home** (what now, and am I on
  track?), **Quests** (what am I working toward?), **Habits** (what do I keep doing?), **Stats**
  (what does the data say?), **Library** (what have I watched, read, heard?).
- They sit on a narrow rail on wide screens and a bottom tab bar on narrow ones. Sub-pages are
  text tabs inside a destination, each with its own address.
- Life areas and Catalog are not destinations and are removed (brief phase 2). Adventure is
  removed. Health is a tab of Stats and shows device data only.
- Calendar becomes **Plan**, a tab of Quests; Entertainment becomes **Library**. A rename applies
  to the UI, addresses, API, and code.
- Old addresses redirect.

## Consequences

- One daily entry point: the quest Today page merges into Home (brief phase 3).
- Page addresses moved under their destination (`/quests/…`, `/stats/…`, `/settings/…`,
  `/library/…`); Habits keeps `/habit` because `/habits` is the API's list.
- The brief lands in seven phases. Between phases some labels are ahead of the API (Library,
  Plan) and some pages are reached through temporary links; [navigation](../product/navigation.md)
  says which.
- Topics the session left open are in [open points](../plans/open-points.md) and are not built.

See [navigation](../product/navigation.md).
