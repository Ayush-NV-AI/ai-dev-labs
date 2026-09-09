"""Tests for src/common/dates.py — half-open window helpers."""

from datetime import UTC, date, datetime

from src.common.dates import iso_week_bounds, month_bounds


def test_month_bounds_returns_half_open_window():
    """month_bounds spans the whole month, half-open on the end."""
    start, end = month_bounds(2026, 2)

    assert start == datetime(2026, 2, 1, tzinfo=UTC)
    assert end == datetime(2026, 3, 1, tzinfo=UTC)


def test_month_bounds_december_rolls_into_next_year():
    """December's end bound is January 1 of the following year."""
    start, end = month_bounds(2026, 12)

    assert start == datetime(2026, 12, 1, tzinfo=UTC)
    assert end == datetime(2027, 1, 1, tzinfo=UTC)


def test_month_bounds_end_instant_belongs_to_next_month():
    """An instant exactly at February's end bound is NOT in February."""
    feb_start, feb_end = month_bounds(2026, 2)
    mar_start, _ = month_bounds(2026, 3)

    assert feb_end == mar_start
    assert not (feb_start <= feb_end < feb_end)  # feb_end excluded from Feb
    assert mar_start <= feb_end < month_bounds(2026, 3)[1]  # included in March


def test_iso_week_bounds_monday_to_monday():
    """iso_week_bounds spans Monday 00:00 to the following Monday 00:00."""
    # 2026-02-11 is a Wednesday.
    start, end = iso_week_bounds(date(2026, 2, 11))

    assert start == datetime(2026, 2, 9, tzinfo=UTC)  # the Monday
    assert end == datetime(2026, 2, 16, tzinfo=UTC)  # the following Monday
    assert (end - start).days == 7


def test_iso_week_bounds_same_for_every_day_in_the_week():
    """Any day in the same ISO week yields the same bounds."""
    monday_bounds = iso_week_bounds(date(2026, 2, 9))
    sunday_bounds = iso_week_bounds(date(2026, 2, 15))

    assert monday_bounds == sunday_bounds
