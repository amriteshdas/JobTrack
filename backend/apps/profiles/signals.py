from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import EmployerProfile, JobSeekerProfile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_role_profile(sender, instance, created, **kwargs):
    """
    Auto-create the correct profile row based on role, for every user
    creation path (API registration, createsuperuser, admin, fixtures,
    data migrations) -- not just the one registration view we happened to
    think about when writing this.

    The tradeoff, stated honestly: signals are implicit. Someone reading
    the registration view will not see this happen. That cost is justified
    here because the rule is a simple, universal invariant -- every user
    has exactly one profile matching their role -- not business logic that
    varies by call site.
    """
    if not created:
        return
    if instance.role == instance.Role.EMPLOYER:
        EmployerProfile.objects.get_or_create(user=instance)
    elif instance.role == instance.Role.JOB_SEEKER:
        JobSeekerProfile.objects.get_or_create(user=instance)
