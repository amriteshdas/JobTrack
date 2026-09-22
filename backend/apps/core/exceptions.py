import logging

from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_default_handler

logger = logging.getLogger("apps")


def custom_exception_handler(exc, context):
    """
    Wraps DRF's default handler so the API has ONE predictable error shape
    everywhere, per the error-handling contract Phase 0 called for:
    {"detail": "...", "code": "..."} for a single error, or DRF's normal
    {"field": ["message"]} shape for serializer validation errors (left
    untouched -- every view in this project already relies on that exact
    shape, e.g. err.response.data.field_name on the frontend).

    Three things happen here that DRF doesn't do by default:
    1. Exceptions DRF already understands (ValidationError, NotFound,
       PermissionDenied, NotAuthenticated, Throttled, MethodNotAllowed)
       get a `code` field added alongside `detail`, taken from the
       exception's own default_code -- so a client can branch on
       `code === "throttled"` instead of parsing the message text.
    2. Two exception types DRF's handler doesn't touch at all -- Django's
       own Http404 and PermissionDenied, which some code paths raise
       directly rather than DRF's versions -- get converted to the same
       envelope instead of propagating into Django's HTML error pages.
    3. Anything else -- a genuine bug -- is logged with its full traceback
       server-side and returned to the client as a generic 500 with NO
       exception details. Returning str(exc) here would leak internals
       (stack traces, SQL fragments, file paths); that's a real
       information-disclosure risk, not a hypothetical one.
    """
    response = drf_default_handler(exc, context)

    if response is not None:
        if isinstance(response.data, dict) and "detail" in response.data and "code" not in response.data:
            code = getattr(exc, "default_code", None) or getattr(exc, "code", None)
            if code:
                response.data["code"] = code
        return response

    if isinstance(exc, Http404):
        return Response(
            {"detail": "Not found.", "code": "not_found"}, status=status.HTTP_404_NOT_FOUND
        )

    if isinstance(exc, PermissionDenied):
        return Response(
            {"detail": "Permission denied.", "code": "permission_denied"},
            status=status.HTTP_403_FORBIDDEN,
        )

    if isinstance(exc, IntegrityError):
        # A database constraint fired that serializer validation didn't
        # catch first -- ideally rare (most constraints in this project
        # have a serializer-level mirror, e.g. Job's salary check in
        # Phase 3), but a race condition can still hit the DB constraint
        # directly. A clean 409 beats a raw 500 with a DB error message.
        logger.warning("IntegrityError reached the exception handler unmirrored: %s", exc)
        return Response(
            {"detail": "This conflicts with existing data.", "code": "conflict"},
            status=status.HTTP_409_CONFLICT,
        )

    logger.exception("Unhandled exception in view: %s", context.get("view"))
    return Response(
        {"detail": "An unexpected error occurred. Please try again.", "code": "server_error"},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
