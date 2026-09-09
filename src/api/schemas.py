"""Pydantic request/response schemas for the API layer.

``ResourceRead`` is inherited from ``main``. This branch adds the order
and customer schemas. Later lab branches add their own alongside the
feature that needs them.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ResourceRead(BaseModel):
    """Response shape for a single resource.

    Attributes:
        id: Primary key.
        name: Display name.
        kind: Resource category, e.g. ``"room"``.
        capacity: How many people or units the resource can serve at once.
        is_active: Whether the resource can currently be booked.
        created_at: When the resource was created, in UTC.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    kind: str
    capacity: int
    is_active: bool
    created_at: datetime


class OrderLineCreate(BaseModel):
    """Request shape for a single order line within :class:`OrderCreate`.

    Attributes:
        resource_id: The resource being ordered.
        quantity: Number of units ordered. Must be positive.
        unit_price: Price per unit. Must be positive.
    """

    resource_id: int
    quantity: int = Field(gt=0)
    unit_price: Decimal = Field(gt=0)


class OrderCreate(BaseModel):
    """Request shape for creating an order.

    Attributes:
        customer_id: The customer placing the order.
        lines: The order's line items. Must contain at least one line.
    """

    customer_id: int
    lines: list[OrderLineCreate] = Field(min_length=1)


class OrderLineRead(BaseModel):
    """Response shape for a single order line.

    Attributes:
        id: Primary key.
        resource_id: The resource ordered.
        quantity: Number of units ordered.
        unit_price: Price per unit, at full precision (unrounded).
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    resource_id: int
    quantity: int
    unit_price: Decimal


class OrderRead(BaseModel):
    """Response shape for a single order.

    Attributes:
        id: Primary key.
        customer_id: The customer who placed the order.
        status: One of ``"pending"`` or ``"cancelled"``.
        total_amount: The order's total, rounded to 2 decimal places.
        created_at: When the order was placed, in UTC.
        lines: The order's line items.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    status: str
    total_amount: Decimal
    created_at: datetime
    lines: list[OrderLineRead]


class CustomerRead(BaseModel):
    """Response shape for a single customer.

    Attributes:
        id: Primary key.
        name: Display name.
        email: Contact email.
        tier: The customer's *resolved* pricing tier — see
            ``CustomerService.resolve_tier`` — never the raw stored
            value.
        created_at: When the customer record was created, in UTC.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    tier: str
    created_at: datetime
