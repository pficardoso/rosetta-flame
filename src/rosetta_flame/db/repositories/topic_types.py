"""Topic types: the lookup table that lists the kinds of Topic."""

from __future__ import annotations

import sqlite3

from rosetta_flame.models.entities import TopicTypeInfo
from rosetta_flame.models.enums import TopicType

_SELECT = "SELECT name, description FROM topic_type"


def _from_row(row: sqlite3.Row) -> TopicTypeInfo:
    return TopicTypeInfo(name=TopicType(row["name"]), description=row["description"])


def get(conn: sqlite3.Connection, name: TopicType | str) -> TopicTypeInfo | None:
    row = conn.execute(f"{_SELECT} WHERE name = ?", (str(name),)).fetchone()
    return _from_row(row) if row else None


def list_all(conn: sqlite3.Connection) -> list[TopicTypeInfo]:
    return [_from_row(row) for row in conn.execute(f"{_SELECT} ORDER BY name")]


def exists(conn: sqlite3.Connection, name: TopicType | str) -> bool:
    return get(conn, name) is not None
