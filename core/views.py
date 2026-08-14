from django.db import connections
from django.db.utils import OperationalError
from rest_framework.views import APIView

from core.utils.responses import error_response, success_response
from apps.destinations.search.client import get_es_client


class HealthCheckView(APIView):
    """
    Liveness/readiness probe. Checks that the app can actually reach
    its dependencies (not just that the Django process is up).
    """

    def get(self, request):
        checks = {
            "database": self._check_database(),
            "elasticsearch": self._check_elasticsearch(),
        }
        healthy = all(checks.values())

        if healthy:
            return success_response({"status": "ok", "checks": checks})

        return error_response(
            "One or more dependencies are unreachable.",
            status=503,
            code="service_unavailable",
            details=checks,
        )

    @staticmethod
    def _check_database() -> bool:
        try:
            with connections["default"].cursor() as cursor:
                cursor.execute("SELECT 1")
            return True
        except OperationalError:
            return False

    @staticmethod
    def _check_elasticsearch() -> bool:
        try:
            return get_es_client().ping()
        except Exception:
            return False