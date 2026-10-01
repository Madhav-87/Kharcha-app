# Student Finance Backend

Django REST API scaffold for the Student Finance React application. API routes
are versioned under `/api/v1/`; the health check is available at
`GET /api/v1/health/` (`GET /api/health/` remains as a compatibility alias).

## Local setup

From this directory, create and activate a virtual environment, install
`requirements.txt`, then copy `.env.example` to `.env` and set a private Django
secret and your MySQL credentials. The default database name is
`student_finance`, matching the supplied MySQL schema.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py runserver
```

The React development server proxies `/api` requests to Django at
`http://127.0.0.1:8000`. Its API helper uses `/api/v1` by default; set
`VITE_API_BASE_URL` only when the API is hosted at a different base URL.

The app modules provide URL includes and now map the supplied schema through
unmanaged Django models. Apply `student_finance_schema_mysql.sql` to create the
tables, triggers, seed data, and reporting views. Do not use Django migrations
to create or alter those schema-owned objects. See
[`docs/mysql-compatibility.md`](docs/mysql-compatibility.md) for the field and
MySQL compatibility decisions.

## Configuration

See `.env.example` for settings. Existing variable names such as `SECRET_KEY`,
`DEBUG`, `ALLOWED_HOSTS`, `FRONTEND_URL`, and `CELERY_BROKER_URL` remain
supported for local setups. `DJANGO_SECRET_KEY` is required (or its legacy
`SECRET_KEY` equivalent); the server refuses to start without it.

Account/authentication endpoints use short-lived signed bearer access tokens
and rotating refresh tokens stored as hashes. Configure `GOOGLE_CLIENT_ID` for
Google sign-in and SMTP settings for password reset email in production. See
[`docs/accounts-auth.md`](docs/accounts-auth.md) for the endpoint contract.

Category customization and saved-payee endpoints are documented in
[`docs/categories-payees.md`](docs/categories-payees.md).

Manual expense creation, editing, soft deletion, filtering, and pagination are
documented in [`docs/expenses.md`](docs/expenses.md).

Monthly and category budgets, usage calculations, and threshold alert behavior
are documented in [`docs/budgets-alerts.md`](docs/budgets-alerts.md).

UPI intent initiation, idempotency, payment status transitions, verified
callbacks, and stale-payment reconciliation are documented in
[`docs/payments.md`](docs/payments.md).

The in-app notification inbox, device token management, and FCM delivery setup
are documented in [`docs/notifications-fcm.md`](docs/notifications-fcm.md).

Dashboard summaries, spend trends, category breakdowns, and budget usage are
documented in [`docs/analytics-dashboard.md`](docs/analytics-dashboard.md).

Celery uses `REDIS_URL` or `CELERY_BROKER_URL`, defaulting to
`redis://localhost:6379/0`. Start Redis before running a worker.

## Project layout

- `config/` contains Django settings, route configuration, and Celery setup.
- `apps/` contains the domain applications.
- `common/` contains shared API utilities and middleware.
- `scripts/` contains data/bootstrap script entry points.
