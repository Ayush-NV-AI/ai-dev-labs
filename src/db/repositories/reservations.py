"""SQLAlchemy-backed :class:`~src.services.ports.ReservationRepository`."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Reservation


class SqlAlchemyReservationRepository:
    """Default ``ReservationRepository`` implementation, backed by
    SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        """Store the session used for all queries.

        Args:
            session: An open async SQLAlchemy session.
        """
        self._session = session

    async def add(self, reservation: Reservation) -> Reservation:
        """Persist a new reservation.

        Args:
            reservation: A fully populated, not-yet-persisted
                :class:`Reservation`.

        Returns:
            The same reservation, after being flushed so its generated
            id is populated.
        """
        self._session.add(reservation)
        await self._session.flush()
        return reservation

    async def get(self, reservation_id: int) -> Reservation | None:
        """Fetch a single reservation by id.

        Args:
            reservation_id: Primary key of the reservation to fetch.

        Returns:
            The matching :class:`Reservation`, or ``None`` if it does not
            exist.
        """
        return await self._session.get(Reservation, reservation_id)

    async def list_overlapping(
        self, resource_id: int, starts_at: datetime, ends_at: datetime
    ) -> list[Reservation]:
        """List existing reservations that overlap a candidate window.

        Half-open overlap test:
        ``starts_at < existing.ends_at AND ends_at > existing.starts_at``.
        A reservation touching the candidate window at a boundary does
        NOT count as overlapping.

        Args:
            resource_id: The resource to check for overlaps against.
            starts_at: Candidate window start, inclusive.
            ends_at: Candidate window end, exclusive.

        Returns:
            Every existing reservation for that resource whose window
            overlaps ``[starts_at, ends_at)``, ordered by ascending id.
        """
        result = await self._session.execute(
            select(Reservation)
            .where(
                Reservation.resource_id == resource_id,
                Reservation.starts_at < ends_at,
                Reservation.ends_at > starts_at,
            )
            .order_by(Reservation.id)
        )
        return list(result.scalars().all())
