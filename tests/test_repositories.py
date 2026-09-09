"""Tests for src/db/repositories/reservations.py.

Pins the half-open overlap rule — including both touching-boundary cases
— before any service or route is built on top of it.
"""

from datetime import UTC, datetime

from src.db.repositories.reservations import SqlAlchemyReservationRepository


async def _seed_resource(db_session_instance, resource_factory):
    resource = resource_factory()
    db_session_instance.add(resource)
    await db_session_instance.commit()
    await db_session_instance.refresh(resource)
    return resource


async def test_add_and_get_round_trip(db_session_instance, resource_factory, reservation_factory):
    """A persisted reservation is fetchable by id afterwards."""
    resource = await _seed_resource(db_session_instance, resource_factory)
    repo = SqlAlchemyReservationRepository(db_session_instance)

    reservation = reservation_factory(
        resource_id=resource.id,
        starts_at=datetime(2026, 3, 2, 9, 0, tzinfo=UTC),
        ends_at=datetime(2026, 3, 2, 10, 0, tzinfo=UTC),
    )
    added = await repo.add(reservation)

    fetched = await repo.get(added.id)
    assert fetched is not None
    assert fetched.resource_id == resource.id


async def test_get_missing_returns_none(db_session_instance):
    """get() returns None rather than raising for a missing id."""
    repo = SqlAlchemyReservationRepository(db_session_instance)

    assert await repo.get(999) is None


async def test_list_overlapping_finds_a_true_overlap(
    db_session_instance, resource_factory, reservation_factory
):
    """A window that genuinely overlaps an existing one is found."""
    resource = await _seed_resource(db_session_instance, resource_factory)
    repo = SqlAlchemyReservationRepository(db_session_instance)
    await repo.add(
        reservation_factory(
            resource_id=resource.id,
            starts_at=datetime(2026, 3, 2, 9, 0, tzinfo=UTC),
            ends_at=datetime(2026, 3, 2, 11, 0, tzinfo=UTC),
        )
    )

    overlapping = await repo.list_overlapping(
        resource.id,
        datetime(2026, 3, 2, 10, 0, tzinfo=UTC),
        datetime(2026, 3, 2, 12, 0, tzinfo=UTC),
    )

    assert len(overlapping) == 1


async def test_list_overlapping_ignores_other_resources(
    db_session_instance, resource_factory, reservation_factory
):
    """An identical window on a different resource is not reported."""
    resource_a = await _seed_resource(db_session_instance, resource_factory)
    resource_b = await _seed_resource(db_session_instance, resource_factory)
    repo = SqlAlchemyReservationRepository(db_session_instance)
    await repo.add(
        reservation_factory(
            resource_id=resource_a.id,
            starts_at=datetime(2026, 3, 2, 9, 0, tzinfo=UTC),
            ends_at=datetime(2026, 3, 2, 11, 0, tzinfo=UTC),
        )
    )

    overlapping = await repo.list_overlapping(
        resource_b.id,
        datetime(2026, 3, 2, 9, 0, tzinfo=UTC),
        datetime(2026, 3, 2, 11, 0, tzinfo=UTC),
    )

    assert overlapping == []


async def test_list_overlapping_touching_start_boundary_is_not_overlapping(
    db_session_instance, resource_factory, reservation_factory
):
    """A candidate window starting exactly when an existing one ends does
    NOT overlap — the defining half-open boundary case."""
    resource = await _seed_resource(db_session_instance, resource_factory)
    repo = SqlAlchemyReservationRepository(db_session_instance)
    existing_end = datetime(2026, 3, 2, 10, 0, tzinfo=UTC)
    await repo.add(
        reservation_factory(
            resource_id=resource.id,
            starts_at=datetime(2026, 3, 2, 9, 0, tzinfo=UTC),
            ends_at=existing_end,
        )
    )

    # Candidate starts exactly at existing_end.
    overlapping = await repo.list_overlapping(
        resource.id,
        existing_end,
        datetime(2026, 3, 2, 11, 0, tzinfo=UTC),
    )

    assert overlapping == []


async def test_list_overlapping_touching_end_boundary_is_not_overlapping(
    db_session_instance, resource_factory, reservation_factory
):
    """A candidate window ending exactly when an existing one starts does
    NOT overlap — the mirror-image half-open boundary case."""
    resource = await _seed_resource(db_session_instance, resource_factory)
    repo = SqlAlchemyReservationRepository(db_session_instance)
    existing_start = datetime(2026, 3, 2, 10, 0, tzinfo=UTC)
    await repo.add(
        reservation_factory(
            resource_id=resource.id,
            starts_at=existing_start,
            ends_at=datetime(2026, 3, 2, 11, 0, tzinfo=UTC),
        )
    )

    # Candidate ends exactly at existing_start.
    overlapping = await repo.list_overlapping(
        resource.id,
        datetime(2026, 3, 2, 9, 0, tzinfo=UTC),
        existing_start,
    )

    assert overlapping == []
