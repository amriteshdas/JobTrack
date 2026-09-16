from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated

from apps.core.permissions import IsEmployer

from .models import EmployerProfile
from .serializers import EmployerProfileSerializer


class EmployerProfileMeView(RetrieveUpdateAPIView):
    """
    GET/PATCH /api/profiles/employer/me/

    There is no lookup by id and no `pk` in the URL. The object is resolved
    from request.user, so "fetch someone else's profile" is not an
    expressible request. Designing the endpoint this way removes a whole
    class of IDOR bugs rather than relying on a permission check to catch them.
    """

    serializer_class = EmployerProfileSerializer
    permission_classes = [IsAuthenticated, IsEmployer]

    def get_object(self):
        profile, _ = EmployerProfile.objects.get_or_create(user=self.request.user)
        return profile
