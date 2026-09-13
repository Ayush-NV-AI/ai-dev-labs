"""Lab 1.1 exercise tests.

Skipped by default. Once you've prompted an implementation of
``summarise_orders``, delete the three ``@pytest.mark.skip(...)`` lines
below and run:

    pytest -q -s tests/test_summary.py -v

``test_summarise_orders_happy_path`` is a real pass/fail check.
``test_summarise_orders_empty_list`` and ``test_summarise_orders_tie``
don't assert a specific answer (the brief deliberately never specifies
one) — they just print what your implementation actually did, so you
have something concrete to compare against a partner who used the
other tool.
"""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from src.db.models import Order
from src.reporting.summary import summarise_orders


def _order(customer_id: int, total: str) -> Order:
    return Order(
        customer_id=customer_id,
        status="pending",
        total_amount=Decimal(total),
        created_at=datetime(2026, 2, 1, tzinfo=UTC),
    )


@pytest.mark.skip("lab exercise")
def test_summarise_orders_happy_path():
    """summarise_orders returns the four required keys for a normal list."""
    orders = [
        _order(customer_id=1, total="10.00"),
        _order(customer_id=1, total="5.00"),
        _order(customer_id=2, total="30.00"),
    ]

    result = summarise_orders(orders)

    assert result["total_revenue"] == Decimal("45.00")
    assert result["order_count"] == 3
    assert result["average_order"] == Decimal("15.00")
    assert result["top_customer_id"] == 2


@pytest.mark.skip("lab exercise")
def test_summarise_orders_empty_list():
    """No specified correct answer — this reports what happened, it
    doesn't grade it. Read the printed line: did it crash, or not?
    """
    try:
        result = summarise_orders([])
        print(f"\nEMPTY LIST -> no crash, returned: {result}")
    except Exception as exc:  # noqa: BLE001 — deliberately broad, this is a probe
        print(f"\nEMPTY LIST -> CRASHED: {type(exc).__name__}: {exc}")


@pytest.mark.skip("lab exercise")
def test_summarise_orders_tie():
    """No specified tie-break rule — this reports the choice made,
    it doesn't grade it.
    """
    orders = [
        _order(customer_id=1, total="50.00"),
        _order(customer_id=2, total="50.00"),
    ]
    result = summarise_orders(orders)
    print(f"\nTIE ON TOP SPEND -> top_customer_id chosen: {result['top_customer_id']}")
