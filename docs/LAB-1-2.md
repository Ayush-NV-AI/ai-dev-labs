# Lab 1.2 — reservations feature brief

Everything is in place except the HTTP surface. Your job: generate the
missing pieces using only natural-language prompts to your assistant, then
wire them up.

## What's already here

- `Reservation` model (`src/db/models.py`)
- A full async repository, `SqlAlchemyReservationRepository`
  (`src/db/repositories/reservations.py`): `add`, `get`, `list_overlapping`
- The `ReservationRepository` port (`src/services/ports.py`)
- A fully documented stub, `create_reservation`
  (`src/services/reservations.py`) — read its docstring, it is the spec
  for the function body
- A fake in-memory repository and a reservation factory for tests
  (`tests/conftest.py`)

## What you need to create

- `ReservationCreate` and `ReservationRead` schemas in `src/api/schemas.py`
- `src/api/routes/reservations.py`
- The body of `create_reservation` in `src/services/reservations.py`
- `tests/test_reservations.py`

## Endpoint contract

`POST /reservations`

| Outcome | Status | Body |
|---|---|---|
| Success | `201` | The created reservation |
| Overlapping window | `409` | Standard error envelope, `error.code == "resource_unavailable"` |
| Invalid window (`ends_at` not after `starts_at`, or window longer than 8 hours) | `422` | Standard error envelope, `error.code == "invalid_window"` |

The error envelope shape is defined in `src/api/errors.py` and is not
specific to this endpoint.

Follow `src/api/routes/resources.py` as the reference pattern for
dependency injection, error propagation and response shaping.
