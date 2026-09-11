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


class NotificationSendRequest(BaseModel):
    """Request body for sending a notification.

    Attributes:
        template_key: Which template to render, e.g.
            ``"reservation_confirmed"``.
        recipient: Destination address for the chosen channel.
        channel: Optional channel override, e.g. ``"log"``. Defaults to the
            template's own channel when omitted.
        context: Values substituted into the template.
    """

    template_key: str
    recipient: str
    channel: str | None = None
    context: dict = {}


class NotificationReplayRequest(BaseModel):
    """Request body for the debug-only notification replay route.

    Attributes:
        record_id: Id of the previously created send record to resend.
    """

    record_id: int


class SendRecordRead(BaseModel):
    """Response shape for a single notification send record.

    Attributes:
        id: Primary key.
        template_key: Which template was rendered for this send.
        channel: Channel the notification was sent through.
        recipient: Destination address.
        subject: Rendered subject line.
        body: Rendered body.
        status: One of ``"pending"``, ``"sent"``, ``"failed"``.
        attempt_count: How many send attempts have been made.
        error: The error from the most recent failed attempt, if any.
        created_at: When the send record was created, in UTC.
        sent_at: When the send succeeded, in UTC, or ``None``.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    template_key: str
    channel: str
    recipient: str
    subject: str
    body: str
    status: str
    attempt_count: int
    error: str | None
    created_at: datetime
    sent_at: datetime | None
