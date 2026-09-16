from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.core.permissions import IsCompanyMember, IsEmployer

from .models import Job
from .serializers import JobSerializer, JobWriteSerializer


class JobViewSet(viewsets.ModelViewSet):
    """
    Job CRUD.

    Search, filtering and sorting are deliberately NOT here -- that is
    Phase 4. This phase covers create/edit/delete/publish and the ownership
    rules around them.
    """

    def get_serializer_class(self):
        return JobWriteSerializer if self.action in (
            "create", "update", "partial_update"
        ) else JobSerializer

    def get_queryset(self):
        # select_related/prefetch_related avoid N+1: without them, serializing
        # 20 jobs would issue 20 queries for companies plus 20 for skills.
        qs = Job.objects.select_related("company", "posted_by__user").prefetch_related("skills")

        if self.action == "list":
            # The public list shows published jobs only. Drafts are filtered
            # out at the QUERYSET level, not hidden in the serializer -- an
            # unpublished job is simply not reachable through this endpoint.
            return qs.filter(status=Job.Status.PUBLISHED)
        return qs

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [AllowAny()]
        if self.action in ("create", "mine"):
            return [IsAuthenticated(), IsEmployer()]
        return [IsAuthenticated(), IsEmployer(), IsCompanyMember()]

    def retrieve(self, request, *args, **kwargs):
        """
        A draft or closed job is visible only to its own company's members.
        Anyone else gets 404, not 403 -- revealing that a hidden job exists
        at a given id is itself an information leak.
        """
        job = self.get_object()
        if job.status != Job.Status.PUBLISHED and not self._user_can_manage(request.user, job):
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(self.get_serializer(job).data)

    @staticmethod
    def _user_can_manage(user, job):
        if not (user and user.is_authenticated and user.is_employer):
            return False
        profile = getattr(user, "employer_profile", None)
        if profile is None:
            return False
        return job.company.memberships.filter(employer_profile=profile).exists()

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated, IsEmployer])
    def mine(self, request):
        """
        GET /api/jobs/mine/ -- every job belonging to this employer's
        companies, in any status. Scoped by membership in the queryset, so
        another employer's jobs are not merely forbidden, they are absent.
        """
        profile = getattr(request.user, "employer_profile", None)
        if profile is None:
            return Response([])

        qs = (
            Job.objects.select_related("company")
            .prefetch_related("skills")
            .filter(company__memberships__employer_profile=profile)
            .distinct()
        )
        return Response(JobSerializer(qs, many=True).data)

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        job = self.get_object()  # runs IsCompanyMember object check
        if job.status == Job.Status.PUBLISHED:
            return Response(
                {"detail": "Job is already published."},
                status=status.HTTP_409_CONFLICT,
            )
        job.status = Job.Status.PUBLISHED
        if job.published_at is None:
            job.published_at = timezone.now()
        job.save(update_fields=["status", "published_at", "updated_at"])
        return Response(JobSerializer(job).data)

    @action(detail=True, methods=["post"])
    def unpublish(self, request, pk=None):
        job = self.get_object()
        job.status = Job.Status.DRAFT
        job.save(update_fields=["status", "updated_at"])
        return Response(JobSerializer(job).data)

    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        """
        Closing stops new applications while keeping the posting and its
        application history intact -- which is why this is a status change
        and not a DELETE.
        """
        job = self.get_object()
        job.status = Job.Status.CLOSED
        job.save(update_fields=["status", "updated_at"])
        return Response(JobSerializer(job).data)
