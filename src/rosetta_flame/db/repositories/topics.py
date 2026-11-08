"""Topics: the items of the teaching program."""

from __future__ import annotations

import sqlite3
from typing import Any

from rosetta_flame.db.connection import transaction
from rosetta_flame.db.repositories._common import new_id, require, update_row
from rosetta_flame.models.entities import Topic
from rosetta_flame.models.enums import ItemType, TopicType

_UPDATABLE = frozenset(
    {"name", "description", "type", "level", "unit", "order_in_program", "source_program"}
)
_SELECT = (
    "SELECT id, name, description, type, level, unit, order_in_program, source_program FROM topic"
)


def _from_row(row: sqlite3.Row) -> Topic:
    return Topic(
        id=row["id"],
        name=row["name"],
        description=row["description"],
        type=TopicType(row["type"]),
        level=row["level"],
        unit=row["unit"],
        order_in_program=row["order_in_program"],
        source_program=row["source_program"],
    )


def create(
    conn: sqlite3.Connection,
    *,
    name: str,
    type: TopicType | str,
    description: str = "",
    level: str | None = None,
    unit: str | None = None,
    order_in_program: int | None = None,
    source_program: str | None = None,
) -> Topic:
    topic_type = TopicType(type)
    item_id = new_id()
    with transaction(conn):
        conn.execute(
            "INSERT INTO learning_item (id, item_type) VALUES (?, ?)",
            (item_id, ItemType.TOPIC.value),
        )
        conn.execute(
            "INSERT INTO topic (id, name, description, type, level, unit,"
            " order_in_program, source_program) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (item_id, name, description, topic_type.value, level, unit, order_in_program,
             source_program),
        )
    return require(get(conn, item_id), "topic")


def get(conn: sqlite3.Connection, topic_id: str) -> Topic | None:
    row = conn.execute(f"{_SELECT} WHERE id = ?", (topic_id,)).fetchone()
    return _from_row(row) if row else None


def list_all(
    conn: sqlite3.Connection,
    *,
    type: TopicType | str | None = None,
    level: str | None = None,
    source_program: str | None = None,
) -> list[Topic]:
    clauses: list[str] = []
    params: list[Any] = []
    if type is not None:
        clauses.append("type = ?")
        params.append(TopicType(type).value)
    if level is not None:
        clauses.append("level = ?")
        params.append(level)
    if source_program is not None:
        clauses.append("source_program = ?")
        params.append(source_program)
    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = conn.execute(
        f"{_SELECT}{where} ORDER BY order_in_program IS NULL, order_in_program, id", params
    ).fetchall()
    return [_from_row(row) for row in rows]


def update(conn: sqlite3.Connection, topic_id: str, **fields: Any) -> Topic:
    if "type" in fields:
        fields["type"] = TopicType(fields["type"])
    update_row(conn, "topic", "id", topic_id, fields, _UPDATABLE)
    return require(get(conn, topic_id), "topic")
