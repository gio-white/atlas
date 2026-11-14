# Design system

Colour tokens, typography, theme, the shell, and shared UI states. Component primitives live in
`web/src/components/ui/`; theme logic in `web/src/lib/theme.ts`; tokens in `web/src/index.css`;
chart colours in `web/src/lib/chartColors.ts`.

## Visual system

A night dashboard shell: near-black navy canvas, raised cards, Inter body. Light mode keeps a
cream canvas so Settings and review pages stay readable. The quest screens are the reference for
surfaces, spacing, and type. There is no game-style decoration: no gradients, gloss, or
per-section colour. Theme is stored as `atlas-theme` and applied in `index.html` before paint;
first visit follows `prefers-color-scheme`; it is changed in Settings → Appearance. Display name
is local-only (`atlas-display-name`, default Alex) and edited in the same place.

## Colour

Every colour is a token in `web/src/index.css`, set once for light (`:root`) and once for dark
(`.dark`, on `<html>`), and exposed to Tailwind through `@theme` as `--color-*`. Components use
the token classes (`bg-accent`, `text-good`, `fill-series-1`), never a Tailwind palette colour
or a hex value.

**Surfaces and text** — `canvas`, `surface`, `raised`, `sidebar`, `ink`, `muted`, `line`. The
card shadow (`--shadow-card`) is neutral in both modes.

**One accent** — `accent` (purple: `#7c3aed` light, `#a78bfa` dark) with `on-accent` for text
on it. It marks what you can act on or where you are: primary buttons, links, the active rail
item and tab, selection, focus rings (`:focus-visible` and `ring-accent`), progress, the now
line, rating stars, badges with a count. It is the only accent outside charts. Sections are
told apart by icon and layout, not colour.

**Meaning colours** — used only for what they mean, and never alone: each sits next to an icon
or a label that says the same thing.

| Token | Means | Example |
| ----- | ----- | ------- |
| `good` (green) | done or kept | Session done ✓, habit "Done", Outcome achieved |
| `warn` (amber) | needs attention | Unconfirmed sessions, "Due today", the As of date while another day is chosen, skipped |
| `bad` (red) | overdue, over a cap, or an error | "Overdue · 12 Nov", screen total over its cap, `role="alert"` messages |

**Chart colours** — used only inside charts and their legends, defined once in
`index.css` and listed in order in `web/src/lib/chartColors.ts` (`SERIES`, `seriesColor`).

| Token | Light | Dark | Use |
| ----- | ----- | ---- | --- |
| `series-1` | `#2a78d6` | `#3987e5` | first series; a single-series chart (daily screen time, time asleep, trends, the hours heatmap) |
| `series-2` … `series-8` | `#eb6834` `#1baf7a` `#eda100` `#e87ba4` `#008300` `#6250d6` `#e34948` | `#d95926` `#199e70` `#c98500` `#d55181` `#0ca30c` `#9085e9` `#e66767` | further series, in this order |
| `data-good` / `data-neutral` / `data-bad` | `#1baf7a` / `#a8a29e` / `#e34948` | `#199e70` / `#64748b` / `#e66767` | Good / Neutral / Bad screen time in charts and the This week split |
| `stage-deep` / `stage-light` / `stage-rem` / `stage-awake` | series 7 / 3 / 1 / 4 | same slots | sleep stages |

Rules for charts:

- Series take colours in the fixed order and never cycle. A ninth slice is drawn in
  `data-neutral` (`seriesColor` returns it past the eighth).
- A colour follows the thing, not its rank: screen categories are coloured by their place in the
  alphabetical list of category slugs, so a category keeps its colour when the ranking changes.
- Charts never use the accent or a meaning colour for a series, so a series never reads as a
  judgment. The one status mark in a chart, the screen score ring, uses the meaning colours with
  its "Good / OK / Poor" label.
- Every chart with two or more series has a legend, and text stays in `ink` / `muted`, never in
  a series colour.
- A night with no stages, and a missing value, is drawn in `data-neutral`, not in a stage colour.

The palette is the validated categorical set: it passes the lightness, chroma, colour-blind
separation, and normal-vision checks on both surfaces (`#fffdf8` light, `#121826` dark). In light
mode aqua, yellow, and pink sit below 3:1 against the card, so they are always shown with a
labelled legend.

## Shell

The shell is a rail of five destinations plus Settings on screens 768px and wider, and a bottom
tab bar on narrower ones (`web/src/components/shell/DestinationNav.tsx`). A rail item is an
icon with its label underneath; the active one takes the accent on icon and label and a raised
surface. Destinations with sub-pages show a row of text tabs under the destination title, the
active tab underlined in the accent (`SectionLayout.tsx`). The header holds the date (the As of
control, amber while another date is chosen) and the accent **Add** button. Behaviour and
wording: [navigation](navigation.md#shell).

Menus use `web/src/components/ui/dropdown-menu.tsx` (Radix dropdown menu). A menu whose items
open a dialog is not modal, so the page stays clickable after the dialog closes.

## Library tiles

The Library home's category tiles (`web/src/components/library/CategoryIcon.tsx`) are the same
neutral rounded tile (`raised` fill, `line` border) with the category's glyph in the accent;
categories differ by glyph only. A title without a poster shows a neutral tile with a film icon.

## Status, empty, loading, and error states

Status uses the meaning colours above, with an icon or label. Empty states say what will appear
and how to get it there; loading uses skeletons; errors use `role="alert"`.
