from django.contrib.auth.views import LoginView
from django.urls import path

from .views import (
    AppLogoutView, RegisterView
)

app_name = "accounts"

urlpatterns = [
    path(
        "login/",
        LoginView.as_view(
            template_name="accounts/login.html",
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path("logout/", AppLogoutView.as_view(), name="logout"),
    path("register/", RegisterView.as_view(), name="register"),
]
