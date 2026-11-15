"""Month counting — the ONE rule used on every screen (docs/DECISIONS.md, D1)."""
import calendar
from datetime import date


def add_months(start: date, n: int) -> date:
    """start + n calendar months, clamped to the last day of the month (31 Jan + 1 = 28/29 Feb)."""
    month_index = start.month - 1 + n
    year = start.year + month_index // 12
    month = month_index % 12 + 1
    day = min(start.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def planning_months(today: date, deadline: date) -> int:
    """Whole months from today until the deadline; partial months are not counted. Never negative."""
    if deadline <= today:
        return 0
    n = (deadline.year - today.year) * 12 + (deadline.month - today.month)
    while n > 0 and add_months(today, n) > deadline:
        n -= 1
    return n
