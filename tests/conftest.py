"""Shared pytest fixtures.

Every test gets an isolated in-memory SQLite database and an async HTTP
client wired to the FastAPI app via ``httpx.ASGITransport`` — no real
network socket, no shared state between tests.
"""

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.app import create_app
from src.db import session as db_session
from src.db.models import Base, Resource


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
            yield session

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
