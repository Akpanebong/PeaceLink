from django.contrib import admin

from .models import TradeConnection, TradeLike, TradeOffer


class TradeConnectionInline(admin.TabularInline):
    model = TradeConnection
    readonly_fields = ("requester_phone", "requester_email")
    fields = ("requester", "requester_phone", "requester_email", "message", "accepted", "quantity_sold")
    extra = 0

    @admin.display(description="Phone")
    def requester_phone(self, obj):
        return obj.requester.phone if obj.pk else ""

    @admin.display(description="Email")
    def requester_email(self, obj):
        return obj.requester.email if obj.pk else ""


@admin.register(TradeOffer)
class TradeOfferAdmin(admin.ModelAdmin):
    list_display = ("commodity", "offer_type", "category", "quantity", "community", "status", "created_at")
    list_filter = ("offer_type", "category", "status")
    search_fields = ("commodity", "location", "community__name", "owner__username")
    inlines = [TradeConnectionInline]


@admin.register(TradeConnection)
class TradeConnectionAdmin(admin.ModelAdmin):
    list_display = ("offer", "requester", "requester_phone", "requester_email", "accepted", "quantity_sold", "created_at")
    list_filter = ("accepted",)

    @admin.display(description="Phone")
    def requester_phone(self, obj):
        return obj.requester.phone

    @admin.display(description="Email")
    def requester_email(self, obj):
        return obj.requester.email


@admin.register(TradeLike)
class TradeLikeAdmin(admin.ModelAdmin):
    list_display = ("offer", "user", "created_at")
    search_fields = ("offer__commodity", "user__username", "user__email", "user__phone")
