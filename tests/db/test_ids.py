import uuid

from rosetta_flame.db.repositories import attempts, mistakes
from rosetta_flame.db.repositories._common import new_id


def test_new_id_is_a_canonical_version_4_uuid():
    value = new_id()
    assert value == str(uuid.UUID(value))
    assert uuid.UUID(value).version == 4


def test_new_ids_are_unique():
    assert len({new_id() for _ in range(1000)}) == 1000


def test_every_entity_gets_a_uuid_id(conn, now, topic, weak_spot, submitted_text, exercise):
    mistake = mistakes.create(
        conn, text_id=submitted_text.id, weak_spot_id=weak_spot.id, original="a",
        correction="b", created_at=now,
    )
    attempt = attempts.record(conn, exercise_id=exercise.id, correct=True, answered_at=now)
    ids = [topic.id, weak_spot.id, submitted_text.id, exercise.id, mistake.id, attempt.id]
    assert len(set(ids)) == len(ids)
    for value in ids:
        assert isinstance(value, str)
        assert value == str(uuid.UUID(value))


def test_foreign_keys_hold_the_same_uuid_text(conn, topic, weak_spot, exercise):
    assert exercise.learning_item_id == weak_spot.id
    assert conn.execute(
        "SELECT item_type FROM learning_item WHERE id = ?", (topic.id,)
    ).fetchone()["item_type"] == "topic"
