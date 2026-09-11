# Capstone Brief

75 minutes covers design, decomposition, build, tests, docs, and a
security gate — so the build itself needs to fit in well under 30
minutes. Pick ONE of the three options below. All three are sized the
same; do not invent a fourth. A team that finishes something small beats
a team that half-builds something ambitious.

---

## Option A — Cancellation fee

A reservation cancelled within 2 hours of its start incurs a fee. The fee
is calculated, recorded, and returned in the cancellation response.

**Acceptance criteria**

1. Cancelling a reservation whose `starts_at` is more than 2 hours in the
   future incurs no fee (fee is zero, or absent — pick one and be
   consistent).
2. Cancelling a reservation whose `starts_at` is within 2 hours (inclusive
   of the boundary — decide which side of "exactly 2 hours" the boundary
   falls on, and be able to say why) incurs a fee, and the fee amount is
   present in the `DELETE /reservations/{id}` response body.
3. The fee is recorded against the reservation (or a related record) so
   it is still visible on a later `GET`, not just in the cancellation
   response at the moment of cancellation.

**Out of scope:** actually charging a payment method, refunds, any
notion of a "fee waiver" or customer-tier discount on the fee, historical
recalculation of fees for reservations cancelled before this shipped.

---

## Option B — Resource blackout windows

A resource can have recurring unavailable windows (e.g. "closed every
Sunday," "no bookings 22:00–06:00 daily"). Reservation creation must
respect them.

**Acceptance criteria**

1. A resource can have one or more blackout windows defined, each
   recurring on a schedule (at minimum: a fixed day-of-week + time range,
   or a fixed daily time range — pick one recurrence shape and be
   explicit that the other is out of scope).
2. Creating a reservation that overlaps a blackout window is rejected,
   using the same half-open-window logic and the same error shape
   (`ResourceUnavailable` → 409) already used for reservation-vs-
   reservation overlap.
3. A reservation that does NOT overlap any blackout window is created
   normally, unaffected by blackout windows on other resources or at
   other times.

**Out of scope:** one-off (non-recurring) blackout windows, blackout
windows that can themselves be booked around with an override/exception,
any UI or bulk-import for defining blackout windows.

---

## Option C — Reservation notes search

A search endpoint over reservation notes, scoped to the caller's own
reservations, paginated.

**Acceptance criteria**

1. `GET /reservations/search?q=...` returns only reservations whose
   `note` contains the query text (case-insensitive substring match is
   sufficient — full-text search is out of scope).
2. Results are scoped to "the caller's own reservations" — since this
   repo has no auth system yet, define scoping via an explicit parameter
   (e.g. a required `customer_id` / `created_by` filter) and say clearly
   in your ADR that this stands in for real caller identity.
3. Results are paginated (`limit`/`offset` or a cursor — your choice),
   and the response makes the total count or "there are more" state
   visible to the caller.

**Out of scope:** full-text search/ranking, searching any field other
than `note`, search across other customers' reservations under any
circumstance, fuzzy/typo-tolerant matching.

---

## Before you build

Write the ADR. State which option you picked and why, and answer the one
ambiguity your option leaves open (the boundary condition in A, the
recurrence shape in B, the scoping stand-in in C) explicitly — don't
leave it to come up during the build.
