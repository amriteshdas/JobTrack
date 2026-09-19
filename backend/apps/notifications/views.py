from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(APIView):
    """GET /api/notifications/ -- always scoped to request.user, never a URL param."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Notification.objects.filter(recipient=request.user)
        return Response(NotificationSerializer(qs, many=True).data)


class MarkNotificationReadView(APIView):
    """PATCH /api/notifications/{id}/read/"""

    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        notification = Notification.objects.filter(pk=pk, recipient=request.user).first()
        if notification is None:
            # Scoped by recipient in the lookup itself, so another user's
            # notification 404s rather than 403s -- same pattern as every
            # other own-resource-only endpoint in this project.
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        if not notification.is_read:
            notification.is_read = True
            notification.save(update_fields=["is_read"])
        return Response(NotificationSerializer(notification).data)
