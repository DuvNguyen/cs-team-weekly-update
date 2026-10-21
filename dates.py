import datetime

def report_period(today: datetime.date):
    """The 14 days ending 2 days ago (GSC data lags ~2 days), matching GSC's custom
    14-day range. Rolling, not anchored to a weekday.
    e.g. today Fri 25 Sep -> 10 Sep .. 23 Sep. Returns (start, end)."""
    end = today - datetime.timedelta(days=2)
    return end - datetime.timedelta(days=13), end

def prev_period(start: datetime.date):
    """The 14-day window immediately before `start`."""
    return start - datetime.timedelta(days=14), start - datetime.timedelta(days=1)
