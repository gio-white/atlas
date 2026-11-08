# Frontend

Stack, hosting, routing, API client, and tooling for the React SPA in `web/`. Each page's
behaviour is in its feature doc under [domain/](../domain/); the route table is
[navigation](../product/navigation.md); tokens and theme are the
[design system](../product/design-system.md).

## Stack and hosting

The UI is a React SPA in `web/` (Vite, TypeScript, Tailwind, shadcn-style primitives). It is the only frontend. It consumes the HTTP API only. FastAPI does not render HTML templates. When `web/dist` is present, GET 404s that are not API routes return `index.html`. `/journal`, `/side-quests`, and `/side-quests/{id}` are both SPA pages and GET API routes, so a document navigation to those paths (`Sec-Fetch-Dest: document` or `Accept: text/html`) gets `index.html` while fetches still get JSON (`SPA_PATHS_SHADOWED_BY_API` in `src/atlas/api/spa.py`). The other quest pages (`/today`, `/inbox`, `/quests/...`, `/calendar`) share no path with the API, and quest detail pages use `/quests/goals/:id` rather than the API's `/goals/{id}`.

## Scope

Implemented this cycle: night app shell (sidebar + top bar), typed `fetch` client, Home dashboard, Week, Area, Habit, Catalog, Screen Time, Entertainment, the quest screens (Main quests, Ambition, the goal quest map, Side quests, Side quest, Inbox, and the task drawer; [quests](../domain/quests.md#screens)), and placeholder Today and Calendar pages that Q3 of the [quest plan](../plans/quests-plan.md) replaces. The SPA does not recompute streaks, score, heatmaps, sleep consistency, library counts, or quest progress, eligibility, chapter state, or next action.

Shared code worth knowing: `web/src/components/settings/` holds configuration panels that load their own data and take an optional `onChanged` (Screen Time and data sources), so they can move between pages unchanged; `web/src/components/sleep/` holds the Sleep page charts; `web/src/lib/freshness.ts` formats "Last updated …" from a record's `created_at`. `web/src/lib/api.ts` has no functions that write sleep nights or screen sessions ([decision 0004](../decisions/0004-device-data-is-display-only.md)). Its **Quests** section is the complete typed client for every quest and time-block endpoint (types `Ambition`, `QuestGoal`, `QuestMilestone`, `SideQuest`, `Chapter`, `QuestTask`, `TimeBlock`, and the view shapes; functions such as `createQuestTask`, `organizeTask`, `promoteTask`, `completeQuestGoal(id, override)`, `createTimeBlock`, `completeTimeBlock`, `getMainQuests`, `getGoalTree`, `getInbox`, `getTodayQuests`, `getQuestCalendar`). Goal and task names carry a `Quest` prefix (`QuestGoal`, `listQuestTasks`) so they never read as the removed shapes. Q2 and Q3 build on it without adding functions. The SPA never recomputes quest progress, eligibility, chapter state, or next action; it shows what the API returns.

## Tooling

The Q2 quest pages (`MainQuestsPage`, `AmbitionPage`, `GoalPage`, `SideQuestsPage`, `SideQuestPage`, `InboxPage`) are `React.lazy` routes in `App.tsx`, so they load in their own chunk on first visit; `Layout` wraps the page outlet in `Suspense` with the `PageLoading` skeleton.

Package manager is pnpm (`web/pnpm-lock.yaml`, `packageManager` in `web/package.json`). Biome is the only linter and formatter (`web/biome.json`). Never npm, yarn, ESLint, Prettier, or oxlint. Dev: `cd web && pnpm install && pnpm dev` on `:5173`; Vite proxies API prefixes to `127.0.0.1:8000`. Document navigations (`Accept: text/html` or `Sec-Fetch-Dest: document`) to overlapping paths (`/screen`, `/sleep`, `/journal`, `/entertainment`, `/side-quests`) still get the SPA; the proxy also forwards the quest API prefixes (`/ambitions`, `/goals`, `/milestones`, `/side-quests`, `/chapters`, `/tasks`, `/time-blocks`). If the API is down, the proxy returns JSON `{detail}` instead of an HTML 502, and review pages keep their chrome with that message. Prod: `cd web && pnpm build` then `atlas serve` serves API and `web/dist` together. Frontend gates: `pnpm lint`, `pnpm test`, `pnpm build`. Vitest runs in Node by default; a component test that renders React opts into the DOM with a `// @vitest-environment jsdom` comment at the top of its file (for example `web/src/pages/displayOnly.test.tsx`).
