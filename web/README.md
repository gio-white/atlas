# Atlas web UI

The Atlas frontend: a React SPA. It talks only to the HTTP API; derived values (streaks, adherence, pace) stay on the server. There is no CLI review UI.

Package manager is pnpm. Linter and formatter is Biome. How to run it is in the [root README](../README.md). Routes are in [docs/product/navigation.md](../docs/product/navigation.md), hosting and tooling in [docs/architecture/frontend.md](../docs/architecture/frontend.md), and the API contract in each feature's doc under [docs/domain/](../docs/domain/).
