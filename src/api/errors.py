"""Error envelope and exception handlers.

Every error response from this API has the same shape:

    {"error": {"code": str, "message": str, "details": dict | None}}

Handlers registered here translate domain exceptions
(:mod:`src.services.errors`) into that envelope with the right HTTP
status. Routes never build error responses by hand — they raise a domain
exception and let these handlers do the translation, so the shape stays
consistent everywhere.
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from src.services.errors import InvalidWindow, NotFound, ResourceUnavailable


def _envelope(code: str, message: str, details: dict | None = None) -> dict:
    """Build the standard error envelope.

    Args:
        code: A short, machine-readable error code.
        message: A human-readable description of what went wrong.
        details: Optional structured extra context.

    Returns:
        A dict matching the ``{"error": {...}}`` envelope shape.
    """
    return {"error": {"code": code, "message": message, "details": details}}


def register_exception_handlers(app: FastAPI) -> None:
    """Register domain-exception handlers on the given app.

    Args:
        app: The FastAPI application to attach handlers to.
    """

    @app.exception_handler(NotFound)
    async def _not_found(_: Request, exc: NotFound) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=_envelope("not_found", str(exc)),
        )

    @app.exception_handler(InvalidWindow)
    async def _invalid_window(_: Request, exc: InvalidWindow) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_envelope("invalid_window", str(exc)),
        )

    @app.exception_handler(ResourceUnavailable)
    async def _resource_unavailable(_: Request, exc: ResourceUnavailable) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=_envelope("resource_unavailable", str(exc)),
        )
