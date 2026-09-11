"""Tests for the notifications package and its API routes."""

from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from src.api.app import create_app
from src.config import get_settings
from src.db import session as db_session
from src.notifications.channels.email import (
    EmailChannel,
    EmailProviderError,
    PermanentSendError,
    TransientSendError,
)
from src.notifications.channels.log import LogChannel
from src.notifications.dispatcher import (
    ChannelNotConfigured,
    NotificationDispatcher,
    SqlAlchemySendRecordRepository,
)
from src.notifications.models import NotificationStatus, SendRecord
from src.notifications.scheduling import UpcomingBooking, reminders_due
from src.notifications.templates import TemplateNotFound, TemplateRenderError, get_template, render

# --- templates -------------------------------------------------------------


def test_render_happy_path():
    """render() substitutes context values into the template's subject/body."""
    subject, body = render(
        "reservation_confirmed",
        {"customer_name": "Ada", "resource_name": "Studio A", "starts_at": "2026-01-01T10:00"},
    )
    assert subject == "Your reservation is confirmed"
    assert "Ada" in body
    assert "Studio A" in body


def test_render_missing_context_key_raises():
    """render() raises TemplateRenderError when required context is missing."""
    with pytest.raises(TemplateRenderError):
        render("reservation_confirmed", {"customer_name": "Ada"})


def test_get_template_unknown_key_raises():
    """get_template() raises TemplateNotFound for an unregistered key."""
    with pytest.raises(TemplateNotFound):
        get_template("does_not_exist")


# --- channels ----------------------------------------------------------------


class _FlakyClient:
    """Fake email provider client that fails a fixed number of times."""

    def __init__(self, failures: list[Exception]) -> None:
        self._failures = list(failures)
        self.calls = 0

    async def send(self, recipient: str, subject: str, body: str) -> None:
        self.calls += 1
        if self._failures:
            raise self._failures.pop(0)


async def test_email_channel_retries_on_429_then_succeeds():
    """A 429 is retryable; the channel retries and eventually succeeds."""
    client = _FlakyClient([EmailProviderError(429, "rate limited")])
    channel = EmailChannel(client, max_attempts=3, backoff_seconds=0)

    await channel.send("a@example.com", "subj", "body")

    assert client.calls == 2


async def test_email_channel_retries_on_timeout():
    """A timeout is treated as retryable even though it is not a 4xx/5xx."""
    client = _FlakyClient([TimeoutError("slow")])
    channel = EmailChannel(client, max_attempts=3, backoff_seconds=0)

    await channel.send("a@example.com", "subj", "body")

    assert client.calls == 2


async def test_email_channel_does_not_retry_plain_4xx():
    """A non-429 4xx is not retried and surfaces as a PermanentSendError."""
    client = _FlakyClient([EmailProviderError(400, "bad request")])
    channel = EmailChannel(client, max_attempts=3, backoff_seconds=0)

    with pytest.raises(PermanentSendError):
        await channel.send("a@example.com", "subj", "body")

    assert client.calls == 1


async def test_email_channel_exhausts_retries_as_transient():
    """Repeated transient failures beyond max_attempts still raise."""
    client = _FlakyClient([EmailProviderError(500, "boom")] * 5)
    channel = EmailChannel(client, max_attempts=2, backoff_seconds=0)

    with pytest.raises(TransientSendError):
        await channel.send("a@example.com", "subj", "body")

    assert client.calls == 2


async def test_log_channel_records_sends():
    """LogChannel simply appends every send for local inspection."""
    channel = LogChannel()

    await channel.send("a@example.com", "subj", "body")

    assert channel.sent == [("a@example.com", "subj", "body")]


# --- dispatcher --------------------------------------------------------------


async def test_dispatcher_success_records_sent(db_session_instance):
    """A successful dispatch persists a SendRecord with status 'sent'."""
    repository = SqlAlchemySendRecordRepository(db_session_instance)
    dispatcher = NotificationDispatcher({"log": LogChannel()}, repository)

    record = await dispatcher.dispatch(
        template_key="reservation_confirmed",
        recipient="a@example.com",
        context={"customer_name": "Ada", "resource_name": "Studio A", "starts_at": "10:00"},
        channel_name="log",
    )

    assert record.status == NotificationStatus.SENT.value
    assert record.attempt_count == 1
    assert record.sent_at is not None


async def test_dispatcher_failure_records_failed_and_raises(db_session_instance):
    """A channel failure is persisted as 'failed' and re-raised."""

    class _AlwaysFails:
        name = "log"

        async def send(self, recipient: str, subject: str, body: str) -> None:
            raise RuntimeError("channel down")

    repository = SqlAlchemySendRecordRepository(db_session_instance)
    dispatcher = NotificationDispatcher({"log": _AlwaysFails()}, repository)

    with pytest.raises(RuntimeError):
        await dispatcher.dispatch(
            template_key="reservation_confirmed",
            recipient="a@example.com",
            context={"customer_name": "Ada", "resource_name": "Studio A", "starts_at": "10:00"},
            channel_name="log",
        )

    result = await db_session_instance.execute(
        select(SendRecord).where(SendRecord.recipient == "a@example.com")
    )
    persisted = result.scalar_one()
    assert persisted.status == NotificationStatus.FAILED.value
    assert persisted.error == "channel down"


async def test_dispatcher_unconfigured_channel_raises(db_session_instance):
    """Requesting a channel that isn't registered raises ChannelNotConfigured."""
    repository = SqlAlchemySendRecordRepository(db_session_instance)
    dispatcher = NotificationDispatcher({}, repository)

    with pytest.raises(ChannelNotConfigured):
        await dispatcher.dispatch(
            template_key="reservation_confirmed",
            recipient="a@example.com",
            context={"customer_name": "Ada", "resource_name": "Studio A", "starts_at": "10:00"},
            channel_name="log",
        )


# --- scheduling ----------------------------------------------------------------


def test_reminders_due_filters_to_window():
    """reminders_due() only returns bookings starting within [now, now+window)."""
    now = datetime(2026, 1, 1, 9, 0, tzinfo=UTC)
    window = timedelta(hours=1)
    bookings = [
        UpcomingBooking(1, "a@example.com", now - timedelta(minutes=1), "reservation_reminder"),
        UpcomingBooking(2, "b@example.com", now, "reservation_reminder"),
        UpcomingBooking(3, "c@example.com", now + timedelta(minutes=30), "reservation_reminder"),
        UpcomingBooking(4, "d@example.com", now + timedelta(hours=1), "reservation_reminder"),
    ]

    due = reminders_due(bookings, now, window)

    assert [b.id for b in due] == [2, 3]


# --- API routes ----------------------------------------------------------------


async def test_send_and_get_notification_round_trip(client):
    """POST /notifications then GET /notifications/{id} round-trips."""
    response = await client.post(
        "/notifications",
        json={
            "template_key": "reservation_confirmed",
            "recipient": "a@example.com",
            "channel": "log",
            "context": {"customer_name": "Ada", "resource_name": "Studio A", "starts_at": "10:00"},
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "sent"
    assert body["channel"] == "log"

    get_response = await client.get(f"/notifications/{body['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["recipient"] == "a@example.com"


async def test_get_notification_404(client):
    """GET /notifications/{id} for a missing id returns 404."""
    response = await client.get("/notifications/999999")
    assert response.status_code == 404


async def test_send_notification_unconfigured_channel_422(client):
    """POST /notifications with an unknown channel returns 422."""
    response = await client.post(
        "/notifications",
        json={
            "template_key": "reservation_confirmed",
            "recipient": "a@example.com",
            "channel": "carrier_pigeon",
            "context": {"customer_name": "Ada", "resource_name": "Studio A", "starts_at": "10:00"},
        },
    )
    assert response.status_code == 422


async def test_replay_route_absent_by_default(client):
    """POST /notifications/_replay does not exist when the flag is off.

    The path still matches ``GET /notifications/{record_id}`` (with
    ``record_id="_replay"``), so Starlette reports 405 Method Not Allowed
    rather than a plain 404 — either way, no replay route is reachable.
    """
    response = await client.post("/notifications/_replay", json={"record_id": 1})
    assert response.status_code == 405


async def _noop_init_models() -> None:
    return None


@pytest_asyncio.fixture
async def replay_enabled_client(session_factory, monkeypatch):
    """A client built with settings.enable_notification_replay = True."""
    monkeypatch.setenv("ENABLE_NOTIFICATION_REPLAY", "true")
    get_settings.cache_clear()

    async def _override_get_session():
        async with session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            else:
                await session.commit()

    monkeypatch.setattr("src.api.app.init_models", _noop_init_models)

    app = create_app()
    app.dependency_overrides[db_session.get_session] = _override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    get_settings.cache_clear()


async def test_replay_route_present_when_flag_enabled(replay_enabled_client):
    """POST /notifications/_replay resends a previous send record's content."""
    original = await replay_enabled_client.post(
        "/notifications",
        json={
            "template_key": "reservation_confirmed",
            "recipient": "a@example.com",
            "channel": "log",
            "context": {"customer_name": "Ada", "resource_name": "Studio A", "starts_at": "10:00"},
        },
    )
    assert original.status_code == 201
    record_id = original.json()["id"]

    replay = await replay_enabled_client.post(
        "/notifications/_replay", json={"record_id": record_id}
    )

    assert replay.status_code == 200
    body = replay.json()
    assert body["status"] == "sent"
    assert body["recipient"] == "a@example.com"
    assert body["id"] != record_id


async def test_replay_route_404_for_missing_record(replay_enabled_client):
    """POST /notifications/_replay 404s for a record id that doesn't exist."""
    response = await replay_enabled_client.post(
        "/notifications/_replay", json={"record_id": 999999}
    )
    assert response.status_code == 404
