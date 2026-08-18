from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("login/", views.PeaceLinkLoginView.as_view(), name="login"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("profile/", views.profile, name="profile"),
    path("language/", views.set_language_preference, name="set_language_preference"),
    path("logout/", views.logout_view, name="logout"),
    path(
        "password/change/",
        auth_views.PasswordChangeView.as_view(
            template_name="account/password_change.html",
            extra_context={"title": "Change Password"},
        ),
        name="password_change",
    ),
    path(
        "password/change/done/",
        auth_views.PasswordChangeDoneView.as_view(template_name="account/password_change_done.html"),
        name="password_change_done",
    ),
    path(
        "password/reset/",
        auth_views.PasswordResetView.as_view(
            template_name="account/password_reset.html",
            extra_context={"title": "Reset Password"},
        ),
        name="password_reset",
    ),
    path(
        "password/reset/done/",
        auth_views.PasswordResetDoneView.as_view(template_name="account/password_reset_done.html"),
        name="password_reset_done",
    ),
    path(
        "password/reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="account/password_reset_confirm.html",
            extra_context={"title": "Set New Password"},
        ),
        name="password_reset_confirm",
    ),
    path(
        "password/reset/complete/",
        auth_views.PasswordResetCompleteView.as_view(template_name="account/password_reset_complete.html"),
        name="password_reset_complete",
    ),
]
