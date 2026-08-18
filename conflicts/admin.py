from django.contrib import admin

from .models import CaseUpdate, ConflictCase, Referral


class CaseUpdateInline(admin.TabularInline):
    model = CaseUpdate
    extra = 0


class ReferralInline(admin.TabularInline):
    model = Referral
    extra = 0


@admin.register(ConflictCase)
class ConflictCaseAdmin(admin.ModelAdmin):
    list_display = ("case_id", "conflict_type", "community_a", "community_b", "severity", "stage", "assigned_node")
    list_filter = ("conflict_type", "severity", "stage")
    search_fields = ("case_id", "reporter_name", "description", "community_a__name", "community_b__name")
    inlines = [CaseUpdateInline, ReferralInline]
