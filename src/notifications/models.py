from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models import Base


def _now() -> datetime:
    return datetime.now(UTC)


class NotificationStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class NotificationTemplate:
    def __init__(self, key: str, channel: str, subject: str, body: str) -> None:
        self.key = key
        self.channel = channel
        self.subject = subject
        self.body = body


class SendRecord(Base):
    __tablename__ = "notification_send_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_key: Mapped[str] = mapped_column(String(100), nullable=False)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)
    recipient: Mapped[str] = mapped_column(String(320), nullable=False)
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=NotificationStatus.PENDING.value
    )
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
