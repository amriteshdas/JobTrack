from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsEmployer, IsJobSeeker
from apps.jobs.models import Job
from apps.notifications.models import Notification
from apps.notifications.services import notify

from .models import Application, SavedJob
from .serializers import (
    ApplicationCreateSerializer,
    ApplicationSerializer,
    ApplicationStatusUpdateSerializer,
    SavedJobSerializer,
)


class SavedJobListView(APIView):
    """
    GET  /api/saved-jobs/          -- list my saved jobs
    POST /api/saved-jobs/          body: {"job": <id>}  -- save a job

    A plain APIView rather than a ViewSet: there are only two operations
    (list, create) plus a delete-by-job-id below that doesn't fit REST's
    usual /saved-jobs/{id}/ shape as cleanly (the frontend has the job id
    on hand, not the SavedJob row id). Forcing this into ModelViewSet's
    conventions would fight the shape of the actual UI interaction more
    than it would help.
    """

    permission_classes = [IsAuthenticated, IsJobSeeker]

    def get(self, request):
        # select_related/prefetch_related here for the same reason as
        # Job's own list view in Phase 4: avoid N+1 across saved jobs' company
        # and skills when serializing the nested JobSerializer.
        qs = (
            SavedJob.objects.filter(user=request.user)
            .select_related("job__company", "job__posted_by__user")
            .prefetch_related("job__skills")
        )
        return Response(SavedJobSerializer(qs, many=True).data)

    def post(self, request):
        job_id = request.data.get("job")
        job = Job.objects.filter(id=job_id).first()
        if job is None or job.status == Job.Status.DRAFT:
            # DRAFT jobs are invisible to outsiders -- same rule as
            # JobViewSet.retrieve() and ApplyToJobView (Phase 6).
            return Response({"job": "Job not found."}, status=status.HTTP_404_NOT_FOUND)

        if not job.is_open:
            # CLOSED (or past its deadline) is a real, previously-public job
            # -- not worth bookmarking further, but not a privacy concern
            # either, so this is a 400, not a 404.
            return Response(
                {"job": "This job is no longer accepting applications."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        saved, created = SavedJob.objects.get_or_create(user=request.user, job=job)
        if not created:
            return Response(
                {"detail": "Job is already saved."}, status=status.HTTP_409_CONFLICT
            )
        return Response(SavedJobSerializer(saved).data, status=status.HTTP_201_CREATED)


class SavedJobDetailView(APIView):
    """DELETE /api/saved-jobs/{job_id}/ -- unsave, keyed by JOB id, not SavedJob id."""

    permission_classes = [IsAuthenticated, IsJobSeeker]

    def delete(self, request, job_id):
        deleted, _ = SavedJob.objects.filter(user=request.user, job_id=job_id).delete()
        if not deleted:
            return Response(
                {"detail": "This job is not in your saved list."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class ApplyToJobView(APIView):
    """
    POST /api/jobs/{job_id}/apply/

    All the "can this happen" checks Phase 0 called for live here, each
    with its own status code so the frontend can show a specific message
    rather than a generic "something went wrong":
      - not authenticated                    -> 401 (handled by permission_classes)
      - not a job seeker                     -> 403 (handled by permission_classes)
      - job does not exist / is not published -> 404 (existence-leak prevention)
      - job's deadline has passed             -> 400
      - already applied                       -> 409
    """

    permission_classes = [IsAuthenticated, IsJobSeeker]

    def post(self, request, job_id):
        job = Job.objects.filter(id=job_id).first()
        if job is None or job.status == Job.Status.DRAFT:
            # DRAFT jobs are invisible to outsiders (see JobViewSet.retrieve);
            # applying to one must fail the same way a lookup would.
            return Response({"detail": "Job not found."}, status=status.HTTP_404_NOT_FOUND)

        if not job.is_open:
            # Covers both CLOSED and PUBLISHED-but-past-deadline. Unlike
            # DRAFT, the job itself is real and was publicly known, so this
            # is a 400 ("can't do that"), not a 404 ("doesn't exist").
            return Response(
                {"detail": "This job is no longer accepting applications."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if Application.objects.filter(job=job, applicant=request.user).exists():
            return Response(
                {"detail": "You have already applied to this job."},
                status=status.HTTP_409_CONFLICT,
            )

        serializer = ApplicationCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        # job/applicant come from the URL and the token -- never the body.
        application = serializer.save(job=job, applicant=request.user)

        notify(
            recipient=job.posted_by.user,
            notification_type=Notification.NotificationType.NEW_APPLICATION,
            title="New application received",
            message=f"{request.user.full_name or request.user.email} applied to {job.title}.",
        )

        return Response(
            ApplicationSerializer(application, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class MyApplicationsView(APIView):
    """GET /api/applications/mine/ -- the seeker's own applications, any status."""

    permission_classes = [IsAuthenticated, IsJobSeeker]

    def get(self, request):
        qs = (
            Application.objects.filter(applicant=request.user)
            .select_related("job__company", "job__posted_by__user")
            .prefetch_related("job__skills")
        )
        return Response(ApplicationSerializer(qs, many=True, context={"request": request}).data)


class WithdrawApplicationView(APIView):
    """
    POST /api/applications/{id}/withdraw/

    Only the applicant who owns this application may withdraw it -- scoped
    by filtering on `applicant=request.user` in the lookup itself, so a
    withdraw attempt on someone else's application 404s rather than 403s
    (existence of another seeker's application to a given job is not
    something a third party should be able to confirm).
    """

    permission_classes = [IsAuthenticated, IsJobSeeker]

    def post(self, request, pk):
        application = Application.objects.filter(pk=pk, applicant=request.user).first()
        if application is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        if application.status == Application.Status.WITHDRAWN:
            return Response(
                {"detail": "This application has already been withdrawn."},
                status=status.HTTP_409_CONFLICT,
            )

        application.status = Application.Status.WITHDRAWN
        application.save(update_fields=["status", "updated_at"])
        return Response(ApplicationSerializer(application, context={"request": request}).data)


class JobApplicantsView(APIView):
    """
    GET /api/jobs/{job_id}/applicants/

    Object-level check done explicitly here (company membership), not via
    IsCompanyMember's has_object_permission -- that permission class expects
    DRF's get_object() to have run on the object being checked, but here the
    "object" from the URL is a Job while the data being returned is its
    Applications, so the membership check is written directly against the
    job the same way IsCompanyMember would, rather than forcing the fit.
    """

    permission_classes = [IsAuthenticated, IsEmployer]

    def get(self, request, job_id):
        job = Job.objects.filter(id=job_id).first()
        if job is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        profile = getattr(request.user, "employer_profile", None)
        is_member = profile and job.company.memberships.filter(employer_profile=profile).exists()
        if not is_member:
            # 404, matching Job.retrieve()'s principle: a competitor should
            # not be able to distinguish "this job has zero applicants" from
            # "I'm not allowed to see this job's applicants" from "this job
            # doesn't belong to me" -- all three look identical from outside.
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        qs = (
            Application.objects.filter(job=job)
            .select_related("applicant__jobseeker_profile")
            .prefetch_related("applicant__jobseeker_profile__skills")
        )
        return Response(ApplicationSerializer(qs, many=True, context={"request": request}).data)


class ApplicationStatusView(APIView):
    """
    PATCH /api/applications/{id}/status/   body: {"status": "shortlisted"}

    Object-level authorization written explicitly (via the job's company
    membership) for the same reason as JobApplicantsView above.
    """

    permission_classes = [IsAuthenticated, IsEmployer]

    def patch(self, request, pk):
        application = Application.objects.select_related(
            "job__company", "applicant"
        ).filter(pk=pk).first()
        if application is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        profile = getattr(request.user, "employer_profile", None)
        is_member = (
            profile
            and application.job.company.memberships.filter(employer_profile=profile).exists()
        )
        if not is_member:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ApplicationStatusUpdateSerializer(instance=application, data=request.data)
        serializer.is_valid(raise_exception=True)
        old_status = application.status
        serializer.save()

        # Every important status change creates a notification, per Phase 0.
        notify(
            recipient=application.applicant,
            notification_type=Notification.NotificationType.APPLICATION_STATUS_CHANGED,
            title=f"Your application status changed",
            message=(
                f"Your application for {application.job.title} moved from "
                f"{old_status.replace('_', ' ')} to {application.status.replace('_', ' ')}."
            ),
        )

        return Response(ApplicationSerializer(application, context={"request": request}).data)
