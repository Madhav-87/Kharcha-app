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

The app modules currently provide URL includes for their API areas, but their
endpoints and schema-aligned models are still being implemented. Apply the
provided MySQL schema as the database source of truth; wait for the model phase
before using Django migrations against that database.

## Configuration

See `.env.example` for settings. Existing variable names such as `SECRET_KEY`,
`DEBUG`, `ALLOWED_HOSTS`, `FRONTEND_URL`, and `CELERY_BROKER_URL` remain
supported for local setups. `DJANGO_SECRET_KEY` is required (or its legacy
`SECRET_KEY` equivalent); the server refuses to start without it.

Celery uses `REDIS_URL` or `CELERY_BROKER_URL`, defaulting to
`redis://localhost:6379/0`. Start Redis before running a worker.

## Project layout

- `config/` contains Django settings, route configuration, and Celery setup.
- `apps/` contains the domain applications.
- `common/` contains shared API utilities and middleware.
- `scripts/` contains data/bootstrap script entry points.
