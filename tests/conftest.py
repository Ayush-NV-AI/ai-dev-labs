"""Shared pytest fixtures.

Every test gets an isolated in-memory SQLite database and an async HTTP
client wired to the FastAPI app via ``httpx.ASGITransport`` — no real
network socket, no shared state between tests.
"""

from collections.abc import AsyncGenerator
from datetime import datetime

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.app import create_app
from src.db import session as db_session
from src.db.models import Base, Reservation, Resource


@pytest_asyncio.fixture
async def engine():
    """Provide a fresh in-memory SQLite engine per test."""
    test_engine = db_session.make_engine("sqlite+aiosqlite:///:memory:")
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield test_engine
    await test_engine.dispose()


@pytest_asyncio.fixture
async def session_factory(engine):
    """Provide a session factory bound to the per-test engine."""
    return db_session.make_session_factory(engine)


@pytest_asyncio.fixture
async def db_session_instance(session_factory) -> AsyncGenerator[AsyncSession]:
    """Provide a single open session for tests that touch the DB directly."""
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(session_factory, monkeypatch) -> AsyncGenerator[AsyncClient]:
    """Provide an async client for the FastAPI app, DB dependency overridden.

    The app's ``get_session`` dependency is swapped for one bound to the
    per-test in-memory engine, and the app's own startup ``init_models``
    call is skipped since the fixture above already created the schema.
    """

    async def _override_get_session() -> AsyncGenerator[AsyncSession]:
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


async def _noop_init_models() -> None:
    """Stand-in for ``init_models`` used when a test engine already has
    its schema created."""
    return None


@pytest.fixture
def resource_factory():
    """Return a factory for building :class:`Resource` instances in tests."""

    def _make(
        name: str = "Studio A",
        kind: str = "room",
        capacity: int = 4,
        is_active: bool = True,
    ) -> Resource:
        return Resource(name=name, kind=kind, capacity=capacity, is_active=is_active)

    return _make


@pytest.fixture
def reservation_factory():
    """Return a factory for building :class:`Reservation` instances in
    tests."""

    def _make(
        resource_id: int,
        starts_at: datetime,
        ends_at: datetime,
        note: str | None = None,
    ) -> Reservation:
        return Reservation(
            resource_id=resource_id,
            starts_at=starts_at,
            ends_at=ends_at,
            note=note,
        )

    return _make


class FakeReservationRepository:
    """In-memory :class:`~src.services.ports.ReservationRepository` for
    tests that don't need a real database.

    Implements the same half-open overlap rule as the SQLAlchemy-backed
    repository in ``src.db.repositories.reservations``, so a service
    tested against this fake sees identical overlap behaviour to
    production.
    """

    def __init__(self) -> None:
        """Start with an empty store and an id counter at 1."""
        self._items: dict[int, Reservation] = {}
        self._next_id = 1

    async def add(self, reservation: Reservation) -> Reservation:
        """Assign an id and store the reservation.

        Args:
            reservation: A not-yet-persisted :class:`Reservation`.

        Returns:
            The same reservation, with its ``id`` populated.
        """
        reservation.id = self._next_id
        self._next_id += 1
        self._items[reservation.id] = reservation
        return reservation

    async def get(self, reservation_id: int) -> Reservation | None:
        """Fetch a stored reservation by id.

        Args:
            reservation_id: Primary key of the reservation to fetch.

        Returns:
            The matching reservation, or ``None`` if it isn't stored.
        """
        return self._items.get(reservation_id)

    async def list_overlapping(
        self, resource_id: int, starts_at: datetime, ends_at: datetime
    ) -> list[Reservation]:
        """List stored reservations that overlap a candidate window.

        Args:
            resource_id: The resource to check for overlaps against.
            starts_at: Candidate window start, inclusive.
            ends_at: Candidate window end, exclusive.

        Returns:
            Every stored reservation for that resource whose window
            overlaps ``[starts_at, ends_at)``.
        """
        return [
            r
            for r in self._items.values()
            if r.resource_id == resource_id and r.starts_at < ends_at and r.ends_at > starts_at
        ]


@pytest.fixture
def fake_reservation_repo() -> FakeReservationRepository:
    """Provide a fresh :class:`FakeReservationRepository` per test."""
    return FakeReservationRepository()
