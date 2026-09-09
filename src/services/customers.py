"""Customer service and its default repository implementation."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import VALID_CUSTOMER_TIERS, Customer
from src.services.errors import NotFound
from src.services.ports import CustomerRepository


class SqlAlchemyCustomerRepository:
    """Default :class:`CustomerRepository` backed by SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        """Store the session used for all queries.

        Args:
            session: An open async SQLAlchemy session.
        """
        self._session = session

    async def get(self, customer_id: int) -> Customer | None:
        """Fetch a single customer by id.

        Args:
            customer_id: Primary key of the customer to fetch.

        Returns:
            The matching :class:`Customer`, or ``None`` if it does not
            exist.
        """
        return await self._session.get(Customer, customer_id)

    async def list_all(self) -> list[Customer]:
        """Fetch every customer, ordered by id.

        Returns:
            All customers, ordered by ascending id.
        """
        result = await self._session.execute(select(Customer).order_by(Customer.id))
        return list(result.scalars().all())


class CustomerService:
    """Application service for reading customers and resolving pricing tier.

    Depends on the :class:`~src.services.ports.CustomerRepository`
    protocol so callers (and tests) can supply any implementation.
    """

    def __init__(self, repository: CustomerRepository) -> None:
        """Store the repository used to satisfy every method below.

        Args:
            repository: Any object satisfying
                :class:`~src.services.ports.CustomerRepository`.
        """
        self._repository = repository

    async def get_customer(self, customer_id: int) -> Customer:
        """Fetch a single customer, raising if it does not exist.

        Args:
            customer_id: Primary key of the customer to fetch.

        Returns:
            The matching :class:`Customer`.

        Raises:
            NotFound: If no customer with that id exists.
        """
        customer = await self._repository.get(customer_id)
        if customer is None:
            raise NotFound(f"customer {customer_id} not found")
        return customer

    async def list_customers(self) -> list[Customer]:
        """Fetch every customer.

        Returns:
            All customers, ordered by ascending id.
        """
        return await self._repository.list_all()

    def resolve_tier(self, customer: Customer) -> str:
        """Resolve the effective pricing tier for a customer.

        The stored ``tier`` column is free text rather than a database
        enum, so it can drift out of sync with the set of tiers the
        pricing logic actually understands (e.g. after a tier is
        retired). This resolves that drift at read time rather than
        rejecting the write: any value outside
        :data:`~src.db.models.VALID_CUSTOMER_TIERS` falls back to
        ``"standard"``, the safest (least-discounted) tier.

        Args:
            customer: The customer whose tier to resolve.

        Returns:
            One of :data:`~src.db.models.VALID_CUSTOMER_TIERS`.
        """
        if customer.tier in VALID_CUSTOMER_TIERS:
            return customer.tier
        return "standard"
