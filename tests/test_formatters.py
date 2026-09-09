"""Tests for src/reporting/formatters.py — the only place money rounds."""

from decimal import Decimal

from src.reporting.formatters import format_money, format_money_str


def test_format_money_rounds_half_up():
    """Exact halfway values round up, not to even (banker's rounding)."""
    assert format_money(Decimal("1.005")) == Decimal("1.01")
    assert format_money(Decimal("2.675")) == Decimal("2.68")


def test_format_money_leaves_already_rounded_values_unchanged():
    """A value already at 2 decimal places is returned unchanged."""
    assert format_money(Decimal("19.99")) == Decimal("19.99")


def test_format_money_pads_short_decimals():
    """A value with fewer than 2 decimal places is padded to 2."""
    assert format_money(Decimal("5")) == Decimal("5.00")


def test_format_money_str_always_shows_two_places():
    """The string form always shows exactly 2 decimal places."""
    assert format_money_str(Decimal("5")) == "5.00"
    assert format_money_str(Decimal("1.005")) == "1.01"
