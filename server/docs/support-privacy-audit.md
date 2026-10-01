# Support, privacy, and audit API

Support and privacy endpoints require an authenticated, active account. Responses
use the standard success envelope. All issue and request lookups are scoped to
the authenticated user.

## Support issues

- `POST /api/v1/support/issues/` creates a support issue. Required: `subject`;
  optional: `description`, `expense_public_id`, or `payment_public_id`. A report
  can be linked to one owned expense or payment, or be a general/account issue.
- `GET /api/v1/support/issues/` lists the user's issues, newest first. Supports
  `page` (default `1`) and `page_size` (default `20`, maximum `100`).
- `GET /api/v1/support/issues/{public_id}/` reads one of the user's issues.

The schema has no issue category field, so the subject/description carry the
issue type and optional resource links. Users cannot update or resolve issue
status through this API.

## Privacy requests

- `GET /api/v1/settings/privacy/` returns account status, the latest 20 export
  requests, and any active deletion request.
- `POST /api/v1/settings/export-data/` queues a full JSON export. A Celery worker
  builds it under `PRIVATE_EXPORT_ROOT`, outside public media serving. When ready,
  `file_url` points to an authenticated, user-scoped download endpoint. Export
  payloads omit password hashes, refresh-token hashes, FCM tokens, and 2FA secrets.
- `POST /api/v1/settings/delete-account/` requires `{ "confirm": true }` and
  schedules deletion 30 days later. The grace period is stored in
  `data_requests.scheduled_for`; no data is immediately removed. `DELETE` on the
  same URL cancels an outstanding request during the grace period.

Starting an export requires a running Celery worker and configured broker. Set
`PRIVATE_EXPORT_ROOT` to a private, access-controlled directory in deployed
environments. Downloads require both the signed request link and the owning
user's active bearer authentication.

The deletion endpoint records and schedules the user's request; final deletion
must be carried out by the account-retention process after `scheduled_for`.
The project does not infer retention rules for financial records.

## Audit events

Audit records are server-side only and are not exposed by these endpoints. The
backend records authentication/session changes, account and settings changes,
support/privacy requests, manual expense deletion, payment creation, and payment
status transitions. Audit metadata excludes passwords, raw bearer/refresh
tokens, FCM tokens, and payment notes. Entity IDs are internal database IDs and
are not returned in normal API responses.
