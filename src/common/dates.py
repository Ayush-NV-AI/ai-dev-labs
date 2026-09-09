"""Date/time window helpers.

House convention, binding on every module in this repo: **all time windows
are HALF-OPEN, ``[start, end)``.** A window's start instant is included; a
window's end instant is not. Two windows that touch at a boundary — one
ending exactly when the other starts — do not overlap.

This matters beyond this module. The overlap rule for reservation windows
(``lab-1-2-scaffold`` and later) is defined in exactly these terms, so
getting comfortable with half-open bounds here pays off on Day 2.
"""

from datetime import UTC, date, datetime, timedelta


def month_bounds(year: int, month: int) -> tuple[datetime, datetime]:
    """Return the half-open ``[start, end)`` bounds of a calendar month.

    Args:
        year: Calendar year, e.g. ``2026``.
        month: Calendar month, 1-12.

    Returns:
        A ``(start, end)`` pair of UTC datetimes. ``start`` is midnight on
        the first of the month; ``end`` is midnight on the first of the
        following month. An instant ``t`` is in the month iff
        ``start <= t < end``.
    """
    start = datetime(year, month, 1, tzinfo=UTC)
    if month == 12:
        end = datetime(year + 1, 1, 1, tzinfo=UTC)
    else:
        end = datetime(year, month + 1, 1, tzinfo=UTC)
    return start, end


def iso_week_bounds(day: date) -> tuple[datetime, datetime]:
    """Return the half-open ``[start, end)`` bounds of an ISO week.

    The ISO week runs Monday through Sunday. Any day within the week may
    be passed in; the bounds are the same regardless of which day of that
    week is given.

    Args:
        day: Any date falling within the target week.

    Returns:
        A ``(start, end)`` pair of UTC datetimes. ``start`` is midnight on
        that week's Monday; ``end`` is midnight on the following Monday,
        seven days later. An instant ``t`` is in the week iff
        ``start <= t < end``.
    """
    monday = day - timedelta(days=day.isoweekday() - 1)
    start = datetime(monday.year, monday.month, monday.day, tzinfo=UTC)
    end = start + timedelta(days=7)
    return start, end
