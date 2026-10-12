from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView

from .forms import ProfileForm, RegistrationForm


class PeaceLinkLoginView(LoginView):
    template_name = "account/login.html"
    redirect_authenticated_user = True


class RegisterView(CreateView):
    form_class = RegistrationForm
    template_name = "account/register.html"
    success_url = reverse_lazy("login")
    extra_context = {"title": "Register for PeaceLink"}

    def form_valid(self, form):
        messages.success(self.request, "Your PeaceLink account has been created. Sign in to continue.")
        return super().form_valid(form)


class ProfileUpdateView(UpdateView):
    form_class = ProfileForm
    template_name = "account/profile.html"
    success_url = reverse_lazy("home")
    extra_context = {"title": "My PeaceLink Profile"}

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Profile updated.")
        return super().form_valid(form)


@login_required
def profile(request):
    return ProfileUpdateView.as_view()(request)


def logout_view(request):
    logout(request)
    messages.success(request, "You have been signed out.")
    return redirect("login")

