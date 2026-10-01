# Notifications and FCM

All inbox and device endpoints require an active account and bearer access
token. Notifications are the in-app source of truth; push delivery is an
optional asynchronous copy sent to active devices.

## Notification inbox

- `GET /api/v1/notifications/` lists the caller's notifications. Optional
  filters are `unread_only=true` and `type`; results are paginated with `page`
  and `page_size` (1 to 100, default 20). The response includes an overall
  `unread_count`.
- `PATCH /api/v1/notifications/{public_id}/` accepts `{"is_read":true}` to
  mark a notification read or `false` to mark it unread.
- `POST /api/v1/notifications/read-all/` marks all of the caller's unread
  notifications as read.

Notification IDs use public UUIDs. The feed never exposes database IDs or
another user's notifications.

## Device tokens

- `GET /api/v1/notifications/devices/` lists registered device metadata.
- `POST /api/v1/notifications/devices/` registers or refreshes a token using
  `fcm_token`, `platform` (`web`, `android`, or `ios`), and optional
  `device_label` and `app_version`. Token values are never returned by the API.
- `POST /api/v1/notifications/devices/unregister/` accepts `fcm_token` and
  deactivates that token for the caller.

Register tokens only after the client obtains them from Firebase. A token that
is registered to another account is reassigned to the authenticated account.

## FCM delivery

Set `FCM_PROJECT_ID` and `FCM_SERVICE_ACCOUNT_FILE` in `server/.env` to enable
push delivery. The service account needs permission to send messages in the
Firebase project, and the Firebase Cloud Messaging API must be enabled. Store
the service-account JSON file outside the repository. The server obtains
short-lived OAuth credentials with the Firebase Messaging scope and sends
through the FCM HTTP v1 `projects.messages.send` endpoint. [Firebase's HTTP v1
guide](https://firebase.google.com/docs/cloud-messaging/send/v1-api) documents
the endpoint and required authorization scope.

Start a Celery worker and Redis for asynchronous delivery. Notification
preference flags in account settings control whether budget, payment, and
system notifications are created and delivered; `push_enabled` controls FCM
separately, so disabling push leaves the in-app inbox available. Each device
send is recorded in `notification_deliveries`. Transient failures are retried;
FCM's unregistered token response deactivates that device.
