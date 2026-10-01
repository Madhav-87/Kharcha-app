from django.contrib import admin
from django.urls import include, path

from common.views import health_check

urlpatterns = [
    path("api/health/", health_check, name="health-check"),
    path("api/v1/health/", health_check, name="v1-health-check"),
    path("admin/", admin.site.urls),
    path("api/v1/", include("apps.accounts.urls")),
    path("api/v1/categories/", include("apps.categories.urls")),
    path("api/v1/payees/", include("apps.payments.payee_urls")),
    path("api/v1/payments/", include("apps.payments.urls")),
    path("api/v1/expenses/", include("apps.expenses.urls")),
    path("api/v1/budgets/", include("apps.budgets.urls")),
    path("api/v1/analytics/", include("apps.analytics.urls")),
    path("api/v1/notifications/", include("apps.notifications.urls")),
    path("api/v1/support/", include("apps.support.urls")),
]
