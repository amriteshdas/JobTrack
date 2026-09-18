from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    EducationViewSet,
    EmployerProfileMeView,
    ExperienceViewSet,
    JobSeekerProfileMeView,
    UpdateSkillsView,
)

app_name = "profiles"

router = DefaultRouter()
router.register("seeker/me/education", EducationViewSet, basename="education")
router.register("seeker/me/experience", ExperienceViewSet, basename="experience")

urlpatterns = [
    path("employer/me/", EmployerProfileMeView.as_view(), name="employer-me"),
    path("seeker/me/", JobSeekerProfileMeView.as_view(), name="seeker-me"),
    path("seeker/me/skills/", UpdateSkillsView.as_view(), name="seeker-skills"),
    path("", include(router.urls)),
]
