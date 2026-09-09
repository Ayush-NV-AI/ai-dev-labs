"""Trainer reference — do not run in lab.

Full characterization suite for src/legacy/pricing.py. This pins down
the module's actual current behaviour, bugs included, so a refactor can
be checked against it. Un-skip locally to confirm the suite passes
against the current module, then re-skip before committing.
"""

from decimal import Decimal

import pytest

from src.legacy.pricing import price_order

pytestmark = pytest.mark.skip("trainer reference — do not run in lab")


def test_tier_and_threshold_discounts_stack():
    """Tier and threshold discounts are both applied — they stack,
    almost certainly unintentionally, and that stacking must survive any
    refactor."""
    order = {"amount": 600, "quantity": 2, "rush": False, "region": "TX"}
    customer = {"tier": "gold"}

    # gold tier discount (10%) + threshold discount (5%) = 15% off 600
    assert price_order(order, customer, []) == 510.0


def test_threshold_comparison_excludes_the_exact_boundary():
    """An order for exactly the threshold amount gets NO threshold
    discount — the comparison is `>`, not `>=`."""
    at_threshold = {"amount": 500, "quantity": 2, "rush": False, "region": "TX"}
    just_above = {"amount": 500.01, "quantity": 2, "rush": False, "region": "TX"}
    customer = {"tier": "gold"}

    # at_threshold: only the 10% tier discount applies -> 500 - 50 = 450
    assert price_order(at_threshold, customer, []) == 450.0
    # just_above: both discounts apply
    assert price_order(just_above, customer, []) == 425.01


def test_double_rounding_is_a_cent_off_a_single_rounding():
    """Rounding happens twice (once on the discount, once on the final
    total), which for this input lands a cent above what rounding only
    once at the end would give (990.00)."""
    order = {"amount": 1000.005, "quantity": 1, "rush": False, "region": "CA"}
    customer = {"tier": "bronze"}

    assert price_order(order, customer, []) == 990.01


def test_unknown_customer_tier_silently_gets_the_gold_rate():
    """A tier the pricing table doesn't recognise falls through to the
    gold rate rather than raising or defaulting to no discount."""
    order = {"amount": 200, "quantity": 1, "region": "TX"}
    customer = {"tier": "platinum"}  # not bronze/silver/gold

    assert price_order(order, customer, []) == 180.0


def test_negative_computed_price_is_clamped_to_zero():
    """A promo big enough to drive the price negative is silently
    clamped to zero rather than surfacing the bad promo data."""
    order = {"amount": 100, "quantity": 1, "region": "TX"}
    customer = {"tier": "bronze"}
    promos = [{"type": "fixed", "value": 500}]

    assert price_order(order, customer, promos) == 0.0


def test_invalid_promos_payload_returns_a_string_not_a_number():
    """Passing something other than a list for promos returns an error
    string — the third of the module's three inconsistent return types
    (Decimal, float, str)."""
    result = price_order({"amount": 10, "quantity": 1}, {"tier": "gold"}, "not-a-list")

    assert result == "invalid promos payload"


def test_decimal_input_returns_a_decimal_result():
    """A Decimal-typed order amount produces a Decimal result — the
    module's arithmetic is not consistently one numeric type."""
    order = {"amount": Decimal("300.00"), "quantity": 1, "region": "TX"}
    customer = {"tier": "silver"}

    result = price_order(order, customer, [])

    assert isinstance(result, Decimal)
    assert result == Decimal("285.00")
