"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from apps.core.views import health_check

urlpatterns = [
    path('admin/', admin.site.urls),
    # Temporary Phase 1 endpoint only, to prove the API/DB/DRF stack works.
    # Real domain routes (auth/, jobs/, applications/, ...) are added
    # incrementally starting in Phase 2, each wired via its own app's urls.py
    # and included here as apps get built out.
    path('api/health/', health_check, name='health-check'),
]
