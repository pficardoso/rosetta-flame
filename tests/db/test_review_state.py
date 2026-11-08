from datetime import date

import pytest

from rosetta_flame.db.repositories import review_state
from rosetta_flame.models.enums import ItemType, Status


def test_ensure_creates_a_new_state_once(conn, now, weak_spot):
    first = review_state.ensure(conn, weak_spot.id, now=now)
    assert first.status is Status.NEW
    assert first.next_review_date is None
    assert first.interval_step == 0
    review_state.update(
        conn, weak_spot.id, status=Status.LEARNING, next_review_date=date(2026, 11, 9),
        interval_step=1, now=now,
    )
    again = review_state.ensure(conn, weak_spot.id, now=now)
    assert again.status is Status.LEARNING  # ensure never overwrites


def test_get_missing_returns_none(conn, weak_spot):
    assert review_state.get(conn, weak_spot.id) is None


def test_update_and_missing_state(conn, now, topic, missing_id):
    review_state.ensure(conn, topic.id, now=now)
    updated = review_state.update(
        conn, topic.id, status="Reviewing", next_review_date=date(2026, 11, 15),
        interval_step=3, now=now,
    )
    assert updated.status is Status.REVIEWING
    assert updated.next_review_date == date(2026, 11, 15)
    assert updated.updated_at == now
    with pytest.raises(LookupError):
        review_state.update(
            conn, missing_id, status="New", next_review_date=None, interval_step=0, now=now
        )


def test_due_returns_items_on_or_before_today(conn, now, topic, weak_spot):
    review_state.ensure(conn, topic.id, now=now)
    review_state.ensure(conn, weak_spot.id, now=now)
    assert review_state.due(conn, date(2026, 11, 30)) == []  # New items have no date

    review_state.update(
        conn, topic.id, status=Status.LEARNING, next_review_date=date(2026, 11, 9),
        interval_step=1, now=now,
    )
    review_state.update(
        conn, weak_spot.id, status=Status.LEARNING, next_review_date=date(2026, 11, 8),
        interval_step=1, now=now,
    )
    assert [s.learning_item_id for s in review_state.due(conn, date(2026, 11, 8))] == [weak_spot.id]
    both = review_state.due(conn, date(2026, 11, 9))
    assert [s.learning_item_id for s in both] == [weak_spot.id, topic.id]  # oldest first


def test_due_can_filter_by_item_type(conn, now, topic, weak_spot):
    for item in (topic, weak_spot):
        review_state.ensure(conn, item.id, now=now)
        review_state.update(
            conn, item.id, status=Status.LEARNING, next_review_date=date(2026, 11, 8),
            interval_step=1, now=now,
        )
    topics_due = review_state.due(conn, date(2026, 11, 8), item_type=ItemType.TOPIC)
    weak_due = review_state.due(conn, date(2026, 11, 8), item_type="weak_spot")
    assert [s.learning_item_id for s in topics_due] == [topic.id]
    assert [s.learning_item_id for s in weak_due] == [weak_spot.id]
