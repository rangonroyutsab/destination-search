"""
Global DRF exception handler.
"""

from rest_framework.views import exception_handler as drf_exception_handler

from core.utils.responses import error_response


def custom_exception_handler(exc, context):
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
