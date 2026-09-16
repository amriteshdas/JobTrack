from django.urls import path

from .views import EmployerProfileMeView

app_name = "profiles"

urlpatterns = [
    path("employer/me/", EmployerProfileMeView.as_view(), name="employer-me"),
]
