from django.contrib.auth.views import LoginView
from django.urls import path

from .views import base

app_name = "warehouse"

urlpatterns = [
    path("", base, name="base"),
]
