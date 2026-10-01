# Accounts and authentication API

All routes are under `/api/v1/`. Protected routes accept
`Authorization: Bearer <access_token>`; every authenticated request checks that
the corresponding `auth_sessions` row is still active.

## Endpoints

| Method | Route | Purpose |
|---|---|---|
| `POST` | `/auth/register/` | Create an account and first session |
| `POST` | `/auth/login/` | Sign in by email or phone and password |
| `POST` | `/auth/google/` | Verify a Google ID token and sign in |
| `POST` | `/auth/refresh/` | Rotate a refresh token and issue a new access token |
| `POST` | `/auth/logout/` | Revoke the current session |
| `POST` | `/auth/forgot-password/` | Send a one-time reset link when an active account exists |
| `POST` | `/auth/reset-password/` | Set a new password using the one-time token |
| `POST` | `/auth/change-password/` | Change the current user's password |
| `GET` | `/auth/me/` | Return the current profile |
| `GET` | `/auth/sessions/` | List the user's sessions |
| `DELETE` | `/auth/sessions/` | Revoke every session |
| `DELETE` | `/auth/sessions/all/` | Alias to revoke every session |
| `DELETE` | `/auth/sessions/{public_id}/` | Revoke one of the user's sessions |
| `GET/PATCH` | `/users/me/` | Read/update editable profile fields |
| `GET/PATCH` | `/settings/` | Read/update financial and notification preferences |
| `GET/PATCH` | `/onboarding/` | Read/save onboarding progress |
| `POST` | `/onboarding/complete/` | Mark onboarding complete |

Registration accepts `full_name`, `email`, `password`, `confirm_password`,
and optional `phone`, `display_name`, `college_name`, and
`monthly_budget_paise`. Login accepts `identifier`, `password`, and optional
`device_label`. Money remains integer paise.

Example registration request:

```json
{
  "full_name": "Rahul Sharma",
  "email": "rahul@example.edu",
  "phone": "+919876543210",
  "password": "a-long-unique-passphrase",
  "confirm_password": "a-long-unique-passphrase",
  "monthly_budget_paise": 1000000
}
```

Successful login/register/refresh responses contain `access_token`,
`refresh_token`, `token_type`, `expires_in`, `session_public_id`, and a public
user summary. The access token is a signed, short-lived Django token; it is not
a standards-based JWT. Refresh tokens are random opaque values stored only as
SHA-256 hashes in `auth_sessions` and rotate on every refresh.

## Session IDs and revocation

The supplied `auth_sessions` table has no `public_id` column. The API therefore
returns a stable HMAC-derived 64-character public handle, never the numeric
database ID. Access-token claims carry that handle. Authentication checks it
against the user's active database sessions, so logout, password reset, or
session revocation invalidates access tokens immediately. Rotating `SECRET_KEY`
also invalidates existing access tokens and session handles.

## Password reset and Google sign-in

Reset tokens are random, one-use values. Only their SHA-256 hashes are stored;
the raw token is sent in a reset email and is never returned by the API. In
debug mode Django prints email to the console. Production needs SMTP variables
in `.env`.

Google sign-in verifies the ID token signature, audience, expiry, and verified
email with `google-auth`; set `GOOGLE_CLIENT_ID`. Firebase is not used for
authentication.

Registration, login, Google sign-in, refresh, password reset, and forgot
password are rate limited. Error responses use the shared
`{success, error: {code, message, fields}}` envelope.
