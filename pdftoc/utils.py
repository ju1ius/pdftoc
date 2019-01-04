from datetime import datetime, timedelta, timezone


def local_timezone():
    timestamp = 42
    dt_utc = datetime.utcfromtimestamp(timestamp)
    dt_local = datetime.fromtimestamp(timestamp)
    diff = dt_local - dt_utc
    return timezone(diff)


def local_now():
    return datetime.now(local_timezone())
