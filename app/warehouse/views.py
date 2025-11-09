from django.contrib.auth.views import LogoutView
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy


def base(request: HttpRequest) -> HttpResponse:
    return render(request, "warehouse/base.html")
