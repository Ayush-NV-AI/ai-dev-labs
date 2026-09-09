"""SQLAlchemy ORM models.

``Resource`` is inherited from ``main``. This branch (``lab-1-1-compare``)
adds ``Customer``, ``Order`` and ``OrderLine`` for the orders/reporting
feature set. ``Reservation`` is added separately in ``lab-1-2-scaffold``.
"""

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Declarative base shared by every ORM model in this repo."""


def _utcnow() -> datetime:
    """Return the current UTC time.

    Returns:
        A timezone-aware ``datetime`` in UTC, used as the default for
        ``created_at`` columns.
    """
    return datetime.now(UTC)


class Resource(Base):
    """A bookable resource, e.g. a meeting room or a piece of equipment.

    Attributes:
        id: Primary key.
        name: Display name shown to callers.
        kind: Category of resource (e.g. ``"room"``, ``"equipment"``).
        capacity: How many people or units the resource can serve at once.
        is_active: Whether the resource can currently be booked.
        created_at: When the resource was created, in UTC.
    """

    __tablename__ = "resources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    kind: Mapped[str] = mapped_column(String(50), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


#: Pricing tiers a customer can be assigned. Any other stored value is
#: treated as unrecognised and resolved down to ``"standard"`` — see
#: ``CustomerService.resolve_tier`` in ``src/services/customers.py``.
VALID_CUSTOMER_TIERS = ("standard", "silver", "gold")


class Customer(Base):
    """A customer who places orders.

    Attributes:
        id: Primary key.
        name: Display name.
        email: Contact email, unique per customer.
        tier: Pricing tier — one of :data:`VALID_CUSTOMER_TIERS`. Stored as
            free text rather than a database enum so an unrecognised
            value fails soft (resolved to ``"standard"``) instead of
            failing the write.
        created_at: When the customer record was created, in UTC.
    """

    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    tier: Mapped[str] = mapped_column(String(20), nullable=False, default="standard")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Order(Base):
    """An order placed by a customer, made up of one or more order lines.

    Attributes:
        id: Primary key.
        customer_id: Foreign key to :class:`Customer`.
        status: One of ``"pending"`` or ``"cancelled"``.
        total_amount: Sum of every line's ``unit_price * quantity``,
            rounded once by :func:`src.reporting.formatters.format_money`
            at creation time. This column is the only place an order's
            total is stored — it is never recomputed ad hoc elsewhere.
        created_at: When the order was placed, in UTC.
        lines: The order's line items.
    """

    __tablename__ = "orders"
    __table_args__ = (Index("ix_orders_customer_id", "customer_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2, asdecimal=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    lines: Mapped[list["OrderLine"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )


class OrderLine(Base):
    """A single line item within an :class:`Order`.

    Attributes:
        id: Primary key.
        order_id: Foreign key to the owning :class:`Order`.
        resource_id: Foreign key to the :class:`Resource` being ordered.
        quantity: Number of units ordered. Always a positive integer.
        unit_price: Price per unit, in the same currency as the order.
            Never rounded here — rounding only happens once, in
            :func:`src.reporting.formatters.format_money`, applied to the
            order's total.
        order: The owning :class:`Order`.
    """

    __tablename__ = "order_lines"
    __table_args__ = (Index("ix_order_lines_order_id", "order_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    resource_id: Mapped[int] = mapped_column(ForeignKey("resources.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2, asdecimal=True), nullable=False)

    order: Mapped["Order"] = relationship(back_populates="lines")
