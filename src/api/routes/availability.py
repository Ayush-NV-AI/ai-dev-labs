"""Resource availability route.

Follows the same dependency-injection pattern as
:mod:`src.api.routes.resources`: a small dependency builds what the route
needs from a request-scoped session, the route body calls exactly one
computation, and domain exceptions propagate to the handlers in
:mod:`src.api.errors`.
"""

from datetime import UTC, date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas import AvailabilitySlotRead
from src.db.models import Reservation
from src.db.session import get_session
from src.services.availability import free_slots
from src.services.resources import ResourceService, SqlAlchemyResourceRepository

router = APIRouter(prefix="/resources", tags=["availability"])


def get_resource_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ResourceService:
    """Build a :class:`ResourceService` for the current request.

    Args:
        session: Request-scoped database session, injected by FastAPI.

    Returns:
        A :class:`ResourceService` backed by the SQLAlchemy repository.
    """
    return ResourceService(SqlAlchemyResourceRepository(session))


@router.get("/{resource_id}/availability", response_model=list[AvailabilitySlotRead])
async def get_availability(
    resource_id: int,
    date: date,
    session: Annotated[AsyncSession, Depends(get_session)],
    resource_service: Annotated[ResourceService, Depends(get_resource_service)],
) -> list[AvailabilitySlotRead]:
    """List a resource's free windows for a single day.

    Args:
        resource_id: The resource to check.
        date: The day to check, as an ISO date (``?date=2026-03-02``).
        session: Request-scoped database session, injected by FastAPI.
        resource_service: Injected :class:`ResourceService`, used only to
            confirm the resource exists.

    Returns:
        The resource's free windows on that day, earliest first.

    Raises:
        src.services.errors.NotFound: If no resource with that id exists.
            Mapped to a 404 by the registered exception handler.
    """
    await resource_service.get_resource(resource_id)

    result = await session.execute(
        select(Reservation).where(Reservation.resource_id == resource_id)
    )
    reservations = list(result.scalars().all())

    day = datetime(date.year, date.month, date.day, tzinfo=UTC)
    slots = free_slots(resource_id, day, reservations)
    return [AvailabilitySlotRead(starts_at=start, ends_at=end) for start, end in slots]
