from typing import Protocol


class Channel(Protocol):
    name: str

    async def send(self, recipient: str, subject: str, body: str) -> None: ...
