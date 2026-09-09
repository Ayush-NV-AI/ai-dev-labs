"""Money formatting.

This is the **only** module in the codebase allowed to round a money
value. Everywhere else — models, services, aggregates — Decimal arithmetic
is carried at full precision and rounding is deferred to a call into this
module. Money is always :class:`~decimal.Decimal`, never ``float``:
floats cannot represent most decimal fractions exactly, and repeated
float arithmetic on prices silently drifts.
"""

from decimal import ROUND_HALF_UP, Decimal

_TWO_PLACES = Decimal("0.01")


def format_money(amount: Decimal) -> Decimal:
    """Round a money amount to 2 decimal places, half-up.

    Args:
        amount: The amount to round. Must already be a ``Decimal`` — this
            function does not accept ``float``.

    Returns:
        ``amount`` rounded to 2 decimal places using
        :data:`decimal.ROUND_HALF_UP` (e.g. ``1.005`` rounds to ``1.01``,
        never ``1.00``).
    """
    return amount.quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)


def format_money_str(amount: Decimal) -> str:
    """Render a money amount as a fixed 2-decimal-place string.

    Args:
        amount: The amount to render.

    Returns:
        The rounded amount as a string, e.g. ``"12.50"``, never
        ``"12.5"`` or ``"12.500"``.
    """
    return f"{format_money(amount):.2f}"
