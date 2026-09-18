from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.core.permissions import IsCompanyMember, IsEmployer

from .filters import JobFilter
from .models import Job
from .serializers import JobSerializer, JobWriteSerializer


class JobViewSet(viewsets.ModelViewSet):
    """
    Job CRUD plus the public search/filter/sort/paginate surface.

    Everything under `GET /api/jobs/?...` is ONE endpoint. Query params
    compose freely:
        ?search=python&location=Kolkata&work_mode=remote&ordering=-salary_min
    which is exactly the "design cleanly rather than separate endpoints for
    every filter" requirement from Phase 0, and is what django-filter,
    SearchFilter and OrderingFilter give us together for almost no code.
    """

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = JobFilter

    # SearchFilter does a case-insensitive LIKE '%term%' across these fields
    # -- it is NOT full-text search (no ranking, no stemming, no relevance
    # score) and it cannot use a normal B-tree index efficiently on large
    # text columns. That upgrade path (Postgres GIN + tsvector) is exactly
    # what Phase 0 flagged as a Phase-9 optimization once real query volume
    # justifies it. For MVP scale this is the right amount of engineering.
    search_fields = ["title", "description", "location", "company__name"]

    # Whitelisted explicitly -- OrderingFilter with no `ordering_fields` will
    # accept ANY model field name, including ones on related tables reachable
    # through '__', which is both a surprising API surface and a way for a
    # client to force an expensive, unindexed sort.
    ordering_fields = ["created_at", "published_at", "salary_min", "experience_required"]
    ordering = ["-published_at"]  # default: newest first

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
