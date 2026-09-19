from django.conf import settings
from django.db import models


class Notification(models.Model):
    """
    A generic in-app notification. `notification_type` is a plain string
    enum rather than a foreign key to some polymorphic "source" table --
    the frontend only ever needs to render (title, message, is_read) plus
    enough context in `notification_type` to pick an icon/route. Keeping it
    this simple is deliberate: Phase 0 explicitly deferred email delivery
    (Celery + a real provider) to Phase 10, and this table's shape does not
    need to change at all when that lands -- email becomes an additional
    consumer of the same "notify this user" event, not a redesign.
    """

    class NotificationType(models.TextChoices):
        APPLICATION_STATUS_CHANGED = "application_status_changed", "Application status changed"
        NEW_APPLICATION = "new_application", "New application received"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=40, choices=NotificationType.choices)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]
        indexes = [
            # The only two read patterns this table serves: "my notifications,
            # newest first" and "my UNREAD count for a badge". Both are
            # covered by one composite index rather than two separate ones.
            models.Index(fields=["recipient", "-created_at"], name="idx_notif_recipient_created"),
            models.Index(fields=["recipient", "is_read"], name="idx_notif_recipient_unread"),
        ]

    def __str__(self):
        return f"{self.notification_type} -> {self.recipient.email}"
