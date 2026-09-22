import pytest


@pytest.fixture(autouse=True)
def _disable_rate_limiting_cache(settings):
    """
    ScopedRateThrottle counts requests through Django's cache framework.
    Without this, the "auth" scope's 10/min limit would trip partway
    through the test suite -- dozens of tests log in via the `auth`
    fixture, often several times each, all within the same test run and
    (by default) the same LocMemCache instance that persists across test
    cases in one process.

    Swapping in DummyCache (a cache that stores nothing and always misses)
    makes every throttle check pass, every time, without deleting or
    special-casing the throttle logic itself -- the real rate limiting
    still runs in dev/prod, this only neutralizes it for the test session.
    autouse=True because forgetting to add this fixture to a new test file
    that happens to call login several times would be exactly the kind of
    intermittent, hard-to-debug failure worth preventing by default.
    """
    settings.CACHES = {
        "default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}
    }
