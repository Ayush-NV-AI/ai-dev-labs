"""Training material — deliberately insecure.

Seeded example for the broad-except-pass rule.
"""


def best_effort_cache_write(cache, key: str, value: str) -> None:
    """Write to an optional cache, tolerating any failure silently."""
    try:
        cache.set(key, value)
    except Exception:
        pass


def best_effort_cleanup(path: str) -> None:
    """Remove a temp file, ignoring literally anything that goes wrong."""
    import os

    try:
        os.remove(path)
    except:
        pass
