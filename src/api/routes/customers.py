"""Customer routes.

Read-only, following the same dependency-injection and response-shaping
pattern as :mod:`src.api.routes.resources`. The one difference: the
``tier`` field in the response is the *resolved* tier
(:meth:`~src.services.customers.CustomerService.resolve_tier`), not the
raw stored column, so a response never surfaces an unrecognised tier
value to a caller.
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas import CustomerRead
from src.db.session import get_session
from src.services.customers import CustomerService, SqlAlchemyCustomerRepository

router = APIRouter(prefix="/customers", tags=["customers"])


def get_customer_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CustomerService:
    """Build a :class:`CustomerService` for the current request.

    Args:
        session: Request-scoped database session, injected by FastAPI.

    Returns:
        A :class:`CustomerService` backed by the SQLAlchemy repository.
    """
    return CustomerService(SqlAlchemyCustomerRepository(session))


def _to_read_model(service: CustomerService, customer) -> CustomerRead:
    """Build a :class:`CustomerRead` with the resolved tier applied.

    Args:
        service: The service used to resolve the tier.
        customer: The ORM instance to convert.

    Returns:
        A :class:`CustomerRead` whose ``tier`` is the resolved value.
    """
    read_model = CustomerRead.model_validate(customer)
    return read_model.model_copy(update={"tier": service.resolve_tier(customer)})


@router.get("", response_model=list[CustomerRead])
async def list_customers(
    service: Annotated[CustomerService, Depends(get_customer_service)],
) -> list[CustomerRead]:
    """List every customer.

    Args:
        service: Injected :class:`CustomerService`.

    Returns:
        Every customer, ordered by ascending id, with tiers resolved.
    """
    customers = await service.list_customers()
    return [_to_read_model(service, c) for c in customers]


@router.get("/{customer_id}", response_model=CustomerRead)
async def get_customer(
    customer_id: int,
    service: Annotated[CustomerService, Depends(get_customer_service)],
) -> CustomerRead:
    """Fetch a single customer by id.

    Args:
        customer_id: Primary key of the customer to fetch.
        service: Injected :class:`CustomerService`.

    Returns:
        The matching customer, with its tier resolved.

    Raises:
        src.services.errors.NotFound: If no customer with that id exists.
            Mapped to a 404 by the registered exception handler.
    """
    customer = await service.get_customer(customer_id)
    return _to_read_model(service, customer)
