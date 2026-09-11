# Lab 3.1 — Design Brief: Notifications for the Booking Service

## The ask

Customers must be told when a reservation is confirmed, changed, cancelled,
or about to start. Operations wants a record of what was sent, so they can
answer "did the customer actually get told?" without guessing. The channel
mix will grow: email today, SMS and push later. Nobody wants to redesign
this again when that happens.

That is the whole ask. Everything below is context for making it real,
not a hidden checklist of required components.

## Real numbers

Design with these, not with adjectives:

- **12,000 reservations/day**, peaking at **6x** load in a two-hour window
  (the morning booking rush).
- **Notification volume is ~3.5x reservation volume** — a single
  reservation event can fan out into multiple notifications (confirmation,
  a later reminder, an operations copy, etc.).
- **99.5% availability target on the booking API.** Notifications are
  allowed to lag behind a reservation event, but a notification must not
  be silently lost.
- **The email provider allows 300 requests/minute**, with a p99 latency of
  2.4 seconds per request.
- **Retention: 24 months of send records, auditable.** An auditor must be
  able to reconstruct what was sent, to whom, when, and — see EU data
  residency below — from where.

## Real constraints

- **4 engineers**, 2 of them junior. No dedicated platform team to lean on.
- **On-call rotation of 3**, already stretched across other services.
- **9 weeks to first release.**
- **The booking API must not get slower.** It is already on a latency SLO
  and notifications are not allowed to put that at risk, whatever
  mechanism connects the two.
- **EU data residency.** Recipient data must not leave the EU, and the
  auditor accepts send-record logs only if they show which region
  processed the send.

## Deliberate ambiguities

These are left unresolved on purpose. Resolving them is part of the design
work, not a gap in this brief:

- Whether a notification is **transactional** (must happen, arguably in
  the same unit of work as the reservation change) or **eventual** (best
  effort, decoupled, may lag).
- Whether the **send record is a projection** (a read model rebuilt from
  events elsewhere) **or the source of truth** for "did this get sent."
- Whether **templating belongs in this service**, or in a shared
  templating service that other parts of the business might also want.

## Anti-requirements

Constraints on the *solution space*, not the problem — included so the
obvious answer is not the only defensible one:

- **A new Kafka cluster is not available within the 9 weeks.** Any design
  that assumes one exists is not shippable on this timeline.
- **The team has no Kubernetes experience and no platform support to lean
  on.** A design that assumes a platform team will operate it for you is
  not shippable with this team.

## What a good answer looks like

A good answer picks a position on each ambiguity above, explains the
trade-off it accepts, and respects every constraint and anti-requirement.
It does not need to be the "best" architecture in the abstract — it needs
to be defensible for *this* team, *this* timeline, and *these* numbers.

Write your decision as an ADR using `docs/LAB-3-1-ADR-TEMPLATE.md` and file
it under `docs/adr/`.
