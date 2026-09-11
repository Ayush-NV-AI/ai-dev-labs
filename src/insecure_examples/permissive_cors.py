"""Training material — deliberately insecure.

Seeded example for the permissive-cors rule.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def build_app_with_open_cors() -> FastAPI:
    """Build an app that allows any origin, to unblock a frontend quickly."""
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return app
