"""Application configuration.

Settings are loaded from environment variables (and an optional ``.env``
file for local development) via ``pydantic-settings``. Nothing secret is
ever hardcoded here — only defaults that are safe to commit, such as the
local SQLite connection string.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the booking service.

    Attributes:
        app_name: Human-readable service name, used in docs and logging.
        database_url: SQLAlchemy async connection string. Defaults to a
            local SQLite file so the service runs with zero external
            dependencies; point this elsewhere (e.g. Postgres) via the
            ``DATABASE_URL`` environment variable in other environments.
        debug: Enables verbose error responses. Must be ``False`` in any
            environment that is reachable by anyone other than the
            developer running it locally.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "ai-dev-labs booking service"
    database_url: str = "sqlite+aiosqlite:///./app.db"
    debug: bool = False


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide :class:`Settings` instance.

    Cached with ``lru_cache`` so settings are parsed from the environment
    once per process rather than on every call.

    Returns:
        The singleton :class:`Settings` instance.
    """
    return Settings()
