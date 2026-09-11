from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class UpcomingBooking:
    id: int
    recipient: str
    starts_at: datetime
    template_key: str
    context: dict = field(default_factory=dict)


def reminders_due(
    bookings: list[UpcomingBooking], now: datetime, window: timedelta
) -> list[UpcomingBooking]:
    window_end = now + window
    return [b for b in bookings if now <= b.starts_at < window_end]
