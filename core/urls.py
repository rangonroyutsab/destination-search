from django.contrib import admin
from django.urls import include, path

from core.views import HealthCheckView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/health/", HealthCheckView.as_view(), name="health"),
    path("api/v1/destinations/", include("apps.destinations.urls")),
]
