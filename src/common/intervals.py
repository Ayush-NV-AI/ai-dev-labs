"""Interval helpers for time windows.

House convention (see ``src.common.dates`` on branches that have it):
windows are HALF-OPEN, ``[start, end)``. Every function here is written
against that convention.
"""

from datetime import datetime


def overlaps(
    a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime
) -> bool:
    """Return whether two half-open windows overlap.

    Two windows overlap iff ``a_start < b_end`` and ``b_start < a_end``.
    A window that touches another at a boundary — ending exactly when
    the other starts — does not overlap it.

    Args:
        a_start: Start of window A, inclusive.
        a_end: End of window A, exclusive.
        b_start: Start of window B, inclusive.
        b_end: End of window B, exclusive.

    Returns:
        ``True`` if the two windows share any instant, ``False``
        otherwise.
    """
    return a_start <= b_end and b_start < a_end


def contains(start: datetime, end: datetime, point: datetime) -> bool:
    """Return whether a point falls inside a half-open window.

    Args:
        start: Window start, inclusive.
        end: Window end, exclusive.
        point: The instant to test.

    Returns:
        ``True`` if ``start <= point < end``.
    """
    return start <= point < end


def merge_windows(
    windows: list[tuple[datetime, datetime]],
) -> list[tuple[datetime, datetime]]:
    """Merge a list of windows, combining any that overlap or touch.

    Args:
        windows: Windows to merge, in any order.

    Returns:
        The windows sorted by start time, with any overlapping or
        touching runs combined into a single window each.
    """
    if not windows:
        return []

    ordered = sorted(windows, key=lambda w: w[0])
    merged = [ordered[0]]
    for start, end in ordered[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:
            if end > last_end:
                merged[-1] = (last_start, end)
        else:
            merged.append((start, end))
    return merged


def split_on_boundary(
    start: datetime, end: datetime, boundary: datetime
) -> tuple[tuple[datetime, datetime], tuple[datetime, datetime]]:
    """Split a window into two at a boundary instant.

    Args:
        start: Window start, inclusive.
        end: Window end, exclusive.
        boundary: The instant to split at.

    Returns:
        A ``(before, after)`` pair of windows. ``before`` covers
        ``[start, boundary)`` and ``after`` covers ``[boundary, end)``,
        each clamped to ``[start, end)``. Either half collapses to a
        zero-length window (``start == end``) if the boundary falls
        outside the original window on that side.
    """
    if boundary <= start:
        return (start, start), (start, end)
    if boundary >= end:
        return (start, end), (end, end)
    return (start, boundary), (boundary, end)
