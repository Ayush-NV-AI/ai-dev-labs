"""Tests for bulk notification send."""

from src.notifications.bulk import BulkSendService
from src.notifications.channels.log import LogChannel
from src.notifications.dispatcher import SqlAlchemySendRecordRepository


async def test_send_bulk_sends_to_every_recipient(db_session_instance):
    """send_bulk() creates a sent record for every recipient in the batch."""
    repository = SqlAlchemySendRecordRepository(db_session_instance)
    log_channel = LogChannel()
    service = BulkSendService({"log": log_channel}, repository, db_session_instance)

    recipients = ["a@example.com", "b@example.com", "c@example.com"]
    results = await service.send_bulk(
        "reservation_reminder",
        recipients,
        "log",
        {"customer_name": "Ada", "resource_name": "Studio A", "starts_at": "10:00"},
    )

    assert [r.recipient for r in results] == recipients
    assert all(r.status == "sent" for r in results)
    assert len(log_channel.sent) == 3


async def test_send_bulk_via_api_round_trip(client):
    """POST /notifications/bulk sends to an explicit recipient list."""
    response = await client.post(
        "/notifications/bulk",
        json={
            "template_key": "reservation_reminder",
            "recipients": ["a@example.com", "b@example.com"],
            "channel": "log",
            "context": {"customer_name": "Ada", "resource_name": "Studio A", "starts_at": "10:00"},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert {r["recipient"] for r in body} == {"a@example.com", "b@example.com"}
    assert all(r["status"] == "sent" for r in body)


async def test_send_bulk_via_api_requires_recipients(client):
    """POST /notifications/bulk 422s when no recipients resolve at all."""
    response = await client.post(
        "/notifications/bulk",
        json={
            "template_key": "reservation_reminder",
            "context": {"customer_name": "Ada", "resource_name": "Studio A", "starts_at": "10:00"},
        },
    )

    assert response.status_code == 422


async def test_resolve_recipients_matches_past_sends(client, db_session_instance):
    """recipient_filter resolves recipients from prior send history."""
    await client.post(
        "/notifications",
        json={
            "template_key": "reservation_confirmed",
            "recipient": "match-me@example.com",
            "channel": "log",
            "context": {"customer_name": "Ada", "resource_name": "Studio A", "starts_at": "10:00"},
        },
    )

    response = await client.post(
        "/notifications/bulk",
        json={
            "template_key": "reservation_reminder",
            "recipient_filter": "match-me",
            "channel": "log",
            "context": {"customer_name": "Ada", "resource_name": "Studio A", "starts_at": "10:00"},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert [r["recipient"] for r in body] == ["match-me@example.com"]
