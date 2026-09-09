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
            reservation: A fully populated, not-yet-persisted
                :class:`Reservation`.

        Returns:
            The same reservation, after being flushed so its generated
            id is populated.
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
        """List existing reservations that overlap a candidate window.

        Windows are half-open, ``[starts_at, ends_at)``: a reservation
        overlaps the candidate window iff
        ``starts_at < existing.ends_at AND ends_at > existing.starts_at``.
        A reservation that touches the candidate window at a boundary —
        ending exactly when it starts, or starting exactly when it ends —
        does NOT overlap.

        Args:
            resource_id: The resource to check for overlaps against.
            starts_at: Candidate window start, inclusive.
            ends_at: Candidate window end, exclusive.

        Returns:
            Every existing reservation for that resource whose window
            overlaps ``[starts_at, ends_at)``, in no particular
            guaranteed order.
        """
        ...
