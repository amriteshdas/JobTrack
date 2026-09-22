"""
Root URL configuration.

Routes are grouped by app, each included via that app's own urls.py.
The one exception is a handful of endpoints (saved-jobs, apply, applicants,
interviews) that live under apps.applications/apps.interviews but sit at
the API root rather than a per-app prefix, because their URLs read more
naturally as /api/jobs/{id}/apply/ than as /api/applications/jobs/{id}/apply/.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

from apps.core.views import health_check

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health_check, name='health-check'),
    path('api/auth/', include('apps.users.urls')),
    path('api/profiles/', include('apps.profiles.urls')),
    path('api/companies/', include('apps.companies.urls')),
    path('api/jobs/', include('apps.jobs.urls')),
    path('api/', include('apps.applications.urls')),
    path('api/', include('apps.interviews.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
    path('api/dashboard/', include('apps.dashboard.urls')),

    # API documentation. schema/ serves the raw OpenAPI 3 spec (JSON);
    # docs/ and redoc/ are two different UIs over the same spec -- Swagger
    # UI is better for trying requests interactively (has an Authorize
    # button for the JWT), Redoc is better for reading as a reference doc.
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

if settings.DEBUG:
    # Dev only. In production a real web server or object storage serves media.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
