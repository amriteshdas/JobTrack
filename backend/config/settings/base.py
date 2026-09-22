"""
Base settings — shared between dev and prod.

Why split settings into base/dev/prod instead of one settings.py:
A single settings.py inevitably grows an if/else ladder on DEBUG, or worse,
developers hand-edit it before deploying and forget to edit it back. Three
files with dev/prod importing from base makes the difference between
environments explicit and reviewable in a diff, without duplicating the
90% that's identical (installed apps, REST framework config, etc.).
"""

from pathlib import Path
from datetime import timedelta
import environ

# ---------------------------------------------------------------------------
# Paths & environment loading
# ---------------------------------------------------------------------------

# BASE_DIR = backend/ (three levels up from this file: settings/base.py -> settings -> config -> backend)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False),
)

# Reads backend/.env if present. In production, real environment variables
# (set by the hosting platform) take precedence over anything in a .env file.
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
]

# Every app lives under apps.<name> per the Phase 0 app structure.
LOCAL_APPS = [
    "apps.core",
    "apps.users",
    "apps.profiles",
    "apps.companies",
    "apps.jobs",
    "apps.applications",
    "apps.interviews",
    "apps.notifications",
    "apps.dashboard",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

AUTH_USER_MODEL = "users.User"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",  # must sit above CommonMiddleware
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ---------------------------------------------------------------------------
# Database — PostgreSQL only, credentials always from the environment
# ---------------------------------------------------------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DATABASE_NAME"),
        "USER": env("DATABASE_USER"),
        "PASSWORD": env("DATABASE_PASSWORD"),
        "HOST": env("DATABASE_HOST", default="localhost"),
        "PORT": env("DATABASE_PORT", default="5432"),
    }
}

# ---------------------------------------------------------------------------
# Password validation (default Django validators are fine for the MVP)
# ---------------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# I18N / static / media
# ---------------------------------------------------------------------------

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Cache -- backs the auth-endpoint rate limiting below (ScopedRateThrottle
# stores its request counts here).
# ---------------------------------------------------------------------------
# LocMemCache is IN-PROCESS: with more than one worker process (any real
# deployment), each worker has its own independent counter, so the "10/min"
# limit actually becomes "10/min per worker" -- a real gap, not a
# theoretical one. Fixing it needs a cache shared across processes (Redis),
# which Phase 0 deliberately deferred to Phase 10. Documented here rather
# than silently shipping a limit that looks stricter than it is.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------
# Authentication classes are configured now (SimpleJWT) so the setting exists
# and is correct, but no login/register views are implemented until Phase 2 —
# this only wires the JWT *parser*, it doesn't create any way to obtain a token yet.

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "EXCEPTION_HANDLER": "apps.core.exceptions.custom_exception_handler",
    # ScopedRateThrottle is a no-op for any view that doesn't set
    # `throttle_scope`, so registering it globally here does NOT rate-limit
    # the whole API -- only the specific views that opt in (register/login,
    # see their throttle_scope = "auth"). Blanket throttling on every
    # endpoint is deliberately out of scope for the MVP: without real
    # traffic data, picking sensible per-endpoint limits is guesswork, and
    # guessed limits are as likely to block legitimate users as attackers.
    # Auth endpoints are the one place a conservative limit is justified
    # regardless of traffic data, because credential-stuffing risk doesn't
    # depend on how popular the site is.
    "DEFAULT_THROTTLE_CLASSES": ("rest_framework.throttling.ScopedRateThrottle",),
    "DEFAULT_THROTTLE_RATES": {
        "auth": "10/min",
    },
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "JobTrack API",
    "DESCRIPTION": (
        "REST API for JobTrack, a two-sided job marketplace. "
        "Endpoints are grouped by app below; each requires the auth/role "
        "noted in its description. Authenticate via /api/auth/login/, "
        "then use the Authorize button with `Bearer <access_token>`."
    ),
    "VERSION": "1.0.0",
    # Without this, drf-spectacular includes its own schema/docs endpoints
    # in the generated schema -- meta-documentation nobody needs.
    "SERVE_INCLUDE_SCHEMA": False,
    # Keeps generated operationIds readable (e.g. "jobs_list" rather than
    # a path-derived hash) across the ViewSets and APIViews mixed
    # throughout this project.
    "COMPONENT_SPLIT_REQUEST": True,
    # Job, Application, and Interview each have their own `status` field
    # with entirely different choices. Without this, drf-spectacular can't
    # tell the three apart (they're all just fields named "status") and
    # auto-generates hash-suffixed names like "Status324Enum" in the
    # schema -- functionally fine, but useless for a human reading the docs.
    "ENUM_NAME_OVERRIDES": {
        "JobStatusEnum": "apps.jobs.models.Job.Status",
        "ApplicationStatusEnum": "apps.applications.models.Application.Status",
        "InterviewStatusEnum": "apps.interviews.models.Interview.Status",
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# ---------------------------------------------------------------------------
# CORS — local frontend only; tightened further in prod.py
# ---------------------------------------------------------------------------

CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=["http://localhost:5173"],
)
