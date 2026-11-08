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

## Data layer

SQLite through the standard library `sqlite3`, with numbered SQL migrations in
`src/rosetta_flame/db/migrations/`.

```python
from rosetta_flame.db import open_database
from rosetta_flame.db.repositories import topics

conn = open_database()  # data/rosetta_flame.db, created and migrated on first use
topic = topics.create(conn, name="Quantifiers", type="grammar")
```

- Set `ROSETTA_FLAME_DB` to use a different database file.
- Every id is a UUID (version 4) stored as text and generated in Python. The schema rejects
  ids that do not have the UUID shape.
- Topics and Weak Spots are both rows of `learning_item`; `review_state` and `exercise`
  point to it.
- Change the schema by adding a new file such as `0002_description.sql`. Never edit a
  migration that has already been applied.
- Timestamps are stored in UTC. Each attempt also stores its calendar day in the
  Europe/Lisbon timezone, which the "5 different days" rule uses.

## Layout

- `src/rosetta_flame/db/` - SQLite connection, migrations and repositories (the data layer)
- `src/rosetta_flame/models/` - enums and data classes
- `src/rosetta_flame/core/` - main logic
- `src/rosetta_flame/services/` - external services such as the Claude API
- `src/rosetta_flame/utils/` - small helpers
- `tests/` - test suite
- `scripts/` - one-off helper scripts
- `data/` - local data (gitignored)
- `docs/` - documentation
