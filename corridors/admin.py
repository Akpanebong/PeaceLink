from django.contrib import admin

from .models import CorridorNotice, CorridorResponse, CorridorRoute


@admin.register(CorridorRoute)
class CorridorRouteAdmin(admin.ModelAdmin):
    list_display = ("name", "origin", "destination", "risk_level", "active")
    list_filter = ("risk_level", "active")


class CorridorResponseInline(admin.TabularInline):
    model = CorridorResponse
    fields = ("responder", "response_type", "notes", "negotiation_outcome", "created_at")
    readonly_fields = ("created_at",)
    extra = 0


@admin.register(CorridorResponse)
class CorridorResponseAdmin(admin.ModelAdmin):
    list_display = ("notice", "responder", "response_type", "created_at")
    list_filter = ("response_type", "created_at")
    search_fields = ("notice__herd_group", "responder__username", "notes", "negotiation_outcome")


@admin.register(CorridorNotice)
class CorridorNoticeAdmin(admin.ModelAdmin):
    list_display = ("herd_group", "route", "cattle_count", "arrival_date", "status")
    list_filter = ("status", "arrival_date")
    inlines = [CorridorResponseInline]
