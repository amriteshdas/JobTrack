from datetime import timedelta

from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.applications.models import Application, SavedJob
from apps.core.permissions import IsEmployer, IsJobSeeker
from apps.jobs.models import Job
from apps.jobs.serializers import JobSerializer

# Statuses that count as "still active" from the seeker's point of view --
# used to decide which recent applications are worth surfacing prominently.
ACTIVE_STATUSES = [
    Application.Status.APPLIED,
    Application.Status.UNDER_REVIEW,
    Application.Status.SHORTLISTED,
    Application.Status.INTERVIEW,
]


class SeekerDashboardView(APIView):
    """
    GET /api/dashboard/seeker/

    One response, several aggregates -- the frontend renders this as stat
    cards plus two short lists, in a single request rather than five. Every
    count here is a database COUNT/annotate, not len(queryset), so the
    query cost does not grow with how many applications a seeker has built
    up over time.
    """

    permission_classes = [IsAuthenticated, IsJobSeeker]

    def get(self, request):
        user = request.user
        applications = Application.objects.filter(applicant=user)

        status_counts = dict(
            applications.values("status").annotate(count=Count("id")).values_list(
                "status", "count"
            )
        )

        recent_applications = (
            applications.select_related("job__company")
            .prefetch_related("job__skills")
            .order_by("-applied_at")[:5]
        )

        recommended_jobs = self._recommended_jobs(user)

        return Response(
            {
                "stats": {
                    "total_applications": applications.count(),
                    "under_review": status_counts.get(Application.Status.UNDER_REVIEW, 0),
                    "shortlisted": status_counts.get(Application.Status.SHORTLISTED, 0),
                    "interview": status_counts.get(Application.Status.INTERVIEW, 0),
                    "selected": status_counts.get(Application.Status.SELECTED, 0),
                    "saved_jobs": SavedJob.objects.filter(user=user).count(),
                },
                "recent_applications": _application_summaries(recent_applications),
                "recommended_jobs": JobSerializer(
                    recommended_jobs, many=True, context={"request": request}
                ).data,
                # Interviews arrive in Phase 8. Surfaced as an explicit empty
                # list now (not omitted) so the frontend's "Upcoming
                # interviews" section already has the right shape to render
                # against once that model exists -- adding real data later
                # is then a backend-only change.
                "upcoming_interviews": [],
            }
        )

    @staticmethod
    def _recommended_jobs(user):
        """
        Skill-overlap heuristic, not AI matching -- that is explicitly
        Phase 10 per the roadmap. "Recommended" here means: published jobs
        sharing at least one skill with the seeker's profile, that they
        have not already applied to, newest first. If the seeker has no
        skills yet (or none match), fall back to recent published jobs so
        the section is never empty for a new account.
        """
        profile = getattr(user, "jobseeker_profile", None)
        applied_job_ids = Application.objects.filter(applicant=user).values_list(
            "job_id", flat=True
        )
        base = (
            Job.objects.filter(status=Job.Status.PUBLISHED)
            .exclude(id__in=applied_job_ids)
            .select_related("company")
            .prefetch_related("skills")
        )

        if profile is not None:
            skill_ids = profile.skills.values_list("id", flat=True)
            if skill_ids:
                matched = base.filter(skills__in=skill_ids).distinct().order_by("-published_at")[:5]
                if matched:
                    return matched

        return base.order_by("-published_at")[:5]


class EmployerDashboardView(APIView):
    """
    GET /api/dashboard/employer/

    Everything scoped to companies this employer is a MEMBER of -- the same
    membership check used everywhere else since Phase 3, just applied to
    aggregate queries instead of single-row lookups.
    """

    permission_classes = [IsAuthenticated, IsEmployer]

    def get(self, request):
        profile = getattr(request.user, "employer_profile", None)
        if profile is None:
            return Response(_empty_employer_dashboard())

        jobs = Job.objects.filter(company__memberships__employer_profile=profile).distinct()
        applications = Application.objects.filter(job__in=jobs)

        status_counts = dict(
            applications.values("status").annotate(count=Count("id")).values_list(
                "status", "count"
            )
        )

        recent_jobs = jobs.select_related("company").order_by("-created_at")[:5]

        applications_per_job = list(
            jobs.annotate(
                application_count=Count("applications", filter=~Q(applications__status="withdrawn"))
            )
            .order_by("-application_count")[:8]
            .values("id", "title", "application_count")
        )

        applications_over_time = list(
            applications.filter(applied_at__gte=timezone.now() - timedelta(days=30))
            .annotate(day=TruncDate("applied_at"))
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )

        return Response(
            {
                "stats": {
                    "total_jobs": jobs.count(),
                    "active_jobs": jobs.filter(status=Job.Status.PUBLISHED).count(),
                    "applications_received": applications.count(),
                    "shortlisted": status_counts.get(Application.Status.SHORTLISTED, 0),
                    # Interviews arrive in Phase 8; see SeekerDashboardView's
                    # note on the same tradeoff.
                    "interviews_scheduled": 0,
                },
                "recently_posted_jobs": JobSerializer(
                    recent_jobs, many=True, context={"request": request}
                ).data,
                "charts": {
                    "applications_per_job": [
                        {"job_id": j["id"], "title": j["title"], "count": j["application_count"]}
                        for j in applications_per_job
                    ],
                    "status_distribution": [
                        {"status": s, "count": c} for s, c in status_counts.items()
                    ],
                    "applications_over_time": [
                        {"date": row["day"].isoformat(), "count": row["count"]}
                        for row in applications_over_time
                    ],
                },
            }
        )


def _application_summaries(applications):
    """
    A deliberately small, flat shape for the "recent applications" list --
    not the full ApplicationSerializer (which nests the entire Job and
    Applicant). The dashboard card only ever renders a title, company, and
    status pill; sending the full nested shape here would cost real payload
    size for fields the page never reads.
    """
    return [
        {
            "id": a.id,
            "job_id": a.job_id,
            "job_title": a.job.title,
            "company_name": a.job.company.name,
            "status": a.status,
            "applied_at": a.applied_at,
        }
        for a in applications
    ]


def _empty_employer_dashboard():
    return {
        "stats": {
            "total_jobs": 0,
            "active_jobs": 0,
            "applications_received": 0,
            "shortlisted": 0,
            "interviews_scheduled": 0,
        },
        "recently_posted_jobs": [],
        "charts": {
            "applications_per_job": [],
            "status_distribution": [],
            "applications_over_time": [],
        },
    }
