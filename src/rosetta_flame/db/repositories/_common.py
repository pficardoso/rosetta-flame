"""Helpers shared by the repository modules."""

from __future__ import annotations

import sqlite3
import uuid
from collections.abc import Collection
from datetime import UTC, date, datetime
from enum import Enum
from typing import Any, TypeVar

T = TypeVar("T")


def dt_to_db(value: datetime) -> str:
    """UTC ISO-8601 text with a fixed width, so text order equals time order."""
    if value.tzinfo is None:
        raise ValueError("datetime must be timezone-aware")
    return value.astimezone(UTC).isoformat(timespec="microseconds")


def dt_from_db(value: str) -> datetime:
    return datetime.fromisoformat(value)


def date_to_db(value: date) -> str:
    return value.isoformat()


def date_from_db(value: str) -> date:
    return date.fromisoformat(value)


def new_id() -> str:
    """A new random UUID (version 4) as canonical lowercase text."""
    return str(uuid.uuid4())


def to_db(value: Any) -> Any:
    """Convert a Python value to what SQLite stores."""
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):  # check before date: datetime is a subclass of date
        return dt_to_db(value)
    if isinstance(value, date):
        return date_to_db(value)
    if isinstance(value, bool):
        return int(value)
    return value


def require(value: T | None, what: str) -> T:
    if value is None:
        raise LookupError(f"{what} not found")
    return value


def update_row(
    conn: sqlite3.Connection,
    table: str,
    id_column: str,
    row_id: str,
    fields: dict[str, Any],
    allowed: Collection[str],
) -> None:
    """UPDATE the given fields of one row. Unknown field names are rejected."""
    unknown = set(fields) - set(allowed)
    if unknown:
        raise ValueError(f"Cannot update {table} fields: {sorted(unknown)}")
    if not fields:
        return
    assignments = ", ".join(f"{name} = ?" for name in fields)
    cursor = conn.execute(
        f"UPDATE {table} SET {assignments} WHERE {id_column} = ?",
        (*(to_db(value) for value in fields.values()), row_id),
    )
    if cursor.rowcount == 0:
        raise LookupError(f"{table} {row_id} not found")
