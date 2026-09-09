"""SQLAlchemy ORM models.

``Resource`` is inherited from ``main``. This branch (``lab-1-2-scaffold``)
adds ``Reservation`` for the reservations feature scaffold.
"""

from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
)
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

    House convention (see ``src.common`` on branches that have it, and
    every reservation-adjacent module in this repo): windows are
    HALF-OPEN, ``[starts_at, ends_at)``. Two reservations that touch at a
    boundary — one ending exactly when the other starts — do not overlap.

    Attributes:
        id: Primary key.
        resource_id: Foreign key to the reserved :class:`Resource`.
        starts_at: Window start, inclusive.
        ends_at: Window end, exclusive. Enforced at the database level to
            be strictly after ``starts_at``.
        note: Optional free-text note, e.g. a purpose for the booking.
        created_at: When the reservation was made, in UTC.
    """

    __tablename__ = "reservations"
    __table_args__ = (
        Index("ix_reservations_resource_id", "resource_id"),
        Index("ix_reservations_resource_window", "resource_id", "starts_at", "ends_at"),
        CheckConstraint("ends_at > starts_at", name="ck_reservations_ends_after_starts"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    resource_id: Mapped[int] = mapped_column(ForeignKey("resources.id"), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
