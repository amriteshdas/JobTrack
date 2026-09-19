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


class Application(models.Model):
    """
    A job seeker's application to a specific job.

    Status is a linear-ish workflow (Applied -> Under Review -> Shortlisted
    -> Interview -> Selected, with Rejected/Withdrawn as exits at any
    point). Modeled as a single CharField with choices, not a separate
    ApplicationStatusHistory table -- Phase 0 did not ask for a full audit
    trail of every transition, only the current status, so adding that
    table now would be speculative complexity. If "show me the history of
    this application" becomes a real requirement, that is a additive
    migration away, not a redesign.
    """

    class Status(models.TextChoices):
        APPLIED = "applied", "Applied"
        UNDER_REVIEW = "under_review", "Under Review"
        SHORTLISTED = "shortlisted", "Shortlisted"
        INTERVIEW = "interview", "Interview"
        SELECTED = "selected", "Selected"
        REJECTED = "rejected", "Rejected"
        WITHDRAWN = "withdrawn", "Withdrawn"

    # Transitions an employer may apply via the status-change endpoint.
    # WITHDRAWN is deliberately absent -- only the applicant can withdraw
    # their own application (a separate, dedicated endpoint), and an
    # employer moving an application back to APPLIED is not a real-world
    # action either.
    EMPLOYER_ALLOWED_STATUSES = {
        Status.UNDER_REVIEW,
        Status.SHORTLISTED,
        Status.INTERVIEW,
        Status.SELECTED,
        Status.REJECTED,
    }

    job = models.ForeignKey(
        "jobs.Job", on_delete=models.CASCADE, related_name="applications"
    )
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="applications"
    )

    # Snapshotted at application time, not a live FK to the seeker's current
    # profile resume. If the candidate replaces their resume next week, the
    # employer reviewing THIS application should keep seeing the document
    # that was actually submitted -- exactly like a real hiring pipeline.
    resume = models.FileField(upload_to="application_resumes/")
    cover_letter = models.TextField(blank=True)

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.APPLIED
    )

    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "applications"
        ordering = ["-applied_at"]
        constraints = [
            # A job seeker cannot apply to the same job twice. Enforced at
            # the DATABASE level for the same concurrency reason as
            # SavedJob and CompanyMembership: a double-submitted form under
            # a race condition cannot create two rows even if the
            # application-level check (below, in the view) somehow raced.
            models.UniqueConstraint(fields=["job", "applicant"], name="uniq_application"),
        ]
        indexes = [
            # "My applications" (seeker) and "applicants for this job"
            # (employer) are the two read patterns this table exists to
            # serve; each gets its own index rather than relying on the FK's
            # default index alone, since both filter AND sort by these pairs.
            models.Index(fields=["applicant", "-applied_at"], name="idx_app_applicant"),
            models.Index(fields=["job", "status"], name="idx_app_job_status"),
        ]

    def __str__(self):
        return f"{self.applicant.email} -> {self.job.title} ({self.status})"
