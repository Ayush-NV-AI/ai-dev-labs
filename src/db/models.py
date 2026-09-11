"""SQLAlchemy ORM models.

Only :class:`Resource` exists on ``main``. The rest of the booking domain
(reservations, orders, customers) is layered on by individual lab
branches, each of which owns the migration-equivalent for its own tables
so participants see one model added at a time rather than a domain dumped
on them up front. This branch (``lab-4-1-agent``) adds :class:`Reservation`.
"""

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


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


class Reservation(Base):
    """A booking of a resource for a half-open time window.

    Windows are HALF-OPEN ``[starts_at, ends_at)`` — a reservation ending
    exactly when another starts does not overlap it. See
    :mod:`src.db.repositories.reservations` for the query that enforces
    this.

    Attributes:
        id: Primary key.
        resource_id: Foreign key to the reserved :class:`Resource`.
        starts_at: Start of the reservation window, in UTC.
        ends_at: End of the reservation window (exclusive), in UTC.
        note: Optional free-text note attached at creation.
        created_at: When the reservation was created, in UTC.
        cancelled_at: When the reservation was cancelled, in UTC, or
            ``None`` if it is still active.
    """

    __tablename__ = "reservations"
    __table_args__ = (
        Index("ix_reservations_resource_window", "resource_id", "starts_at", "ends_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    resource_id: Mapped[int] = mapped_column(
        ForeignKey("resources.id"), nullable=False, index=True
    )
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
