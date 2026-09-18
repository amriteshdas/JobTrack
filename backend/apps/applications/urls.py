from django.urls import path

from .views import SavedJobDetailView, SavedJobListView

app_name = "applications"

urlpatterns = [
    path("saved-jobs/", SavedJobListView.as_view(), name="saved-jobs"),
    path("saved-jobs/<int:job_id>/", SavedJobDetailView.as_view(), name="saved-job-detail"),
]
