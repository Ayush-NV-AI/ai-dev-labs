"""Repository ports.

These ``Protocol`` classes describe the persistence contract each service
depends on, without committing to a concrete implementation. Services take
a repository as a constructor or function argument typed against the
protocol; tests can then supply an in-memory fake without touching the
database.
"""

from typing import Protocol

from src.db.models import Customer, Order, Resource


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


class OrderRepository(Protocol):
    """Persistence contract for :class:`~src.db.models.Order`."""

    async def add(self, order: Order) -> Order:
        """Persist a new order, including its lines.

        Args:
            order: A fully populated, not-yet-persisted :class:`Order`.

        Returns:
            The same order, after being flushed so its generated id (and
            its lines' ids) are populated.
        """
        ...

    async def get(self, order_id: int) -> Order | None:
        """Fetch a single order by id, with its lines loaded.

        Args:
            order_id: Primary key of the order to fetch.

        Returns:
            The matching :class:`Order`, or ``None`` if it does not exist.
        """
        ...

    async def list_for_customer(self, customer_id: int) -> list[Order]:
        """Fetch every order placed by one customer, with lines loaded.

        Args:
            customer_id: Primary key of the customer whose orders to
                fetch.

        Returns:
            That customer's orders, ordered by ascending id.
        """
        ...


class CustomerRepository(Protocol):
    """Persistence contract for :class:`~src.db.models.Customer`."""

    async def get(self, customer_id: int) -> Customer | None:
        """Fetch a single customer by id.

        Args:
            customer_id: Primary key of the customer to fetch.

        Returns:
            The matching :class:`Customer`, or ``None`` if it does not
            exist.
        """
        ...

    async def list_all(self) -> list[Customer]:
        """Fetch every customer.

        Returns:
            All customers, in no particular guaranteed order.
        """
        ...
