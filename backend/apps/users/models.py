from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    Placeholder custom user model for Phase 1.

    Why this exists already, in Phase 1, when authentication itself is a
    Phase 2 feature:

    Django writes AUTH_USER_MODEL into every app's very first migration as
    a foreign-key target (e.g. Company.employer -> settings.AUTH_USER_MODEL).
    If we start with Django's built-in `auth.User` and later switch to a
    custom model, every migration that already references the user table
    has to be rewritten — in a real project with real data this becomes a
    genuinely painful migration. Because Phase 0 already decided JobTrack
    needs a custom User (email login, `role` field), the safe move is to
    point AUTH_USER_MODEL at this model from the very first `migrate`,
    even though we are not yet adding the email-login behavior or the
    `role` field.

    Deliberately NOT added yet (this is Phase 2 work):
        - email as the USERNAME_FIELD
        - role field (seeker / employer)
        - custom manager for role-aware user creation

    For now this is intentionally just `AbstractUser` with zero changes,
    so Phase 1 stays scoped to "foundation only" as instructed.
    """

    pass
