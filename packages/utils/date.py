import datetime


def coop_date_today():
    return (
        datetime.datetime.now()
        .astimezone(datetime.timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )
