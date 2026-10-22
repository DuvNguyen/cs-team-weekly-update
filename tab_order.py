# tab_order.py — puts the SEO sheet's tabs newest first. Tab names carry the dates ("12/10-23/10-New") but no year,
# so each date gets the year that lands closest to today (late December tabs are last year's once it is January).
import datetime as dt
import re

RANGE = re.compile(r"(\d{1,2})/(\d{1,2})\s*-\s*(\d{1,2})/(\d{1,2})")


def _today() -> dt.date:
    return dt.date.today()


def _nearest(day: int, month: int, today: dt.date) -> dt.date | None:
    options = []
    for year in (today.year - 1, today.year, today.year + 1):
        try:
            options.append(dt.date(year, month, day))
        except ValueError:
            return None                                   # a date that does not exist (31/2)
    return min(options, key=lambda d: abs((d - today).days))


def _span(name: str, today: dt.date) -> tuple[dt.date, dt.date] | None:
    m = RANGE.search(name)
    if not m:
        return None
    d1, m1, d2, m2 = map(int, m.groups())
    end = _nearest(d2, m2, today)
    if end is None:
        return None
    try:
        start = dt.date(end.year, m1, d1)
        if start > end:
            start = dt.date(end.year - 1, m1, d1)         # a tab that runs over New Year starts in the year before
    except ValueError:
        return None
    return start, end


def newest_first(tabs: list[str], today: dt.date | None = None) -> list[str]:
    """Tabs with dates, newest first (by end date, then start date); the rest follow in the sheet's own order."""
    today = today or _today()
    spans = {t: _span(t, today) for t in tabs}
    dated = sorted((t for t in tabs if spans[t]), key=lambda t: (spans[t][1], spans[t][0]), reverse=True)
    return dated + [t for t in tabs if not spans[t]]
