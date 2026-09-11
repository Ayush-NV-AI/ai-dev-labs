"""Repository ports.

These ``Protocol`` classes describe the persistence contract each service
depends on, without committing to a concrete implementation. Services take
a repository as a constructor or function argument typed against the
protocol; tests can then supply an in-memory fake without touching the
database.
"""

from datetime import datetime
from typing import Protocol

from src.db.models import Reservation, Resource


class ResourceRepository(Protocol):
    """Persistence contract for :class:`~src.db.models.Resource`."""

    async def get(self, resource_id: int) -> Resource | None:
        """Fetch a single resource by id.

        Args:
            resource_id: Primary key of the resource to fetch.

        Returns:
            The matching :class:`Resource`, or ``None`` if it does not
            exist.
        """
        ...

    async def list_all(self) -> list[Resource]:
        """Fetch every resource.

        Returns:
            All resources, in no particular guaranteed order.
        """
        ...


class ReservationRepository(Protocol):
    """Persistence contract for :class:`~src.db.models.Reservation`."""

    async def add(self, reservation: Reservation) -> Reservation:
        """Persist a new reservation.

        Args:
            reservation: The reservation to add.

        Returns:
            The same reservation, with its primary key populated.
        """
        ...

    async def get(self, reservation_id: int) -> Reservation | None:
        """Fetch a single reservation by id.

        Args:
            reservation_id: Primary key of the reservation to fetch.

        Returns:
            The matching :class:`Reservation`, or ``None`` if it does not
            exist.
        """
        ...

    async def list_overlapping(
        self, resource_id: int, starts_at: datetime, ends_at: datetime
    ) -> list[Reservation]:
        """List active reservations overlapping a candidate window.

        Args:
            resource_id: Which resource's reservations to check.
            starts_at: Start of the candidate window.
            ends_at: End of the candidate window (exclusive).

        Returns:
            Every active reservation overlapping the candidate window.
        """
        ...

    async def cancel(self, reservation_id: int, cancelled_at: datetime) -> Reservation:
        """Mark a reservation cancelled.

        Args:
            reservation_id: Primary key of the reservation to cancel.
            cancelled_at: Timestamp to record as the cancellation time.

        Returns:
            The now-cancelled reservation.
        """
        ...
