"""Applies the numbered ``.sql`` files in ``migrations/`` in order."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from importlib import resources

from rosetta_flame.db.connection import transaction
from rosetta_flame.db.repositories._common import dt_to_db
from rosetta_flame.utils.time import utc_now

MIGRATIONS_PACKAGE = "rosetta_flame.db.migrations"


@dataclass(frozen=True)
class Migration:
    version: int
    name: str
    sql: str


def load_migrations() -> list[Migration]:
    """All migration files, sorted by their numeric prefix (``0001_initial.sql`` -> 1)."""
    found: list[Migration] = []
    for entry in resources.files(MIGRATIONS_PACKAGE).iterdir():
        if not entry.name.endswith(".sql"):
            continue
        prefix = entry.name.partition("_")[0]
        if not prefix.isdigit():
            raise ValueError(f"Migration file name must start with a number: {entry.name}")
        found.append(Migration(int(prefix), entry.name, entry.read_text(encoding="utf-8")))
    found.sort(key=lambda migration: migration.version)
    versions = [migration.version for migration in found]
    if len(versions) != len(set(versions)):
        raise ValueError("Two migration files share the same version number")
    return found


def split_statements(sql: str) -> list[str]:
    """Split a script into single statements (safe for ``;`` inside strings)."""
    statements: list[str] = []
    buffer = ""
    for line in sql.splitlines(keepends=True):
        buffer += line
        if sqlite3.complete_statement(buffer):
            statement = buffer.strip()
            if statement:
                statements.append(statement)
            buffer = ""
    leftover = [
        line for line in buffer.splitlines() if line.strip() and not line.strip().startswith("--")
    ]
    if leftover:
        raise ValueError("Migration ends with an incomplete statement")
    return statements


def applied_versions(conn: sqlite3.Connection) -> set[int]:
    _ensure_version_table(conn)
    return {row["version"] for row in conn.execute("SELECT version FROM schema_migrations")}


def apply_migrations(conn: sqlite3.Connection, *, now: datetime | None = None) -> list[int]:
    """Apply every pending migration. Returns the versions applied (empty if up to date).

    Each migration runs in its own transaction together with its version record, so a
    failure leaves the database exactly as it was.
    """
    moment = now or utc_now()
    done = applied_versions(conn)
    newly_applied: list[int] = []
    for migration in load_migrations():
        if migration.version in done:
            continue
        with transaction(conn):
            for statement in split_statements(migration.sql):
                conn.execute(statement)
            conn.execute(
                "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)",
                (migration.version, dt_to_db(moment)),
            )
        newly_applied.append(migration.version)
    return newly_applied


def _ensure_version_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations ("
        "version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)"
    )
