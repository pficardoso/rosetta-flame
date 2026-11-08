import sqlite3

import pytest

from rosetta_flame.db import apply_migrations, connect
from rosetta_flame.db.migrate import Migration, split_statements

EXPECTED_TABLES = {
    "learning_item",
    "topic",
    "weak_spot",
    "weak_spot_topic",
    "review_state",
    "text",
    "mistake",
    "exercise",
    "attempt",
    "schema_migrations",
}


def _names(conn, kind):
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type = ?", (kind,))
    return {row["name"] for row in rows}


def test_initial_migration_creates_tables_and_view(conn):
    assert EXPECTED_TABLES <= _names(conn, "table")
    assert "learning_item_detail" in _names(conn, "view")


def test_foreign_keys_are_enabled(conn):
    assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1


def test_applying_twice_changes_nothing(conn):
    assert apply_migrations(conn) == []
    versions = [row["version"] for row in conn.execute("SELECT version FROM schema_migrations")]
    assert 1 in versions
    assert len(versions) == len(set(versions))


def test_failed_migration_is_rolled_back(monkeypatch):
    bad = Migration(1, "0001_bad.sql", "CREATE TABLE a (x INTEGER);\nINSERT INTO missing VALUES (1);")
    monkeypatch.setattr("rosetta_flame.db.migrate.load_migrations", lambda: [bad])
    conn = connect(":memory:")
    with pytest.raises(sqlite3.OperationalError):
        apply_migrations(conn)
    assert "a" not in _names(conn, "table")
    assert conn.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0] == 0


def test_split_statements_handles_semicolons_in_strings_and_comments():
    sql = (
        "-- first; with a semicolon in a comment\n"
        "CREATE TABLE a (x TEXT DEFAULT 'a;b');\n"
        "\n"
        "INSERT INTO a VALUES ('c');\n"
        "-- trailing comment\n"
    )
    statements = split_statements(sql)
    assert len(statements) == 2
    assert "'a;b'" in statements[0]
    assert statements[1].startswith("INSERT INTO a")


def test_split_statements_rejects_incomplete_statement():
    with pytest.raises(ValueError):
        split_statements("CREATE TABLE a (x INTEGER)")
