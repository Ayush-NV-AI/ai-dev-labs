"""Pydantic request/response schemas for the API layer.

Only ``ResourceRead`` exists on ``main``. Later lab branches add their own
schemas alongside the feature that needs them.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


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


class ReservationCreate(BaseModel):
    """Request body for creating a reservation.

    Attributes:
        resource_id: Which resource to reserve.
        starts_at: Start of the requested window.
        ends_at: End of the requested window (exclusive; windows in this
            repo are HALF-OPEN, see ``src/db/models.py``).
        note: Optional free-text note to attach.
    """

    resource_id: int
    starts_at: datetime
    ends_at: datetime
    note: str | None = None


class ReservationRead(BaseModel):
    """Response shape for a single reservation.

    Attributes:
        id: Primary key.
        resource_id: Which resource is reserved.
        starts_at: Start of the reservation window.
        ends_at: End of the reservation window (exclusive).
        note: Optional free-text note attached at creation.
        created_at: When the reservation was created, in UTC.
        cancelled_at: When the reservation was cancelled, in UTC, or
            ``None`` if it is still active.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    resource_id: int
    starts_at: datetime
    ends_at: datetime
    note: str | None
    created_at: datetime
    cancelled_at: datetime | None
