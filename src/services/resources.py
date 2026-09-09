"""Resource service and its default repository implementation.

This module is the reference pattern for a "read a thing, or raise
NotFound" service: a thin repository backed by SQLAlchemy, and a service
that depends on the :class:`~src.services.ports.ResourceRepository`
protocol rather than the concrete implementation, so tests can substitute
a fake.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Resource
from src.services.errors import NotFound
from src.services.ports import ResourceRepository


class SqlAlchemyResourceRepository:
    """Default :class:`ResourceRepository` backed by SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        """Store the session used for all queries.

        Args:
            session: An open async SQLAlchemy session.
        """
        self._session = session

    async def get(self, resource_id: int) -> Resource | None:
        """Fetch a single resource by id.

        Args:
            resource_id: Primary key of the resource to fetch.

        Returns:
            The matching :class:`Resource`, or ``None`` if it does not
            exist.
        """
        return await self._session.get(Resource, resource_id)

    async def list_all(self) -> list[Resource]:
        """Fetch every resource, ordered by id.

        Returns:
            All resources, ordered by ascending id.
        """
        result = await self._session.execute(select(Resource).order_by(Resource.id))
        return list(result.scalars().all())


class ResourceService:
    """Application service for reading resources.

    Depends on the :class:`~src.services.ports.ResourceRepository`
    protocol so callers (and tests) can supply any implementation.
    """

    def __init__(self, repository: ResourceRepository) -> None:
        """Store the repository used to satisfy every method below.

        Args:
            repository: Any object satisfying
                :class:`~src.services.ports.ResourceRepository`.
        """
        self._repository = repository

    async def get_resource(self, resource_id: int) -> Resource:
        """Fetch a single resource, raising if it does not exist.

        Args:
            resource_id: Primary key of the resource to fetch.

        Returns:
            The matching :class:`Resource`.

        Raises:
            NotFound: If no resource with that id exists.
        """
        resource = await self._repository.get(resource_id)
        if resource is None:
            raise NotFound(f"resource {resource_id} not found")
        return resource

    async def list_resources(self) -> list[Resource]:
        """Fetch every resource.

        Returns:
            All resources, ordered by ascending id.
        """
        return await self._repository.list_all()
