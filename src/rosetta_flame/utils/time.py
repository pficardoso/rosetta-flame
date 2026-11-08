"""Time helpers.

Timestamps are stored in UTC. Calendar days use the learner's timezone.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

from rosetta_flame.config import TIMEZONE


def utc_now() -> datetime:
    return datetime.now(UTC)


def local_date(moment: datetime, tz: str = TIMEZONE) -> date:
    """The calendar day of ``moment`` in timezone ``tz``."""
    if moment.tzinfo is None:
        raise ValueError("moment must be timezone-aware")
    return moment.astimezone(ZoneInfo(tz)).date()
