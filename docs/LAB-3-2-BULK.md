# Bulk notification send

Adds `POST /notifications/bulk`: one template, rendered once, sent to
every recipient in a batch. Recipients can be given explicitly, resolved
from a `recipient_filter` against past send history, or both.

New files:

- `src/notifications/bulk_types.py` — `BulkSendResult`, the per-recipient
  result row.
- `src/notifications/bulk.py` — `BulkSendService`: recipient resolution
  and the batch send loop.
- `src/api/routes/notifications.py` — the new route (existing file).
- `src/api/schemas.py` — `BulkSendRequest` (existing file).
- `tests/test_bulk_send.py` — coverage for the service and the route.

Review this the way you'd review any PR before merge: triage every
finding into ACT (must fix before merge), JUDGE (defensible either way),
or IGNORE (style the linter already owns). Do not assume a green
`pytest -q` means the diff is safe to merge.
