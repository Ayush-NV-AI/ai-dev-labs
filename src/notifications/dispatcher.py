from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.notifications import templates
from src.notifications.channels.base import Channel
from src.notifications.models import NotificationStatus, SendRecord


class ChannelNotConfigured(Exception):
    pass


class SendRecordNotFound(Exception):
    pass


class SqlAlchemySendRecordRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self, *, template_key: str, channel: str, recipient: str, subject: str, body: str
    ) -> SendRecord:
        record = SendRecord(
            template_key=template_key,
            channel=channel,
            recipient=recipient,
            subject=subject,
            body=body,
            status=NotificationStatus.PENDING.value,
            attempt_count=0,
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def get(self, record_id: int) -> SendRecord | None:
        return await self._session.get(SendRecord, record_id)

    async def mark_sent(self, record_id: int) -> None:
        record = await self._session.get(SendRecord, record_id)
        if record is None:
            raise SendRecordNotFound(record_id)
        record.status = NotificationStatus.SENT.value
        record.attempt_count += 1
        record.sent_at = datetime.now(UTC)

    async def mark_failed(self, record_id: int, error: str) -> None:
        record = await self._session.get(SendRecord, record_id)
        if record is None:
            raise SendRecordNotFound(record_id)
        record.status = NotificationStatus.FAILED.value
        record.attempt_count += 1
        record.error = error


class NotificationDispatcher:
    def __init__(
        self, channels: dict[str, Channel], repository: SqlAlchemySendRecordRepository
    ) -> None:
        self._channels = channels
        self._repository = repository

    async def dispatch(
        self,
        *,
        template_key: str,
        recipient: str,
        context: dict,
        channel_name: str | None = None,
    ) -> SendRecord:
        template = templates.get_template(template_key)
        resolved_channel_name = channel_name or template.channel
        channel = self._channels.get(resolved_channel_name)
        if channel is None:
            raise ChannelNotConfigured(resolved_channel_name)

        subject, body = templates.render(template_key, context)

        record = await self._repository.create(
            template_key=template_key,
            channel=resolved_channel_name,
            recipient=recipient,
            subject=subject,
            body=body,
        )

        try:
            await channel.send(recipient, subject, body)
        except Exception as exc:
            await self._repository.mark_failed(record.id, str(exc))
            raise
        await self._repository.mark_sent(record.id)
        return await self._repository.get(record.id)
