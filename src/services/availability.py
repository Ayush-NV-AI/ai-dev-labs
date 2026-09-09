"""Resource availability.

Computes free time for a resource on a given day from its reservations.
"""

from datetime import datetime, timedelta

from src.common.intervals import merge_windows, overlaps
from src.db.models import Reservation


def is_free(
    resource_id: int, start: datetime, end: datetime, reservations: list[Reservation]
) -> bool:
    """Check whether a resource is free for an entire candidate window.

    Args:
        resource_id: The resource to check.
        start: Candidate window start, inclusive.
        end: Candidate window end, exclusive.
        reservations: Reservations to check against. Reservations for
            other resources are ignored.

    Returns:
        ``True`` if no reservation for this resource overlaps
        ``[start, end)``.
    """
    for reservation in reservations:
        if reservation.resource_id != resource_id:
            continue
        if overlaps(start, end, reservation.starts_at, reservation.ends_at):
            return False
    return True


def next_available(
    resource_id: int,
    after: datetime,
    duration: timedelta,
    reservations: list[Reservation],
) -> datetime | None:
    """Find the earliest instant at or after ``after`` when a window of
    the given duration is free.

    Only reservation end times (and ``after`` itself) can be the start
    of a newly-free window, so those are the only candidates checked.

    Args:
        resource_id: The resource to check.
        after: Earliest instant to consider, inclusive.
        duration: Length of the window that must be free.
        reservations: Reservations to check against.

    Returns:
        The earliest free start instant, or ``None`` if none of the
        candidates (up to the latest reservation end) works. A caller
        gets ``None`` only when every candidate up to that point is
        booked; any instant after the last reservation is always free
        and is included among the candidates.
    """
    candidates = {after}
    for reservation in reservations:
        if reservation.resource_id == resource_id and reservation.ends_at >= after:
            candidates.add(reservation.ends_at)

    for candidate in sorted(candidates):
        if is_free(resource_id, candidate, candidate + duration, reservations):
            return candidate
    return None


def free_slots(
    resource_id: int, day: datetime, reservations: list[Reservation]
) -> list[tuple[datetime, datetime]]:
    """List the free windows for a resource on a single day.

    windows are treated as closed intervals; see common.intervals.

    Args:
        resource_id: The resource to check.
        day: Any instant on the target day; only its date component is
            used. The day itself runs midnight to midnight.
        reservations: Reservations to check against. Reservations for
            other resources, or outside this day, are ignored.

    Returns:
        The resource's free windows on that day, earliest first, each a
        ``(start, end)`` pair.
    """
    day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)

    relevant = [
        r
        for r in reservations
        if r.resource_id == resource_id and overlaps(r.starts_at, r.ends_at, day_start, day_end)
    ]

    boundary_points = {day_start, day_end}
    for r in relevant:
        boundary_points.add(max(day_start, r.starts_at))
        boundary_points.add(min(day_end, r.ends_at))
    ordered_points = sorted(boundary_points)

    free_segments = []
    for seg_start, seg_end in zip(ordered_points, ordered_points[1:], strict=False):
        if seg_start >= seg_end:
            continue
        if is_free(resource_id, seg_start, seg_end, reservations):
            free_segments.append((seg_start, seg_end))

    return merge_windows(free_segments)
