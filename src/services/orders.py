"""Order service and its default repository implementation."""

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.models import Order, OrderLine
from src.reporting.formatters import format_money
from src.services.errors import NotFound
from src.services.ports import CustomerRepository, OrderRepository


@dataclass(frozen=True, slots=True)
class OrderLineInput:
    """One requested line item, before it becomes a persisted
    :class:`~src.db.models.OrderLine`.

    Attributes:
        resource_id: The resource being ordered.
        quantity: Number of units ordered. Must be positive.
        unit_price: Price per unit. Must be positive. Carried at full
            precision — not rounded here.
    """

    resource_id: int
    quantity: int
    unit_price: Decimal


class SqlAlchemyOrderRepository:
    """Default :class:`OrderRepository` backed by SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        """Store the session used for all queries.

        Args:
            session: An open async SQLAlchemy session.
        """
        self._session = session

    async def add(self, order: Order) -> Order:
        """Persist a new order, including its lines.

        Args:
            order: A fully populated, not-yet-persisted :class:`Order`.

        Returns:
            The same order, after being flushed so its generated id (and
            its lines' ids) are populated.
        """
        self._session.add(order)
        await self._session.flush()
        await self._session.refresh(order, attribute_names=["lines"])
        return order

    async def get(self, order_id: int) -> Order | None:
        """Fetch a single order by id, with its lines loaded.

        Args:
            order_id: Primary key of the order to fetch.

        Returns:
            The matching :class:`Order`, or ``None`` if it does not exist.
        """
        result = await self._session.execute(
            select(Order).where(Order.id == order_id).options(selectinload(Order.lines))
        )
        return result.scalar_one_or_none()

    async def list_for_customer(self, customer_id: int) -> list[Order]:
        """Fetch every order placed by one customer, with lines loaded.

        Args:
            customer_id: Primary key of the customer whose orders to
                fetch.

        Returns:
            That customer's orders, ordered by ascending id.
        """
        result = await self._session.execute(
            select(Order)
            .where(Order.customer_id == customer_id)
            .options(selectinload(Order.lines))
            .order_by(Order.id)
        )
        return list(result.scalars().all())


class OrderService:
    """Application service for creating, cancelling and listing orders.

    Depends on the :class:`~src.services.ports.OrderRepository` and
    :class:`~src.services.ports.CustomerRepository` protocols so callers
    (and tests) can supply any implementation.
    """

    def __init__(
        self,
        order_repository: OrderRepository,
        customer_repository: CustomerRepository,
    ) -> None:
        """Store the repositories used to satisfy every method below.

        Args:
            order_repository: Any object satisfying
                :class:`~src.services.ports.OrderRepository`.
            customer_repository: Any object satisfying
                :class:`~src.services.ports.CustomerRepository`, used to
                confirm the customer placing an order exists.
        """
        self._orders = order_repository
        self._customers = customer_repository

    async def create(self, customer_id: int, lines: list[OrderLineInput]) -> Order:
        """Create a new order for a customer.

        The order's total is the sum of every line's
        ``unit_price * quantity``, rounded exactly once via
        :func:`~src.reporting.formatters.format_money` before it is
        stored.

        Args:
            customer_id: The customer placing the order.
            lines: The order's line items. Must be non-empty; enforced by
                the API schema layer, not re-checked here.

        Returns:
            The persisted :class:`Order`, with its lines loaded.

        Raises:
            NotFound: If no customer with that id exists.
        """
        customer = await self._customers.get(customer_id)
        if customer is None:
            raise NotFound(f"customer {customer_id} not found")

        raw_total = sum((line.unit_price * line.quantity for line in lines), Decimal("0"))
        order = Order(
            customer_id=customer_id,
            status="pending",
            total_amount=format_money(raw_total),
        )
        order.lines = [
            OrderLine(
                resource_id=line.resource_id,
                quantity=line.quantity,
                unit_price=line.unit_price,
            )
            for line in lines
        ]
        return await self._orders.add(order)

    async def get_order(self, order_id: int) -> Order:
        """Fetch a single order, raising if it does not exist.

        Args:
            order_id: Primary key of the order to fetch.

        Returns:
            The matching :class:`Order`, with its lines loaded.

        Raises:
            NotFound: If no order with that id exists.
        """
        order = await self._orders.get(order_id)
        if order is None:
            raise NotFound(f"order {order_id} not found")
        return order

    async def cancel(self, order_id: int) -> Order:
        """Cancel an order.

        Idempotent: cancelling an already-cancelled order simply returns
        it unchanged rather than raising.

        Args:
            order_id: Primary key of the order to cancel.

        Returns:
            The order, with ``status`` set to ``"cancelled"``.

        Raises:
            NotFound: If no order with that id exists.
        """
        order = await self._orders.get(order_id)
        if order is None:
            raise NotFound(f"order {order_id} not found")
        order.status = "cancelled"
        return order

    async def list_for_customer(self, customer_id: int) -> list[Order]:
        """List every order placed by one customer.

        Args:
            customer_id: Primary key of the customer whose orders to list.

        Returns:
            That customer's orders, ordered by ascending id, with lines
            loaded.

        Raises:
            NotFound: If no customer with that id exists.
        """
        customer = await self._customers.get(customer_id)
        if customer is None:
            raise NotFound(f"customer {customer_id} not found")
        return await self._orders.list_for_customer(customer_id)
