"""Tests for src/common/intervals.py."""

from datetime import datetime

from src.common.intervals import contains, merge_windows, overlaps, split_on_boundary

T0 = datetime(2026, 3, 2, 8, 0)
T1 = datetime(2026, 3, 2, 9, 0)
T2 = datetime(2026, 3, 2, 10, 0)
T3 = datetime(2026, 3, 2, 11, 0)
T4 = datetime(2026, 3, 2, 12, 0)


def test_overlaps_true_for_windows_that_genuinely_overlap():
    """Two windows that share a real (non-instantaneous) span overlap."""
    assert overlaps(T0, T2, T1, T3) is True


def test_overlaps_true_when_one_window_fully_contains_the_other():
    """A window entirely inside another counts as overlapping."""
    assert overlaps(T0, T4, T1, T2) is True


def test_overlaps_false_for_clearly_disjoint_windows():
    """Two windows with a real gap between them do not overlap."""
    assert overlaps(T0, T1, T3, T4) is False


def test_overlaps_is_symmetric_for_a_clear_overlap():
    """Argument order doesn't change the result for a genuine overlap."""
    assert overlaps(T0, T2, T1, T3) == overlaps(T1, T3, T0, T2)


def test_overlaps_is_symmetric_for_a_clear_disjoint_case():
    """Argument order doesn't change the result when clearly disjoint."""
    assert overlaps(T0, T1, T3, T4) == overlaps(T3, T4, T0, T1)


def test_contains_point_inside_window():
    """A point strictly between start and end is contained."""
    assert contains(T0, T2, T1) is True


def test_contains_start_is_inclusive():
    """The window's own start instant is contained."""
    assert contains(T0, T2, T0) is True


def test_contains_end_is_exclusive():
    """The window's own end instant is NOT contained."""
    assert contains(T0, T2, T2) is False


def test_contains_point_outside_window():
    """A point outside the window entirely is not contained."""
    assert contains(T0, T1, T3) is False


def test_merge_windows_combines_overlapping_windows():
    """Two overlapping windows merge into one spanning both."""
    assert merge_windows([(T0, T2), (T1, T3)]) == [(T0, T3)]


def test_merge_windows_combines_touching_windows():
    """Two windows that touch (one ends when the other starts) merge
    into one contiguous window."""
    assert merge_windows([(T0, T1), (T1, T2)]) == [(T0, T2)]


def test_merge_windows_keeps_disjoint_windows_separate():
    """Two windows with a real gap between them stay separate."""
    assert merge_windows([(T0, T1), (T3, T4)]) == [(T0, T1), (T3, T4)]


def test_merge_windows_sorts_unsorted_input():
    """Input order doesn't matter — output is sorted by start."""
    assert merge_windows([(T3, T4), (T0, T1)]) == [(T0, T1), (T3, T4)]


def test_merge_windows_absorbs_a_fully_contained_window():
    """A window fully inside another contributes nothing extra."""
    assert merge_windows([(T0, T4), (T1, T2)]) == [(T0, T4)]


def test_merge_windows_empty_input():
    """An empty list merges to an empty list."""
    assert merge_windows([]) == []


def test_merge_windows_single_window():
    """A single window is returned unchanged."""
    assert merge_windows([(T0, T1)]) == [(T0, T1)]


def test_split_on_boundary_inside_the_window():
    """A boundary inside the window splits it into two real pieces."""
    before, after = split_on_boundary(T0, T2, T1)

    assert before == (T0, T1)
    assert after == (T1, T2)


def test_split_on_boundary_at_the_exact_start():
    """A boundary at the window's own start yields an empty 'before'."""
    before, after = split_on_boundary(T0, T2, T0)

    assert before == (T0, T0)
    assert after == (T0, T2)


def test_split_on_boundary_at_the_exact_end():
    """A boundary at the window's own end yields an empty 'after'."""
    before, after = split_on_boundary(T0, T2, T2)

    assert before == (T0, T2)
    assert after == (T2, T2)


def test_split_on_boundary_before_the_window_start():
    """A boundary before the window entirely yields an empty 'before'."""
    before, after = split_on_boundary(T1, T3, T0)

    assert before == (T1, T1)
    assert after == (T1, T3)


def test_split_on_boundary_after_the_window_end():
    """A boundary after the window entirely yields an empty 'after'."""
    before, after = split_on_boundary(T1, T3, T4)

    assert before == (T1, T3)
    assert after == (T3, T3)
