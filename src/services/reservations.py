"""Reservation creation.

The implementation is the Lab 1.2 exercise: participants generate the body
of ``create_reservation`` from natural-language prompts against the
docstring below and ``docs/LAB-1-2.md``.
"""

from typing import TYPE_CHECKING

from src.db.models import Reservation
from src.services.ports import ReservationRepository

if TYPE_CHECKING:
    # Not implemented yet on this branch — participants add it to
    # src/api/schemas.py as part of the Lab 1.2 exercise. Guarded by
    # TYPE_CHECKING so this module imports cleanly before that happens.
    from src.api.schemas import ReservationCreate


async def create_reservation(
    payload: "ReservationCreate",
    repo: ReservationRepository,
) -> Reservation:
    """Create a reservation for a resource.

    Args:
        payload: The requested reservation window and metadata
            (``resource_id``, ``starts_at``, ``ends_at``, and an optional
            ``note``). ``ReservationCreate`` is defined in
            ``src.api.schemas`` by whoever implements this function —
            it does not exist yet on this branch.
        repo: Repository used to check for overlaps against existing
            reservations and to persist the new one.

    Returns:
        The persisted :class:`~src.db.models.Reservation`.

    Raises:
        InvalidWindow: If ``ends_at`` is not strictly after ``starts_at``,
            or if the window is longer than 8 hours.
        ResourceUnavailable: If the requested window overlaps an existing
            reservation for the same resource.
    """
    ...
