from .models import Notification


def notify(recipient, notification_type, title, message):
    """
    The one place a Notification row gets created, called from wherever an
    event happens (application submitted, status changed). Centralizing
    this -- rather than calling Notification.objects.create() at each call
    site -- is what will let Phase 10 add "also send an email" or "also
    push via websocket" in ONE function instead of hunting down every place
    a notification currently gets created.
    """
    return Notification.objects.create(
        recipient=recipient,
        notification_type=notification_type,
        title=title,
        message=message,
    )
