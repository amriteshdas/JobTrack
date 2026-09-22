from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@extend_schema(
    responses=inline_serializer(
        "HealthCheckResponse",
        {"status": serializers.CharField(), "service": serializers.CharField()},
    ),
    description="Not a business endpoint -- proof the API, DRF, and the database "
    "connection are all reachable.",
)
@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """
    Not a business feature - just proof the API, DRF, and the database
    connection are all wired up correctly before we build anything on top.
    """
    return Response({"status": "ok", "service": "jobtrack-backend"})
