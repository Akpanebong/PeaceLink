from django.contrib import admin

from .models import Activity, Alert, Community, Stakeholder, TranslationCache


@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
    list_display = ("name", "county", "payam", "ethnic_group", "trust_score", "is_active")
    list_filter = ("county", "ethnic_group", "is_active")
    search_fields = ("name", "county", "payam", "boma")


@admin.register(Stakeholder)
class StakeholderAdmin(admin.ModelAdmin):
    list_display = ("name", "holder_id", "stakeholder_type", "designation", "organization", "email", "phone", "active")
    list_filter = ("stakeholder_type", "active")
    search_fields = ("name", "designation", "organization", "email", "phone")


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ("title", "level", "community", "assigned_to", "is_read", "created_at")
    list_filter = ("level", "is_read")


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("verb", "detail", "actor", "happened_at")
    list_filter = ("accent",)


@admin.register(TranslationCache)
class TranslationCacheAdmin(admin.ModelAdmin):
    list_display = ("target_language", "source_language", "provider", "updated_at")
    list_filter = ("target_language", "provider")
    search_fields = ("source_text", "translated_text")
    readonly_fields = ("source_hash", "created_at", "updated_at")
