# Design system

Colour tokens, typography, theme, and shared UI states. Component primitives live in
`web/src/components/ui/`; theme logic in `web/src/lib/theme.ts`; tokens in `web/src/index.css`.

## Visual system

Visual system is a night dashboard shell: near-black navy canvas, raised cards, Inter body, category accents (iris purple, ember orange, screen blue, goal green, quick yellow, sleep indigo, health rose, adventure teal, entertainment fuchsia). Light mode keeps a cream canvas so Catalog and review pages stay readable. Theme is stored as `atlas-theme` and applied in `index.html` before paint; first visit follows `prefers-color-scheme`. Display name is local-only (`atlas-display-name`, default Alex).

## Status, empty, loading, and error states

Status uses green / amber / red in both modes. Empty states include a Catalog action; loading uses skeletons; errors use `role="alert"`.

## Sleep stage colours

Sleep stage colors (deep violet, light aqua, REM blue, awake amber) are separate tokens per theme, validated for colorblind separation.
