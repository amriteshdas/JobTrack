from django.urls import path

from .views import InterviewDetailView, MyInterviewsView, ScheduleInterviewView

app_name = "interviews"

urlpatterns = [
    path("applications/<int:application_id>/interviews/", ScheduleInterviewView.as_view(), name="schedule"),
    path("interviews/mine/", MyInterviewsView.as_view(), name="mine"),
    path("interviews/<int:pk>/", InterviewDetailView.as_view(), name="detail"),
]
