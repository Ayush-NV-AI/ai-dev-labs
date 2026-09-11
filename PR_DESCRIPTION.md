<!--
Intended PR text for: lab-3-2-review-me -> lab-3-2-undocumented
Paste the section below verbatim as the PR title + description once this
branch is pushed to a real host. Not opened as a real PR here -- no
remote is configured in this build. See SCOPE_NOTES.md.
-->

## Title

feat: bulk notification send

## Description

Adds bulk send support for notifications: one template, rendered once,
sent out to a batch of recipients in a single call. Recipients can be
supplied explicitly, resolved from existing send history via a filter, or
both.

New: `src/notifications/bulk.py`, `src/notifications/bulk_types.py`,
`POST /notifications/bulk`. Reuses the existing channel registry and
send-record repository, so behaviour matches a single send in everything
except batching.

Tests cover the service and the route end to end and are green. Should be
a quick review — it's additive and follows the existing dispatch pattern
closely.
