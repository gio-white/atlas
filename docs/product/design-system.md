# Design system

Colour tokens, typography, theme, the shell, and shared UI states. Component primitives live in
`web/src/components/ui/`; theme logic in `web/src/lib/theme.ts`; tokens in `web/src/index.css`.

## Visual system

Visual system is a night dashboard shell: near-black navy canvas, raised cards, Inter body, category accents (iris purple, ember orange, screen blue, goal green, quick yellow, sleep indigo, health rose, adventure teal, entertainment fuchsia). Light mode keeps a cream canvas so Settings and review pages stay readable. Theme is stored as `atlas-theme` and applied in `index.html` before paint; first visit follows `prefers-color-scheme`; it is changed in Settings → Appearance. Display name is local-only (`atlas-display-name`, default Alex) and edited in the same place.

## Shell

The shell is a rail of five destinations plus Settings on screens 768px and wider, and a bottom
tab bar on narrower ones (`web/src/components/shell/DestinationNav.tsx`). A rail item is an
icon with its label underneath; the active one takes the `iris` accent on icon and label and a
raised surface. Destinations with sub-pages show a row of text tabs under the destination title,
the active tab underlined in `iris` (`SectionLayout.tsx`). The header holds the date (the As of
control, amber while another date is chosen) and the `iris` **Add** button. Sections are told
apart by icon and layout; the per-section accents below are still used inside pages until the
visual pass (redesign brief, phase 7) reduces them to one accent. Behaviour and wording:
[navigation](navigation.md#shell).

Menus use `web/src/components/ui/dropdown-menu.tsx` (Radix dropdown menu). A menu whose items
open a dialog is not modal, so the page stays clickable after the dialog closes.

## Status, empty, loading, and error states

Status uses green / amber / red in both modes. Empty states say what will appear and how to get it there; loading uses skeletons; errors use `role="alert"`.

## Sleep stage colours

Sleep stage colors (deep violet, light aqua, REM blue, awake amber) are separate tokens per theme, validated for colorblind separation.
