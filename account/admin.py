from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(UserAdmin):
    list_display = ("username", "email", "phone", "role", "community", "is_staff", "is_active")
    list_filter = ("role", "preferred_language", "is_staff", "is_active")
    search_fields = ("username", "email", "phone", "first_name", "last_name", "organization")
    fieldsets = UserAdmin.fieldsets + (
        (
            "PeaceLink profile",
            {
                "fields": (
                    "role",
                    "phone",
                    "community",
                    "organization",
                    "designation",
                    "preferred_language",
                    "trust_score",
                    "ussd_identifier",
                )
            },
        ),
    )
