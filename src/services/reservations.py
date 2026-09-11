"""Reservation service: create and cancel reservations.

Both functions are complete and tested on this branch. Waitlisting (an
opt-in alternative to a bare 409 on overlap, and promotion of the
earliest matching waitlist entry when a reservation is cancelled) is
described in docs/LAB-4-1-SPEC.md and is NOT implemented here — that is
the feature this lab branch exists to build.
"""

from datetime import UTC, datetime

from src.db.models import Reservation
from src.services.errors import InvalidWindow, NotFound, ResourceUnavailable
from src.services.ports import ReservationRepository


async def create_reservation(
    resource_id: int,
    starts_at: datetime,
    ends_at: datetime,
    note: str | None,
    repo: ReservationRepository,
) -> Reservation:
    """Create a reservation if the requested window is valid and free.

    Args:
        resource_id: Which resource to reserve.
        starts_at: Start of the requested window.
        ends_at: End of the requested window (exclusive; windows in this
            repo are HALF-OPEN).
        note: Optional free-text note to attach.
        repo: Injected :class:`~src.services.ports.ReservationRepository`.

    Returns:
        The newly created reservation.

    Raises:
        InvalidWindow: If ``ends_at`` is not strictly after ``starts_at``.
        ResourceUnavailable: If the window overlaps an existing active
            reservation for the same resource.
    """
    if ends_at <= starts_at:
        raise InvalidWindow("ends_at must be strictly after starts_at")

    overlapping = await repo.list_overlapping(resource_id, starts_at, ends_at)
    if overlapping:
        raise ResourceUnavailable(
            f"resource {resource_id} is unavailable for the requested window"
        )

    return await repo.add(
        Reservation(resource_id=resource_id, starts_at=starts_at, ends_at=ends_at, note=note)
    )


async def cancel_reservation(reservation_id: int, repo: ReservationRepository) -> Reservation:
    """Cancel a reservation.

    Args:
        reservation_id: Primary key of the reservation to cancel.
        repo: Injected :class:`~src.services.ports.ReservationRepository`.

    Returns:
        The now-cancelled reservation.

    Raises:
        NotFound: If no reservation with that id exists, or it is already
            cancelled.
    """
    existing = await repo.get(reservation_id)
    if existing is None or existing.cancelled_at is not None:
        raise NotFound(f"reservation {reservation_id} not found")

    return await repo.cancel(reservation_id, datetime.now(UTC))
