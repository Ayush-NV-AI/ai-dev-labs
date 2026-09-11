"""Tests for the reservation service, repository, and routes.

create_reservation and cancel_reservation are complete and tested here.
Waitlisting (see docs/LAB-4-1-SPEC.md) is not implemented on this branch.
"""

from datetime import UTC, datetime

import pytest

from src.db.repositories.reservations import SqlAlchemyReservationRepository
from src.services.errors import InvalidWindow, NotFound, ResourceUnavailable
from src.services.reservations import cancel_reservation, create_reservation

# --- repository: half-open overlap boundaries -------------------------------


async def test_list_overlapping_excludes_touching_end_boundary(
    db_session_instance, resource_factory, reservation_factory
):
    """A reservation ending exactly when another starts does not overlap."""
    resource = resource_factory()
    db_session_instance.add(resource)
    await db_session_instance.flush()

    existing = reservation_factory(
        resource.id,
        starts_at=datetime(2026, 1, 1, 9, 0, tzinfo=UTC),
        ends_at=datetime(2026, 1, 1, 10, 0, tzinfo=UTC),
    )
    db_session_instance.add(existing)
    await db_session_instance.flush()

    repo = SqlAlchemyReservationRepository(db_session_instance)
    overlapping = await repo.list_overlapping(
        resource.id,
        datetime(2026, 1, 1, 10, 0, tzinfo=UTC),
        datetime(2026, 1, 1, 11, 0, tzinfo=UTC),
    )

    assert overlapping == []


async def test_list_overlapping_excludes_touching_start_boundary(
    db_session_instance, resource_factory, reservation_factory
):
    """A reservation starting exactly when another ends does not overlap."""
    resource = resource_factory()
    db_session_instance.add(resource)
    await db_session_instance.flush()

    existing = reservation_factory(
        resource.id,
        starts_at=datetime(2026, 1, 1, 10, 0, tzinfo=UTC),
        ends_at=datetime(2026, 1, 1, 11, 0, tzinfo=UTC),
    )
    db_session_instance.add(existing)
    await db_session_instance.flush()

    repo = SqlAlchemyReservationRepository(db_session_instance)
    overlapping = await repo.list_overlapping(
        resource.id,
        datetime(2026, 1, 1, 9, 0, tzinfo=UTC),
        datetime(2026, 1, 1, 10, 0, tzinfo=UTC),
    )

    assert overlapping == []


async def test_list_overlapping_detects_genuine_overlap(
    db_session_instance, resource_factory, reservation_factory
):
    """A window that genuinely overlaps an existing one is detected."""
    resource = resource_factory()
    db_session_instance.add(resource)
    await db_session_instance.flush()

    existing = reservation_factory(
        resource.id,
        starts_at=datetime(2026, 1, 1, 9, 0, tzinfo=UTC),
        ends_at=datetime(2026, 1, 1, 11, 0, tzinfo=UTC),
    )
    db_session_instance.add(existing)
    await db_session_instance.flush()

    repo = SqlAlchemyReservationRepository(db_session_instance)
    overlapping = await repo.list_overlapping(
        resource.id,
        datetime(2026, 1, 1, 10, 0, tzinfo=UTC),
        datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
    )

    assert [r.id for r in overlapping] == [existing.id]


async def test_list_overlapping_excludes_cancelled(
    db_session_instance, resource_factory, reservation_factory
):
    """A cancelled reservation never counts as an overlap."""
    resource = resource_factory()
    db_session_instance.add(resource)
    await db_session_instance.flush()

    existing = reservation_factory(
        resource.id,
        starts_at=datetime(2026, 1, 1, 9, 0, tzinfo=UTC),
        ends_at=datetime(2026, 1, 1, 11, 0, tzinfo=UTC),
        cancelled_at=datetime(2026, 1, 1, 8, 0, tzinfo=UTC),
    )
    db_session_instance.add(existing)
    await db_session_instance.flush()

    repo = SqlAlchemyReservationRepository(db_session_instance)
    overlapping = await repo.list_overlapping(
        resource.id,
        datetime(2026, 1, 1, 9, 30, tzinfo=UTC),
        datetime(2026, 1, 1, 10, 30, tzinfo=UTC),
    )

    assert overlapping == []


# --- service -----------------------------------------------------------------


async def test_create_reservation_service_happy_path(db_session_instance, resource_factory):
    """create_reservation persists a reservation for a free window."""
    resource = resource_factory()
    db_session_instance.add(resource)
    await db_session_instance.flush()

    repo = SqlAlchemyReservationRepository(db_session_instance)
    starts_at = datetime(2026, 1, 1, 9, 0, tzinfo=UTC)
    ends_at = datetime(2026, 1, 1, 10, 0, tzinfo=UTC)

    reservation = await create_reservation(resource.id, starts_at, ends_at, "note", repo)

    assert reservation.id is not None
    assert reservation.resource_id == resource.id
    assert reservation.cancelled_at is None


async def test_create_reservation_service_invalid_window_raises(
    db_session_instance, resource_factory
):
    """ends_at not strictly after starts_at raises InvalidWindow."""
    resource = resource_factory()
    db_session_instance.add(resource)
    await db_session_instance.flush()

    repo = SqlAlchemyReservationRepository(db_session_instance)
    same_instant = datetime(2026, 1, 1, 9, 0, tzinfo=UTC)

    with pytest.raises(InvalidWindow):
        await create_reservation(resource.id, same_instant, same_instant, None, repo)


async def test_create_reservation_service_overlap_raises(
    db_session_instance, resource_factory, reservation_factory
):
    """An overlapping window raises ResourceUnavailable."""
    resource = resource_factory()
    db_session_instance.add(resource)
    await db_session_instance.flush()

    existing = reservation_factory(
        resource.id,
        starts_at=datetime(2026, 1, 1, 9, 0, tzinfo=UTC),
        ends_at=datetime(2026, 1, 1, 11, 0, tzinfo=UTC),
    )
    db_session_instance.add(existing)
    await db_session_instance.flush()

    repo = SqlAlchemyReservationRepository(db_session_instance)

    with pytest.raises(ResourceUnavailable):
        await create_reservation(
            resource.id,
            datetime(2026, 1, 1, 10, 0, tzinfo=UTC),
            datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
            None,
            repo,
        )


async def test_cancel_reservation_service_happy_path(
    db_session_instance, resource_factory, reservation_factory
):
    """cancel_reservation sets cancelled_at on an active reservation."""
    resource = resource_factory()
    db_session_instance.add(resource)
    await db_session_instance.flush()

    reservation = reservation_factory(resource.id)
    db_session_instance.add(reservation)
    await db_session_instance.flush()

    repo = SqlAlchemyReservationRepository(db_session_instance)
    cancelled = await cancel_reservation(reservation.id, repo)

    assert cancelled.cancelled_at is not None


async def test_cancel_reservation_service_missing_raises_not_found(db_session_instance):
    """cancel_reservation on a missing id raises NotFound."""
    repo = SqlAlchemyReservationRepository(db_session_instance)

    with pytest.raises(NotFound):
        await cancel_reservation(999999, repo)


async def test_cancel_reservation_service_already_cancelled_raises_not_found(
    db_session_instance, resource_factory, reservation_factory
):
    """Cancelling an already-cancelled reservation raises NotFound."""
    resource = resource_factory()
    db_session_instance.add(resource)
    await db_session_instance.flush()

    reservation = reservation_factory(
        resource.id, cancelled_at=datetime(2026, 1, 1, 8, 0, tzinfo=UTC)
    )
    db_session_instance.add(reservation)
    await db_session_instance.flush()

    repo = SqlAlchemyReservationRepository(db_session_instance)

    with pytest.raises(NotFound):
        await cancel_reservation(reservation.id, repo)


# --- routes --------------------------------------------------------------------


async def test_create_reservation_route_201(client, db_session_instance, resource_factory):
    """POST /reservations returns 201 and the created reservation."""
    resource = resource_factory()
    db_session_instance.add(resource)
    await db_session_instance.commit()
    await db_session_instance.refresh(resource)

    response = await client.post(
        "/reservations",
        json={
            "resource_id": resource.id,
            "starts_at": "2026-01-01T09:00:00Z",
            "ends_at": "2026-01-01T10:00:00Z",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["resource_id"] == resource.id
    assert body["cancelled_at"] is None


async def test_create_reservation_route_422_invalid_window(
    client, db_session_instance, resource_factory
):
    """POST /reservations with a non-positive window returns 422."""
    resource = resource_factory()
    db_session_instance.add(resource)
    await db_session_instance.commit()
    await db_session_instance.refresh(resource)

    response = await client.post(
        "/reservations",
        json={
            "resource_id": resource.id,
            "starts_at": "2026-01-01T09:00:00Z",
            "ends_at": "2026-01-01T09:00:00Z",
        },
    )

    assert response.status_code == 422


async def test_create_reservation_route_overlap_returns_exact_409_envelope(
    client, db_session_instance, resource_factory
):
    """POST /reservations on an overlapping window returns the EXACT 409 envelope.

    This assertion is deliberately strict. When adding waitlisting, the
    non-waitlist path (``waitlist`` omitted or ``false``) MUST still
    return this exact body unchanged -- only the waitlist=true path gets
    new behaviour (a 202 with the waitlist entry). If this test is
    failing, the fix is to preserve this response, not to loosen the
    assertion.
    """
    resource = resource_factory()
    db_session_instance.add(resource)
    await db_session_instance.commit()
    await db_session_instance.refresh(resource)

    first = await client.post(
        "/reservations",
        json={
            "resource_id": resource.id,
            "starts_at": "2026-01-01T09:00:00Z",
            "ends_at": "2026-01-01T11:00:00Z",
        },
    )
    assert first.status_code == 201

    response = await client.post(
        "/reservations",
        json={
            "resource_id": resource.id,
            "starts_at": "2026-01-01T10:00:00Z",
            "ends_at": "2026-01-01T12:00:00Z",
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "error": {
            "code": "resource_unavailable",
            "message": f"resource {resource.id} is unavailable for the requested window",
            "details": None,
        }
    }


async def test_cancel_reservation_route_200(client, db_session_instance, resource_factory):
    """DELETE /reservations/{id} cancels an active reservation."""
    resource = resource_factory()
    db_session_instance.add(resource)
    await db_session_instance.commit()
    await db_session_instance.refresh(resource)

    create_response = await client.post(
        "/reservations",
        json={
            "resource_id": resource.id,
            "starts_at": "2026-01-01T09:00:00Z",
            "ends_at": "2026-01-01T10:00:00Z",
        },
    )
    reservation_id = create_response.json()["id"]

    response = await client.delete(f"/reservations/{reservation_id}")

    assert response.status_code == 200
    assert response.json()["cancelled_at"] is not None


async def test_cancel_reservation_route_404_envelope(client):
    """DELETE /reservations/{id} for a missing id returns the standard envelope."""
    response = await client.delete("/reservations/999999")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
