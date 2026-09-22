from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsEmployer, IsJobSeeker

from .models import Education, EmployerProfile, Experience, JobSeekerProfile
from .serializers import (
    EducationSerializer,
    EmployerProfileSerializer,
    ExperienceSerializer,
    JobSeekerProfileSerializer,
    JobSeekerProfileWriteSerializer,
    UpdateSkillsSerializer,
)


class EmployerProfileMeView(RetrieveUpdateAPIView):
    """
    GET/PATCH /api/profiles/employer/me/

    No `pk` in the URL -- the object always comes from request.user, so
    "fetch someone else's profile" is not an expressible request.
    """

    serializer_class = EmployerProfileSerializer
    permission_classes = [IsAuthenticated, IsEmployer]

    def get_object(self):
        profile, _ = EmployerProfile.objects.get_or_create(user=self.request.user)
        return profile


class JobSeekerProfileMeView(RetrieveUpdateAPIView):
    """
    GET/PATCH /api/profiles/seeker/me/

    Same pattern as EmployerProfileMeView: the object is resolved from the
    token, never a URL parameter, which removes a class of IDOR bugs by
    construction rather than by remembering to check ownership.
    """

    permission_classes = [IsAuthenticated, IsJobSeeker]

    def get_serializer_class(self):
        return (
            JobSeekerProfileWriteSerializer
            if self.request.method in ("PATCH", "PUT")
            else JobSeekerProfileSerializer
        )

    def get_object(self):
        profile, _ = JobSeekerProfile.objects.get_or_create(user=self.request.user)
        return profile


class UpdateSkillsView(APIView):
    """PUT /api/profiles/seeker/me/skills/ -- replace the full skill list."""

    permission_classes = [IsAuthenticated, IsJobSeeker]

    @extend_schema(request=UpdateSkillsSerializer, responses=JobSeekerProfileSerializer)
    def put(self, request):
        profile, _ = JobSeekerProfile.objects.get_or_create(user=request.user)
        serializer = UpdateSkillsSerializer(data=request.data, context={"profile": profile})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(JobSeekerProfileSerializer(profile).data)


class _OwnProfileNestedViewSet(viewsets.ModelViewSet):
    """
    Shared base for Education and Experience: both are simple CRUD lists
    scoped to "entries belonging to MY profile", nothing more. Factoring
    this out means the ownership-scoping logic is written and tested once,
    not duplicated (and potentially drifting) across two viewsets.
    """

    permission_classes = [IsAuthenticated, IsJobSeeker]

    def get_queryset(self):
        # drf-spectacular introspects this method at schema-generation time
        # with an AnonymousUser and no real request -- get_or_create(user=
        # AnonymousUser) would raise. This guard is the standard pattern
        # for that (recommended by drf-spectacular's own warning message),
        # not a security check: schema generation never serves real traffic.
        if getattr(self, "swagger_fake_view", False):
            return self.queryset_model.objects.none()

        # Scoping happens in the QUERYSET, not via an object-level
        # permission check -- so another job seeker's entries are not
        # merely forbidden to edit, they are absent from a list/retrieve
        # entirely. This is the same "unreachable beats guarded" pattern
        # used for Job.mine in Phase 3.
        profile, _ = JobSeekerProfile.objects.get_or_create(user=self.request.user)
        return self.queryset_model.objects.filter(profile=profile)

    def perform_create(self, serializer):
        profile, _ = JobSeekerProfile.objects.get_or_create(user=self.request.user)
        serializer.save(profile=profile)


class EducationViewSet(_OwnProfileNestedViewSet):
    serializer_class = EducationSerializer
    queryset_model = Education


class ExperienceViewSet(_OwnProfileNestedViewSet):
    serializer_class = ExperienceSerializer
    queryset_model = Experience
