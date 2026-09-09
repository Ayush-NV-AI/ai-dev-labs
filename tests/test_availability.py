"""Tests for src/services/availability.py."""

from datetime import datetime, timedelta

from src.db.models import Reservation
from src.services.availability import free_slots, is_free, next_available

DAY = datetime(2026, 3, 2)
DAY_START = datetime(2026, 3, 2, 0, 0)
DAY_END = datetime(2026, 3, 3, 0, 0)


def _reservation(resource_id, starts_at, ends_at):
    return Reservation(resource_id=resource_id, starts_at=starts_at, ends_at=ends_at)


# --- is_free ---------------------------------------------------------------


def test_is_free_true_with_no_reservations():
    """A resource with no reservations at all is free for any window."""
    window_start = datetime(2026, 3, 2, 9, 0)
    window_end = datetime(2026, 3, 2, 10, 0)

    assert is_free(1, window_start, window_end, []) is True


def test_is_free_true_ignores_other_resources():
    """A reservation for a different resource doesn't block this one."""
    other_resource_reservation = _reservation(
        2, datetime(2026, 3, 2, 9, 0), datetime(2026, 3, 2, 10, 0)
    )

    assert (
        is_free(
            1,
            datetime(2026, 3, 2, 9, 0),
            datetime(2026, 3, 2, 10, 0),
            [other_resource_reservation],
        )
        is True
    )


def test_is_free_false_when_window_overlaps_a_reservation():
    """A candidate window that genuinely overlaps a reservation is not
    free."""
    reservation = _reservation(1, datetime(2026, 3, 2, 9, 0), datetime(2026, 3, 2, 10, 0))

    result = is_free(1, datetime(2026, 3, 2, 9, 30), datetime(2026, 3, 2, 9, 45), [reservation])

    assert result is False


def test_is_free_true_for_a_clearly_disjoint_window():
    """A candidate window with a real gap before a reservation is free."""
    reservation = _reservation(1, datetime(2026, 3, 2, 9, 0), datetime(2026, 3, 2, 10, 0))

    assert is_free(1, datetime(2026, 3, 2, 7, 0), datetime(2026, 3, 2, 8, 0), [reservation]) is True


def test_is_free_true_for_a_window_ending_exactly_when_a_reservation_starts():
    """A candidate window that ends exactly when a reservation starts is
    free — the two windows only touch, per the house half-open
    convention."""
    reservation = _reservation(1, datetime(2026, 3, 2, 9, 0), datetime(2026, 3, 2, 10, 0))

    assert is_free(1, datetime(2026, 3, 2, 8, 0), datetime(2026, 3, 2, 9, 0), [reservation]) is True


# --- next_available ----------------------------------------------------


def test_next_available_returns_after_when_no_reservations():
    """With no reservations, the earliest free instant is 'after' itself."""
    after = datetime(2026, 3, 2, 9, 0)

    assert next_available(1, after, timedelta(minutes=30), []) == after


def test_next_available_returns_after_when_already_free():
    """When 'after' is already free for the full duration, it is
    returned immediately."""
    reservation = _reservation(1, datetime(2026, 3, 2, 9, 0), datetime(2026, 3, 2, 10, 0))
    after = datetime(2026, 3, 2, 12, 0)

    assert next_available(1, after, timedelta(minutes=30), [reservation]) == after


# --- free_slots ----------------------------------------------------------


def test_free_slots_full_day_free_with_no_reservations():
    """With no reservations, the whole day is one free slot."""
    assert free_slots(1, DAY, []) == [(DAY_START, DAY_END)]


def test_free_slots_includes_the_leading_slot_before_a_reservation():
    """The free time before the day's first reservation is reported."""
    reservation = _reservation(1, datetime(2026, 3, 2, 9, 0), datetime(2026, 3, 2, 10, 0))

    slots = free_slots(1, DAY, [reservation])

    assert (DAY_START, datetime(2026, 3, 2, 9, 0)) in slots


def test_free_slots_never_overlaps_a_reservation():
    """No reported free slot overlaps the reservation it was computed
    against."""
    reservation = _reservation(1, datetime(2026, 3, 2, 9, 0), datetime(2026, 3, 2, 10, 0))

    slots = free_slots(1, DAY, [reservation])

    for slot_start, slot_end in slots:
        assert not (slot_start < reservation.ends_at and reservation.starts_at < slot_end)


def test_free_slots_includes_the_slot_immediately_after_a_reservation():
    """The free time right after a reservation, before the next thing
    (here, the end of the day), is reported."""
    reservation = _reservation(1, datetime(2026, 3, 2, 9, 0), datetime(2026, 3, 2, 10, 0))

    slots = free_slots(1, DAY, [reservation])

    assert (datetime(2026, 3, 2, 10, 0), DAY_END) in slots


def test_free_slots_includes_the_gap_between_two_reservations():
    """A real gap between two same-day reservations is reported as a
    free slot."""
    first = _reservation(1, datetime(2026, 3, 2, 9, 0), datetime(2026, 3, 2, 10, 0))
    second = _reservation(1, datetime(2026, 3, 2, 14, 0), datetime(2026, 3, 2, 15, 0))

    slots = free_slots(1, DAY, [first, second])

    assert (datetime(2026, 3, 2, 10, 0), datetime(2026, 3, 2, 14, 0)) in slots


def test_free_slots_includes_the_final_slot_of_the_day():
    """The free time after the day's last reservation, running to
    midnight, is reported."""
    first = _reservation(1, datetime(2026, 3, 2, 9, 0), datetime(2026, 3, 2, 10, 0))
    second = _reservation(1, datetime(2026, 3, 2, 14, 0), datetime(2026, 3, 2, 15, 0))

    slots = free_slots(1, DAY, [first, second])

    assert (datetime(2026, 3, 2, 15, 0), DAY_END) in slots
