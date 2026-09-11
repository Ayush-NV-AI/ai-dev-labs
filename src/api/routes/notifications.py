"""Notification routes.

Two always-on routes (send, get-by-id) plus one debug-only route
(``POST /notifications/_replay``) that is only registered on the app when
``settings.enable_notification_replay`` is true — see
:func:`src.api.app.create_app`. When the flag is off, the replay path
simply does not exist and FastAPI returns a plain 404 for it, the same as
any other unknown path.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas import NotificationReplayRequest, NotificationSendRequest, SendRecordRead
from src.db.session import get_session
from src.notifications.channels.email import EmailChannel, EmailProviderClient
from src.notifications.channels.log import LogChannel
from src.notifications.dispatcher import (
    ChannelNotConfigured,
    NotificationDispatcher,
    SqlAlchemySendRecordRepository,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])
debug_router = APIRouter(prefix="/notifications", tags=["notifications-debug"])


class _NullEmailProviderClient(EmailProviderClient):
    """Stand-in email provider used until a real one is configured.

    Never actually contacts an email provider; it only lets the channel
    and dispatch flow be exercised end to end in this training repo.
    """

    async def send(self, recipient: str, subject: str, body: str) -> None:
        """Pretend to send an email, always succeeding."""
        return None


def _build_channels() -> dict[str, EmailChannel | LogChannel]:
    """Build the channel registry used by both live routes below.

    Returns:
        A mapping of channel name to a configured channel instance.
    """
    return {
        "email": EmailChannel(_NullEmailProviderClient()),
        "log": LogChannel(),
    }


def get_dispatcher(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> NotificationDispatcher:
    """Build a :class:`NotificationDispatcher` for the current request.

    Args:
        session: Request-scoped database session, injected by FastAPI.

    Returns:
        A dispatcher wired to the SQLAlchemy send-record repository and
        the default channel registry.
    """
    repository = SqlAlchemySendRecordRepository(session)
    return NotificationDispatcher(_build_channels(), repository)


@router.post("", response_model=SendRecordRead, status_code=status.HTTP_201_CREATED)
async def send_notification(
    payload: NotificationSendRequest,
    dispatcher: Annotated[NotificationDispatcher, Depends(get_dispatcher)],
) -> SendRecordRead:
    """Render and send a notification, recording the outcome.

    Args:
        payload: Which template to render, for whom, and through which
            channel.
        dispatcher: Injected :class:`NotificationDispatcher`.

    Returns:
        The resulting send record.

    Raises:
        fastapi.HTTPException: 422 if the requested (or template-default)
            channel is not configured.
    """
    try:
        record = await dispatcher.dispatch(
            template_key=payload.template_key,
            recipient=payload.recipient,
            context=payload.context,
            channel_name=payload.channel,
        )
    except ChannelNotConfigured as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"channel not configured: {exc}",
        ) from exc
    return SendRecordRead.model_validate(record)


@router.get("/{record_id}", response_model=SendRecordRead)
async def get_notification(
    record_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SendRecordRead:
    """Fetch a single send record by id.

    Args:
        record_id: Primary key of the send record to fetch.
        session: Request-scoped database session, injected by FastAPI.

    Returns:
        The matching send record.

    Raises:
        fastapi.HTTPException: 404 if no send record with that id exists.
    """
    repository = SqlAlchemySendRecordRepository(session)
    record = await repository.get(record_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="send record not found")
    return SendRecordRead.model_validate(record)


@debug_router.post("/_replay", response_model=SendRecordRead)
async def replay_notification(
    payload: NotificationReplayRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SendRecordRead:
    """Re-send a previously created send record, unchanged, for debugging.

    Only registered on the app when
    ``settings.enable_notification_replay`` is true. Resends the exact
    subject/body already stored on the original record rather than
    re-rendering the template, so a replay reflects what was actually
    sent the first time even if the template has since changed.

    Args:
        payload: Identifies which send record to replay.
        session: Request-scoped database session, injected by FastAPI.

    Returns:
        The new send record created for the replay attempt.

    Raises:
        fastapi.HTTPException: 404 if the original send record does not
            exist, 422 if its channel is not configured, 502 if the
            replay send itself fails.
    """
    repository = SqlAlchemySendRecordRepository(session)
    original = await repository.get(payload.record_id)
    if original is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="send record not found")

    channel = _build_channels().get(original.channel)
    if channel is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"channel not configured: {original.channel}",
        )

    record = await repository.create(
        template_key=original.template_key,
        channel=original.channel,
        recipient=original.recipient,
        subject=original.subject,
        body=original.body,
    )
    try:
        await channel.send(original.recipient, original.subject, original.body)
    except Exception as exc:
        await repository.mark_failed(record.id, str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail="replay failed"
        ) from exc
    await repository.mark_sent(record.id)
    return SendRecordRead.model_validate(await repository.get(record.id))
