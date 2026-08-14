"""
Custom exception classes AND the DRF handler that
turns them into the standard response envelope.
"""

from rest_framework.views import exception_handler as drf_exception_handler

from core.utils.responses import error_response


class ServiceUnavailableError(Exception):
    """Raised by any service layer when a downstream dependency can't be reached.
    Caught by custom_exception_handler below and turned into a 503
    - no view or app needs its own try/except for it.
    """


def custom_exception_handler(exc, context):
    if isinstance(exc, ServiceUnavailableError):
        return error_response(
            str(exc) or "Service temporarily unavailable.",
            status=503,
            code="service_unavailable",
        )

    response = drf_exception_handler(exc, context)
    if response is None:
        return None

    return error_response(
        _extract_message(response.data),
        status=response.status_code,
        details=response.data,
    )


def _extract_message(data) -> str:
    if isinstance(data, dict):
        detail = data.get("detail")
        if detail:
            return str(detail)
        return "Validation failed."
    if isinstance(data, list) and data:
        return str(data[0])
    return "An error occurred."
