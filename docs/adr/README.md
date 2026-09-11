# Architecture Decision Records

This directory holds ADRs for the booking service, one file per decision.

## Convention

- File name: `NNNN-short-kebab-title.md`, e.g. `0001-notification-delivery-model.md`.
- Numbers are sequential and never reused, even if a decision is later
  superseded — look at the highest existing number in this directory and
  add one. The first ADR in a fresh checkout is `0001`.
- Use `docs/LAB-3-1-ADR-TEMPLATE.md` as the starting point for a new
  record. Keep the four sections (Context, Options, Decision,
  Consequences); don't add new top-level sections per ADR.
- A superseded ADR is not deleted. Set its `Status` to
  `Superseded by ADR-NNNN` and leave the rest of the file as a historical
  record — the reasoning that was good enough at the time is still worth
  reading later.
- One ADR per decision, not one ADR per meeting. If a discussion didn't
  land on a decision, it doesn't get a file yet.
