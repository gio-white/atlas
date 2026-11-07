# Testing

What to test in each layer. Python tests live in `tests/<layer>/`; web tests sit next to the
code as `web/src/**/*.test.ts`.

Tests by layer:

| Layer      | How it is tested                                         |
| ---------- | -------------------------------------------------------- |
| `domain`   | Plain lists and dataclasses, no database                 |
| `services` | In-memory SQLite session                                 |
| `api`      | FastAPI `TestClient`, no live server                     |
| `cli`      | Typer's runner where it adds value; prefer service tests |

## Drift checks

Two tests keep docs and code from drifting apart:

- `tests/test_docs_drift.py` — every route in the FastAPI app appears in an API table under
  `docs/`, and every documented route exists.
- `web/src/docs-drift.test.ts` — every route path in `web/src/App.tsx` appears in
  `docs/product/navigation.md`.

The docs gate itself (hook logic) is tested in `tests/test_docs_gate.py`.
