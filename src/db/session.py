"""Async database engine and session factory.

Uses SQLite via ``aiosqlite`` by default so the service and its tests run
with no external dependencies. The connection string lives in
:mod:`src.config` so a deployment can point at Postgres or another engine
without touching this module.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.config import get_settings


def make_engine(database_url: str | None = None) -> AsyncEngine:
    """Create a new async SQLAlchemy engine.

    Args:
        database_url: Optional override of the configured connection
            string. Primarily used by tests to point at an in-memory
            database.

    Returns:
        A configured :class:`~sqlalchemy.ext.asyncio.AsyncEngine`.
    """
    url = database_url or get_settings().database_url
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_async_engine(url, connect_args=connect_args)


def make_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Build a session factory bound to the given engine.

    Args:
        engine: The engine sessions should be bound to.

    Returns:
        An ``async_sessionmaker`` producing :class:`AsyncSession` objects.
    """
    return async_sessionmaker(bind=engine, expire_on_commit=False)


_engine = make_engine()
_session_factory = make_session_factory(_engine)


async def get_session() -> AsyncGenerator[AsyncSession]:
    """FastAPI dependency yielding a request-scoped database session.

    Yields:
        An open :class:`AsyncSession` that is closed automatically when
        the request finishes.
    """
    async with _session_factory() as session:
        yield session


async def init_models() -> None:
    """Create every registered table against the module-level engine.

    A real deployment against a persistent database would use proper
    migrations instead; this keeps the zero-setup SQLite default working
    out of the box for participants and in tests.
    """
    from src.db.models import Base

    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
