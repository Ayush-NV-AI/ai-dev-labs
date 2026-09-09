"""Order aggregation for reporting.

Pure functions over already-fetched :class:`~src.db.models.Order`
instances — no database access here. Keeping aggregation separate from
persistence means these functions are trivial to unit test with plain
Python objects.
"""

from decimal import Decimal

from src.common.dates import month_bounds
from src.db.models import Order
from src.reporting.formatters import format_money


def revenue_by_month(orders: list[Order]) -> dict[str, Decimal]:
    """Total revenue per calendar month, keyed by month start date.

    Cancelled orders are excluded — a cancelled order never contributed
    revenue. Each order is bucketed using the house half-open month
    convention from :func:`src.common.dates.month_bounds`: an order
    belongs to the month whose ``[start, end)`` window contains its
    ``created_at``.

    Args:
        orders: Orders to aggregate, in any order.

    Returns:
        A dict mapping each month's start date (ISO ``"YYYY-MM-01"``) to
        that month's total revenue, rounded once via
        :func:`~src.reporting.formatters.format_money`.
    """
    totals: dict[str, Decimal] = {}
    for order in orders:
        if order.status == "cancelled":
            continue
        month_start, _ = month_bounds(order.created_at.year, order.created_at.month)
        key = month_start.date().isoformat()
        totals[key] = totals.get(key, Decimal("0")) + order.total_amount
    return {key: format_money(total) for key, total in totals.items()}


def orders_by_status(orders: list[Order]) -> dict[str, int]:
    """Count orders per status value.

    Args:
        orders: Orders to aggregate, in any order.

    Returns:
        A dict mapping each distinct ``status`` value found to how many
        orders have it.
    """
    counts: dict[str, int] = {}
    for order in orders:
        counts[order.status] = counts.get(order.status, 0) + 1
    return counts
