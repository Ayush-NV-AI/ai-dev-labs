"""Lab 1.1 exercise tests — happy path only.

Skipped on every branch except when a participant is actively working the
exercise. The edge cases (empty list, ties on top spend) are deliberately
not tested here — see docs/LAB-1-1.md.
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
