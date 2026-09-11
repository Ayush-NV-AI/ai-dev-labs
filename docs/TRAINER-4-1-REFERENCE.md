# Trainer Reference — Lab 4.1 Waitlisting (worked implementation)

**Trainer-only.** This is a complete worked reference for comparing
against participant output. It is markdown, not code — no `.py` file on
this branch implements any of this, by design (see `docs/LAB-4-1-SPEC.md`,
"ABSENT" list). Do not distribute this file to participants before the
lab.

## 1. Model — `src/db/models.py` (addition)

```python
class WaitlistEntry(Base):
    """A request to be notified/promoted when a resource frees up.

    Attributes:
        id: Primary key.
        resource_id: Foreign key to the desired Resource.
        starts_at: Start of the desired window.
        ends_at: End of the desired window (exclusive).
        note: Optional free-text note.
        created_at: When the entry was created, in UTC. Promotion order
            is FIFO on this column.
        promoted_at: When the entry was promoted into a real
            reservation, in UTC, or None if still waiting.
        promoted_reservation_id: FK to the reservation created by
            promotion, or None until promoted.
    """

    __tablename__ = "waitlist_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    resource_id: Mapped[int] = mapped_column(ForeignKey("resources.id"), nullable=False, index=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    promoted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    promoted_reservation_id: Mapped[int | None] = mapped_column(
        ForeignKey("reservations.id"), nullable=True
    )
```

## 2. Port — `src/services/ports.py` (addition)

```python
class WaitlistRepository(Protocol):
    async def add(self, entry: WaitlistEntry) -> WaitlistEntry: ...

    async def list_active_for_resource(
        self, resource_id: int, now: datetime
    ) -> list[WaitlistEntry]:
        """Non-expired, non-promoted entries for a resource, oldest first."""
        ...

    async def mark_promoted(self, entry_id: int, reservation_id: int, promoted_at: datetime) -> WaitlistEntry: ...
```

`list_active_for_resource` excludes `promoted_at IS NOT NULL` and
`starts_at <= now` (expired), and orders by `created_at ASC` so the
caller gets FIFO for free.

## 3. Repository — `src/db/repositories/waitlist.py`

```python
class SqlAlchemyWaitlistRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, entry: WaitlistEntry) -> WaitlistEntry:
        self._session.add(entry)
        await self._session.flush()
        return entry

    async def list_active_for_resource(self, resource_id: int, now: datetime) -> list[WaitlistEntry]:
        result = await self._session.execute(
            select(WaitlistEntry)
            .where(
                WaitlistEntry.resource_id == resource_id,
                WaitlistEntry.promoted_at.is_(None),
                WaitlistEntry.starts_at > now,
            )
            .order_by(WaitlistEntry.created_at.asc())
        )
        return list(result.scalars().all())

    async def mark_promoted(self, entry_id: int, reservation_id: int, promoted_at: datetime) -> WaitlistEntry:
        entry = await self._session.get(WaitlistEntry, entry_id)
        entry.promoted_at = promoted_at
        entry.promoted_reservation_id = reservation_id
        await self._session.flush()
        return entry
```

Note `starts_at > now`, not `>=` — an entry whose window starts exactly
now is already unbookable and counts as expired, consistent with the
house half-open convention treating "now" as the boundary.

## 4. Service changes — `src/services/reservations.py`

```python
async def create_reservation(
    resource_id, starts_at, ends_at, note, repo, *,
    waitlist: bool = False,
    waitlist_repo: WaitlistRepository | None = None,
):
    if ends_at <= starts_at:
        raise InvalidWindow("ends_at must be strictly after starts_at")

    overlapping = await repo.list_overlapping(resource_id, starts_at, ends_at)
    if overlapping:
        if not waitlist:
            raise ResourceUnavailable(
                f"resource {resource_id} is unavailable for the requested window"
            )
        entry = WaitlistEntry(resource_id=resource_id, starts_at=starts_at, ends_at=ends_at, note=note)
        return await waitlist_repo.add(entry)  # caller (route) distinguishes the two return types

    return await repo.add(Reservation(resource_id=resource_id, starts_at=starts_at, ends_at=ends_at, note=note))


async def cancel_reservation(reservation_id, repo, *, waitlist_repo: WaitlistRepository | None = None):
    existing = await repo.get(reservation_id)
    if existing is None or existing.cancelled_at is not None:
        raise NotFound(f"reservation {reservation_id} not found")

    cancelled = await repo.cancel(reservation_id, datetime.now(UTC))

    if waitlist_repo is not None:
        await _promote_next_fitting_entry(cancelled.resource_id, repo, waitlist_repo)

    return cancelled


async def _promote_next_fitting_entry(resource_id, repo, waitlist_repo):
    now = datetime.now(UTC)
    for entry in await waitlist_repo.list_active_for_resource(resource_id, now):
        # Idempotency: an entry already promoted by a concurrent/retried
        # cancel is excluded by list_active_for_resource's WHERE clause,
        # so this loop can never promote the same entry twice.
        still_overlapping = await repo.list_overlapping(resource_id, entry.starts_at, entry.ends_at)
        if still_overlapping:
            continue  # no double-booking: skip, try the next-earliest entry
        reservation = await repo.add(
            Reservation(resource_id=resource_id, starts_at=entry.starts_at, ends_at=entry.ends_at, note=entry.note)
        )
        await waitlist_repo.mark_promoted(entry.id, reservation.id, now)
        return  # promote at most one entry per cancellation
```

**Idempotency argument:** promotion only ever reads entries where
`promoted_at IS NULL`. The moment an entry is promoted, `mark_promoted`
sets `promoted_at`, which excludes it from every future call to
`list_active_for_resource` — including a retried or duplicate cancel
request for the same reservation. A second cancel of an
already-cancelled reservation is separately rejected by the existing
`NotFound` check before promotion logic even runs.

**No-double-booking argument:** promotion re-checks `list_overlapping`
for the entry's exact window immediately before creating the
reservation, inside the same unit of work as the cancellation. If
anything else now occupies that window, the entry is skipped in favour
of the next-earliest one rather than forced through.

## 5. API — `src/api/routes/reservations.py` (changes)

- `ReservationCreate` gains `waitlist: bool = False`.
- The route branches on the service's return type: a `Reservation` is
  wrapped in `ReservationRead` with `201`; a `WaitlistEntry` is wrapped in
  a new `WaitlistEntryRead` with `202`.
- New route: `GET /waitlist?resource_id=` → `list[WaitlistEntryRead]`,
  backed by `list_active_for_resource`.

## 6. Tests

One test module per acceptance criterion in `docs/LAB-4-1-SPEC.md`'s
"Suggested acceptance tests" list, plus repository-level tests for
`list_active_for_resource`'s expiry boundary (`starts_at == now` is
expired) mirroring the existing overlap-boundary tests in
`tests/test_reservations.py`.

## What a plan review should catch

- The promotion re-check re-runs `list_overlapping`, which already
  excludes cancelled reservations and is half-open-correct — reusing it
  here rather than writing a second overlap query is the right call and
  worth calling out explicitly in a plan.
- `cancel_reservation`'s existing contract (raises `NotFound` for a
  missing or already-cancelled reservation, returns the cancelled
  reservation) is unchanged; promotion is an addition to its side effects,
  not a change to its return type or its existing raise conditions. A
  plan that proposes changing what `cancel_reservation` returns should be
  challenged.
- `notifications_stub.py` should not appear anywhere in the plan.
