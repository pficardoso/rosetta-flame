"""Weak Spots: custom items created from the learner's mistakes."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from datetime import datetime
from typing import Any

from rosetta_flame.db.connection import transaction
from rosetta_flame.db.repositories._common import (
    dt_from_db,
    dt_to_db,
    new_id,
    require,
    update_row,
)
from rosetta_flame.models.entities import WeakSpot
from rosetta_flame.models.enums import ItemType

_UPDATABLE = frozenset({"name", "description"})
_SELECT = "SELECT id, name, description, created_at FROM weak_spot"


def _from_row(row: sqlite3.Row) -> WeakSpot:
    return WeakSpot(
        id=row["id"],
        name=row["name"],
        description=row["description"],
        created_at=dt_from_db(row["created_at"]),
    )


def create(
    conn: sqlite3.Connection,
    *,
    name: str,
    created_at: datetime,
    description: str = "",
    topic_ids: Iterable[str] = (),
) -> WeakSpot:
    """Create a weak spot, optionally linked to parent topics, all or nothing."""
    item_id = new_id()
    with transaction(conn):
        conn.execute(
            "INSERT INTO learning_item (id, item_type) VALUES (?, ?)",
            (item_id, ItemType.WEAK_SPOT.value),
        )
        conn.execute(
            "INSERT INTO weak_spot (id, name, description, created_at) VALUES (?, ?, ?, ?)",
            (item_id, name, description, dt_to_db(created_at)),
        )
        for topic_id in topic_ids:
            link_topic(conn, item_id, topic_id)
    return require(get(conn, item_id), "weak spot")


def get(conn: sqlite3.Connection, weak_spot_id: str) -> WeakSpot | None:
    row = conn.execute(f"{_SELECT} WHERE id = ?", (weak_spot_id,)).fetchone()
    return _from_row(row) if row else None


def list_all(conn: sqlite3.Connection) -> list[WeakSpot]:
    rows = conn.execute(f"{_SELECT} ORDER BY created_at, id").fetchall()
    return [_from_row(row) for row in rows]


def update(conn: sqlite3.Connection, weak_spot_id: str, **fields: Any) -> WeakSpot:
    update_row(conn, "weak_spot", "id", weak_spot_id, fields, _UPDATABLE)
    return require(get(conn, weak_spot_id), "weak spot")


def link_topic(conn: sqlite3.Connection, weak_spot_id: str, topic_id: str) -> None:
    """Link a weak spot to a topic. Linking twice is harmless."""
    conn.execute(
        "INSERT OR IGNORE INTO weak_spot_topic (weak_spot_id, topic_id) VALUES (?, ?)",
        (weak_spot_id, topic_id),
    )


def unlink_topic(conn: sqlite3.Connection, weak_spot_id: str, topic_id: str) -> None:
    conn.execute(
        "DELETE FROM weak_spot_topic WHERE weak_spot_id = ? AND topic_id = ?",
        (weak_spot_id, topic_id),
    )


def topic_ids(conn: sqlite3.Connection, weak_spot_id: str) -> list[str]:
    rows = conn.execute(
        "SELECT topic_id FROM weak_spot_topic WHERE weak_spot_id = ? ORDER BY topic_id",
        (weak_spot_id,),
    ).fetchall()
    return [row["topic_id"] for row in rows]


def list_for_topic(conn: sqlite3.Connection, topic_id: str) -> list[WeakSpot]:
    rows = conn.execute(
        "SELECT w.id, w.name, w.description, w.created_at FROM weak_spot w"
        " JOIN weak_spot_topic l ON l.weak_spot_id = w.id"
        " WHERE l.topic_id = ? ORDER BY w.created_at, w.id",
        (topic_id,),
    ).fetchall()
    return [_from_row(row) for row in rows]
