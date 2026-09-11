"""SQLAlchemy-backed reservation repository."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Reservation


class SqlAlchemyReservationRepository:
    """Default :class:`~src.services.ports.ReservationRepository` implementation."""

    def __init__(self, session: AsyncSession) -> None:
        """Store the session used for all queries.

        Args:
            session: An open async SQLAlchemy session.
        """
        self._session = session

    async def add(self, reservation: Reservation) -> Reservation:
        """Persist a new reservation.

        Args:
            reservation: The reservation to add. Its primary key is
                assigned by the database.

        Returns:
            The same reservation, with its primary key populated.
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
        """List active reservations overlapping a candidate window.

        Windows are HALF-OPEN: overlap iff
        ``existing.starts_at < ends_at AND existing.ends_at > starts_at``.
        A reservation ending exactly when the candidate window starts (or
        starting exactly when it ends) does NOT overlap. Cancelled
        reservations are excluded.

        Args:
            resource_id: Which resource's reservations to check.
            starts_at: Start of the candidate window.
            ends_at: End of the candidate window (exclusive).

        Returns:
            Every active reservation for that resource that overlaps the
            candidate window, in no particular guaranteed order.
        """
        result = await self._session.execute(
            select(Reservation).where(
                Reservation.resource_id == resource_id,
                Reservation.cancelled_at.is_(None),
                Reservation.starts_at < ends_at,
                Reservation.ends_at > starts_at,
            )
        )
        return list(result.scalars().all())

    async def cancel(self, reservation_id: int, cancelled_at: datetime) -> Reservation:
        """Mark a reservation cancelled.

        Args:
            reservation_id: Primary key of the reservation to cancel.
            cancelled_at: Timestamp to record as the cancellation time.

        Returns:
            The now-cancelled reservation.

        Raises:
            ValueError: If no reservation with that id exists. Callers
                that already checked existence (e.g. the service layer)
                will not hit this.
        """
        reservation = await self._session.get(Reservation, reservation_id)
        if reservation is None:
            raise ValueError(f"reservation {reservation_id} not found")
        reservation.cancelled_at = cancelled_at
        await self._session.flush()
        return reservation
