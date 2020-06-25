from datetime import datetime

import pytz


def time_to_unix_utc(get_time, time_string, ts_tz="Europe/London"):
    """Convert HH:MM London time into a UTC Unix timestamp."""
    # get today's date
    date = get_time.date()
    # the time of the tide turning point
    time = datetime.strptime(time_string, "%H:%M").time()
    # combine the two, using London's timezone (GMT in winter, BST in summer)
    combined = pytz.timezone(ts_tz).localize(datetime.combine(date, time))
    # return a UTC Unix timestamp integer
    return int(combined.astimezone(pytz.utc).strftime("%s"))


def utc_now():
    return pytz.utc.localize(datetime.utcnow())
