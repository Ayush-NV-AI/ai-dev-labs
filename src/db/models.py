"""SQLAlchemy ORM models.

Only :class:`Resource` exists on ``main``. The rest of the booking domain
(reservations, orders, customers) is layered on by individual lab
branches, each of which owns the migration-equivalent for its own tables
so participants see one model added at a time rather than a domain dumped
on them up front.
"""

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Integer, String
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
