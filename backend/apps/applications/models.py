from django.conf import settings
from django.db import models


class SavedJob(models.Model):
    """
    A job seeker's bookmark list.

    Deliberately built now, in Phase 5, even though Application (the same
    app's other model) waits for Phase 6. SavedJob has no dependency on
    Application -- it only needs User and Job, both of which already exist
    -- and shipping it here is what lets the "Save job" button on the job
    details page (stubbed disabled since Phase 4) finally turn on.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_jobs"
    )
    job = models.ForeignKey(
        "jobs.Job", on_delete=models.CASCADE, related_name="saved_by"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "saved_jobs"
        ordering = ["-created_at"]
        constraints = [
            # Enforced in the DATABASE, not just checked in the view, so a
            # double-tapped "Save" button under concurrency cannot create
            # two rows -- the same reasoning as CompanyMembership's
            # uniqueness constraint back in Phase 3.
            models.UniqueConstraint(fields=["user", "job"], name="uniq_saved_job"),
        ]
        indexes = [
            # "Show me my saved jobs" is the only read pattern this table
            # serves; this index is exactly that query.
            models.Index(fields=["user", "-created_at"], name="idx_saved_user_created"),
        ]

    def __str__(self):
        return f"{self.user.email} saved {self.job.title}"
