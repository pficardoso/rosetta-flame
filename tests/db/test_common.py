from datetime import UTC, date, datetime, timedelta, timezone

import pytest

from rosetta_flame.db.repositories._common import (
    date_from_db,
    date_to_db,
    dt_from_db,
    dt_to_db,
    update_row,
)


def test_datetime_round_trips_as_utc():
    lisbon_summer = timezone(timedelta(hours=1))
    moment = datetime(2026, 7, 2, 0, 30, tzinfo=lisbon_summer)
    stored = dt_to_db(moment)
    assert stored.endswith("+00:00")
    assert dt_from_db(stored) == moment
    assert dt_from_db(stored).tzinfo is not None


def test_stored_datetimes_sort_like_time():
    earlier = datetime(2026, 11, 8, 19, 0, tzinfo=UTC)
    later = earlier + timedelta(microseconds=1)
    assert dt_to_db(earlier) < dt_to_db(later)


def test_naive_datetime_is_rejected():
    with pytest.raises(ValueError):
        dt_to_db(datetime(2026, 11, 8, 19, 0))


def test_date_round_trip():
    assert date_from_db(date_to_db(date(2026, 11, 8))) == date(2026, 11, 8)


def test_update_row_rejects_unknown_fields(conn, topic):
    with pytest.raises(ValueError):
        update_row(conn, "topic", "id", topic.id, {"id": 5}, {"name"})
