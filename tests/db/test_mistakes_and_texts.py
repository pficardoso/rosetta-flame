import pytest

from rosetta_flame.db.repositories import mistakes, texts, weak_spots


def test_text_round_trip_and_newest_first(conn, now, submitted_text, missing_id):
    assert texts.get(conn, submitted_text.id) == submitted_text
    assert submitted_text.submitted_at == now
    later = texts.create(conn, content="Second", submitted_at=now.replace(hour=20))
    assert [t.id for t in texts.list_all(conn)] == [later.id, submitted_text.id]
    assert texts.get(conn, missing_id) is None


def test_create_and_list_mistakes(conn, now, submitted_text, weak_spot):
    mistake = mistakes.create(
        conn, text_id=submitted_text.id, weak_spot_id=weak_spot.id, original="many water",
        correction="much water", explanation="Water is uncountable.", created_at=now,
    )
    assert mistakes.get(conn, mistake.id) == mistake
    assert mistake.dismissed is False
    assert mistakes.list_for_text(conn, submitted_text.id) == [mistake]
    assert mistakes.list_for_weak_spot(conn, weak_spot.id) == [mistake]


def test_dismissed_mistakes_are_hidden_by_default(conn, now, submitted_text, weak_spot):
    mistake = mistakes.create(
        conn, text_id=submitted_text.id, weak_spot_id=weak_spot.id, original="a",
        correction="b", created_at=now,
    )
    dismissed = mistakes.dismiss(conn, mistake.id)
    assert dismissed.dismissed is True
    assert mistakes.list_for_weak_spot(conn, weak_spot.id) == []
    assert mistakes.list_for_weak_spot(conn, weak_spot.id, include_dismissed=True) == [dismissed]
    assert mistakes.dismiss(conn, mistake.id, dismissed=False).dismissed is False


def test_edit_and_reassign_a_mistake(conn, now, submitted_text, weak_spot, missing_id):
    other = weak_spots.create(conn, name="a/an", created_at=now)
    mistake = mistakes.create(
        conn, text_id=submitted_text.id, weak_spot_id=weak_spot.id, original="a",
        correction="b", created_at=now,
    )
    edited = mistakes.update(conn, mistake.id, correction="c", weak_spot_id=other.id)
    assert (edited.correction, edited.weak_spot_id) == ("c", other.id)
    with pytest.raises(ValueError):
        mistakes.update(conn, mistake.id, text_id=1)
    with pytest.raises(LookupError):
        mistakes.update(conn, missing_id, correction="x")
