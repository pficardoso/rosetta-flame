# Rosetta Flame

An app that helps me learn and improve my English.

## Setup (uv)

This project uses [uv](https://docs.astral.sh/uv/) to manage Python and dependencies.

```bash
uv sync          # creates .venv, installs the project and dev tools
```

## Run

```bash
uv run rosetta-flame --help
# or
uv run python -m rosetta_flame
```

## Test and lint

```bash
uv run pytest
uv run ruff check .
```

## Dependencies

```bash
uv add <package>          # runtime dependency
uv add --dev <package>    # dev-only dependency
uv remove <package>
```

## Layout

- `src/rosetta_flame/core/` - main logic
- `src/rosetta_flame/models/` - data classes / schemas
- `src/rosetta_flame/services/` - APIs, database, file I/O
- `src/rosetta_flame/utils/` - small helpers
- `tests/` - test suite
- `scripts/` - one-off helper scripts
- `data/` - local data (gitignored)
- `docs/` - documentation
