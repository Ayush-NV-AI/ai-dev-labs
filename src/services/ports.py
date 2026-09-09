"""Repository ports.

These ``Protocol`` classes describe the persistence contract each service
depends on, without committing to a concrete implementation. Services take
a repository as a constructor or function argument typed against the
protocol; tests can then supply an in-memory fake without touching the
database.
"""

from typing import Protocol

from src.db.models import Resource


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
