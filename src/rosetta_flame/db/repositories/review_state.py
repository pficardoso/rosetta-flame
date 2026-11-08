"""Review state: status and next review date of a learning item."""

from __future__ import annotations

import sqlite3
from datetime import date, datetime
from typing import Any

from rosetta_flame.db.repositories._common import (
    date_from_db,
    date_to_db,
    dt_from_db,
    dt_to_db,
    require,
)
from rosetta_flame.models.entities import ReviewState
from rosetta_flame.models.enums import ItemType, Status

_SELECT = (
    "SELECT r.learning_item_id, r.status, r.next_review_date, r.interval_step, r.updated_at"
    " FROM review_state r"
)


def _from_row(row: sqlite3.Row) -> ReviewState:
    next_date = row["next_review_date"]
    return ReviewState(
        learning_item_id=row["learning_item_id"],
        status=Status(row["status"]),
        next_review_date=date_from_db(next_date) if next_date else None,
        interval_step=row["interval_step"],
        updated_at=dt_from_db(row["updated_at"]),
    )


def get(conn: sqlite3.Connection, learning_item_id: str) -> ReviewState | None:
    row = conn.execute(f"{_SELECT} WHERE r.learning_item_id = ?", (learning_item_id,)).fetchone()
    return _from_row(row) if row else None


def ensure(conn: sqlite3.Connection, learning_item_id: str, *, now: datetime) -> ReviewState:
    """Return the item's review state, creating it as New if it has none yet."""
    conn.execute(
        "INSERT OR IGNORE INTO review_state"
        " (learning_item_id, status, next_review_date, interval_step, updated_at)"
        " VALUES (?, ?, NULL, 0, ?)",
        (learning_item_id, Status.NEW.value, dt_to_db(now)),
    )
    return require(get(conn, learning_item_id), "review state")


def update(
    conn: sqlite3.Connection,
    learning_item_id: str,
    *,
    status: Status | str,
    next_review_date: date | None,
    interval_step: int,
    now: datetime,
) -> ReviewState:
    cursor = conn.execute(
        "UPDATE review_state SET status = ?, next_review_date = ?, interval_step = ?,"
        " updated_at = ? WHERE learning_item_id = ?",
        (
            Status(status).value,
            date_to_db(next_review_date) if next_review_date else None,
            interval_step,
            dt_to_db(now),
            learning_item_id,
        ),
    )
    if cursor.rowcount == 0:
        raise LookupError(f"review state for learning item {learning_item_id} not found")
    return require(get(conn, learning_item_id), "review state")


def due(
    conn: sqlite3.Connection, today: date, *, item_type: ItemType | str | None = None
) -> list[ReviewState]:
    """Review states whose next review date is ``today`` or earlier, oldest first."""
    sql = (
        f"{_SELECT} JOIN learning_item li ON li.id = r.learning_item_id"
        " WHERE r.next_review_date IS NOT NULL AND r.next_review_date <= ?"
    )
    params: list[Any] = [date_to_db(today)]
    if item_type is not None:
        sql += " AND li.item_type = ?"
        params.append(ItemType(item_type).value)
    sql += " ORDER BY r.next_review_date, r.learning_item_id"
    return [_from_row(row) for row in conn.execute(sql, params).fetchall()]
