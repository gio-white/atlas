# Configuration

Code: `src/atlas/settings.py`.

| Variable   | Default                         | Meaning                                                                      |
| ---------- | ------------------------------- | ---------------------------------------------------------------------------- |
| `ATLAS_DB` | `~/.local/share/atlas/atlas.db` | SQLite database file; the parent directory is created if missing             |
| `ATLAS_TZ` | system local timezone           | IANA name (`Europe/Berlin`) used to resolve "today" into `Entry.occurred_on` |

`atlas/settings.py` reads both into a frozen `Settings` value object via `load_settings(env=None)`, which defaults to `os.environ` and accepts an explicit mapping so tests never mutate the real environment. `~` in `ATLAS_DB` is expanded; a blank or unset value falls back to the default. An `ATLAS_TZ` that is not a known IANA zone raises `SettingsError` at load time instead of silently drifting to UTC. `Settings.today()` is the single place the wall clock is read for occurrence dates.

Resolving the path is deliberately side-effect free: the database file and its parent directory are created by the engine module, not by reading configuration.

The API is served with `uv run atlas serve` or `uv run uvicorn atlas.api.app:app --reload`, bound to `127.0.0.1`. Single user, no auth, no remote exposure. CORS is limited to the Vite origins above.
