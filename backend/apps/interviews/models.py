from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Interview(models.Model):
    """
    A scheduled interview against a specific Application.

    Deliberately a ForeignKey to Application, not a OneToOne -- real hiring
    pipelines have multiple rounds (phone screen, technical, onsite) against
    the same application, and Phase 0's brief never said "one interview per
    application". Modeling this as 1:many now costs nothing; modeling it as
    1:1 and migrating to 1:many later, once real rounds exist, would be a
    genuinely painful migration on a table with live data.
    """

    class InterviewType(models.TextChoices):
        PHONE = "phone", "Phone"
        VIDEO = "video", "Video"
        ONSITE = "onsite", "Onsite"

    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    application = models.ForeignKey(
        "applications.Application", on_delete=models.CASCADE, related_name="interviews"
    )
    scheduled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="interviews_scheduled"
    )

    interview_type = models.CharField(max_length=20, choices=InterviewType.choices)
    scheduled_at = models.DateTimeField()

    # Exactly one of these should be meaningfully filled, enforced in the
    # serializer (a CHECK constraint expressing "meeting_link is blank XOR
    # location is blank" is possible in Postgres but reads worse than it
    # protects -- this is a UX rule about a scheduling form, not a data
    # integrity invariant worth enforcing at the schema level).
    meeting_link = models.URLField(blank=True, help_text="For phone/video interviews.")
    location = models.CharField(max_length=255, blank=True, help_text="For onsite interviews.")

    notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.SCHEDULED
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "interviews"
        ordering = ["scheduled_at"]
        indexes = [
            # "My upcoming interviews" (both seeker and employer dashboards)
            # is the one read pattern this table exists to serve -- filter
            # by status, sort by when it happens.
            models.Index(fields=["status", "scheduled_at"], name="idx_interview_status_time"),
        ]

    def __str__(self):
        return f"{self.get_interview_type_display()} interview for application #{self.application_id}"

    def clean(self):
        if not self.meeting_link and not self.location:
            raise ValidationError(
                "Provide a meeting link (phone/video) or a location (onsite)."
            )
