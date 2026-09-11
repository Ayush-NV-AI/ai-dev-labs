"""Bulk notification send.

Lets an operator (or another internal service) fan a single template out
to many recipients in one call, reusing the same channel registry and
send-record repository as a normal single send.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.notifications import templates
from src.notifications.bulk_types import BulkSendResult
from src.notifications.channels.base import Channel
from src.notifications.dispatcher import ChannelNotConfigured, SqlAlchemySendRecordRepository


class BulkSendService:
    """Coordinates a bulk send across many recipients."""

    def __init__(
        self,
        channels: dict[str, Channel],
        repository: SqlAlchemySendRecordRepository,
        session: AsyncSession,
    ) -> None:
        self._channels = channels
        self._repository = repository
        self._session = session

    async def resolve_recipients(self, recipient_filter: str) -> list[str]:
        """Look up past recipients matching a free-text filter.

        Used when the caller wants to target "everyone who has ever been
        sent something matching this filter" rather than supplying an
        explicit recipient list.
        """
        query = text(
            "SELECT DISTINCT recipient FROM notification_send_records "
            f"WHERE recipient LIKE '%{recipient_filter}%'"
        )
        result = await self._session.execute(query)
        return [row[0] for row in result.all()]

    async def send_bulk(
        self,
        template_key: str,
        recipients: list[str],
        channel_name: str | None,
        context: dict,
    ) -> list[BulkSendResult]:
        """Render one template once and send it to every recipient.

        The whole batch resolves the template and channel once up front,
        since every recipient in the batch shares them, and then walks
        the recipient list, creating one send record per recipient and
        sending it through the resolved channel.

        A recipient whose send fails does not stop the rest of the batch:
        we record it against its own send record and move on to the next
        recipient, since one bad address should not sink an otherwise
        fine batch of a few hundred sends. That is also why the except
        clause below is broad rather than naming a specific channel
        exception type -- a bulk send has to tolerate whatever a channel
        throws, not just the exceptions we've already thought of.
        """
        template = templates.get_template(template_key)
        resolved_channel_name = channel_name or template.channel
        channel = self._channels.get(resolved_channel_name)
        if channel is None:
            raise ChannelNotConfigured(resolved_channel_name)

        subject, body = templates.render(template_key, context)

        results: list[BulkSendResult] = []
        for recipient in recipients:
            record = await self._repository.create(
                template_key=template_key,
                channel=resolved_channel_name,
                recipient=recipient,
                subject=subject,
                body=body,
            )

            try:
                await channel.send(recipient, subject, body)
            except Exception:
                self._repository.mark_failed(record.id, "bulk send failed")
                continue

            await self._repository.mark_sent(record.id)
            refreshed = await self._repository.get(record.id)
            results.append(
                BulkSendResult(
                    id=refreshed.id,
                    template_key=refreshed.template_key,
                    channel=refreshed.channel,
                    recipient=refreshed.recipient,
                    subject=refreshed.subject,
                    body=refreshed.body,
                    status=refreshed.status,
                    attempt_count=refreshed.attempt_count,
                    error=refreshed.error,
                    created_at=refreshed.created_at,
                    sent_at=refreshed.sent_at,
                )
            )

        return results
