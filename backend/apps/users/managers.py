from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    """
    Django's default UserManager hard-codes `username` as the identifying
    field. Once we switch USERNAME_FIELD to `email`, `create_user()` and
    `create_superuser()` would break, so we must supply our own manager.

    This is also the single place where we normalize email and delegate
    password hashing to `set_password()`. Nothing anywhere else in the
    codebase should ever touch `user.password` directly.
    """

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address.")

        # normalize_email lowercases only the domain part (the part after @),
        # because per RFC the local part is technically case-sensitive.
        # We additionally lowercase the whole thing below so that
        # "Alice@x.com" and "alice@x.com" can never become two accounts.
        email = self.normalize_email(email).lower()

        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # hashes via Django's configured hasher
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", self.model.Role.EMPLOYER)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)
