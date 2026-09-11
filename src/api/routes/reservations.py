"""Reservation routes.

Follows the reference pattern in :mod:`src.api.routes.resources`: a
dependency builds the repository from the request-scoped session, the
route body calls exactly one service function, and domain exceptions
propagate to the handlers in :mod:`src.api.errors`.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas import ReservationCreate, ReservationRead
from src.db.repositories.reservations import SqlAlchemyReservationRepository
from src.db.session import get_session
from src.services.ports import ReservationRepository
from src.services.reservations import cancel_reservation, create_reservation

router = APIRouter(prefix="/reservations", tags=["reservations"])


def get_reservation_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ReservationRepository:
    """Build a :class:`ReservationRepository` for the current request.

    Args:
        session: Request-scoped database session, injected by FastAPI.

    Returns:
        A :class:`~src.db.repositories.reservations.SqlAlchemyReservationRepository`.
    """
    return SqlAlchemyReservationRepository(session)


@router.post("", response_model=ReservationRead, status_code=status.HTTP_201_CREATED)
async def create_reservation_route(
    payload: ReservationCreate,
    repo: Annotated[ReservationRepository, Depends(get_reservation_repository)],
) -> ReservationRead:
    """Create a reservation.

    Args:
        payload: The requested resource, window, and optional note.
        repo: Injected :class:`~src.services.ports.ReservationRepository`.

    Returns:
        The newly created reservation.

    Raises:
        src.services.errors.InvalidWindow: Mapped to a 422.
        src.services.errors.ResourceUnavailable: Mapped to a 409 -- the
            window overlaps an existing active reservation.
    """
    reservation = await create_reservation(
        resource_id=payload.resource_id,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
        note=payload.note,
        repo=repo,
    )
    return ReservationRead.model_validate(reservation)


@router.delete("/{reservation_id}", response_model=ReservationRead)
async def cancel_reservation_route(
    reservation_id: int,
    repo: Annotated[ReservationRepository, Depends(get_reservation_repository)],
) -> ReservationRead:
    """Cancel a reservation.

    Args:
        reservation_id: Primary key of the reservation to cancel.
        repo: Injected :class:`~src.services.ports.ReservationRepository`.

    Returns:
        The now-cancelled reservation.

    Raises:
        src.services.errors.NotFound: Mapped to a 404 -- no such
            reservation, or it is already cancelled.
    """
    reservation = await cancel_reservation(reservation_id, repo)
    return ReservationRead.model_validate(reservation)
