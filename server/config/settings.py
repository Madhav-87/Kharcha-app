"""Django settings for the Student Finance API."""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv
from corsheaders.defaults import default_headers

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_bool(name: str, default: bool = False, *, legacy_name: str | None = None) -> bool:
    value = os.getenv(name)
    if value is None and legacy_name:
        value = os.getenv(legacy_name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "", *, legacy_name: str | None = None) -> list[str]:
    value = os.getenv(name)
    if value is None and legacy_name:
        value = os.getenv(legacy_name)
    if value is None:
        value = default
    return [item.strip() for item in value.split(",") if item.strip()]


DEBUG = env_bool("DJANGO_DEBUG", legacy_name="DEBUG")
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY") or os.getenv("SECRET_KEY", "")
if not SECRET_KEY:
    raise ImproperlyConfigured(
        "Set DJANGO_SECRET_KEY (or the legacy SECRET_KEY) in server/.env."
    )

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1", legacy_name="ALLOWED_HOSTS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "apps.accounts.apps.AccountsConfig",
    "apps.categories.apps.CategoriesConfig",
    "apps.payments.apps.PaymentsConfig",
    "apps.expenses.apps.ExpensesConfig",
    "apps.budgets.apps.BudgetsConfig",
    "apps.analytics.apps.AnalyticsConfig",
    "apps.notifications.apps.NotificationsConfig",
    "apps.support.apps.SupportConfig",
    "apps.audit.apps.AuditConfig",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"
AUTH_USER_MODEL = "accounts.User"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.getenv("DB_NAME", "student_finance"),
        "USER": os.getenv("DB_USER", "root"),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", "127.0.0.1"),
        "PORT": os.getenv("DB_PORT", "3306"),
        "OPTIONS": {"charset": "utf8mb4"},
        "CONN_MAX_AGE": int(os.getenv("DB_CONN_MAX_AGE", "60")),
        "CONN_HEALTH_CHECKS": True,
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
# Store/interpret database timestamps in UTC. Reporting SQL applies IST offsets.
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"
PRIVATE_EXPORT_ROOT = Path(os.getenv("PRIVATE_EXPORT_ROOT", BASE_DIR / "private_exports")).resolve()
DEFAULT_AUTO_FIELD = "common.db_fields.UnsignedBigAutoField"

CORS_ALLOWED_ORIGINS = env_list(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:5173",
    legacy_name="FRONTEND_URL",
)
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")
CORS_ALLOW_CREDENTIALS = env_bool("CORS_ALLOW_CREDENTIALS", True)
CORS_ALLOW_HEADERS = (*default_headers, "idempotency-key")

REST_FRAMEWORK = {
    "EXCEPTION_HANDLER": "common.exceptions.api_exception_handler",
    "DEFAULT_PERMISSION_CLASSES": [
        "apps.accounts.permissions.IsActiveAccount",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.accounts.authentication.SignedBearerAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "auth_register": "5/hour",
        "auth_login": "10/minute",
        "auth_google": "10/minute",
        "auth_forgot_password": "3/hour",
        "auth_reset_password": "10/hour",
        "auth_refresh": "30/hour",
    },
}

ACCESS_TOKEN_TTL_SECONDS = int(os.getenv("ACCESS_TOKEN_TTL_SECONDS", "900"))
REFRESH_SESSION_TTL_DAYS = int(os.getenv("REFRESH_SESSION_TTL_DAYS", "30"))
PASSWORD_RESET_TTL_MINUTES = int(os.getenv("PASSWORD_RESET_TTL_MINUTES", "30"))
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
UPI_CALLBACK_SECRET = os.getenv("UPI_CALLBACK_SECRET", "")
FCM_PROJECT_ID = os.getenv("FCM_PROJECT_ID", "")
FCM_SERVICE_ACCOUNT_FILE = os.getenv("FCM_SERVICE_ACCOUNT_FILE", "")
FRONTEND_PASSWORD_RESET_URL = os.getenv(
    "FRONTEND_PASSWORD_RESET_URL", "http://localhost:5173/reset-password"
)

EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend"
    if DEBUG
    else "django.core.mail.backends.smtp.EmailBackend",
)
EMAIL_HOST = os.getenv("EMAIL_HOST", "localhost")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "25"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", False)
EMAIL_USE_SSL = env_bool("EMAIL_USE_SSL", False)
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "Student Finance <no-reply@example.com>")

# Respect explicit deployment settings while using secure cookie defaults outside
# local development. HTTPS termination/proxy details remain deployment-specific.
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", not DEBUG)
CSRF_COOKIE_SECURE = env_bool("CSRF_COOKIE_SECURE", not DEBUG)
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", False)
SECURE_PROXY_SSL_HEADER = (
    ("HTTP_X_FORWARDED_PROTO", "https")
    if env_bool("TRUST_X_FORWARDED_PROTO", False)
    else None
)
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

CELERY_BROKER_URL = os.getenv("REDIS_URL") or os.getenv(
    "CELERY_BROKER_URL", "redis://localhost:6379/0"
)
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", CELERY_BROKER_URL)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_BEAT_SCHEDULE = {
    "reconcile-stale-upi-payments": {
        "task": "payments.reconcile_stale_payments",
        "schedule": 300.0,
    },
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "{levelname} {asctime} {name}: {message}", "style": "{"},
    },
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "simple"}},
    "root": {"handlers": ["console"], "level": os.getenv("LOG_LEVEL", "INFO")},
}
