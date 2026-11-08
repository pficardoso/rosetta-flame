"""Learning items: Topics and Weak Spots seen together."""

from __future__ import annotations

import sqlite3

from rosetta_flame.models.entities import LearningItem
from rosetta_flame.models.enums import ItemType

_SELECT = "SELECT id, item_type, name, description FROM learning_item_detail"


def _from_row(row: sqlite3.Row) -> LearningItem:
    return LearningItem(
        id=row["id"],
        item_type=ItemType(row["item_type"]),
        name=row["name"],
        description=row["description"],
    )


def get(conn: sqlite3.Connection, learning_item_id: str) -> LearningItem | None:
    row = conn.execute(f"{_SELECT} WHERE id = ?", (learning_item_id,)).fetchone()
    return _from_row(row) if row else None


def list_all(
    conn: sqlite3.Connection, *, item_type: ItemType | str | None = None
) -> list[LearningItem]:
    if item_type is None:
        rows = conn.execute(f"{_SELECT} ORDER BY item_type, name, id").fetchall()
    else:
        rows = conn.execute(
            f"{_SELECT} WHERE item_type = ? ORDER BY name, id", (ItemType(item_type).value,)
        ).fetchall()
    return [_from_row(row) for row in rows]
