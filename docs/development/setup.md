# Setup

How to install and run Atlas is in the root [README](../../README.md). This page holds the
project configuration behind it.

## Dependencies and tool configuration

Dependencies are declared in `pyproject.toml` and pinned in `uv.lock`; `uv_build` is the build backend. Ruff and pytest are configured in the same `pyproject.toml`: ruff at line length 100 targeting `py312` with `E`, `F`, `I`, `UP`, `B`, `SIM`, and `TID` selected (and `ruff format` at the same width), pytest with `testpaths = ["tests"]` and `--strict-markers --strict-config`. Ruff skips `.claude/skills/` (vendored skill helper scripts) and `.claude/rules/` (illustrative examples) but lints `.claude/hooks/`. Frontend dependencies are declared in `web/package.json` and pinned in `web/pnpm-lock.yaml`; Biome is configured in `web/biome.json` (2-space indent, line width 100, single quotes).

## Enable the docs gate (once per clone)

```bash
git config core.hooksPath .githooks
```

See [docs-sync](docs-sync.md).
