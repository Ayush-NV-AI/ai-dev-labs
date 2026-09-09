"""Resource routes.

This is the reference pattern for every route in this repo. Read it
before writing a new one. The pattern is:

1. A small dependency function builds the service from a request-scoped
   session (dependency injection — no route talks to the database or the
   ORM directly).
2. The route body calls exactly one service method and does nothing else.
3. Domain exceptions (:mod:`src.services.errors`) propagate unhandled;
   the handlers in :mod:`src.api.errors` turn them into the standard
   error envelope. Routes never construct error responses themselves.
4. Responses are shaped by a ``response_model`` (:mod:`src.api.schemas`),
   built with ``from_attributes`` so ORM instances convert directly.
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas import ResourceRead
from src.db.session import get_session
from src.services.resources import ResourceService, SqlAlchemyResourceRepository

router = APIRouter(prefix="/resources", tags=["resources"])


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


@router.get("", response_model=list[ResourceRead])
async def list_resources(
    service: Annotated[ResourceService, Depends(get_resource_service)],
) -> list[ResourceRead]:
    """List every resource.

    Args:
        service: Injected :class:`ResourceService`.

    Returns:
        Every resource, ordered by ascending id.
    """
    resources = await service.list_resources()
    return [ResourceRead.model_validate(r) for r in resources]


@router.get("/{resource_id}", response_model=ResourceRead)
async def get_resource(
    resource_id: int,
    service: Annotated[ResourceService, Depends(get_resource_service)],
) -> ResourceRead:
    """Fetch a single resource by id.

    Args:
        resource_id: Primary key of the resource to fetch.
        service: Injected :class:`ResourceService`.

    Returns:
        The matching resource.

    Raises:
        src.services.errors.NotFound: If no resource with that id exists.
            Mapped to a 404 by the registered exception handler.
    """
    resource = await service.get_resource(resource_id)
    return ResourceRead.model_validate(resource)
