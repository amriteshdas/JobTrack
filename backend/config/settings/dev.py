from .base import *  # noqa: F401,F403

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# In dev we want the browsable API and permissive local error pages —
# both already implied by DEBUG=True and the base REST_FRAMEWORK config.
