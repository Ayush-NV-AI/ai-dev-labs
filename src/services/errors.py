"""Domain-level exceptions.

Services raise these instead of HTTP-specific errors. The API layer
(:mod:`src.api.errors`) maps each one onto an HTTP status and the
service layer stays free of any knowledge of HTTP.
"""


class NotFound(Exception):
    """Raised when a requested entity does not exist."""


class InvalidWindow(Exception):
    """Raised when a time window is malformed (e.g. end not after start)."""


class ResourceUnavailable(Exception):
    """Raised when a resource cannot satisfy the request (e.g. a booking
    conflict)."""
