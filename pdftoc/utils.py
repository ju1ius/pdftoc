from datetime import datetime, timedelta, timezone
from typing import Iterable


def local_timezone():
    timestamp = 42
    dt_utc = datetime.utcfromtimestamp(timestamp)
    dt_local = datetime.fromtimestamp(timestamp)
    diff = dt_local - dt_utc
    return timezone(diff)


def local_now():
    return datetime.now(local_timezone())


def all_equal(items: Iterable) -> bool:
    it = iter(items)
    try:
        first = next(it)
    except StopIteration:
        return False
    return all(x == first for x in it)
