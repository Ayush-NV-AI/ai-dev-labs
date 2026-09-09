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
