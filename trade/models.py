from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.urls import reverse

from core.models import Community, TimeStampedModel


class TradeOffer(TimeStampedModel):
    class Category(models.TextChoices):
        GRAIN = "grain", "Grain"
        LIVESTOCK = "livestock", "Livestock"
        FISH = "fish", "Fish"
        CRAFTS = "crafts", "Crafts"
        SERVICES = "services", "Services"
        OTHER = "other", "Other"

    class OfferType(models.TextChoices):
        SELL = "sell", "Selling"
        BUY = "buy", "Buying"
        EXCHANGE = "exchange", "Exchange"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        MATCHED = "matched", "Matched"
        COMPLETED = "completed", "Completed"
        CLOSED = "closed", "Closed"

    image = models.ImageField(upload_to="trade_products/", blank=True, null=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="trade_offers")
    community = models.ForeignKey(Community, on_delete=models.SET_NULL, null=True, blank=True, related_name="trade_offers")
    commodity = models.CharField(max_length=140)
    category = models.CharField(max_length=24, choices=Category.choices, default=Category.GRAIN)
    quantity = models.CharField(max_length=80)
    offer_type = models.CharField(max_length=16, choices=OfferType.choices)
    location = models.CharField(max_length=160)
    contact_method = models.CharField(max_length=120, help_text="Phone, USSD callback, or voice message")
    description = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN, db_index=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.get_offer_type_display()} {self.commodity}"

    def get_absolute_url(self):
        return reverse("trade_detail", kwargs={"pk": self.pk})

    @property
    def numeric_quantity(self):
        cleaned = []
        decimal_seen = False
        for char in self.quantity:
            if char.isdigit():
                cleaned.append(char)
            elif char == "." and not decimal_seen:
                cleaned.append(char)
                decimal_seen = True
            elif cleaned:
                break
        if not cleaned:
            return None
        try:
            return Decimal("".join(cleaned))
        except InvalidOperation:
            return None

    @property
    def sold_quantity(self):
        return self.connections.filter(accepted=True).aggregate(total=Sum("quantity_sold"))["total"] or 0

    @property
    def remaining_quantity(self):
        total = self.numeric_quantity
        if total is None:
            return None
        remaining = total - self.sold_quantity
        return max(remaining, Decimal("0"))

    @property
    def remaining_quantity_display(self):
        remaining = self.remaining_quantity
        if remaining is None:
            return "Text quantity"
        return remaining

    @property
    def is_sold_out(self):
        remaining = self.remaining_quantity
        return remaining is not None and remaining <= 0

    def sync_sales_status(self, save=True):
        remaining = self.remaining_quantity
        if remaining is not None and remaining <= 0:
            self.status = self.Status.COMPLETED
        elif self.connections.exists():
            self.status = self.Status.MATCHED
        else:
            self.status = self.Status.OPEN
        if save:
            self.save(update_fields=["status", "updated_at"])
        return self.status


class TradeConnection(TimeStampedModel):
    offer = models.ForeignKey(TradeOffer, on_delete=models.CASCADE, related_name="connections")
    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="trade_connections")
    message = models.TextField(blank=True)
    accepted = models.BooleanField(default=False)
    quantity_sold = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        unique_together = ("offer", "requester")
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.requester} -> {self.offer}"


class TradeLike(TimeStampedModel):
    offer = models.ForeignKey(TradeOffer, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="trade_likes")

    class Meta:
        unique_together = ("offer", "user")
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.user} likes {self.offer}"
