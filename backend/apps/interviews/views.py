from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.applications.models import Application
from apps.core.permissions import IsEmployer
from apps.notifications.models import Notification
from apps.notifications.services import notify

from .models import Interview
from .serializers import InterviewCreateSerializer, InterviewSerializer, InterviewUpdateSerializer


def _is_company_member(user, job):
    profile = getattr(user, "employer_profile", None)
    return bool(profile and job.company.memberships.filter(employer_profile=profile).exists())


class ScheduleInterviewView(APIView):
    """
    POST /api/applications/{id}/interviews/

    Scheduling an interview also moves the application to INTERVIEW status
    if it isn't already there -- this mirrors the real workflow Phase 0
    described (shortlist -> interview -> selected) rather than requiring
    the employer to separately remember to update status after booking.
    An application already further along (selected/rejected) is left
    alone; only a "still in progress" application gets auto-advanced.
    """

    permission_classes = [IsAuthenticated, IsEmployer]

    def post(self, request, application_id):
        application = Application.objects.select_related(
            "job__company", "applicant"
        ).filter(pk=application_id).first()
        if application is None or not _is_company_member(request.user, application.job):
            # Same existence-disclosure principle as every object-level
            # check since Phase 3: a competitor should not be able to tell
            # "doesn't exist" from "not yours" from the response.
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        if application.status == Application.Status.WITHDRAWN:
            return Response(
                {"detail": "Cannot schedule an interview for a withdrawn application."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = InterviewCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        interview = serializer.save(application=application, scheduled_by=request.user)

        if application.status in (
            Application.Status.APPLIED,
            Application.Status.UNDER_REVIEW,
            Application.Status.SHORTLISTED,
        ):
            application.status = Application.Status.INTERVIEW
            application.save(update_fields=["status", "updated_at"])

        notify(
            recipient=application.applicant,
            notification_type=Notification.NotificationType.APPLICATION_STATUS_CHANGED,
            title="Interview scheduled",
            message=(
                f"An interview for {application.job.title} has been scheduled for "
                f"{interview.scheduled_at.strftime('%b %d, %Y at %I:%M %p')}."
            ),
        )

        return Response(
            InterviewSerializer(interview, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class MyInterviewsView(APIView):
    """
    GET /api/interviews/mine/

    One endpoint for both roles, branching on request.user.role, rather
    than two separate URLs -- the response shape (InterviewSerializer) is
    identical either way; only the filter differs. This mirrors
    ApplicationSerializer's "same row, two audiences" pattern from Phase 6.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        base = Interview.objects.select_related(
            "application__job__company", "application__applicant__jobseeker_profile"
        )

        if user.is_job_seeker:
            qs = base.filter(application__applicant=user)
        elif user.is_employer:
            profile = getattr(user, "employer_profile", None)
            if profile is None:
                return Response([])
            qs = base.filter(
                application__job__company__memberships__employer_profile=profile
            ).distinct()
        else:
            qs = Interview.objects.none()

        return Response(InterviewSerializer(qs, many=True, context={"request": request}).data)


class InterviewDetailView(APIView):
    """PATCH /api/interviews/{id}/ -- reschedule, add notes, or change status."""

    permission_classes = [IsAuthenticated, IsEmployer]

    def patch(self, request, pk):
        interview = Interview.objects.select_related("application__job__company").filter(pk=pk).first()
        if interview is None or not _is_company_member(request.user, interview.application.job):
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = InterviewUpdateSerializer(
            instance=interview, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(InterviewSerializer(interview, context={"request": request}).data)
