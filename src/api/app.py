"""FastAPI application factory.

Only the health route lives here on ``main``. Feature routers are
included by later lab branches, each adding its own ``app.include_router``
call next to the ones already there.
"""

from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI

from src.api.errors import register_exception_handlers
from src.api.routes import reservations, resources
from src.config import get_settings
from src.db.session import init_models

health_router = APIRouter()


@health_router.get("/health")
async def health() -> dict:
    """Liveness check.

    Returns:
        A small JSON body confirming the service is up.
    """
    return {"status": "ok"}


@asynccontextmanager
async def _lifespan(_: FastAPI):
    """Create tables on startup for the local SQLite default.

    A production deployment pointed at a real database would use proper
    migrations instead; this keeps the zero-setup SQLite path working out
    of the box for participants.
    """
    await init_models()
    yield


def create_app() -> FastAPI:
    """Build and configure the FastAPI application.

    Returns:
        A fully configured :class:`FastAPI` instance, ready to serve.
    """
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=_lifespan)

    register_exception_handlers(app)

    app.include_router(health_router)
    app.include_router(resources.router)
    app.include_router(reservations.router)

    return app
