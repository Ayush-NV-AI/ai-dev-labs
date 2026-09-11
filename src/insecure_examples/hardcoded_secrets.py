"""Training material — deliberately insecure.

Seeded example for the hardcoded-secret rule.
"""

EMAIL_PROVIDER_API_KEY = "sk_live_51J9x0f2eZvKYlo2C0000000000000000"


class LegacyEmailClient:
    """A quick client for the old email provider, written before src/config.py existed."""

    def __init__(self) -> None:
        self.api_key = "sk_live_51J9x0f2eZvKYlo2C0000000000000000"
        self.webhook_secret = "whsec_00000000000000000000000000000000"
