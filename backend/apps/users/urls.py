from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    LoginView,
    LogoutView,
    MeView,
    RegisterView,
)

app_name = "users"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    # SimpleJWT's stock refresh view is used unchanged. With
    # ROTATE_REFRESH_TOKENS and BLACKLIST_AFTER_ROTATION enabled, each call
    # returns a NEW refresh token and blacklists the one just used, so a
    # stolen refresh token has a very short useful life.
    path("refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
]
