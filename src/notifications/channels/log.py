class LogChannel:
    name = "log"

    def __init__(self) -> None:
        self.sent: list[tuple[str, str, str]] = []

    async def send(self, recipient: str, subject: str, body: str) -> None:
        self.sent.append((recipient, subject, body))
