"""Training material — deliberately insecure.

Seeded example for the requests-tls-verification-disabled rule.
"""

import httpx
import requests


def fetch_provider_status(status_url: str) -> dict:
    """Check an upstream provider's status page, ignoring TLS errors."""
    response = requests.get(status_url, verify=False, timeout=5)
    return response.json()


async def notify_internal_webhook(payload: dict) -> None:
    """Post to an internal webhook over a self-signed endpoint."""
    async with httpx.AsyncClient(verify=False) as client:
        await client.post("https://internal.example/webhook", json=payload)
