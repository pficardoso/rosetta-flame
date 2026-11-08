"""The database itself must refuse invalid data, whatever the Python code does."""

import sqlite3

import pytest

from rosetta_flame.db.repositories import review_state
from rosetta_flame.db.repositories._common import new_id


def test_topic_needs_a_learning_item(conn, missing_id):
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO topic (id, name, type) VALUES (?, 'x', 'grammar')", (missing_id,))


def test_weak_spot_cannot_take_over_a_topics_learning_item(conn, topic):
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO weak_spot (id, name, created_at) VALUES (?, 'x', 'now')", (topic.id,)
        )


def test_learning_item_type_is_restricted(conn):
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO learning_item (id, item_type) VALUES (?, 'bogus')", (new_id(),))


def test_learning_item_in_use_cannot_be_deleted(conn, topic):
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("DELETE FROM learning_item WHERE id = ?", (topic.id,))


@pytest.mark.parametrize("bad_id", ["1", "not-a-uuid", "0123456789abcdef0123456789abcdef"])
def test_ids_must_look_like_uuids(conn, bad_id):
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO learning_item (id, item_type) VALUES (?, 'topic')", (bad_id,))
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO text (id, content, submitted_at) VALUES (?, 'x', 'now')", (bad_id,)
        )


def test_integer_ids_are_rejected(conn):
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO text (id, content, submitted_at) VALUES (1, 'x', 'now')")


def test_ids_cannot_be_null(conn):
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO text (id, content, submitted_at) VALUES (NULL, 'x', 'now')")


def test_status_is_restricted(conn, now, weak_spot):
    review_state.ensure(conn, weak_spot.id, now=now)
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "UPDATE review_state SET status = 'Bogus' WHERE learning_item_id = ?",
            (weak_spot.id,),
        )


def test_review_state_needs_an_existing_learning_item(conn, now, missing_id):
    with pytest.raises(sqlite3.IntegrityError):
        review_state.ensure(conn, missing_id, now=now)


def test_exercise_needs_an_existing_learning_item(conn, missing_id):
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO exercise (id, learning_item_id, type, prompt, answer, source,"
            " created_at) VALUES (?, ?, 'fill_in_the_blank', 'p', 'a', 'generic', 'now')",
            (new_id(), missing_id),
        )


def test_multiple_choice_needs_options(conn, weak_spot):
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO exercise (id, learning_item_id, type, prompt, answer, source,"
            " created_at) VALUES (?, ?, 'multiple_choice', 'p', 'a', 'generic', 'now')",
            (new_id(), weak_spot.id),
        )


def test_options_must_be_valid_json(conn, weak_spot):
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO exercise (id, learning_item_id, type, prompt, answer, options_json,"
            " source, created_at)"
            " VALUES (?, ?, 'multiple_choice', 'p', 'a', 'not json', 'generic', 'now')",
            (new_id(), weak_spot.id),
        )


def test_mistake_needs_an_existing_text(conn, weak_spot, missing_id):
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO mistake (id, text_id, weak_spot_id, original, correction, created_at)"
            " VALUES (?, ?, ?, 'a', 'b', 'now')",
            (new_id(), missing_id, weak_spot.id),
        )


def test_attempt_correct_flag_is_restricted(conn, exercise):
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO attempt (id, exercise_id, correct, answered_at, local_date)"
            " VALUES (?, ?, 2, 'now', '2026-11-08')",
            (new_id(), exercise.id),
        )
