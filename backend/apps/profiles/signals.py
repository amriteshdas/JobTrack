from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import EmployerProfile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_employer_profile(sender, instance, created, **kwargs):
    """
    Auto-create the profile row when an employer registers.

    Why a signal rather than doing this inside RegisterSerializer.create():
    users can also be created by `createsuperuser`, the Django admin, a data
    migration, or a test fixture. Putting the rule in a signal means it
    holds for every creation path, not just the one API endpoint we happened
    to think about.

    The tradeoff, stated honestly: signals are implicit. Someone reading the
    registration view will not see this happen. That is a real readability
    cost, and for more complex logic an explicit service function called
    from each entry point is usually the better choice. It is justified here
    because the rule is a simple, universal invariant: an employer always
    has exactly one profile.
    """
    if not created:
        return
    if instance.role == instance.Role.EMPLOYER:
        EmployerProfile.objects.get_or_create(user=instance)
