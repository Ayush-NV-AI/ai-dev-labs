"""Tests for src/reporting/aggregates.py."""

from datetime import UTC, datetime
from decimal import Decimal

from src.db.models import Order
from src.reporting.aggregates import orders_by_status, revenue_by_month


def _order(customer_id: int, status: str, total: str, created_at: datetime) -> Order:
    return Order(
        customer_id=customer_id,
        status=status,
        total_amount=Decimal(total),
        created_at=created_at,
    )


def test_revenue_by_month_groups_and_sums():
    """Orders in the same month are summed under one key."""
    orders = [
        _order(1, "pending", "10.00", datetime(2026, 2, 5, tzinfo=UTC)),
        _order(1, "pending", "5.50", datetime(2026, 2, 27, tzinfo=UTC)),
        _order(1, "pending", "3.00", datetime(2026, 3, 1, tzinfo=UTC)),
    ]

    result = revenue_by_month(orders)

    assert result == {
        "2026-02-01": Decimal("15.50"),
        "2026-03-01": Decimal("3.00"),
    }


def test_revenue_by_month_excludes_cancelled_orders():
    """A cancelled order contributes nothing to monthly revenue."""
    orders = [
        _order(1, "pending", "10.00", datetime(2026, 2, 5, tzinfo=UTC)),
        _order(1, "cancelled", "99.00", datetime(2026, 2, 6, tzinfo=UTC)),
    ]

    result = revenue_by_month(orders)

    assert result == {"2026-02-01": Decimal("10.00")}


def test_revenue_by_month_empty_input():
    """An empty order list produces an empty dict, not an error."""
    assert revenue_by_month([]) == {}


def test_orders_by_status_counts_each_status():
    """Each status value is counted independently."""
    orders = [
        _order(1, "pending", "1.00", datetime(2026, 2, 1, tzinfo=UTC)),
        _order(1, "pending", "1.00", datetime(2026, 2, 1, tzinfo=UTC)),
        _order(1, "cancelled", "1.00", datetime(2026, 2, 1, tzinfo=UTC)),
    ]

    assert orders_by_status(orders) == {"pending": 2, "cancelled": 1}


def test_orders_by_status_empty_input():
    """An empty order list produces an empty dict, not an error."""
    assert orders_by_status([]) == {}
