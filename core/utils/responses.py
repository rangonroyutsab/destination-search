"""
Standard response envelope.

Success:
    {"success": true, "data": {...}, "error": null}

Failure:
    {"success": false, "data": null, "error": {"code": "...", "message": "...", "details": ...}}
"""

from typing import Any

from rest_framework.response import Response

_DEFAULT_CODES = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    429: "too_many_requests",
    500: "internal_error",
    501: "not_implemented",
    503: "service_unavailable",
}


def success_response(
    data: Any = None, *, status: int = 200, meta: dict | None = None
) -> Response:
    body: dict = {"success": True, "data": data, "error": None}
    if meta is not None:
        body["meta"] = meta
    return Response(body, status=status)


def error_response(
    message: str,
    *,
    status: int = 400,
    code: str | None = None,
    details: Any = None,
) -> Response:
    body = {
        "success": False,
        "data": None,
        "error": {
            "code": code or _DEFAULT_CODES.get(status, "error"),
            "message": message,
            "details": details,
        },
    }
    return Response(body, status=status)
