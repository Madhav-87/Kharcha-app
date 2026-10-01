# UPI payment initiation and reconciliation

Payment records and linked expenses are created inside one database
transaction. Money is sent as integer paise, and every endpoint except the
signed callback requires an active account and bearer access token. The UPI
URI is an app handoff request; opening it does not prove that money moved.

## Initiate and inspect

- `GET /api/v1/payments/upi-apps/` lists active UPI app metadata.
- `POST /api/v1/payments/initiate/` requires an `Idempotency-Key` header of
  8–80 characters and a body containing `amount_paise`, `category_public_id`,
  and either `payee_public_id` or both `payee_name` and `payee_upi_id`. Optional
  fields are `note` and `upi_app_code`. The amount limit is 10,000,000 paise.
- The response includes the payment, a `upi://pay` URI with a unique reference
  code, and `idempotent_replay`. Repeating the same key and request returns the
  same payment; reusing the key with different details returns HTTP 409.
- Initiation creates a pending UPI expense linked to the payment. The
  payment insert trigger records the initial state event.
- `GET /api/v1/payments/?status=processing&page=1&page_size=20` lists the
  caller's payment attempts. `GET /api/v1/payments/{public_id}/` returns one
  attempt and its event history.

After handing off to the payment app, the client can call
`POST /api/v1/payments/{public_id}/redirected/` to move the attempt from
`initiated` to `processing`.

## User reports and verified results

`POST /api/v1/payments/{public_id}/report/` accepts
`{"outcome":"completed"}` or `{"outcome":"not_completed"}`. A user report
of completion moves the payment to `unknown`, pending independent verification;
it does not mark it successful. A report that it was not completed moves it to
`cancelled`.

The provider callback is `POST /api/v1/payments/callbacks/upi/`. Configure a
private `UPI_CALLBACK_SECRET` and send an `X-UPI-Signature` header containing
the lowercase hex HMAC-SHA256 of the exact request body (optionally prefixed
with `sha256=`). The signed JSON includes `reference_code`, `status`
(`successful` or `failed`), and for success a required `upi_txn_ref`; an
optional `failure_reason` can accompany failure. Callbacks are unavailable
until a secret is configured. Successful verified results set
`confirmed_by=upi_callback` and a resolution timestamp; the schema's status
trigger synchronizes the linked expense and appends the event.

Terminal `successful`, `failed`, and `cancelled` states cannot be changed.
`unknown` attempts can later receive a verified success or failure. Successful
payments also re-evaluate affected budget alerts.

## Reconciliation

The reconciler moves `initiated` or `processing` attempts older than 20 minutes
to `unknown`. It never guesses success or failure. Run it manually with
`python manage.py reconcile_payments`, or start Celery Beat to enqueue the
reconciliation task every five minutes:

```powershell
celery -A config.celery worker -l info
celery -A config.celery beat -l info
```

Stale attempts remain visible in payment history for review. Only a signed
provider result or another trusted reconciliation source can resolve them.
