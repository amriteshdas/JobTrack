from django.urls import path

from .views import (
    ApplicationStatusView,
    ApplyToJobView,
    JobApplicantsView,
    MyApplicationsView,
    SavedJobDetailView,
    SavedJobListView,
    WithdrawApplicationView,
)

app_name = "applications"

urlpatterns = [
    path("saved-jobs/", SavedJobListView.as_view(), name="saved-jobs"),
    path("saved-jobs/<int:job_id>/", SavedJobDetailView.as_view(), name="saved-job-detail"),

    path("jobs/<int:job_id>/apply/", ApplyToJobView.as_view(), name="apply"),
    path("jobs/<int:job_id>/applicants/", JobApplicantsView.as_view(), name="applicants"),

    path("applications/mine/", MyApplicationsView.as_view(), name="mine"),
    path("applications/<int:pk>/withdraw/", WithdrawApplicationView.as_view(), name="withdraw"),
    path("applications/<int:pk>/status/", ApplicationStatusView.as_view(), name="status"),
]
