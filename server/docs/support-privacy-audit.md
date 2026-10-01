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
  Files and download links expire after seven days when Celery Beat runs the
  export cleanup task.
- `POST /api/v1/settings/delete-account/` requires `{ "confirm": true }` and
  schedules deletion 30 days later. The grace period is stored in
  `data_requests.scheduled_for`; no data is immediately removed. `DELETE` on the
  same URL cancels an outstanding request during the grace period. Celery Beat
  runs the due-request processor hourly; requests wait an additional day while
  the account has initiated, processing, or unknown UPI payments.

Starting an export and processing due deletion requests require a running Celery
worker and configured broker; export cleanup and deletion scheduling require
Celery Beat. The web process and worker must share
`PRIVATE_EXPORT_ROOT`, which must be outside public media and access-controlled.
Downloads require both the signed request link and the owning user's active
bearer authentication.

After the grace period and once no UPI payment is unresolved, the deletion task
removes the user's account and related schema-owned records. It anonymizes prior
audit IP/metadata and keeps a minimal system audit event. The schema cascades
`data_requests` with account deletion, so the deletion request row itself is
removed as part of that purge.

## Audit events

Audit records are server-side only and are not exposed by these endpoints. The
backend records authentication/session changes, account and settings changes,
support/privacy requests, manual expense deletion, payment creation, and payment
status transitions. Audit metadata excludes passwords, raw bearer/refresh
tokens, FCM tokens, and payment notes. Entity IDs are internal database IDs and
are not returned in normal API responses.
