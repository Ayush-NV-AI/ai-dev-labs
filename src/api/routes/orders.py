"""Order routes.

Full CRUD, following the same pattern as
:mod:`src.api.routes.resources`: dependency-injected service, one service
call per route, domain exceptions left to propagate to the handlers in
:mod:`src.api.errors`, responses shaped by ``response_model``.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas import OrderCreate, OrderRead
from src.db.session import get_session
from src.services.customers import SqlAlchemyCustomerRepository
from src.services.orders import OrderLineInput, OrderService, SqlAlchemyOrderRepository

router = APIRouter(prefix="/orders", tags=["orders"])


def get_order_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> OrderService:
    """Build an :class:`OrderService` for the current request.

    Args:
        session: Request-scoped database session, injected by FastAPI.

    Returns:
        An :class:`OrderService` backed by the SQLAlchemy repositories.
    """
    return OrderService(
        SqlAlchemyOrderRepository(session),
        SqlAlchemyCustomerRepository(session),
    )


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: OrderCreate,
    service: Annotated[OrderService, Depends(get_order_service)],
) -> OrderRead:
    """Create a new order.

    Args:
        payload: The requested customer and line items.
        service: Injected :class:`OrderService`.

    Returns:
        The newly created order.

    Raises:
        src.services.errors.NotFound: If the customer does not exist.
            Mapped to a 404 by the registered exception handler.
    """
    lines = [
        OrderLineInput(
            resource_id=line.resource_id,
            quantity=line.quantity,
            unit_price=line.unit_price,
        )
        for line in payload.lines
    ]
    order = await service.create(payload.customer_id, lines)
    return OrderRead.model_validate(order)


@router.get("", response_model=list[OrderRead])
async def list_orders_for_customer(
    customer_id: int,
    service: Annotated[OrderService, Depends(get_order_service)],
) -> list[OrderRead]:
    """List every order placed by one customer.

    Args:
        customer_id: The customer whose orders to list. Required.
        service: Injected :class:`OrderService`.

    Returns:
        That customer's orders, ordered by ascending id.

    Raises:
        src.services.errors.NotFound: If the customer does not exist.
            Mapped to a 404 by the registered exception handler.
    """
    orders = await service.list_for_customer(customer_id)
    return [OrderRead.model_validate(o) for o in orders]


@router.get("/{order_id}", response_model=OrderRead)
async def get_order(
    order_id: int,
    service: Annotated[OrderService, Depends(get_order_service)],
) -> OrderRead:
    """Fetch a single order by id.

    Args:
        order_id: Primary key of the order to fetch.
        service: Injected :class:`OrderService`.

    Returns:
        The matching order.

    Raises:
        src.services.errors.NotFound: If no order with that id exists.
            Mapped to a 404 by the registered exception handler.
    """
    order = await service.get_order(order_id)
    return OrderRead.model_validate(order)


@router.delete("/{order_id}", response_model=OrderRead)
async def cancel_order(
    order_id: int,
    service: Annotated[OrderService, Depends(get_order_service)],
) -> OrderRead:
    """Cancel an order.

    Args:
        order_id: Primary key of the order to cancel.
        service: Injected :class:`OrderService`.

    Returns:
        The order, with ``status`` set to ``"cancelled"``.

    Raises:
        src.services.errors.NotFound: If no order with that id exists.
            Mapped to a 404 by the registered exception handler.
    """
    order = await service.cancel(order_id)
    return OrderRead.model_validate(order)
