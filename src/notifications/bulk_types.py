"""Result type for a single bulk-send attempt.

Deliberately close in shape to :class:`~src.notifications.models.SendRecord`
-- see the PR description for why this doesn't just reuse that type.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class BulkSendResult:
    """One row of a bulk-send response.

    Attributes:
        id: The underlying send record's primary key.
        template_key: Which template was rendered for this recipient.
        channel: Channel this recipient was sent through.
        recipient: Destination address.
        subject: Rendered subject line.
        body: Rendered body.
        status: One of "pending", "sent", "failed".
        attempt_count: How many send attempts have been made.
        error: The error from the most recent failed attempt, if any.
        created_at: When the send record was created, in UTC.
        sent_at: When the send succeeded, in UTC, or None.
    """

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
