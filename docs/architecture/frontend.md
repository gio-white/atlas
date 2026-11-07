# Frontend

Stack, hosting, routing, API client, and tooling for the React SPA in `web/`. Each page's
behaviour is in its feature doc under [domain/](../domain/); the route table is
[navigation](../product/navigation.md); tokens and theme are the
[design system](../product/design-system.md).

## Stack and hosting

The UI is a React SPA in `web/` (Vite, TypeScript, Tailwind, shadcn-style primitives). It is the only frontend. It consumes the HTTP API only. FastAPI does not render HTML templates. When `web/dist` is present, GET 404s that are not API routes return `index.html`. `/tasks` and `/journal` are both SPA pages and GET API routes, so a document navigation to exactly those paths (`Sec-Fetch-Dest: document` or `Accept: text/html`) gets `index.html` while fetches still get JSON.

## Scope

Implemented this cycle: night app shell (sidebar + top bar), typed `fetch` client, Home dashboard, Week, Area, Habit, Goals, Catalog, Screen Time, Entertainment, Tasks, and milestone toggles on goal detail. The SPA does not recompute streaks, score, heatmaps, or library counts.

## Tooling

Package manager is pnpm (`web/pnpm-lock.yaml`, `packageManager` in `web/package.json`). Biome is the only linter and formatter (`web/biome.json`). Never npm, yarn, ESLint, Prettier, or oxlint. Dev: `cd web && pnpm install && pnpm dev` on `:5173`; Vite proxies API prefixes to `127.0.0.1:8000`. Document navigations (`Accept: text/html` or `Sec-Fetch-Dest: document`) to overlapping paths (`/screen`, `/sleep`, `/tasks`, `/journal`, `/entertainment`) still get the SPA. If the API is down, the proxy returns JSON `{detail}` instead of an HTML 502, and review pages keep their chrome with that message. Prod: `cd web && pnpm build` then `atlas serve` serves API and `web/dist` together. Frontend gates: `pnpm lint`, `pnpm test`, `pnpm build`.
