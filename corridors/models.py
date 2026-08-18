from django.conf import settings
from django.db import models
from django.urls import reverse

from core.models import Community, TimeStampedModel


class CorridorRoute(TimeStampedModel):
    name = models.CharField(max_length=160)
    origin = models.ForeignKey(Community, on_delete=models.CASCADE, related_name="origin_routes")
    destination = models.ForeignKey(Community, on_delete=models.CASCADE, related_name="destination_routes")
    description = models.TextField()
    risk_level = models.CharField(
        max_length=16,
        choices=(("low", "Low"), ("medium", "Medium"), ("high", "High")),
        default="medium",
    )
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class CorridorNotice(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACKNOWLEDGED = "acknowledged", "Acknowledged"
        NEGOTIATING = "negotiating", "Negotiating"
        CLOSED = "closed", "Closed"

    route = models.ForeignKey(CorridorRoute, on_delete=models.CASCADE, related_name="notices")
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="corridor_notices")
    herd_group = models.CharField(max_length=160)
    cattle_count = models.PositiveIntegerField()
    arrival_date = models.DateField()
    message = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)

    class Meta:
        ordering = ("arrival_date", "-created_at")

    def __str__(self):
        return f"{self.herd_group} via {self.route}"

    def get_absolute_url(self):
        return reverse("corridor_detail", kwargs={"pk": self.pk})


class CorridorResponse(TimeStampedModel):
    notice = models.ForeignKey(CorridorNotice, on_delete=models.CASCADE, related_name="responses")
    responder = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="corridor_responses")
    response_type = models.CharField(
        max_length=20,
        choices=(("acknowledge", "Acknowledge"), ("negotiate", "Negotiate route")),
    )
    notes = models.TextField(blank=True)
    negotiation_outcome = models.TextField(
        blank=True,
        help_text="Final community response after route negotiation.",
    )

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.get_response_type_display()} - {self.notice}"
