from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsJobSeeker
from apps.jobs.models import Job

from .models import SavedJob
from .serializers import SavedJobSerializer


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
        if job is None:
            return Response({"job": "Job not found."}, status=status.HTTP_404_NOT_FOUND)

        if job.status != Job.Status.PUBLISHED:
            # Saving a draft/closed job would leak that it exists -- same
            # visibility principle as Job.retrieve() in Phase 4.
            return Response({"job": "Job not found."}, status=status.HTTP_404_NOT_FOUND)

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
