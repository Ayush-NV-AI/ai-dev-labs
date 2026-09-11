# Lab 4.1 — Feature Spec: Reservation Waitlisting

## Behaviour

Today, a reservation request that overlaps an existing active booking is
rejected outright with a 409. This feature lets a caller opt into a
waitlist instead of a bare rejection: when the overlapping booking is
later cancelled, the earliest-created matching waitlist entry is
automatically promoted into a real reservation.

Nothing about the existing, working `create_reservation` /
`cancel_reservation` behaviour changes for a caller who does not opt in.

## Acceptance criteria

1. **Opt-in on create.** `POST /reservations` accepts a new optional
   `waitlist: bool` field, defaulting to `false`.
   - `waitlist=false` (or omitted) and the window overlaps an existing
     active reservation: unchanged, exact existing 409 response.
     `test_create_reservation_route_overlap_returns_exact_409_envelope`
     in `tests/test_reservations.py` pins this response body byte for
     byte — it must still pass unmodified.
   - `waitlist=true` and the window overlaps an existing active
     reservation: **202 Accepted**, body is the created waitlist entry,
     not a 409.
   - `waitlist=true` and the window does NOT overlap anything: behaves
     exactly like today — 201, a real reservation is created, no
     waitlist entry.

2. **Promotion on cancel.** When an active reservation is cancelled via
   `DELETE /reservations/{id}`:
   - If one or more waitlist entries exist for that resource whose
     requested window would now fit (no remaining overlap with any other
     still-active reservation), the **earliest-created** matching entry
     is promoted: a new reservation is created for its window, and the
     waitlist entry is marked promoted (or removed — your choice, make
     it explicit in your design).
   - Promotion must be **idempotent**: cancelling the same reservation
     twice, or any retry of the cancel request, must not create a second
     reservation for an already-promoted entry.
   - Promotion must **never double-book**: if the promoted entry's window
     no longer fits (e.g. something else was booked in the meantime),
     skip it and try the next-earliest matching entry instead of forcing
     the booking through.

3. **Expiry.** A waitlist entry whose requested window has already
   started (`starts_at <= now`) is expired: it must not be promoted, and
   should not appear in `GET /waitlist` as a live entry. Decide and
   document whether an expired entry is deleted, hidden, or flagged —
   just make it observable in the API response.

4. **Read surface.** `GET /waitlist` lists current (non-expired,
   non-promoted) waitlist entries, at minimum filterable by
   `resource_id`.

## Suggested acceptance tests (write these, or equivalents)

- `test_create_reservation_waitlist_true_on_overlap_returns_202`
- `test_create_reservation_waitlist_false_on_overlap_still_returns_409`
  (must reuse or match the exact body asserted in the existing test
  named above — do not weaken that test to make this one pass)
- `test_create_reservation_waitlist_true_no_overlap_returns_201_no_waitlist_entry`
- `test_cancel_reservation_promotes_earliest_waitlist_entry`
- `test_cancel_reservation_promotion_is_idempotent_on_repeat_cancel`
- `test_cancel_reservation_promotion_skips_entry_that_no_longer_fits`
- `test_expired_waitlist_entry_is_not_promoted`
- `test_get_waitlist_excludes_expired_and_promoted_entries`
- `test_get_waitlist_filters_by_resource_id`

## Out of scope

- Actually notifying a customer that their waitlist entry was promoted.
  `src/services/notifications_stub.py` exists on this branch and is
  explicitly out of scope — do not wire it into the promotion path.
- Any channel/template concerns from the notifications lab branches.
- A UI or any client-facing change beyond the two routes above.
- Reordering or prioritising the waitlist by anything other than
  creation order (no priority tiers, no customer tiers).
