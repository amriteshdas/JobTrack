from django.db.models import Count, Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.core.permissions import IsCompanyMember, IsCompanyOwner, IsEmployer
from apps.jobs.models import Job
from apps.profiles.models import EmployerProfile

from .models import Company, CompanyMembership
from .serializers import (
    AddMemberSerializer,
    CompanyMembershipSerializer,
    CompanySerializer,
)


class CompanyViewSet(viewsets.ModelViewSet):
    """
    Public read, member-only write.

    Company pages are part of the public marketplace, so list/retrieve are
    open. Everything that mutates requires employer role AND membership of
    that specific company.
    """

    serializer_class = CompanySerializer
    lookup_field = "slug"

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["industry", "company_size", "location"]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "founded_year"]

    def get_queryset(self):
        # annotate() computes the open-jobs count in the same SQL query.
        # Without it, serializing N companies would fire N extra COUNT
        # queries -- the classic N+1 problem.
        # order_by() is explicit rather than relying on Meta.ordering:
        # annotate() can clear the default ordering, and an unordered
        # queryset makes pagination non-deterministic -- the same row can
        # appear on page 1 and page 2, or never appear at all.
        return Company.objects.annotate(
            open_jobs_count=Count(
                "jobs", filter=Q(jobs__status=Job.Status.PUBLISHED), distinct=True
            )
        ).order_by("name", "id")

    def get_permissions(self):
        if self.action in ("list", "retrieve", "jobs"):
            return [AllowAny()]
        if self.action == "create":
            return [IsAuthenticated(), IsEmployer()]
        if self.action in ("members", "add_member", "remove_member"):
            return [IsAuthenticated(), IsEmployer(), IsCompanyOwner()]
        return [IsAuthenticated(), IsEmployer(), IsCompanyMember()]

    def perform_create(self, serializer):
        profile, _ = EmployerProfile.objects.get_or_create(user=self.request.user)
        company = serializer.save()
        # Whoever creates a company becomes its owner. Without this the
        # creator would immediately be locked out of their own company,
        # since every write path requires a membership row.
        CompanyMembership.objects.create(
            company=company,
            employer_profile=profile,
            membership_role=CompanyMembership.MembershipRole.OWNER,
        )

    @action(detail=True, methods=["get"])
    def jobs(self, request, slug=None):
        """
        GET /api/companies/{slug}/jobs/ -- the company's published jobs.

        A separate action rather than nesting jobs inside CompanySerializer:
        the company detail page and the company's job list are fetched at
        different times and cached differently in a real frontend, and a
        company with hundreds of postings would otherwise bloat every
        single company detail response whether or not the client wants the
        job list right now.
        """
        company = self.get_object()
        jobs = (
            Job.objects.select_related("company")
            .prefetch_related("skills")
            .filter(company=company, status=Job.Status.PUBLISHED)
            .order_by("-published_at")
        )
        from apps.jobs.serializers import JobSerializer

        page = self.paginate_queryset(jobs)
        if page is not None:
            return self.get_paginated_response(JobSerializer(page, many=True).data)
        return Response(JobSerializer(jobs, many=True).data)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated, IsEmployer])
    def mine(self, request):
        """GET /api/companies/mine/ -- companies this employer belongs to."""
        profile = getattr(request.user, "employer_profile", None)
        if profile is None:
            return Response([])
        qs = self.get_queryset().filter(memberships__employer_profile=profile)
        return Response(self.get_serializer(qs, many=True).data)

    @action(detail=True, methods=["get"])
    def members(self, request, slug=None):
        company = self.get_object()  # triggers IsCompanyOwner object check
        qs = company.memberships.select_related("employer_profile__user")
        return Response(CompanyMembershipSerializer(qs, many=True).data)

    @action(detail=True, methods=["post"], url_path="members/add")
    def add_member(self, request, slug=None):
        company = self.get_object()
        serializer = AddMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        profile = EmployerProfile.objects.get(
            user__email=serializer.validated_data["email"]
        )
        membership, created = CompanyMembership.objects.get_or_create(
            company=company,
            employer_profile=profile,
            defaults={"membership_role": serializer.validated_data["membership_role"]},
        )
        if not created:
            # 409 Conflict: the request was well-formed and authorized, but
            # conflicts with existing state. More precise than a generic 400.
            return Response(
                {"detail": "This employer is already a member of the company."},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(
            CompanyMembershipSerializer(membership).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["delete"], url_path="members/(?P<membership_id>[^/.]+)")
    def remove_member(self, request, slug=None, membership_id=None):
        company = self.get_object()
        membership = company.memberships.filter(pk=membership_id).first()
        if membership is None:
            return Response(
                {"detail": "Membership not found."}, status=status.HTTP_404_NOT_FOUND
            )

        # Guard against a company being orphaned with no one able to manage it.
        if (
            membership.membership_role == CompanyMembership.MembershipRole.OWNER
            and company.memberships.filter(
                membership_role=CompanyMembership.MembershipRole.OWNER
            ).count() == 1
        ):
            return Response(
                {"detail": "Cannot remove the only owner of a company."},
                status=status.HTTP_409_CONFLICT,
            )

        membership.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
