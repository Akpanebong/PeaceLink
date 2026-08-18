from django.contrib import admin

from .models import Agreement, AgreementNotice


class AgreementNoticeInline(admin.TabularInline):
    model = AgreementNotice
    extra = 0


@admin.register(Agreement)
class AgreementAdmin(admin.ModelAdmin):
    list_display = ("agreement_id", "community_a", "community_b", "status", "date_signed", "follow_up_date")
    list_filter = ("status", "date_signed")
    search_fields = ("agreement_id", "community_a__name", "community_b__name", "mediators", "escalation_contact")
    inlines = [AgreementNoticeInline]


@admin.register(AgreementNotice)
class AgreementNoticeAdmin(admin.ModelAdmin):
    list_display = ("agreement", "stakeholder", "channel", "delivery_status", "sent_at")
    list_filter = ("channel", "delivery_status")
