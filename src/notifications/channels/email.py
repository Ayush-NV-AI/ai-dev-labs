import asyncio
from typing import Protocol


class EmailProviderError(Exception):
    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code


class EmailProviderClient(Protocol):
    async def send(self, recipient: str, subject: str, body: str) -> None: ...


class TransientSendError(Exception):
    pass


class PermanentSendError(Exception):
    pass


def _classify(exc: Exception) -> Exception:
    if isinstance(exc, TimeoutError):
        return TransientSendError(str(exc))
    if isinstance(exc, EmailProviderError):
        if exc.status_code == 429 or exc.status_code >= 500:
            return TransientSendError(str(exc))
        return PermanentSendError(str(exc))
    return PermanentSendError(str(exc))


class EmailChannel:
    name = "email"

    def __init__(
        self,
        client: EmailProviderClient,
        max_attempts: int = 3,
        backoff_seconds: float = 0.01,
    ) -> None:
        self._client = client
        self._max_attempts = max_attempts
        self._backoff_seconds = backoff_seconds

    async def send(self, recipient: str, subject: str, body: str) -> None:
        attempt = 0
        while True:
            attempt += 1
            try:
                await self._client.send(recipient, subject, body)
                return
            except Exception as exc:
                classified = _classify(exc)
                if isinstance(classified, PermanentSendError) or attempt >= self._max_attempts:
                    raise classified from exc
                await asyncio.sleep(self._backoff_seconds * attempt)
