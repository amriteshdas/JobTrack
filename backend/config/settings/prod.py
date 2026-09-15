from .base import *  # noqa: F401,F403

DEBUG = False

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")  # noqa: F405 (env comes from base.py's `import *`)

# Standard production hardening. These are all no-ops locally and only
# matter once the app is actually served over HTTPS by the host platform.
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 7  # 1 week to start; raise once confirmed stable
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
