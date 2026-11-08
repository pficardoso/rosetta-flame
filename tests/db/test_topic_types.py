"""The TopicType enum and the topic_type table must list the same types."""

import sqlite3

import pytest

from rosetta_flame.db.repositories import topic_types
from rosetta_flame.models.enums import TopicType


def test_enum_matches_table(conn):
    in_table = {row[0] for row in conn.execute("SELECT name FROM topic_type")}
    assert in_table == {t.value for t in TopicType}


def test_every_type_has_a_description(conn):
    assert all(info.description.strip() for info in topic_types.list_all(conn))


def test_get_returns_the_enum(conn):
    info = topic_types.get(conn, "lexical")
    assert info is not None
    assert info.name is TopicType.LEXICAL
    assert topic_types.get(conn, "spelling") is None


def test_database_refuses_a_topic_with_an_unknown_type(conn, missing_id):
    conn.execute("INSERT INTO learning_item (id, item_type) VALUES (?, 'topic')", (missing_id,))
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO topic (id, name, type) VALUES (?, 'x', 'spelling')", (missing_id,)
        )
