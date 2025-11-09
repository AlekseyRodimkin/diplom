from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LogoutView
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import TemplateView, CreateView
from django.contrib.auth import authenticate, login, logout


class AppLogoutView(LogoutView):
    next_page = reverse_lazy("accounts:login")


class RegisterView(CreateView):
    form_class = UserCreationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy("warehouse:base")

    def form_valid(self, form):
        response = super().form_valid(form)
        # Profile.objects.create(user=self.object) or signal
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password1")
        user = authenticate(self.request, username=username, password=password)
        login(request=self.request, user=user)
        return response
