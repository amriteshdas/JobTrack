from django.urls import path

from .views import EmployerDashboardView, SeekerDashboardView

app_name = "dashboard"

urlpatterns = [
    path("seeker/", SeekerDashboardView.as_view(), name="seeker"),
    path("employer/", EmployerDashboardView.as_view(), name="employer"),
]
