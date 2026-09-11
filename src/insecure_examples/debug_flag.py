"""Training material — deliberately insecure.

Seeded example for the debug-flag-enabled rule.
"""

from pydantic_settings import BaseSettings


class QuickSettings(BaseSettings):
    """A settings class copied from a tutorial and never revisited."""

    debug: bool = True


DEBUG = True
